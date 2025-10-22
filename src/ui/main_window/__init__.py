"""MainWindow Module - Refactored with fallback support

Модульная структура главного окна с автоматическим fallback.

**Структура:**
- `main_window.py` - Coordinator (~300 строк)
- `ui_setup.py` - UI construction (~400 строк)
- `qml_bridge.py` - Python↔QML (~300 строк)
- `signals_router.py` - Signal routing (~200 строк)
- `state_sync.py` - State sync (~250 строк)
- `menu_actions.py` - Menu handlers (~150 строк)

**Использование:**
```python
from src.ui.main_window import MainWindow

window = MainWindow(use_qml_3d=True)
window.show()
```

**Fallback:**
При ошибке загрузки рефакторенной версии автоматически
откатывается к оригинальному файлу `../main_window.py`.
"""

# Попытка импортировать рефакторенную версию
_USING_REFACTORED = False

try:
    from .main_window_refactored import MainWindow

    _USING_REFACTORED = True
    print("✅ MainWindow: REFACTORED version loaded (~300 lines coordinator)")
except ImportError as e:
    print(f"⚠️ MainWindow: Refactored version failed ({e}), using LEGACY")
    try:
        from ..main_window import MainWindow

        print("✅ MainWindow: LEGACY version loaded (1053 lines)")
    except ImportError:
        raise ImportError("Cannot load MainWindow (neither refactored nor legacy)")


# Public API
__all__ = ["MainWindow"]


# Версия модуля
__version__ = "4.9.5"


def get_version_info() -> dict:
    """Get module version info

    Returns:
        Dict with version details
    """
    return {
        "version": __version__,
        "using_refactored": _USING_REFACTORED,
        "coordinator_lines": ~300 if _USING_REFACTORED else 1053,
        "modules": 6 if _USING_REFACTORED else 1,
    }
