"""Unified entrypoint for environment setup and test execution.

This script provides a single, cross-platform entry for syncing dependencies
and running the project's primary verification suite. It prioritises the
existing `make check` pipeline when available and falls back to the Python
orchestrator to remain usable on systems without GNU Make (e.g. Windows).
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "tests" / "test_entrypoint.log"


class CommandFailure(RuntimeError):
    """Raised when a command exits with a non-zero status."""


class MissingTool(RuntimeError):
    """Raised when a required tool cannot be located."""


def _log(message: str) -> None:
    print(message)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("a", encoding="utf-8") as log:
        log.write(f"{message}\n")


def _stream_command(
    command: Sequence[str], *, env: dict[str, str] | None = None
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("a", encoding="utf-8") as log:
        log.write(f"$ {' '.join(command)}\n")
        log.flush()
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            cwd=PROJECT_ROOT,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log.write(line)
        process.wait()
        log.flush()
        if process.returncode:
            raise CommandFailure(
                f"Command failed with exit code {process.returncode}: {' '.join(command)}"
            )


def _require_uv() -> str:
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path
    raise MissingTool(
        "`uv` was not found in PATH. Install it via `python scripts/bootstrap_uv.py`."
    )


def _sync_environment(uv_path: str) -> None:
    _log("[entrypoint] Syncing dependencies with uv --frozen --extra dev")
    _stream_command([uv_path, "sync", "--frozen", "--extra", "dev"])


def _prepare_system(system: str) -> None:
    if system != "Linux":
        _log("[entrypoint] Non-Linux host detected; skipping system package prep")
        return

    setup_script = PROJECT_ROOT / "scripts" / "setup_linux.sh"
    if not setup_script.exists():
        _log("[entrypoint] setup_linux.sh missing; skipping system package prep")
        return

    _log(
        "[entrypoint] Ensuring Linux system dependencies via scripts/setup_linux.sh --skip-python --skip-qt"
    )
    _stream_command([str(setup_script), "--skip-python", "--skip-qt"])


def _primary_commands(uv_path: str, suite: str) -> Iterable[Sequence[str]]:
    make_path = shutil.which("make")
    suite_to_target = {
        "verify": ("check", "verify"),
        "tests": ("test-local", "test"),
        "integration": ("test-integration", "test-integration"),
        "unit": ("test-unit", "test-unit"),
        "ui": ("test-ui", "test-ui"),
    }
    make_target, ci_task = suite_to_target[suite]

    if make_path:
        _log(f"[entrypoint] Detected make; delegating to `make {make_target}`")
        yield [make_path, make_target]
    _log("[entrypoint] make not found or bypassed; executing Python ci_tasks")
    yield [
        uv_path,
        "run",
        "--locked",
        "--",
        "python",
        "-m",
        "tools.ci_tasks",
        ci_task,
    ]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Unified test entrypoint")
    parser.add_argument(
        "--suite",
        choices=["verify", "tests", "integration", "unit", "ui"],
        default="verify",
        help="Целевой набор проверок: полный verify, все тесты или только подмножество",
    )
    args = parser.parse_args(argv)

    system = platform.system()
    _log(f"[entrypoint] Detected platform: {system}; suite={args.suite}")

    try:
        uv_path = _require_uv()
        _prepare_system(system)
        _sync_environment(uv_path)
        env = os.environ.copy()
        env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

        for command in _primary_commands(uv_path, args.suite):
            _stream_command(command, env=env)
    except (CommandFailure, MissingTool) as exc:  # pragma: no cover - cli guard
        _log(f"[entrypoint] ERROR: {exc}")
        return 1
    except KeyboardInterrupt:  # pragma: no cover - interactive guard
        _log("[entrypoint] Interrupted by user")
        return 130

    _log("[entrypoint] Test pipeline completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
