"""Capture a reproducible launch trace for the PneumoStabSim application.

The script executes ``app.py`` in environment-report mode, collects console
output, and stores artefacts under ``reports/quality/launch_traces``.  The
resulting logs provide traceability for environment provisioning issues without
requiring a full GUI session on headless agents.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TextIO
from collections.abc import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRACE_ROOT = PROJECT_ROOT / "reports" / "quality" / "launch_traces"
DEFAULT_HISTORY_LIMIT = 5
DOTENV_PATH = PROJECT_ROOT / ".env"
QT_REQUIRED_VARS: tuple[str, ...] = (
    "QT_PLUGIN_PATH",
    "QML2_IMPORT_PATH",
    "QT_QUICK_CONTROLS_STYLE",
)

try:  # Ленивая загрузка реестра переменных окружения
    from tools.env_registry import (
        validate_environment,
        format_matrix_markdown,
        CRITICAL_VARS as _CRITICAL_ENV_VARS,
    )
except Exception:  # pragma: no cover - реестр может отсутствовать в старых ветках
    _CRITICAL_ENV_VARS = ()
    validate_environment = None  # type: ignore
    format_matrix_markdown = None  # type: ignore


def _ensure_trace_dir() -> None:
    TRACE_ROOT.mkdir(parents=True, exist_ok=True)


def _utc_now() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0)


def _trace_log_path(timestamp: _dt.datetime) -> Path:
    safe_stamp = timestamp.isoformat().replace(":", "-")
    return TRACE_ROOT / f"launch_trace_{safe_stamp}.log"


def _render_log_block(body: str) -> list[str]:
    stripped = body.rstrip()
    return ["", "```", stripped, "```", ""]


def _latest_trace_path() -> Path:
    return TRACE_ROOT / "launch_trace_latest.log"


def _status_path() -> Path:
    return TRACE_ROOT / "launch_trace_status.json"


def _prune_old_traces(limit: int) -> None:
    if limit <= 0:
        return

    traces = sorted(
        path
        for path in TRACE_ROOT.glob("launch_trace_*.log")
        if path.name != "launch_trace_latest.log"
    )
    excess = len(traces) - limit
    if excess <= 0:
        return

    for path in traces[:excess]:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _build_command(env_report: Path, passthrough: Sequence[str]) -> list[str]:
    command = [
        sys.executable,
        "app.py",
        "--env-report",
        str(env_report),
        *passthrough,
    ]
    return command


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        env[key.strip()] = value
    return env


def _default_qpa_platform() -> str | None:
    """Return a sensible Qt platform plugin default for the current OS."""

    if sys.platform.startswith("win"):
        # Let Qt decide on Windows so that developer machines respect the
        # system default and any per-shell customisation.
        return None
    if sys.platform == "darwin":
        # macOS ships the Cocoa plugin by default; no override is required.
        return None
    # For Linux containers we prefer the offscreen backend to keep headless
    # automation stable.
    return "offscreen"


def _ensure_qt_defaults(environment: dict[str, str]) -> None:
    environment.setdefault("QT_API", "PySide6")
    if "QT_QPA_PLATFORM" not in environment:
        default_platform = _default_qpa_platform()
        if default_platform is not None:
            environment["QT_QPA_PLATFORM"] = default_platform
    environment.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")


def _compose_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.update(_parse_env_file(DOTENV_PATH))
    _ensure_qt_defaults(env)
    return env


def _status_icon(success: bool, stream: TextIO | None = None) -> str:
    """Return a status icon compatible with the active stdout encoding."""

    icon = "✅" if success else "❌"
    fallback = "OK" if success else "FAIL"

    target_stream = stream if stream is not None else sys.stdout
    encoding = getattr(target_stream, "encoding", None) or sys.getdefaultencoding()

    if os.name == "nt":
        normalized = (encoding or "").lower()
        if normalized not in {
            "utf-8",
            "utf8",
            "utf-16",
            "utf16",
            "utf-32",
            "utf32",
            "utf_8_sig",
            "cp65001",
        }:
            return fallback

    try:
        icon.encode(encoding, errors="strict")
    except (UnicodeEncodeError, LookupError):
        return fallback
    return icon


def _safe_print(text: str, *, stream: TextIO | None = None) -> None:
    """Print text while gracefully degrading unsupported Unicode characters."""

    target = stream if stream is not None else sys.stdout
    try:
        print(text, file=target)
    except UnicodeEncodeError:
        substitutions = {
            "✅": "[OK]",
            "❌": "[FAIL]",
            "⚠️": "[WARN]",
            "🔧": "[INFO]",
        }
        sanitized = text
        for symbol, replacement in substitutions.items():
            sanitized = sanitized.replace(symbol, replacement)
        print(sanitized, file=target)


def _validate_env(environment: dict[str, str]) -> dict[str, object]:
    """Сформировать отчёт проверки переменных окружения (пустой при отсутствии реестра)."""
    if validate_environment is None:  # реестр недоступен
        return {"matrix_markdown": "", "report": {}}
    report = validate_environment(environment)
    md = format_matrix_markdown(report)
    return {"matrix_markdown": md, "report": report}


def run_launch_trace(passthrough: Sequence[str], history_limit: int) -> int:
    _ensure_trace_dir()

    timestamp = _utc_now()
    report_path = (
        TRACE_ROOT / f"environment_report_{timestamp.isoformat().replace(':', '-')}.md"
    )
    command = _build_command(report_path, passthrough)
    environment = _compose_environment()

    # Валидация переменных окружения до запуска
    env_validation = _validate_env(environment)
    env_report = env_validation.get("report", {})
    missing_vars = list(env_report.get("missing", [])) if env_report else []
    empty_vars = list(env_report.get("empty", [])) if env_report else []

    start = time.perf_counter()
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
    )
    duration = time.perf_counter() - start

    log_body = completed.stdout or ""
    log_sections = [
        "# PneumoStabSim Launch Trace",
        "",
        f"- Timestamp: {timestamp.isoformat()}",
        f"- Command: {' '.join(command)}",
        f"- Return code: {completed.returncode}",
        f"- Environment report: {report_path.relative_to(PROJECT_ROOT)}",
        "- Qt environment:",
    ]
    for var in QT_REQUIRED_VARS:
        log_sections.append(f"  - {var}={environment.get(var, '')}")

    if env_validation.get("matrix_markdown"):
        log_sections.append("\n## Environment Variables Matrix")
        log_sections.append(env_validation["matrix_markdown"])
        if missing_vars:
            log_sections.append(
                f"\n⚠ Отсутствуют критичные переменные: {', '.join(sorted(missing_vars))}"
            )
        if empty_vars:
            log_sections.append(
                f"\n⚠ Пустые переменные: {', '.join(sorted(empty_vars))}"
            )

    log_sections.extend(_render_log_block(log_body))
    log_text = "\n".join(log_sections)

    log_path = _trace_log_path(timestamp)
    log_path.write_text(log_text + "\n", encoding="utf-8")
    _latest_trace_path().write_text(log_text + "\n", encoding="utf-8")

    status_payload = {
        "timestamp": timestamp.isoformat(),
        "command": command,
        "return_code": completed.returncode,
        "log_path": str(log_path.relative_to(PROJECT_ROOT)),
        "environment_report": str(report_path.relative_to(PROJECT_ROOT)),
        "success": completed.returncode == 0,
        "duration": duration,
        "env_missing": missing_vars,
        "env_empty": empty_vars,
    }
    _status_path().write_text(
        json.dumps(status_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    _prune_old_traces(history_limit)

    success = completed.returncode == 0
    status_marker = _status_icon(success, stream=sys.stdout)

    summary_lines = [
        "Launch trace summary:",
        f"{status_marker} launch (rc={completed.returncode}, {duration:.2f}s)",
        f" Log file: {log_path.relative_to(PROJECT_ROOT)}",
        f" Environment report: {report_path.relative_to(PROJECT_ROOT)}",
    ]
    missing_qt = [var for var in QT_REQUIRED_VARS if not environment.get(var)]
    if missing_qt:
        summary_lines.append(" Missing Qt variables: " + ", ".join(sorted(missing_qt)))
    if missing_vars:
        summary_lines.append(
            " Missing critical env vars: " + ", ".join(sorted(missing_vars))
        )
    if empty_vars:
        summary_lines.append(
            " Empty critical env vars: " + ", ".join(sorted(empty_vars))
        )
    _safe_print("\n".join(summary_lines))

    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the simulator environment check and persist launch traces.",
    )
    parser.add_argument(
        "--history-limit",
        type=int,
        default=DEFAULT_HISTORY_LIMIT,
        help="How many historical traces to retain (default: 5).",
    )
    parser.add_argument(
        "passthrough",
        nargs=argparse.REMAINDER,
        help=(
            "Optional extra arguments appended to app.py after the environment "
            "report flag."
        ),
    )
    return parser


def _normalise_argv(argv: Sequence[str]) -> list[str]:
    if not argv:
        return []
    normalised: list[str] = []
    flag = "--history-limit"
    for token in argv:
        if token.startswith(flag) and token not in {flag, f"{flag}=", f"{flag}="}:
            suffix = token[len(flag) :]
            if suffix.isdigit():
                normalised.extend([flag, suffix])
                continue
        normalised.append(token)
    return normalised


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    parsed_argv = _normalise_argv(list(argv) if argv is not None else sys.argv[1:])
    args = parser.parse_args(parsed_argv)
    passthrough = tuple(arg for arg in args.passthrough or [] if arg)

    exit_code = run_launch_trace(passthrough, args.history_limit)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
