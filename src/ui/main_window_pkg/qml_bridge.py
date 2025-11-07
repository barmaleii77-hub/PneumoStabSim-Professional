"""Compatibility shim re-exporting the consolidated QML bridge helpers."""

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
