"""Compatibility shim for historical QML bridge import paths.

The refactored QML bridge lives in :mod:`src.ui.qml_bridge`.  This module keeps
an on-disk copy at ``src/ui/main_window/qml_bridge.py`` so that legacy tooling
and tests which load the file directly from that location continue to function
without modification.
"""

from __future__ import annotations

from src.ui.qml_bridge import (
    QMLBridge,
    QMLBridgeMetadata,
    QMLSignalSpec,
    QMLUpdateError,
    QMLUpdateResult,
    describe_routes,
    get_bridge_metadata,
    register_qml_signals,
)

__all__ = [
    "QMLBridge",
    "QMLBridgeMetadata",
    "QMLSignalSpec",
    "QMLUpdateError",
    "QMLUpdateResult",
    "describe_routes",
    "get_bridge_metadata",
    "register_qml_signals",
]

