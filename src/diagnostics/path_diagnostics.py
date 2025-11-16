"""Path diagnostics helpers for PneumoStabSim tests and runtime.

Русскоязычные утилиты для единообразной проверки путей:
- verify_repo_root(): убеждается что рабочая директория == корень репозитория
- collect_path_snapshot(): собирает словарь ключевых путей
- dump_path_snapshot(): сохраняет snapshot в reports/tests/path_diagnostics

Используется автотестами и при запуске приложения с флагом --env-paths.
"""

from __future__ import annotations

from pathlib import Path
import os
import json
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_ROOT = PROJECT_ROOT / "reports" / "tests" / "path_diagnostics"


def verify_repo_root() -> bool:
    """Проверить что cwd совпадает с корнем репозитория.

    Возвращает True если совпадает, иначе False. Не выбрасывает исключения.
    """
    try:
        cwd = Path.cwd().resolve()
        return cwd == PROJECT_ROOT.resolve()
    except Exception:
        return False


def collect_path_snapshot() -> dict[str, Any]:
    """Собрать словарь с ключевыми путями и флагами наличия.

    Поля:
      cwd, project_root, python_exe, settings_file, hdr_dir, qml_dir,
      hdr_dir_exists, settings_exists.
    """
    settings_file = PROJECT_ROOT / "config" / "app_settings.json"
    hdr_dir = PROJECT_ROOT / "assets" / "hdr"
    qml_dir = PROJECT_ROOT / "assets" / "qml"
    return {
        "cwd": str(Path.cwd()),
        "project_root": str(PROJECT_ROOT),
        "python_exe": sys.executable,
        "settings_file": str(settings_file),
        "settings_exists": settings_file.exists(),
        "hdr_dir": str(hdr_dir),
        "hdr_dir_exists": hdr_dir.exists(),
        "qml_dir": str(qml_dir),
        "qml_dir_exists": qml_dir.exists(),
        "env_PATH": os.environ.get("PATH", "")[:512],
    }


def dump_path_snapshot(snapshot: dict[str, Any] | None = None) -> Path | None:
    """Сохранить snapshot в JSON, вернуть путь или None при ошибке."""
    try:
        REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
        payload = snapshot or collect_path_snapshot()
        target = REPORTS_ROOT / "runtime_paths.json"
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return target
    except Exception:
        return None


__all__ = [
    "verify_repo_root",
    "collect_path_snapshot",
    "dump_path_snapshot",
]
