"""Полная проверка проекта (кросс-платформенная Python-альтернатива PowerShell).

Этапы:
  1. sanitize
  2. env-check
  3. ruff format (check)
  4. ruff lint
  5. mypy
  6. qmllint (если доступен)
  7. pytest -vv
  8. launch-trace
  9. app --test-mode

Логи: reports/quality/full_verify_<timestamp>.log
Запуск:
    uv run python -m tools.full_verify --fail-fast --trace-history 3
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

_REPORT_DIR = Path("reports/quality")


def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _log_path() -> Path:
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return _REPORT_DIR / f"full_verify_{_ts()}.log"


def _write(log: Path, message: str) -> None:
    line = f"{_dt.datetime.now().isoformat()} {message}".rstrip()
    print(line)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _run(log: Path, name: str, argv: Sequence[str]) -> int:
    _write(log, f"=== STEP [{name}] START ===")
    try:
        try:
            proc = subprocess.run(
                argv, capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
        except Exception as inner_exc:  # pragma: no cover
            proc = subprocess.run(argv)
            _write(log, f"[fallback] capture disabled: {inner_exc}")
    except Exception as exc:  # pragma: no cover
        _write(log, f"=== STEP [{name}] EXCEPTION: {exc}")
        return 1
    if getattr(proc, "stdout", None):
        _write(log, proc.stdout)
    if getattr(proc, "stderr", None):
        _write(log, proc.stderr)
    _write(log, f"=== STEP [{name}] END (rc={proc.returncode}) ===")
    return proc.returncode


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Кросс-платформенная полная проверка")
    parser.add_argument(
        "--trace-history", type=int, default=10, help="Лимит истории launch-trace"
    )
    parser.add_argument(
        "--fail-fast", action="store_true", help="Останов при первой ошибке"
    )
    args = parser.parse_args(argv)

    log = _log_path()
    _write(log, f"Session log: {log}")
    _write(log, f"Python: {sys.version}")
    _write(log, f"CWD: {os.getcwd()}")

    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    stages: list[tuple[str, list[str]]] = [
        (
            "sanitize",
            [
                "uv",
                "run",
                "python",
                "-m",
                "tools.project_sanitize",
                "--report-history",
                "5",
            ],
        ),
        ("env-check", ["uv", "run", "python", "app.py", "--env-check"]),
        (
            "ruff-format",
            [
                "uv",
                "run",
                "python",
                "-m",
                "ruff",
                "format",
                "--check",
                "app.py",
                "src",
                "tests",
                "tools",
            ],
        ),
        (
            "ruff-lint",
            [
                "uv",
                "run",
                "python",
                "-m",
                "ruff",
                "check",
                "app.py",
                "src",
                "tests",
                "tools",
            ],
        ),
        ("mypy", ["uv", "run", "mypy", "src"]),
    ]

    qmllint = None
    for candidate in ("pyside6-qmllint", "qmllint"):
        if shutil.which(candidate):
            qmllint = candidate
            break
    if qmllint:
        stages.append(("qmllint", [qmllint, "assets/qml/main.qml"]))

    stages.extend(
        [
            ("pytest", ["uv", "run", "pytest", "-vv"]),
            (
                "launch-trace",
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "tools.trace_launch",
                    "--history-limit",
                    str(args.trace_history),
                ],
            ),
            ("app-test-mode", ["uv", "run", "python", "app.py", "--test-mode"]),
        ]
    )

    overall_rc = 0
    for name, cmd in stages:
        rc = _run(log, name, cmd)
        if rc != 0:
            overall_rc = rc
            if args.fail_fast:
                break
    _write(log, "Full verify completed.")
    return overall_rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
