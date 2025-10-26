"""Compatibility module for the refactored main-window package.

This module keeps historical imports such as ``from src.ui.main_window import
MainWindow`` working after the refactored implementation was moved into the
``main_window_pkg`` package.  It simply re-exports the public API from the
package and ensures submodule imports like ``src.ui.main_window.menu_actions``
resolve to the new locations.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any
import sys

_pkg = import_module("src.ui.main_window_pkg")
__doc__ = getattr(_pkg, "__doc__")

if hasattr(_pkg, "__spec__"):
    __spec__ = _pkg.__spec__  # type: ignore[assignment]
if hasattr(_pkg, "__path__"):
    __path__ = list(_pkg.__path__)  # type: ignore[assignment]

MainWindow = _pkg.MainWindow
get_version_info = _pkg.get_version_info
using_refactored = _pkg.using_refactored

qml_bridge = _pkg.qml_bridge
signals_router = _pkg.signals_router
ui_setup = _pkg.ui_setup
state_sync = _pkg.state_sync
menu_actions = _pkg.menu_actions

__version__ = getattr(_pkg, "__version__", "0.0.0")

__all__ = [
    "MainWindow",
    "get_version_info",
    "using_refactored",
    "qml_bridge",
    "signals_router",
    "ui_setup",
    "state_sync",
    "menu_actions",
    "__version__",
]


def __getattr__(name: str) -> Any:
    """Delegate attribute lookups to the underlying package."""

    return getattr(_pkg, name)


# Ensure legacy ``import src.ui.main_window.<module>`` statements keep working by
# aliasing the underlying package modules.
for _child_name in (
    "menu_actions",
    "qml_bridge",
    "signals_router",
    "state_sync",
    "ui_setup",
):
    _child = getattr(_pkg, _child_name, None)
    if isinstance(_child, ModuleType):
        sys.modules[f"{__name__}.{_child_name}"] = _child
