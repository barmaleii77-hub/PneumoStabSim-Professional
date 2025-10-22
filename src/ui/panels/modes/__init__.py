# -*- coding: utf-8 -*-
"""
ModesPanel module - switch fallback mechanism
Модуль панели режимов симуляции с механизмом отката
"""

# Попытка импорта refactored версии
_USING_REFACTORED = False
_IMPORT_ERROR = None

try:
    from .panel_modes_refactored import ModesPanel

    _USING_REFACTORED = True
    print("✅ ModesPanel: Используется REFACTORED версия")
except ImportError as e:
    _IMPORT_ERROR = str(e)
    print(f"⚠️ ModesPanel: Ошибка импорта refactored версии: {e}")
    print("   Откат на оригинальную версию...")

    try:
        from ..panel_modes import ModesPanel

        _USING_REFACTORED = False
        print("✅ ModesPanel: Используется ORIGINAL версия")
    except ImportError as e2:
        print("❌ ModesPanel: Не удалось импортировать ни одну версию!")
        print(f"   Refactored error: {_IMPORT_ERROR}")
        print(f"   Original error: {e2}")
        raise

__all__ = ["ModesPanel"]
