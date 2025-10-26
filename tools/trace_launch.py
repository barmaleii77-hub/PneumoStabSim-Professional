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
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRACE_ROOT = PROJECT_ROOT / "reports" / "quality" / "launch_traces"
DEFAULT_HISTORY_LIMIT = 5
DOTENV_PATH = PROJECT_ROOT / ".env"
QT_REQUIRED_VARS: tuple[str, ...] = (
    "QT_PLUGIN_PATH",
    "QML2_IMPORT_PATH",
    "QT_QUICK_CONTROLS_STYLE",
)


def _ensure_trace_dir() -> None:
    TRACE_ROOT.mkdir(parents=True, exist_ok=True)


def _utc_now() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0)


def _trace_log_path(timestamp: _dt.datetime) -> Path:
    safe_stamp = timestamp.isoformat().replace(":", "-")
    return TRACE_ROOT / f"launch_trace_{safe_stamp}.log"


def _latest_trace_path() -> Path:
    return TRACE_ROOT / "launch_trace_latest.log"


def _status_path() -> Path:
    return TRACE_ROOT / "launch_trace_status.json"


def _prune_old_traces(limit: int) -> None:
    if limit <= 0:
        return

    traces = sorted(TRACE_ROOT.glob("launch_trace_*.log"))
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


def _ensure_qt_defaults(environment: dict[str, str]) -> None:
    environment.setdefault("QT_API", "PySide6")
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")
    environment.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")


def _compose_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.update(_parse_env_file(DOTENV_PATH))
    _ensure_qt_defaults(env)
    return env


def run_launch_trace(passthrough: Sequence[str], history_limit: int) -> int:
    _ensure_trace_dir()

    timestamp = _utc_now()
    report_path = (
        TRACE_ROOT / f"environment_report_{timestamp.isoformat().replace(':', '-')}.md"
    )
    command = _build_command(report_path, passthrough)
    environment = _compose_environment()

    start = time.perf_counter()
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
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
    log_sections.extend(
        [
            "",
            "```",
            log_body.rstrip(),
            "```",
            "",
        ]
    )
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
    }
    _status_path().write_text(
        json.dumps(status_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    _prune_old_traces(history_limit)

    summary_lines = [
        "Launch trace summary:",
        (" ✅ launch" if completed.returncode == 0 else " ❌ launch")
        + f" (rc={completed.returncode}, {duration:.2f}s)",
        f" Log file: {log_path.relative_to(PROJECT_ROOT)}",
        f" Environment report: {report_path.relative_to(PROJECT_ROOT)}",
    ]
    missing_qt = [var for var in QT_REQUIRED_VARS if not environment.get(var)]
    if missing_qt:
        summary_lines.append(" Missing Qt variables: " + ", ".join(sorted(missing_qt)))
    print("\n".join(summary_lines), file=sys.stdout)

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
    """Return an argv list compatible with ``argparse`` expectations."""

    if not argv:
        return []

    normalised: list[str] = []
    flag = "--history-limit"
    for token in argv:
        if token.startswith(flag) and token not in {flag, f"{flag}=", f"{flag}="}:
            suffix = token[len(flag) :]
            # Accept PowerShell style ``--history-limit5`` while leaving
            # ``--history-limit=5`` untouched for the default argparse behaviour.
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
