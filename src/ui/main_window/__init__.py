"""Main window package with refactored and legacy fallbacks."""

from __future__ import annotations

from typing import Any, Dict

__all__ = [
    "MainWindow",
    "get_version_info",
    "using_refactored",
    "qml_bridge",
    "signals_router",
    "ui_setup",
    "state_sync",
    "menu_actions",
]

__version__ = "4.9.5"
_USING_REFACTORED = False

try:
    from .main_window_refactored import MainWindow
except ImportError as refactored_error:
    try:
        from ..main_window_legacy import MainWindow  # type: ignore[misc]
    except (
        ImportError
    ) as legacy_error:  # pragma: no cover - catastrophic import failure
        raise ImportError("Cannot load main-window implementation") from legacy_error
    else:
        _USING_REFACTORED = False
else:
    _USING_REFACTORED = True

from . import menu_actions as _menu_actions  # noqa: E402
from . import qml_bridge as _qml_bridge  # noqa: E402
from . import signals_router as _signals_router  # noqa: E402
from . import state_sync as _state_sync  # noqa: E402
from . import ui_setup as _ui_setup  # noqa: E402


def using_refactored() -> bool:
    """Return ``True`` when the refactored window implementation was imported."""

    return _USING_REFACTORED


def get_version_info() -> Dict[str, Any]:
    """Return diagnostic information about the loaded main-window module."""

    return {
        "version": __version__,
        "using_refactored": _USING_REFACTORED,
        "coordinator_lines": 300 if _USING_REFACTORED else 1053,
        "modules": 6 if _USING_REFACTORED else 1,
    }


qml_bridge = _qml_bridge
signals_router = _signals_router
ui_setup = _ui_setup
state_sync = _state_sync
menu_actions = _menu_actions
