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
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

from tools import merge_conflict_scan

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LINT_TARGETS: tuple[str, ...] = ("app.py", "src", "tests", "tools")
MYPY_TARGETS_FILE = "mypy_targets.txt"
PYTEST_TARGETS_FILE = "pytest_targets.txt"
QML_LINT_TARGETS_FILE = "qmllint_targets.txt"
MYPY_CONFIG = "mypy.ini"


class TaskError(RuntimeError):
    """Raised when a task cannot be executed successfully."""


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


def _run_command(command: Sequence[str]) -> None:
    printable = " ".join(shlex.quote(arg) for arg in command)
    print(f"[ci_tasks] $ {printable}")
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise TaskError(
            f"Command failed with exit code {completed.returncode}: {printable}"
        )


def task_lint() -> None:
    env_targets = _split_env_list(os.environ.get("PYTHON_LINT_PATHS"))
    targets = tuple(dict.fromkeys(env_targets or DEFAULT_LINT_TARGETS))
    existing_targets = _ensure_targets_exist(targets)

    format_cmd = [sys.executable, "-m", "ruff", "format", "--check", *existing_targets]
    check_cmd = [sys.executable, "-m", "ruff", "check", *existing_targets]

    _run_command(format_cmd)
    _run_command(check_cmd)


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
    _run_command(command)


def _resolve_qml_linter() -> str:
    candidates = _split_env_list(os.environ.get("QML_LINTER"))
    if candidates:
        for candidate in candidates:
            path = (
                shutil.which(candidate) if not os.path.isabs(candidate) else candidate
            )
            if path:
                return path if os.path.isabs(candidate) else candidate
        raise TaskError(
            "None of the QML linters specified in QML_LINTER are executable."
        )

    for name in ("qmllint", "pyside6-qmllint"):
        if shutil.which(name):
            return name

    raise TaskError(
        "qmllint or pyside6-qmllint is not installed. Set QML_LINTER to override."
    )


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

    command = [sys.executable, "-m", "pytest", *env_flags, *targets]
    _run_command(command)


def task_qml_lint() -> None:
    linter = _resolve_qml_linter()
    targets = _collect_qml_targets()
    if not targets:
        print("[ci_tasks] No QML lint targets specified; skipping.")
        return

    for target in targets:
        _run_command([linter, str(target)])


def task_verify() -> None:
    """Run linting, type-checking and tests sequentially."""

    task_lint()
    task_typecheck()
    task_qml_lint()
    task_test()


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
    try:
        _ensure_no_merge_conflicts()
        task()
    except TaskError as exc:
        print(f"[ci_tasks] ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
