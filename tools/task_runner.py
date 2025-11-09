"""Cross-platform task runner mirroring key Makefile targets.

The Makefile remains the authoritative definition for Linux runners, but
Windows environments often lack a `make` executable.  This module provides a
Python CLI that dispatches to the same underlying tooling (`tools.ci_tasks`,
`tools.autonomous_check`, etc.) so that quality gates behave identically on
all platforms.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from collections.abc import Callable
from collections.abc import Sequence

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false;qt.qml.debug=true")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UV_SYNC_ARGS = "--frozen --extra dev"
DEFAULT_PYTEST_FLAGS = ("-vv", "--color=yes", "--maxfail=1")
SMOKE_TARGET = Path("tests/smoke")
INTEGRATION_TARGET = Path("tests/integration/test_main_window_qml.py")
AUTONOMOUS_DEFAULT = (
    "--task",
    "verify",
    "--history-limit",
    "10",
    "--sanitize",
    "--launch-trace",
)


class TaskExecutionError(RuntimeError):
    """Raised when a delegated command fails."""

    def __init__(
        self, description: str, command: Sequence[str], returncode: int
    ) -> None:
        super().__init__(
            f"{description} failed with exit code {returncode}: {' '.join(command)}"
        )
        self.description = description
        self.command = tuple(command)
        self.returncode = returncode


def _run(
    command: Sequence[str], *, description: str, env: dict[str, str] | None = None
) -> None:
    print(f"[task-runner] {description}: {' '.join(command)}")
    completed = subprocess.run(
        list(command),
        cwd=PROJECT_ROOT,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise TaskExecutionError(description, command, completed.returncode)


def _uv_binary() -> str:
    candidate = shutil.which(os.environ.get("UV", "uv"))
    if candidate is None:
        raise TaskExecutionError("uv-sync", ("uv", "sync"), returncode=127)
    return candidate


def _uv_sync(extra_args: Sequence[str] | None = None) -> None:
    args = list(
        extra_args
        or shlex.split(os.environ.get("TASK_RUNNER_UV_SYNC_ARGS", DEFAULT_UV_SYNC_ARGS))
    )
    command = [_uv_binary(), "sync", *args]
    _run(command, description="uv-sync")


def _run_ci_task(subcommand: str, extra: Sequence[str]) -> None:
    command = [sys.executable, "-m", "tools.ci_tasks", subcommand, *extra]
    _run(command, description=f"ci_tasks:{subcommand}")


def _run_python_module(module: str, *module_args: str) -> None:
    command = [sys.executable, "-m", module, *module_args]
    _run(command, description=module)


def _run_python_script(script: str, *script_args: str) -> None:
    command = [sys.executable, script, *script_args]
    _run(command, description=script)


def _ensure_reports_dir(relative: str) -> None:
    (PROJECT_ROOT / relative).mkdir(parents=True, exist_ok=True)


def task_check(extra: Sequence[str]) -> None:
    if extra:
        raise ValueError("task 'check' does not accept additional arguments")

    _uv_sync()
    _run_ci_task("verify", ())
    _run_python_script("tools/validate_shaders.py")
    _run_python_script(
        "tools/check_shader_logs.py",
        "reports/shaders",
        "--recursive",
        "--fail-on-warnings",
        "--expect-fallback",
    )
    _run_python_script("tools/render_checks/validate_hdr_orientation.py")
    _run_python_script("tools/update_translations.py", "--check")
    _ensure_reports_dir("reports/environment")
    _run_python_module(
        "tools.environment.verify_qt_setup",
        "--report-dir",
        "reports/environment",
        "--allow-missing-runtime",
    )


def task_verify(extra: Sequence[str]) -> None:
    if extra:
        raise ValueError("task 'verify' does not accept additional arguments")

    task_check(())
    _run(
        [
            sys.executable,
            "-m",
            "pytest",
            *DEFAULT_PYTEST_FLAGS,
            str(SMOKE_TARGET),
        ],
        description="pytest:smoke",
    )
    _run(
        [
            sys.executable,
            "-m",
            "pytest",
            *DEFAULT_PYTEST_FLAGS,
            str(INTEGRATION_TARGET),
        ],
        description="pytest:integration",
    )


def task_uv_sync(extra: Sequence[str]) -> None:
    _uv_sync(extra)


def task_uv_run(extra: Sequence[str]) -> None:
    if not extra:
        raise ValueError("task 'uv-run' expects the command to execute after '--'")
    command = [
        _uv_binary(),
        "run",
        *shlex.split(os.environ.get("UV_RUN_ARGS", "--locked")),
        "--",
        *extra,
    ]
    _run(command, description="uv-run")


def task_lint(extra: Sequence[str]) -> None:
    _run_ci_task("lint", extra)


def task_typecheck(extra: Sequence[str]) -> None:
    _run_ci_task("typecheck", extra)


def task_qml_lint(extra: Sequence[str]) -> None:
    _run_ci_task("qml-lint", extra)


def task_test(extra: Sequence[str]) -> None:
    _run_ci_task("test", extra)


def task_test_unit(extra: Sequence[str]) -> None:
    _run_ci_task("test-unit", extra)


def task_test_integration(extra: Sequence[str]) -> None:
    _run_ci_task("test-integration", extra)


def task_test_ui(extra: Sequence[str]) -> None:
    _run_ci_task("test-ui", extra)


def task_analyze_logs(extra: Sequence[str]) -> None:
    _run_ci_task("analyze-logs", extra)


def task_post_analysis(extra: Sequence[str]) -> None:
    _run_ci_task("post-analysis", extra)


def task_autonomous_check(extra: Sequence[str]) -> None:
    args = list(extra) if extra else list(AUTONOMOUS_DEFAULT)
    _run(
        [sys.executable, "-m", "tools.autonomous_check", *args],
        description="autonomous-check",
    )


def task_autonomous_check_trace(extra: Sequence[str]) -> None:
    args = list(extra) if extra else ["--launch-trace"]
    _run(
        [sys.executable, "-m", "tools.autonomous_check", *args],
        description="autonomous-check-trace",
    )


def task_trace_launch(extra: Sequence[str]) -> None:
    _run(
        [sys.executable, "-m", "tools.trace_launch", *extra], description="trace-launch"
    )


def task_sanitize(extra: Sequence[str]) -> None:
    _run_python_module("tools.project_sanitize", *extra)


def task_smoke(extra: Sequence[str]) -> None:
    target = extra[0] if extra else str(SMOKE_TARGET)
    _run(
        [sys.executable, "-m", "pytest", *DEFAULT_PYTEST_FLAGS, target],
        description="pytest:smoke",
    )


def task_integration(extra: Sequence[str]) -> None:
    target = extra[0] if extra else str(INTEGRATION_TARGET)
    _run(
        [sys.executable, "-m", "pytest", *DEFAULT_PYTEST_FLAGS, target],
        description="pytest:integration",
    )


TASKS: dict[str, Callable[[Sequence[str]], None]] = {
    "uv-sync": task_uv_sync,
    "uv-run": task_uv_run,
    "check": task_check,
    "verify": task_verify,
    "lint": task_lint,
    "typecheck": task_typecheck,
    "qml-lint": task_qml_lint,
    "test": task_test,
    "test-unit": task_test_unit,
    "test-integration": task_test_integration,
    "test-ui": task_test_ui,
    "analyze-logs": task_analyze_logs,
    "post-analysis": task_post_analysis,
    "autonomous-check": task_autonomous_check,
    "autonomous-check-trace": task_autonomous_check_trace,
    "trace-launch": task_trace_launch,
    "sanitize": task_sanitize,
    "smoke": task_smoke,
    "integration": task_integration,
}


def _format_task_list() -> str:
    return "\n".join(f"  - {name}" for name in sorted(TASKS))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Python fallback for PneumoStabSim Makefile targets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available tasks:\n" + _format_task_list(),
    )
    parser.add_argument(
        "task", nargs="?", help="Task to execute (use --list to show options)"
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed to the delegated command",
    )
    parser.add_argument(
        "--list", action="store_true", help="Print available tasks and exit"
    )

    args = parser.parse_args(argv)

    if args.list:
        print(_format_task_list())
        return

    if args.task is None:
        parser.error("task name is required")

    task = TASKS.get(args.task)
    if task is None:
        parser.error(
            f"unknown task '{args.task}'. Use --list to inspect available commands."
        )

    extra = tuple(arg for arg in args.extra if arg)
    try:
        task(extra)
    except TaskExecutionError as exc:
        raise SystemExit(exc.returncode) from exc
    except ValueError as exc:
        print(f"task-runner error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
