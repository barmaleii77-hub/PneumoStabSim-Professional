#!/usr/bin/env python3
"""
Миграция defaults.py → app_settings.json
Переносим ВСЕ 244 параметра из кода в JSON файл
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Добавляем src в path для импорта
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.panels.graphics.defaults import build_defaults, build_quality_presets


def migrate_defaults_to_json():
    """
    Мигрировать defaults.py → config/app_settings.json

    Структура итогового файла:
    {
        "current": { ... текущие настройки ...},
        "defaults_snapshot": { ... сохранённые дефолты ... },
        "metadata": { "version", "last_modified", ... }
    }
    """

    print("=" * 60)
    print("🔄 МИГРАЦИЯ ДЕФОЛТОВ: defaults.py → app_settings.json")
    print("=" * 60)

    # Путь к файлу настроек
    settings_file = Path("config/app_settings.json")

    # Загружаем текущий файл (если существует)
    if settings_file.exists():
        print(f"\n📁 Загружаем существующий файл: {settings_file}")
        with open(settings_file, encoding="utf-8") as f:
            settings = json.load(f)
    else:
        print(f"\n📁 Создаём новый файл: {settings_file}")
        settings = {"current": {}, "defaults_snapshot": {}, "metadata": {}}

    # Получаем все дефолты из defaults.py
    print("\n⚙️ Загружаем дефолты из defaults.py...")
    graphics_defaults = build_defaults()
    quality_presets = build_quality_presets()

    print(f"   ✅ graphics: {count_parameters(graphics_defaults)} параметров")
    print(f"   ✅ quality_presets: {len(quality_presets)} пресетов")

    # Обновляем структуру
    print("\n📝 Обновляем структуру app_settings.json...")

    # Current settings
    if "current" not in settings:
        settings["current"] = {}

    settings["current"]["graphics"] = graphics_defaults
    settings["current"]["quality_presets"] = quality_presets

    # Defaults snapshot (копия current)
    settings["defaults_snapshot"] = {
        "graphics": graphics_defaults,
        "quality_presets": quality_presets,
    }

    # Metadata
    settings["metadata"] = {
        "version": "4.9.5",
        "last_modified": datetime.now().isoformat(),
        "migrated_from": "src/ui/panels/graphics/defaults.py",
        "migration_date": datetime.now().strftime("%Y-%m-%d"),
        "total_parameters": count_parameters(graphics_defaults),
        "description": "Unified settings file - single source of truth",
    }

    # Сохраняем с отступами
    print(f"\n💾 Сохраняем в {settings_file}...")
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    # Статистика
    file_size = settings_file.stat().st_size

    print("\n" + "=" * 60)
    print("✅ МИГРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 60)
    print("\n📊 Статистика:")
    print(f"   Параметров: {count_parameters(graphics_defaults)}")
    print(f"   Размер файла: {file_size:,} байт ({file_size / 1024:.1f} KB)")
    print(f"   Файл: {settings_file.absolute()}")

    print("\n🎯 Следующие шаги:")
    print(f"   1. Проверьте {settings_file}")
    print(
        "   2. Обновите panel_graphics_refactored.py для использования SettingsManager"
    )
    print("   3. Удалите src/ui/panels/graphics/defaults.py")

    print("\n✅ Готово!")


def count_parameters(obj):
    """Рекурсивный подсчёт параметров в словаре"""
    count = 0
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, dict):
                count += count_parameters(value)
            else:
                count += 1
    return count


if __name__ == "__main__":
    try:
        migrate_defaults_to_json()
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
