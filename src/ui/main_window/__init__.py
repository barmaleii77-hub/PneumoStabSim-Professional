"""Compatibility package exposing the refactored main window modules.

The original codebase stored the entire main-window implementation in
``src/ui/main_window.py``.  During the ongoing renovation this logic was split
into dedicated modules under :mod:`src.ui.main_window_pkg`.  Some integration
and test utilities, however, still expect the legacy package layout with
``src/ui/main_window/qml_bridge.py`` and related helpers.  This package bridges
that gap by re-exporting the refactored implementation while keeping the public
API surface stable.
"""

from __future__ import annotations

from typing import Any

from src.ui.main_window_pkg import (
    MainWindow as _PkgMainWindow,
    get_version_info as _pkg_get_version_info,
    menu_actions as _pkg_menu_actions,
    signals_router as _pkg_signals_router,
    state_sync as _pkg_state_sync,
    ui_setup as _pkg_ui_setup,
    using_refactored as _pkg_using_refactored,
)

__all__ = [
    "MainWindow",
    "get_version_info",
    "using_refactored",
    "qml_bridge",
    "signals_router",
    "state_sync",
    "ui_setup",
    "menu_actions",
]

# -- High level coordinator -------------------------------------------------

MainWindow = _PkgMainWindow
get_version_info = _pkg_get_version_info
using_refactored = _pkg_using_refactored

# -- Module compatibility aliases -------------------------------------------

# ``qml_bridge`` is provided as a local module so tests that load it directly
# from the filesystem (``src/ui/main_window/qml_bridge.py``) continue to work.
from . import qml_bridge  # noqa: E402  (import after defining __all__)

# Other helper modules are re-exported from ``main_window_pkg`` without
# creating duplicate source files.  They remain accessible via
# ``src.ui.main_window.signals_router`` etc.
signals_router = _pkg_signals_router
state_sync = _pkg_state_sync
ui_setup = _pkg_ui_setup
menu_actions = _pkg_menu_actions


def describe_modules() -> dict[str, Any]:
    """Return diagnostic information about the exposed helper modules.

    The helper mirrors the structure used by historical tooling that enumerated
    the legacy monolithic file.  Returning a stable mapping keeps those tools
    functioning without requiring additional migrations.
    """

    return {
        "using_refactored": using_refactored(),
        "modules": {
            "qml_bridge": qml_bridge,
            "signals_router": signals_router,
            "state_sync": state_sync,
            "ui_setup": ui_setup,
            "menu_actions": menu_actions,
        },
    }
