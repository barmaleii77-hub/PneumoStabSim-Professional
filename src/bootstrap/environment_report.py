"""Генерация Markdown-отчёта окружения на базе environment_check.

Создаёт файл reports/quality/environment_<timestamp>.md
Запуск:
    uv run python -m src.bootstrap.environment_report
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Sequence

from .environment_check import generate_environment_report

_REPORT_DIR = Path("reports/quality")


def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def save_markdown_report(filename: str | None = None) -> Path:
    report = generate_environment_report()
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = _REPORT_DIR / (filename or f"environment_{_ts()}.md")
    path.write_text(report.to_markdown(), encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:  # noqa: ARG001
    save_markdown_report()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
