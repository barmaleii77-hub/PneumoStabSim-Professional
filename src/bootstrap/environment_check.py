# -*- coding: utf-8 -*-
"""Проверка окружения запуска приложения.

Скрипт выполняет быстрые проверки версии Python/Qt и печатает диагностический отчёт.
"""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass


@dataclass(slots=True)
class EnvReport:
    python: str
    platform: str
    qt: str | None


def collect_env() -> EnvReport:
    """Собрать минимальный отчёт об окружении."""
    try:
        from PySide6.QtCore import qVersion  # type: ignore

        qt_version = qVersion()
    except Exception:
        qt_version = None

    return EnvReport(
        python=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=f"{platform.system()} {platform.release()}",
        qt=qt_version,
    )


def main() -> int:
    report = collect_env()
    print("ENVIRONMENT CHECK")
    print(f"Python: {report.python}")
    print(f"Platform: {report.platform}")
    print(f"Qt: {report.qt or 'unavailable'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
