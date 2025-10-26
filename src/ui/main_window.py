"""Compatibility shim exposing the main window package as a module."""

from __future__ import annotations

from typing import Any, Dict

from .main_window_pkg import (
    MainWindow,
    get_version_info as _get_version_info,
    menu_actions as menu_actions,
    qml_bridge as qml_bridge,
    signals_router as signals_router,
    state_sync as state_sync,
    ui_setup as ui_setup,
    using_refactored as using_refactored,
)

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


def get_version_info() -> Dict[str, Any]:
    """Return the version info from the underlying package."""

    return _get_version_info()
