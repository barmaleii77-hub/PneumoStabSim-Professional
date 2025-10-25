"""Autonomous repository verification runner.

This helper executes the configured quality gates (linting, type checking,
QML linting, and tests) and persists timestamped logs under
``reports/quality``. It is designed so CI agents or local developers can
trigger a single command and later inspect a structured artefact describing
what ran, when, and whether it succeeded.

When requested, the runner can perform an optional repository sanitisation via
``tools.project_sanitize`` before the checks start. This keeps transient
artefacts such as ``__pycache__`` folders or stale Visual Studio workspace
files from polluting the log output and mirrors the "sanitary cleanup" stage
referenced in the modernisation playbooks.

The runner can also perform a launch trace using ``tools.trace_launch`` so
that OpenGL and Qt environment diagnostics are recorded alongside the quality
gate results. This provides a single entry point for both static checks and
runtime bootstrap validation.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports" / "quality"
DEFAULT_HISTORY_LIMIT = 7
DEFAULT_TRACE_HISTORY_LIMIT = 5
DEFAULT_SANITIZE_HISTORY = 3

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


def _build_trace_command(history_limit: int, trace_args: Sequence[str]) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "tools.trace_launch",
        "--history-limit",
        str(history_limit),
        *trace_args,
    ]
    return command


def _run_commands(
    commands: Iterable[tuple[str, Sequence[str]]],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for label, command in commands:
        completed = subprocess.run(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=PROJECT_ROOT,
            check=False,
        )

        results.append(
            {
                "label": label,
                "command": list(command),
                "return_code": completed.returncode,
                "stdout": completed.stdout or "",
            }
        )

    return results


def run_autonomous_check(
    task: str,
    extra_args: Sequence[str],
    history_limit: int,
    launch_trace: bool,
    trace_args: Sequence[str],
    trace_history_limit: int,
    sanitize: bool,
    sanitize_history: int,
) -> int:
    _ensure_report_dir()

    timestamp = _utc_now()
    commands: list[tuple[str, Sequence[str]]] = []

    if sanitize:
        sanitize_command: Sequence[str] = (
            sys.executable,
            "-m",
            "tools.project_sanitize",
            "--report-history",
            str(max(sanitize_history, 0)),
        )
        commands.append(("sanitize", sanitize_command))

    commands.append(("quality", _build_command(task, extra_args)))

    if launch_trace:
        commands.append(
            (
                "launch_trace",
                _build_trace_command(trace_history_limit, trace_args),
            )
        )

    results = _run_commands(commands)

    log_sections = [
        "# PneumoStabSim Autonomous Check",
        "",
        f"- Timestamp: {timestamp.isoformat()}",
        f"- Steps executed: {len(results)}",
        "",
    ]

    for result in results:
        log_sections.extend(
            [
                f"## Step: {result['label']}",
                "",
                f"- Command: {' '.join(result['command'])}",
                f"- Return code: {result['return_code']}",
                "",
                "```",
                str(result["stdout"]).rstrip(),
                "```",
                "",
            ]
        )

    log_text = "\n".join(log_sections)
    log_path = _log_path(timestamp)
    log_path.write_text(log_text + "\n", encoding="utf-8")

    latest_path = _latest_log_path()
    latest_path.write_text(log_text + "\n", encoding="utf-8")

    overall_return_code = max(result["return_code"] for result in results)
    status_payload = {
        "timestamp": timestamp.isoformat(),
        "commands": [
            {
                "label": result["label"],
                "command": result["command"],
                "return_code": result["return_code"],
            }
            for result in results
        ],
        "log_path": str(log_path.relative_to(PROJECT_ROOT)),
        "success": overall_return_code == 0,
    }
    _status_path().write_text(
        json.dumps(status_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    _prune_old_logs(history_limit)

    print(
        "Autonomous check completed with exit code",
        f" {overall_return_code}. Log saved to",
        f" {log_path.relative_to(PROJECT_ROOT)}",
        file=sys.stdout,
    )

    return int(overall_return_code)


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
        "--launch-trace",
        action="store_true",
        help=(
            "Also run tools.trace_launch after completing the selected task "
            "to capture environment diagnostics."
        ),
    )
    parser.add_argument(
        "--trace-history-limit",
        type=int,
        default=None,
        help=(
            "Override how many launch trace artefacts are retained when the "
            "trace step is enabled (default mirrors tools.trace_launch)."
        ),
    )
    parser.add_argument(
        "--sanitize",
        action="store_true",
        help=(
            "Run tools.project_sanitize before executing the selected task to "
            "remove transient artefacts and prune historical logs."
        ),
    )
    parser.add_argument(
        "--sanitize-history",
        type=int,
        default=DEFAULT_SANITIZE_HISTORY,
        help=(
            "How many historical quality artefacts should be kept when the "
            "sanitize step runs (default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--trace-arg",
        dest="trace_args",
        action="append",
        default=None,
        help=(
            "Additional arguments appended to tools.trace_launch. Repeat the "
            "option for multiple values."
        ),
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
    trace_args: Sequence[str] = tuple(arg for arg in args.trace_args or [] if arg)
    trace_history_limit = (
        args.trace_history_limit
        if args.trace_history_limit is not None
        else DEFAULT_TRACE_HISTORY_LIMIT
    )

    exit_code = run_autonomous_check(
        args.task,
        extra_args,
        args.history_limit,
        args.launch_trace,
        trace_args,
        trace_history_limit,
        args.sanitize,
        args.sanitize_history,
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
