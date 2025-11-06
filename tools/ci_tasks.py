"""Command-line helpers for CI and local automation.

This module provides a unified entry point for running the quality gates
referenced by the renovation master plan.  It mirrors the behaviour
described in ``docs/CI.md`` and powers the ``make lint``/``make typecheck``
/``make test`` targets as well as GitHub Actions jobs.

Example usage::

    python -m tools.ci_tasks lint
    python -m tools.ci_tasks typecheck
    python -m tools.ci_tasks test

The implementation keeps the runner intentionally small so it works in both
local developer shells and headless CI agents.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from tools import merge_conflict_scan

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUALITY_REPORT_ROOT = PROJECT_ROOT / "reports" / "quality"
PYTEST_REPORT_ROOT = PROJECT_ROOT / "reports" / "tests"
DEFAULT_LINT_TARGETS: tuple[str, ...] = ("app.py", "src", "tests", "tools")
MYPY_TARGETS_FILE = "mypy_targets.txt"
PYTEST_TARGETS_FILE = "pytest_targets.txt"
PYTEST_UNIT_TARGETS_FILE = "pytest_unit_targets.txt"
PYTEST_INTEGRATION_TARGETS_FILE = "pytest_integration_targets.txt"
PYTEST_UI_TARGETS_FILE = "pytest_ui_targets.txt"
QML_LINT_TARGETS_FILE = "qmllint_targets.txt"
MYPY_CONFIG = "mypy.ini"


class TaskError(RuntimeError):
    """Raised when a task cannot be executed successfully."""


class QualityRunRecorder:
    """Track executed commands and persist a machine-readable summary."""

    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []
        self.root_command: str | None = None
        self.started_at: datetime | None = None

    def start(self, root_command: str) -> None:
        self.entries = []
        self.root_command = root_command
        self.started_at = datetime.now(timezone.utc)

    def ensure_started(self) -> None:
        if self.started_at is None:
            self.start("direct-call")

    def record(
        self,
        *,
        name: str,
        printable_command: str,
        returncode: int,
        log_path: Path | None,
    ) -> None:
        self.ensure_started()
        entry: dict[str, object] = {
            "name": name,
            "command": printable_command,
            "returncode": returncode,
        }
        if log_path is not None:
            try:
                entry["log"] = str(log_path.relative_to(PROJECT_ROOT))
            except ValueError:
                entry["log"] = str(log_path)
        self.entries.append(entry)

    def finalize(self, success: bool) -> None:
        if self.started_at is None or not self.entries:
            return
        QUALITY_REPORT_ROOT.mkdir(parents=True, exist_ok=True)
        payload = {
            "command": self.root_command,
            "success": success,
            "started_at": self.started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "entries": self.entries,
        }
        summary_path = QUALITY_REPORT_ROOT / "verify_status.json"
        summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


RECORDER = QualityRunRecorder()


def _ensure_no_merge_conflicts() -> None:
    conflicted = merge_conflict_scan.find_conflicted_files(
        PROJECT_ROOT, merge_conflict_scan.DEFAULT_EXCLUDES
    )
    if not conflicted:
        return

    for path in conflicted:
        try:
            display = path.relative_to(PROJECT_ROOT)
        except ValueError:
            display = path
        print(f"[ci_tasks] merge conflict marker detected: {display}")
    raise TaskError(
        "Git merge conflict markers detected; resolve them before running CI tasks."
    )


def _split_env_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item for item in shlex.split(value) if item]


def _env_flag(name: str, *, default: bool) -> bool:
    """Interpret an environment variable as a boolean flag."""

    value = os.environ.get(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if not normalized:
        return default

    truthy = {"1", "true", "yes", "on"}
    falsy = {"0", "false", "no", "off"}

    if normalized in truthy:
        return True
    if normalized in falsy:
        return False

    raise TaskError(
        f"Invalid boolean value for {name}: {value!r}. "
        "Expected one of yes/no, true/false, on/off, 1/0."
    )


def _read_targets_file(relative_path: str) -> list[str]:
    path = PROJECT_ROOT / relative_path
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    targets = [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]
    return targets


def _ensure_targets_exist(targets: Iterable[str]) -> list[str]:
    valid: list[str] = []
    missing: list[str] = []
    for target in targets:
        candidate = PROJECT_ROOT / target
        if candidate.exists():
            valid.append(target)
        else:
            missing.append(target)
    if missing:
        raise TaskError(
            "One or more configured targets do not exist: " + ", ".join(missing)
        )
    return valid


@dataclass
class PytestSuite:
    """Configuration for a pytest invocation."""

    name: str
    default_targets: tuple[str, ...]
    env_var: str | None = None
    targets_file: str | None = None
    marker: str | None = None
    extra_args: tuple[str, ...] = ()

    def resolve_targets(self) -> list[str]:
        if self.env_var:
            env_targets = _split_env_list(os.environ.get(self.env_var))
            if env_targets:
                return env_targets
        if self.targets_file:
            file_targets = _read_targets_file(self.targets_file)
            if file_targets:
                return file_targets
        return list(self.default_targets)


def _relative_display(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _run_command(
    command: Sequence[str],
    *,
    task_name: str,
    log_name: str | None,
    append: bool = False,
    header: str | None = None,
) -> None:
    printable = " ".join(shlex.quote(arg) for arg in command)
    print(f"[ci_tasks] $ {printable}")

    log_path: Path | None = None
    file_exists = False
    mode = "w"

    if log_name is not None:
        QUALITY_REPORT_ROOT.mkdir(parents=True, exist_ok=True)
        log_path = QUALITY_REPORT_ROOT / log_name
        file_exists = log_path.exists()
        mode = "a" if append and file_exists else "w"
    elif header:
        # Surface context in the console when no log artifact is produced.
        print(header, end="" if header.endswith("\n") else "\n")

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise TaskError(f"Executable not found for command: {command[0]}") from exc

    assert process.stdout is not None  # for type checkers
    captured_lines: list[str] = []
    for line in process.stdout:
        captured_lines.append(line)
        print(line, end="")

    returncode = process.wait()

    if log_path is not None:
        with log_path.open(mode, encoding="utf-8") as handle:
            if mode == "w":
                handle.write(
                    f"# Log captured {datetime.now(timezone.utc).isoformat()}\n"
                )
            elif file_exists:
                handle.write("\n")
            if header:
                handle.write(header)
                if not header.endswith("\n"):
                    handle.write("\n")
            handle.write(f"$ {printable}\n")
            handle.writelines(captured_lines)
            handle.write(f"\n[exit code: {returncode}]\n")

    RECORDER.record(
        name=task_name,
        printable_command=printable,
        returncode=returncode,
        log_path=log_path,
    )

    if returncode != 0:
        raise TaskError(f"Command failed with exit code {returncode}: {printable}")


def _pytest_suites() -> list[PytestSuite]:
    suites = [
        PytestSuite(
            name="unit",
            default_targets=("tests/unit",),
            env_var="PYTEST_UNIT_TARGETS",
            targets_file=PYTEST_UNIT_TARGETS_FILE,
            marker=None,
        ),
        PytestSuite(
            name="integration",
            default_targets=("tests/integration",),
            env_var="PYTEST_INTEGRATION_TARGETS",
            targets_file=PYTEST_INTEGRATION_TARGETS_FILE,
            marker=None,
        ),
        PytestSuite(
            name="ui",
            default_targets=("tests/ui",),
            env_var="PYTEST_UI_TARGETS",
            targets_file=PYTEST_UI_TARGETS_FILE,
            marker=None,
        ),
    ]

    extra_file = os.environ.get("PYTEST_TARGETS_FILE", PYTEST_TARGETS_FILE)
    extra_targets = _read_targets_file(extra_file)
    if extra_targets:
        suites.append(
            PytestSuite(
                name="extra",
                default_targets=tuple(extra_targets),
                marker=None,
            )
        )

    return suites


def _run_pytest_suites(selected: Sequence[str] | None = None) -> None:
    suites = {suite.name: suite for suite in _pytest_suites()}
    order = [
        "unit",
        "integration",
        "ui",
        *[name for name in suites.keys() if name not in {"unit", "integration", "ui"}],
    ]

    if selected is not None:
        order = [name for name in order if name in selected]

    if not order:
        return

    common_flags = _split_env_list(os.environ.get("PYTEST_FLAGS"))
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    PYTEST_REPORT_ROOT.mkdir(parents=True, exist_ok=True)

    manual_targets = _split_env_list(os.environ.get("PYTEST_TARGETS"))
    if manual_targets:
        existing = _ensure_targets_exist(manual_targets)
        junit_path = PYTEST_REPORT_ROOT / "manual.xml"
        command = [
            sys.executable,
            "-m",
            "pytest",
            *common_flags,
            f"--junitxml={junit_path}",
            *existing,
        ]
        header = "## Suite: manual\n"
        _run_command(
            command,
            task_name="pytest:manual",
            log_name="pytest_manual.log",
            header=header,
        )
        return

    for name in order:
        suite = suites[name]
        targets = suite.resolve_targets()
        if not targets:
            print(
                f"[ci_tasks] No pytest targets configured for suite '{name}'; skipping."
            )
            continue

        existing_targets = _ensure_targets_exist(targets)

        command = [sys.executable, "-m", "pytest", *common_flags]
        if suite.marker:
            command.extend(["-m", suite.marker])
        if suite.extra_args:
            command.extend(list(suite.extra_args))

        junit_path = PYTEST_REPORT_ROOT / f"{name}.xml"
        command.extend([f"--junitxml={junit_path}"])
        command.extend(existing_targets)

        header = f"## Suite: {name}\n"
        _run_command(
            command,
            task_name=f"pytest:{name}",
            log_name=f"pytest_{name}.log",
            header=header,
        )


def task_lint() -> None:
    env_targets = _split_env_list(os.environ.get("PYTHON_LINT_PATHS"))
    targets = tuple(dict.fromkeys(env_targets or DEFAULT_LINT_TARGETS))
    existing_targets = _ensure_targets_exist(targets)

    format_cmd = [sys.executable, "-m", "ruff", "format", "--check", *existing_targets]
    check_cmd = [sys.executable, "-m", "ruff", "check", *existing_targets]

    _run_command(format_cmd, task_name="ruff-format", log_name="ruff_format.log")
    _run_command(check_cmd, task_name="ruff-check", log_name="ruff_check.log")


def task_typecheck() -> None:
    env_targets = _split_env_list(os.environ.get("MYPY_TARGETS"))
    if env_targets:
        targets = env_targets
    else:
        targets = _read_targets_file(MYPY_TARGETS_FILE)
    if not targets:
        # Fallback to whole source tree when no explicit targets are defined
        targets = ["src"]

    targets = _ensure_targets_exist(targets)

    command = [
        sys.executable,
        "-m",
        "mypy",
        "--config-file",
        str(PROJECT_ROOT / MYPY_CONFIG),
        *targets,
    ]
    _run_command(command, task_name="mypy", log_name="mypy.log")


def _resolve_qml_linter() -> tuple[str, ...]:
    """Return the command tuple that should be used to invoke ``qmllint``."""

    def _command_from_candidate(candidate: str) -> tuple[str, ...] | None:
        path_candidate = Path(candidate)
        if path_candidate.is_absolute():
            return (str(path_candidate),) if path_candidate.exists() else None

        resolved = shutil.which(candidate)
        if resolved:
            return (resolved,)
        return None

    candidates = _split_env_list(os.environ.get("QML_LINTER"))
    if candidates:
        for candidate in candidates:
            command = _command_from_candidate(candidate)
            if command is not None:
                return command
        raise TaskError(
            "None of the QML linters specified in QML_LINTER are executable."
        )

    for name in ("qmllint", "pyside6-qmllint"):
        command = _command_from_candidate(name)
        if command is not None:
            return command

    try:
        importlib.import_module("PySide6.scripts.qmllint")
    except ImportError as exc:
        raise TaskError(
            "qmllint or pyside6-qmllint is not installed and PySide6 is unavailable. "
            "Install Qt tooling (e.g. run 'python tools/setup_qt.py') or set QML_LINTER."
        ) from exc

    return (sys.executable, "-m", "PySide6.scripts.qmllint")


def _collect_qml_targets() -> list[Path]:
    env_targets = _split_env_list(os.environ.get("QML_LINT_PATHS"))
    if env_targets:
        configured = env_targets
    else:
        configured = _read_targets_file(QML_LINT_TARGETS_FILE)

    if not configured:
        return []

    collected: list[Path] = []
    for relative in configured:
        candidate = PROJECT_ROOT / relative
        if candidate.is_dir():
            collected.extend(sorted(candidate.rglob("*.qml")))
        elif candidate.exists():
            collected.append(candidate)
        else:
            raise TaskError(f"Configured QML lint target does not exist: {relative}")

    # Remove duplicates while preserving order
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in collected:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def task_test() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    primary_error: TaskError | None = None
    try:
        _run_pytest_suites()
    except TaskError as exc:
        primary_error = exc

    try:
        task_analyze_logs()
    except TaskError as exc:
        if primary_error is None:
            raise
        print(f"[ci_tasks] log analysis skipped due to earlier failure: {exc}")

    if primary_error is not None:
        raise primary_error


def task_test_unit() -> None:
    _run_pytest_suites(["unit"])


def task_test_integration() -> None:
    _run_pytest_suites(["integration"])


def task_test_ui() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    _run_pytest_suites(["ui"])


def task_analyze_logs() -> None:
    command = [sys.executable, "tools/analyze_logs.py"]
    _run_command(
        command,
        task_name="log-analysis",
        log_name="log_analysis.log",
    )


def task_post_analysis() -> None:
    artifact_root = PROJECT_ROOT
    default_inputs = [
        PROJECT_ROOT / "reports" / "tests",
        PROJECT_ROOT / "reports" / "quality",
        PROJECT_ROOT / "reports" / "performance",
        PROJECT_ROOT / "logs",
    ]

    command = [
        sys.executable,
        "-m",
        "tools.test_artifact_analyzer",
        "--artifact-root",
        str(artifact_root),
        "--output-json",
        str(PROJECT_ROOT / "reports" / "tests" / "test_analysis_summary.json"),
        "--output-markdown",
        str(PROJECT_ROOT / "reports" / "tests" / "test_analysis_summary.md"),
    ]

    for input_path in default_inputs:
        command.extend(["--input", str(input_path)])

    _run_command(
        command,
        task_name="post-analysis",
        log_name="test_artifact_analyzer.log",
    )


def task_qml_lint() -> None:
    linter_command = _resolve_qml_linter()
    targets = _collect_qml_targets()
    if not targets:
        print("[ci_tasks] No QML lint targets specified; skipping.")
        return

    capture_logs = _env_flag("CI_TASKS_QML_LOG_ARTIFACTS", default=True)
    log_name = "qmllint.log" if capture_logs else None

    for target in targets:
        relative = _relative_display(target)
        header = f"## Target: {relative}\n"
        _run_command(
            [*linter_command, str(target)],
            task_name=f"qmllint:{relative}",
            log_name=log_name,
            append=capture_logs,
            header=header,
        )


def task_verify() -> None:
    """Run linting, type-checking and tests sequentially."""

    task_lint()
    task_typecheck()
    task_qml_lint()
    task_test()
    task_post_analysis()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CI task runner for PneumoStabSim Professional"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("lint", help="Run Ruff format check and lint")
    subparsers.add_parser("typecheck", help="Run mypy against configured targets")
    subparsers.add_parser(
        "test", help="Run pytest across unit, integration, and UI suites"
    )
    subparsers.add_parser("test-unit", help="Run the unit test suite")
    subparsers.add_parser("test-integration", help="Run the integration test suite")
    subparsers.add_parser("test-ui", help="Run the UI/QML test suite")
    subparsers.add_parser(
        "analyze-logs", help="Analyze application logs for recent runs"
    )
    subparsers.add_parser("qml-lint", help="Run qmllint against configured targets")
    subparsers.add_parser(
        "verify", help="Run lint, typecheck, qml-lint, and tests in sequence"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    task_map = {
        "lint": task_lint,
        "typecheck": task_typecheck,
        "test": task_test,
        "test-unit": task_test_unit,
        "test-integration": task_test_integration,
        "test-ui": task_test_ui,
        "analyze-logs": task_analyze_logs,
        "qml-lint": task_qml_lint,
        "verify": task_verify,
    }

    task = task_map[args.command]

    RECORDER.start(args.command)
    exit_code = 0
    unexpected_error: BaseException | None = None
    try:
        _ensure_no_merge_conflicts()
        task()
    except TaskError as exc:
        print(f"[ci_tasks] ERROR: {exc}", file=sys.stderr)
        exit_code = 1
    except BaseException as exc:  # pragma: no cover - defensive safety net
        unexpected_error = exc
        exit_code = 1
    finally:
        RECORDER.finalize(exit_code == 0)

    if unexpected_error is not None:
        raise unexpected_error
    if exit_code != 0:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
