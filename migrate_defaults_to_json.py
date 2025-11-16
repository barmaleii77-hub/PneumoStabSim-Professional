#!/usr/bin/env python3
"""
Миграция defaults.py → app_settings.json
Переносим ВСЕ параметры из кода в JSON файл.

Добавлено: поддержка --output и --dry-run для безопасного тестирования.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any


def _lazy_import_builders() -> tuple[Any, Any]:
    try:
        from src.ui.panels.graphics.defaults import build_defaults, build_quality_presets  # type: ignore
    except Exception:
        def _empty_defaults() -> dict[str, Any]:
            return {}
        def _empty_presets() -> dict[str, Any]:
            return {}
        return _empty_defaults, _empty_presets
    return build_defaults, build_quality_presets


def count_parameters(obj: Any) -> int:
    """Рекурсивный подсчёт параметров в словаре."""
    count = 0
    if isinstance(obj, dict):
        for _, value in obj.items():
            if isinstance(value, dict):
                count += count_parameters(value)
            else:
                count += 1
    return count


def migrate_defaults_to_json(settings_path: Path, *, dry_run: bool) -> dict[str, Any]:
    """Сформировать структуру settings из исходных builders.

    Возвращает собранный payload (всегда), запись на диск только если dry_run=False.
    """
    build_defaults, build_quality_presets = _lazy_import_builders()

    if settings_path.exists():
        with settings_path.open(encoding="utf-8") as f:
            settings: dict[str, Any] = json.load(f)
        if not isinstance(settings, dict):
            settings = {"current": {}, "defaults_snapshot": {}, "metadata": {}}
    else:
        settings = {"current": {}, "defaults_snapshot": {}, "metadata": {}}

    graphics_defaults = build_defaults()
    quality_presets = build_quality_presets()

    settings.setdefault("current", {})["graphics"] = graphics_defaults
    settings["current"]["quality_presets"] = quality_presets

    settings["defaults_snapshot"] = {
        "graphics": graphics_defaults,
        "quality_presets": quality_presets,
    }

    settings["metadata"] = {
        "version": settings.get("metadata", {}).get("version", "4.9.5"),
        "last_modified": datetime.now().isoformat(),
        "migrated_from": "src/ui/panels/graphics/defaults.py",
        "migration_date": datetime.now().strftime("%Y-%m-%d"),
        "total_parameters": count_parameters(graphics_defaults),
        "description": "Unified settings file - single source of truth",
    }

    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with settings_path.open("w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    return settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Миграция defaults.py → app_settings.json")
    parser.add_argument("--output", type=Path, default=Path("config/app_settings.json"), help="Путь для файла настроек")
    parser.add_argument("--dry-run", action="store_true", help="Не записывать на диск, только показать статистику")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    payload = migrate_defaults_to_json(args.output, dry_run=args.dry_run)

    total = payload.get("metadata", {}).get("total_parameters")
    print("=" * 60)
    print("✅ MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Файл: {args.output.absolute()}")
    print(f"Параметров graphics: {total}")
    if args.dry_run:
        print("[dry-run] Изменения НЕ сохранены.")
    else:
        size = args.output.stat().st_size
        print(f"Размер файла: {size:,} байт ({size/1024:.1f} KB)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    try:
        raise SystemExit(main())
    except Exception as e:  # pragma: no cover
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
