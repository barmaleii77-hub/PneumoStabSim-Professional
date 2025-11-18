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
from typing import Iterable, Literal, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "tests" / "test_entrypoint.log"
PERFORMANCE_REPORTS = [
    PROJECT_ROOT / "reports" / "tests" / "render_sync_performance.json",
    PROJECT_ROOT / "reports" / "tests" / "panel_rendering_performance.json",
]


class CommandFailure(RuntimeError):
    """Raised when a command exits with a non-zero status."""


class MissingTool(RuntimeError):
    """Raised when a required tool cannot be located."""


def _reset_log() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("", encoding="utf-8")


def _announce_reports() -> None:
    for report in PERFORMANCE_REPORTS:
        report.parent.mkdir(parents=True, exist_ok=True)
        _log(
            f"[entrypoint] Performance metrics will be written to {report.relative_to(PROJECT_ROOT)}"
        )


def _log(message: str) -> None:
    print(message)
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


def _configure_qt_environment(uv_path: str) -> None:
    _log("[entrypoint] Exporting Qt environment variables via tools/setup_qt.py")
    _stream_command(
        [
            uv_path,
            "run",
            "--locked",
            "--",
            "python",
            "tools/setup_qt.py",
            "--configure-env",
            "--check",
        ]
    )


def _preinstall_dependencies(system: str, uv_path: str) -> bool:
    """Perform platform-specific dependency preparation."""

    _log(f"[entrypoint] Platform detected by platform.system(): {system}")

    if system == "Linux":
        make_path = shutil.which("make")
        if make_path:
            _log("[entrypoint] Preinstalling dependencies via `make uv-sync`")
            _stream_command([make_path, "uv-sync"])
        else:
            _log("[entrypoint] GNU Make not available; using uv sync fallback")
            _sync_environment(uv_path)
        _configure_qt_environment(uv_path)
        return True

    if system == "Windows":
        setup_script = PROJECT_ROOT / "scripts" / "setup_dev.py"
        if setup_script.exists():
            _log("[entrypoint] Preinstalling dependencies via scripts/setup_dev.py")
            _stream_command([sys.executable, str(setup_script)])
        else:
            _log("[entrypoint] setup_dev.py missing; falling back to uv sync")
            _sync_environment(uv_path)
        _configure_qt_environment(uv_path)
        return True

    return False


def _prepare_system(system: str) -> None:
    if system == "Linux":
        setup_script = PROJECT_ROOT / "scripts" / "setup_linux.sh"
        if not setup_script.exists():
            _log("[entrypoint] setup_linux.sh missing; skipping system package prep")
            return

        _log(
            "[entrypoint] Ensuring Linux system dependencies via scripts/setup_linux.sh --skip-python --skip-qt"
        )
        _stream_command([str(setup_script), "--skip-python", "--skip-qt"])
        return

    if system == "Windows":
        setup_script = PROJECT_ROOT / "scripts" / "setup_dev.py"
        if not setup_script.exists():
            _log("[entrypoint] setup_dev.py missing; skipping Windows system prep")
            return

        _log("[entrypoint] Running scripts/setup_dev.py to refresh Windows toolchain")
        _stream_command([sys.executable, str(setup_script)])
        return

    _log(f"[entrypoint] No system prep defined for platform '{system}'")


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified test entrypoint")
    parser.add_argument(
        "--scope",
        choices=["main", "integration", "all"],
        default="all",
        help=(
            "Test scope: `main` runs the primary verification task, "
            "`integration` adds integration/performance suites, `all` executes both"
        ),
    )
    return parser.parse_args(list(argv))


def _primary_commands(uv_path: str, scope: Literal["main", "integration", "all"]) -> Iterable[Sequence[str]]:
    """Yield the matrix of quality gates to execute for the platform."""

    if scope in {"main", "integration", "all"}:
        _log("[entrypoint] Running quality matrix: ruff, mypy, qmllint, pytest")
        yield [
            uv_path,
            "run",
            "--locked",
            "--",
            "python",
            "-m",
            "tools.ci_tasks",
            "lint",
        ]
        yield [
            uv_path,
            "run",
            "--locked",
            "--",
            "python",
            "-m",
            "tools.ci_tasks",
            "typecheck",
        ]
        yield [
            uv_path,
            "run",
            "--locked",
            "--",
            "python",
            "-m",
            "tools.ci_tasks",
            "qml-lint",
        ]
        yield [
            uv_path,
            "run",
            "--locked",
            "--",
            "python",
            "-m",
            "tools.ci_tasks",
            "test",
        ]

    if scope in {"integration", "all"}:
        _log("[entrypoint] Executing integration and performance test suites")
        yield [
            uv_path,
            "run",
            "--locked",
            "--",
            "pytest",
            "tests/integration",
            "tests/performance",
            "--maxfail",
            "1",
        ]


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    system = platform.system()
    _reset_log()
    _log(f"[entrypoint] Detected platform: {system} (scope={args.scope})")
    _announce_reports()

    try:
        uv_path = _require_uv()
        _prepare_system(system)
        preinstall_performed = _preinstall_dependencies(system, uv_path)
        if not preinstall_performed:
            _sync_environment(uv_path)
            _configure_qt_environment(uv_path)
        env = os.environ.copy()
        env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
        env.setdefault("PSS_HEADLESS", "1")

        failures: list[str] = []

        for command in _primary_commands(uv_path, args.scope):
            try:
                _stream_command(command, env=env)
            except CommandFailure as exc:
                failures.append(str(exc))
                _log(f"[entrypoint] Captured failure, continuing to next command: {exc}")

        if failures:
            for failure in failures:
                _log(f"[entrypoint] FAILURE: {failure}")
            return 1
    except MissingTool as exc:  # pragma: no cover - cli guard
        _log(f"[entrypoint] ERROR: {exc}")
        return 1
    except KeyboardInterrupt:  # pragma: no cover - interactive guard
        _log("[entrypoint] Interrupted by user")
        return 130

    _log("[entrypoint] Test pipeline completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
