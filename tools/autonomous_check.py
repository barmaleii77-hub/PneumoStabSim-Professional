"""Autonomous repository verification runner.

This helper executes the configured quality gates (linting, type checking,
QML linting, and tests) and persists timestamped logs under
``reports/quality``. It is designed so CI agents or local developers can
trigger a single command and later inspect a structured artefact describing
what ran, when, and whether it succeeded.
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
REPORT_DIR = PROJECT_ROOT / "reports" / "quality"
DEFAULT_HISTORY_LIMIT = 7

_TASK_COMMANDS: dict[str, Sequence[str]] = {
    "verify": ("-m", "tools.ci_tasks", "verify"),
    "lint": ("-m", "tools.ci_tasks", "lint"),
    "typecheck": ("-m", "tools.ci_tasks", "typecheck"),
    "qml-lint": ("-m", "tools.ci_tasks", "qml-lint"),
    "test": ("-m", "tools.ci_tasks", "test"),
}


def _ensure_report_dir() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _utc_now() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0)


def _log_path(timestamp: _dt.datetime) -> Path:
    safe_stamp = timestamp.isoformat().replace(":", "-")
    return REPORT_DIR / f"autonomous_check_{safe_stamp}.log"


def _latest_log_path() -> Path:
    return REPORT_DIR / "autonomous_check_latest.log"


def _status_path() -> Path:
    return REPORT_DIR / "autonomous_check_status.json"


def _prune_old_logs(limit: int) -> None:
    if limit <= 0:
        return

    log_files = sorted(REPORT_DIR.glob("autonomous_check_*.log"))
    excess = len(log_files) - limit
    if excess <= 0:
        return

    for path in log_files[:excess]:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _build_command(task: str, extra_args: Sequence[str]) -> list[str]:
    if task not in _TASK_COMMANDS:
        valid = ", ".join(sorted(_TASK_COMMANDS))
        raise ValueError(f"Unknown task '{task}'. Valid options: {valid}")

    command = [sys.executable, *_TASK_COMMANDS[task], *extra_args]
    return command


def run_autonomous_check(
    task: str, extra_args: Sequence[str], history_limit: int
) -> int:
    _ensure_report_dir()

    timestamp = _utc_now()
    command = _build_command(task, extra_args)

    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
    )

    log_body = completed.stdout or ""
    header = [
        "# PneumoStabSim Autonomous Check",
        "",
        f"- Timestamp: {timestamp.isoformat()}",
        f"- Command: {' '.join(command)}",
        f"- Return code: {completed.returncode}",
        "",
        "```",
        log_body.rstrip(),
        "```",
        "",
    ]

    log_text = "\n".join(header)
    log_path = _log_path(timestamp)
    log_path.write_text(log_text + "\n", encoding="utf-8")

    latest_path = _latest_log_path()
    latest_path.write_text(log_text + "\n", encoding="utf-8")

    status_payload = {
        "timestamp": timestamp.isoformat(),
        "command": command,
        "return_code": completed.returncode,
        "log_path": str(log_path.relative_to(PROJECT_ROOT)),
        "success": completed.returncode == 0,
    }
    _status_path().write_text(
        json.dumps(status_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    _prune_old_logs(history_limit)

    print(
        f"Autonomous check completed with exit code {completed.returncode}. "
        f"Log saved to {log_path.relative_to(PROJECT_ROOT)}",
        file=sys.stdout,
    )

    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run repository quality gates and persist logs under reports/quality.",
    )
    parser.add_argument(
        "--task",
        choices=sorted(_TASK_COMMANDS),
        default="verify",
        help="Which tools.ci_tasks command to execute (default: verify).",
    )
    parser.add_argument(
        "--history-limit",
        type=int,
        default=DEFAULT_HISTORY_LIMIT,
        help="How many historical log files to retain (default: 7).",
    )
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help=(
            "Optional additional arguments appended to the selected task. "
            "Start the list with '--' if the first value looks like an option."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    extra_args: Sequence[str] = tuple(arg for arg in args.extra_args or [] if arg)

    exit_code = run_autonomous_check(args.task, extra_args, args.history_limit)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
