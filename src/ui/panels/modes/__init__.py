# -*- coding: utf-8 -*-
"""
ModesPanel module -swith fallback mechanism
Модуль панели режимов симуляции с механизмом отката
"""
import sys
from typing import Any

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
        # Откат на оригинальную версию
        from ..panel_modes import ModesPanel
        _USING_REFACTORED = False
        print("✅ ModesPanel: Используется ORIGINAL версия")
    except ImportError as e2:
        print(f"❌ ModesPanel: Не удалось импортировать ни одну версию!")
        print(f"   Refactored error: {_IMPORT_ERROR}")
        print(f"   Original error: {e2}")
        raise

# Экспорт дополнительных компонентов (если доступны)
__all__ = ['ModesPanel']

if _USING_REFACTORED:
    try:
        from .state_manager import ModesStateManager
        from .defaults import (
            DEFAULT_MODES_PARAMS,
            DEFAULT_PHYSICS_OPTIONS,
            MODE_PRESETS,
            PARAMETER_RANGES
        )
        __all__.extend([
            'ModesStateManager',
            'DEFAULT_MODES_PARAMS',
            'DEFAULT_PHYSICS_OPTIONS',
            'MODE_PRESETS',
            'PARAMETER_RANGES'
        ])
    except ImportError:
        pass


def get_version_info() -> dict[str, Any]:
    """Получить информацию о версии модуля"""
    return {
        'using_refactored': _USING_REFACTORED,
        'import_error': _IMPORT_ERROR,
        'available_exports': __all__,
        'module_path': __file__
    }


def is_refactored() -> bool:
    """Проверить, используется ли refactored версия"""
    return _USING_REFACTORED
