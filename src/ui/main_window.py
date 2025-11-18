"""Compatibility shim for legacy imports of :mod:`src.ui.main_window`.

This module proxies to the refactored implementation in
:mod:`src.ui.main_window_pkg` while keeping backward compatibility for older
entrypoints and tests that still import ``MainWindow`` from the historical
location.  Keep this file lightweight: the heavy Qt imports remain lazy inside
``main_window_pkg`` so that non-GUI tooling can continue to run in headless
CI environments.
"""

from __future__ import annotations

from src.ui.main_window_pkg import (
    MainWindow,
    get_version_info,
    menu_actions,
    signals_router,
    state_sync,
    ui_setup,
    using_refactored,
)

__all__ = [
    "MainWindow",
    "get_version_info",
    "using_refactored",
    "signals_router",
    "state_sync",
    "ui_setup",
    "menu_actions",
]
