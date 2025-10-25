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
import subprocess
import sys
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRACE_ROOT = PROJECT_ROOT / "reports" / "quality" / "launch_traces"
DEFAULT_HISTORY_LIMIT = 5


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


def run_launch_trace(passthrough: Sequence[str], history_limit: int) -> int:
    _ensure_trace_dir()

    timestamp = _utc_now()
    report_path = (
        TRACE_ROOT / f"environment_report_{timestamp.isoformat().replace(':', '-')}.md"
    )
    command = _build_command(report_path, passthrough)

    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
    )

    log_body = completed.stdout or ""
    log_sections = [
        "# PneumoStabSim Launch Trace",
        "",
        f"- Timestamp: {timestamp.isoformat()}",
        f"- Command: {' '.join(command)}",
        f"- Return code: {completed.returncode}",
        f"- Environment report: {report_path.relative_to(PROJECT_ROOT)}",
        "",
        "```",
        log_body.rstrip(),
        "```",
        "",
    ]
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
    }
    _status_path().write_text(
        json.dumps(status_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    _prune_old_traces(history_limit)

    print(
        "Launch trace completed with exit code"
        f" {completed.returncode}. Log saved to"
        f" {log_path.relative_to(PROJECT_ROOT)}",
        file=sys.stdout,
    )

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


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    passthrough = tuple(arg for arg in args.passthrough or [] if arg)

    exit_code = run_launch_trace(passthrough, args.history_limit)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
