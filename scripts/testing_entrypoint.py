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
import threading
from datetime import timedelta
from pathlib import Path
from typing import Iterable, Literal, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "tests" / "test_entrypoint.log"
PERFORMANCE_REPORTS = [
    PROJECT_ROOT / "reports" / "tests" / "render_sync_performance.json",
    PROJECT_ROOT / "reports" / "tests" / "panel_rendering_performance.json",
]
DEFAULT_ENV_VARS: dict[str, str] = {
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    "PSS_HEADLESS": "1",
    "QT_QPA_PLATFORM": "offscreen",
    "QT_QUICK_BACKEND": "software",
    "LIBGL_ALWAYS_SOFTWARE": "1",
}
DEFAULT_TIMEOUT = int(timedelta(minutes=45).total_seconds())


def _coerce_timeout(raw_value: str | None) -> tuple[int, str | None]:
    if raw_value is None:
        return DEFAULT_TIMEOUT, None

    try:
        parsed = int(raw_value)
    except ValueError:
        return DEFAULT_TIMEOUT, raw_value

    if parsed <= 0:
        return DEFAULT_TIMEOUT, raw_value

    return parsed, None


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
    command: Sequence[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
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

        def _drain_output() -> None:
            for line in process.stdout:
                print(line, end="")
                log.write(line)

        stream_thread = threading.Thread(target=_drain_output, daemon=True)
        stream_thread.start()

        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timeout_message = (
                f"[entrypoint] Command timed out after {timeout}s: {' '.join(command)}"
            )
            print(timeout_message)
            log.write(timeout_message + "\n")
            process.kill()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
        finally:
            stream_thread.join()

        if process.poll() is None:
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


def _sync_environment(uv_path: str, *, env: dict[str, str], timeout: int) -> None:
    _log("[entrypoint] Syncing dependencies with uv --frozen --extra dev")
    _stream_command(
        [uv_path, "sync", "--frozen", "--extra", "dev"], env=env, timeout=timeout
    )


def _configure_qt_environment(
    uv_path: str, *, env: dict[str, str], timeout: int
) -> None:
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
        ],
        env=env,
        timeout=timeout,
    )


def _preinstall_dependencies(
    system: str, uv_path: str, *, env: dict[str, str], timeout: int
) -> bool:
    """Perform platform-specific dependency preparation."""

    _log(f"[entrypoint] Platform detected by platform.system(): {system}")

    if system == "Linux":
        make_path = shutil.which("make")
        if make_path:
            _log("[entrypoint] Preinstalling dependencies via `make uv-sync`")
            _stream_command([make_path, "uv-sync"], env=env, timeout=timeout)
        else:
            _log("[entrypoint] GNU Make not available; using uv sync fallback")
            _sync_environment(uv_path, env=env, timeout=timeout)
        _configure_qt_environment(uv_path, env=env, timeout=timeout)
        return True

    if system == "Windows":
        setup_script = PROJECT_ROOT / "scripts" / "setup_dev.py"
        if setup_script.exists():
            _log("[entrypoint] Preinstalling dependencies via scripts/setup_dev.py")
            _stream_command(
                [sys.executable, str(setup_script)], env=env, timeout=timeout
            )
        else:
            _log("[entrypoint] setup_dev.py missing; falling back to uv sync")
            _sync_environment(uv_path, env=env, timeout=timeout)
        _configure_qt_environment(uv_path, env=env, timeout=timeout)
        return True

    return False


def _prepare_system(system: str, *, env: dict[str, str], timeout: int) -> None:
    if system == "Linux":
        setup_script = PROJECT_ROOT / "scripts" / "setup_linux.sh"
        if not setup_script.exists():
            _log("[entrypoint] setup_linux.sh missing; skipping system package prep")
            return

        _log(
            "[entrypoint] Ensuring Linux system dependencies via scripts/setup_linux.sh --skip-python --skip-qt"
        )
        _stream_command(
            [str(setup_script), "--skip-python", "--skip-qt"], env=env, timeout=timeout
        )
        return

    if system == "Windows":
        setup_script = PROJECT_ROOT / "scripts" / "setup_dev.py"
        if not setup_script.exists():
            _log("[entrypoint] setup_dev.py missing; skipping Windows system prep")
            return

        _log("[entrypoint] Running scripts/setup_dev.py to refresh Windows toolchain")
        _stream_command([sys.executable, str(setup_script)], env=env, timeout=timeout)
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
    parser.add_argument(
        "--platform",
        choices=["auto", "linux", "windows"],
        default="auto",
        help="Override detected platform (auto detects via platform.system())",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=(
            "Per-command timeout in seconds. Defaults to PSS_ENTRYPOINT_TIMEOUT_SECONDS "
            f"or {DEFAULT_TIMEOUT} seconds."
        ),
    )
    return parser.parse_args(list(argv))


def _resolve_platform(requested: str) -> str:
    if requested.lower() == "auto":
        return platform.system()

    mapping = {"linux": "Linux", "windows": "Windows"}
    return mapping.get(requested.lower(), platform.system())


def _primary_commands(
    uv_path: str, scope: Literal["main", "integration", "all"]
) -> Iterable[Sequence[str]]:
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
    system = _resolve_platform(args.platform)
    env = os.environ.copy()
    for key, value in DEFAULT_ENV_VARS.items():
        env.setdefault(key, value)
    timeout_value, timeout_override = _coerce_timeout(
        os.environ.get("PSS_ENTRYPOINT_TIMEOUT_SECONDS")
    )
    if args.timeout is not None:
        timeout_value = args.timeout
    _reset_log()
    _log(
        "[entrypoint] Detected platform: "
        f"{system} (scope={args.scope}, timeout={timeout_value}s)"
    )
    if timeout_override is not None and args.timeout is None:
        _log(
            "[entrypoint] Invalid PSS_ENTRYPOINT_TIMEOUT_SECONDS value "
            f"'{timeout_override}', defaulting to {timeout_value}s"
        )
    _announce_reports()

    try:
        uv_path = _require_uv()
        _prepare_system(system, env=env, timeout=timeout_value)
        preinstall_performed = _preinstall_dependencies(
            system, uv_path, env=env, timeout=timeout_value
        )
        if not preinstall_performed:
            _sync_environment(uv_path, env=env, timeout=timeout_value)
            _configure_qt_environment(uv_path, env=env, timeout=timeout_value)

        failures: list[str] = []

        for command in _primary_commands(uv_path, args.scope):
            try:
                _stream_command(command, env=env, timeout=timeout_value)
            except CommandFailure as exc:
                failures.append(str(exc))
                _log(
                    f"[entrypoint] Captured failure, continuing to next command: {exc}"
                )

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
