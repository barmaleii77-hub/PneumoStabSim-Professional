#!/usr/bin/env python3
"""Cross-platform bootstrapper for running the PneumoStabSim test matrix.

The script is designed to be executed from the repository root on both Linux
containers and Windows workstations.  It performs the following steps:

1. Ensures that the `uv` package manager is installed and synchronised with the
   lockfile.
2. Applies a consistent set of Qt/graphics environment defaults required for
   headless test execution.
3. Optionally validates the Qt runtime configuration via
   :mod:`tools.environment.verify_qt_setup`.
4. Runs the requested :mod:`tools.task_runner` task (``verify`` by default),
   which covers the full lint/test matrix used in CI.

The helper is intentionally simple so it can be invoked by automation scripts,
CI pipelines, or developers who just want a one-liner that works the same on
Linux and Windows.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TASK = "verify"
DEFAULT_ENVIRONMENT = {
    "QT_QPA_PLATFORM": "offscreen",
    "QT_QUICK_BACKEND": "software",
    "LIBGL_ALWAYS_SOFTWARE": "1",
    "MESA_GL_VERSION_OVERRIDE": "4.1",
    "MESA_GLSL_VERSION_OVERRIDE": "410",
}


class CommandError(RuntimeError):
    """Raised when a delegated command exits with a non-zero status."""

    def __init__(self, description: str, command: Iterable[str], returncode: int):
        joined = " ".join(command)
        super().__init__(f"{description} failed with exit code {returncode}: {joined}")
        self.description = description
        self.command = tuple(command)
        self.returncode = returncode


def _normalise_args(command: Iterable[str]) -> list[str]:
    items: list[str] = []
    for item in command:
        text = str(item).strip()
        if not text:
            continue
        items.append(text)
    if not items:
        raise ValueError("command must contain at least one non-empty argument")
    return items


def run_command(
    command: Iterable[str], *, description: str, env: dict[str, str] | None = None
) -> None:
    """Execute *command* relative to :data:`PROJECT_ROOT`.

    A small amount of structured logging is emitted so that CI logs are
    predictable and easy to scan.
    """

    args = _normalise_args(command)
    printable = " ".join(args)
    print(f"[bootstrap-tests] {description}")
    print(f"[bootstrap-tests] $ {printable}")
    completed = subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise CommandError(description, args, completed.returncode)


def ensure_uv_sync(*, force_install: bool) -> str:
    """Install ``uv`` (if necessary) and synchronise dependencies.

    Returns the resolved path to the ``uv`` executable so subsequent calls can
    reuse it without another ``PATH`` lookup.
    """

    bootstrap_cmd = [sys.executable, "scripts/bootstrap_uv.py"]
    if force_install:
        bootstrap_cmd.append("--force")
    bootstrap_cmd.append("--sync")
    run_command(bootstrap_cmd, description="Ensure uv is available and synced")
    uv_binary = shutil.which(os.environ.get("UV", "uv"))
    if not uv_binary:
        raise RuntimeError(
            "uv executable was not found on PATH after running bootstrap_uv.py"
        )
    return uv_binary


def _prepare_environment(overrides: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key, value in DEFAULT_ENVIRONMENT.items():
        env.setdefault(key, value)
    if overrides:
        env.update(overrides)
    return env


def run_qt_verification(uv_binary: str, *, skip_check: bool) -> None:
    if skip_check:
        return

    reports_dir = PROJECT_ROOT / "reports" / "environment"
    reports_dir.mkdir(parents=True, exist_ok=True)
    env = _prepare_environment()
    run_command(
        [
            uv_binary,
            "run",
            "--locked",
            "--",
            "python",
            "-m",
            "tools.environment.verify_qt_setup",
            "--allow-missing-runtime",
            "--report-dir",
            str(reports_dir),
        ],
        description="Validate Qt runtime configuration",
        env=env,
    )


def run_task_matrix(
    uv_binary: str,
    *,
    task: str,
    task_args: Iterable[str],
    env_overrides: dict[str, str],
) -> None:
    args = [arg for arg in task_args if arg and arg != "--"]
    env = _prepare_environment(env_overrides)
    run_command(
        [
            uv_binary,
            "run",
            "--locked",
            "--",
            "python",
            "-m",
            "tools.task_runner",
            task,
            *args,
        ],
        description=f"Run tools.task_runner {task}",
        env=env,
    )


def _detect_platform_label() -> str:
    system = platform.system() or "Unknown"
    release = platform.release()
    arch = platform.machine() or ""
    label = system
    if release:
        label += f" {release}"
    if arch:
        label += f" ({arch})"
    return label


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Provision the PneumoStabSim test environment and execute the standard "
            "verification suite with consistent defaults on Linux and Windows."
        )
    )
    parser.add_argument(
        "--task",
        default=DEFAULT_TASK,
        help=(
            "tools.task_runner task to execute after provisioning (default: "
            f"{DEFAULT_TASK!r})."
        ),
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Only prepare dependencies without running the task runner.",
    )
    parser.add_argument(
        "--skip-qt-check",
        action="store_true",
        help="Do not run tools.environment.verify_qt_setup after syncing dependencies.",
    )
    parser.add_argument(
        "--force-uv-install",
        action="store_true",
        help="Reinstall uv even if it is already present on PATH.",
    )
    parser.add_argument(
        "task_args",
        nargs=argparse.REMAINDER,
        help=(
            "Additional arguments forwarded to tools.task_runner. "
            "Use `--` to separate them from the bootstrapper options."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("[bootstrap-tests] Detected platform:", _detect_platform_label())
    uv_binary = ensure_uv_sync(force_install=args.force_uv_install)
    run_qt_verification(uv_binary, skip_check=args.skip_qt_check)
    if not args.skip_tests:
        run_task_matrix(
            uv_binary,
            task=args.task,
            task_args=args.task_args or (),
            env_overrides={},
        )
    print("[bootstrap-tests] Completed successfully")


if __name__ == "__main__":
    try:
        main()
    except CommandError as exc:
        print(f"[bootstrap-tests] ERROR: {exc}", file=sys.stderr)
        sys.exit(exc.returncode if isinstance(exc.returncode, int) else 1)
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"[bootstrap-tests] Unhandled error: {exc}", file=sys.stderr)
        sys.exit(1)
