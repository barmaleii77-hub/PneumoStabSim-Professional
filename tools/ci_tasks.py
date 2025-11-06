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
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from tools import merge_conflict_scan

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUALITY_REPORT_ROOT = PROJECT_ROOT / "reports" / "quality"
DEFAULT_LINT_TARGETS: tuple[str, ...] = ("app.py", "src", "tests", "tools")
MYPY_TARGETS_FILE = "mypy_targets.txt"
PYTEST_TARGETS_FILE = "pytest_targets.txt"
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


def _relative_display(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _run_command(
    command: Sequence[str],
    *,
    task_name: str,
    log_name: str,
    append: bool = False,
    header: str | None = None,
) -> None:
    printable = " ".join(shlex.quote(arg) for arg in command)
    print(f"[ci_tasks] $ {printable}")

    QUALITY_REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = QUALITY_REPORT_ROOT / log_name
    file_exists = log_path.exists()
    mode = "a" if append and file_exists else "w"

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

    with log_path.open(mode, encoding="utf-8") as handle:
        if mode == "w":
            handle.write(f"# Log captured {datetime.now(timezone.utc).isoformat()}\n")
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
    env_flags = _split_env_list(os.environ.get("PYTEST_FLAGS"))
    env_targets = _split_env_list(os.environ.get("PYTEST_TARGETS"))
    if env_targets:
        targets = env_targets
    else:
        file_name = os.environ.get("PYTEST_TARGETS_FILE", PYTEST_TARGETS_FILE)
        targets = _read_targets_file(file_name) or ["tests"]

    targets = _ensure_targets_exist(targets)

    # Prevent externally installed pytest plugins from interfering with the
    # suite.  Some environments ship plugins that eagerly print debugging
    # information during interpreter start-up which, in turn, breaks our CI
    # expectations (pytest aborts before running any tests).  Unless a caller
    # has explicitly opted in to plugin autoloading, keep it disabled.
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    command = [sys.executable, "-m", "pytest", *env_flags, *targets]
    _run_command(command, task_name="pytest", log_name="pytest.log")


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

    for target in targets:
        relative = _relative_display(target)
        header = f"## Target: {relative}\n"
        _run_command(
            [*linter_command, str(target)],
            task_name=f"qmllint:{relative}",
            log_name="qmllint.log",
            append=True,
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
    subparsers.add_parser("test", help="Run pytest with configured targets")
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
