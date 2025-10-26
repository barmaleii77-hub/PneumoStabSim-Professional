"""Compatibility shim for the PneumoStabSim main window module.

The legacy repository stored the Qt entry point in ``src/ui/main_window.py``
while the refactored implementation split the logic across the
``src/ui/main_window/`` package.  Git cannot auto-merge those layouts,
resulting in recurring tree conflicts.  This module keeps the historic
import path alive and proxies all behaviour to the package now stored in
``src/ui/main_window_pkg``.

Importers may continue to use ``from src.ui.main_window import MainWindow``
or ``from src.ui.main_window import qml_bridge`` exactly as before.  The
shim loads the modular implementation when available and falls back to the
legacy widget on import errors, mirroring the behaviour of the previous
package ``__init__``.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, Dict

__all__ = ["MainWindow", "get_version_info", "using_refactored"]

__version__ = "4.9.5"
_using_refactored = False


def _load_refactored() -> type:
    """Return the refactored ``MainWindow`` implementation."""

    module = import_module(".main_window_pkg.main_window_refactored", __package__)
    return getattr(module, "MainWindow")


try:
    MainWindow = _load_refactored()
    _using_refactored = True
except ImportError:
    from .main_window_legacy import MainWindow  # type: ignore[misc]

    _using_refactored = False


# -- Helper modules ---------------------------------------------------------
# NOTE: These imports are eagerly resolved to keep backwards compatible
# ``from src.ui.main_window import qml_bridge`` style usage working.  They are
# relatively small modules and safe to import at module load time.
_qml_bridge_module = import_module(".main_window_pkg.qml_bridge", __package__)
_signals_router_module = import_module(".main_window_pkg.signals_router", __package__)
_ui_setup_module = import_module(".main_window_pkg.ui_setup", __package__)
_state_sync_module = import_module(".main_window_pkg.state_sync", __package__)
_menu_actions_module = import_module(".main_window_pkg.menu_actions", __package__)

# Public re-exports expected by existing imports.
qml_bridge = _qml_bridge_module
signals_router = _signals_router_module
ui_setup = _ui_setup_module
state_sync = _state_sync_module
menu_actions = _menu_actions_module


def using_refactored() -> bool:
    """Return ``True`` when the refactored window loaded successfully."""

    return _using_refactored


def get_version_info() -> Dict[str, Any]:
    """Report metadata about the loaded main-window implementation."""

    return {
        "version": __version__,
        "using_refactored": _using_refactored,
        "coordinator_lines": 300 if _using_refactored else 1053,
        "modules": 6 if _using_refactored else 1,
    }


# Keep backwards compatibility for ``dir(src.ui.main_window)`` by registering
# helper modules in ``sys.modules``.  This mirrors a package-like layout so
# ``inspect.getmodule`` continues to return sensible paths for the helpers.
def _register_helper_module(attr: str, module: ModuleType) -> None:
    import sys

    qualified = f"{__name__}.{attr}"
    sys.modules.setdefault(qualified, module)


_register_helper_module("qml_bridge", _qml_bridge_module)
_register_helper_module("signals_router", _signals_router_module)
_register_helper_module("ui_setup", _ui_setup_module)
_register_helper_module("state_sync", _state_sync_module)
_register_helper_module("menu_actions", _menu_actions_module)
