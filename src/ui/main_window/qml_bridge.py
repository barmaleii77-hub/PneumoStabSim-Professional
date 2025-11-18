"""Compatibility shim plus 3D bootstrapping helpers.

The refactored QML bridge lives in :mod:`src.ui.qml_bridge`. This module keeps
an on-disk copy at ``src/ui/main_window/qml_bridge.py`` so that legacy tooling
and tests which load the file directly from that location continue to function
without modification. Phase 3 rendering work adds a thin façade for 3D payload
initialisation so Python unit tests can validate the contract without pulling
in the full :mod:`src.ui.main_window_pkg` stack.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from src.common.settings_manager import SettingsManager
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
    "initial_three_d_payload",
    "sync_three_d_state",
]


def _coerce_mapping(candidate: Mapping[str, Any] | None) -> dict[str, Any]:
    if not candidate:
        return {}
    return {str(key): value for key, value in candidate.items()}


def initial_three_d_payload(
    settings_manager: SettingsManager | None = None,
    *,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose the initial 3D payload used by diagnostics scenes.

    The helper draws defaults from ``current.threeD`` when available, falling
    back to a minimal contract expected by the simplified Quick 3D preview
    scene under ``qml/ThreeDScene.qml``.
    """

    defaults = {
        "camera": {
            "azimuth": 35.0,
            "elevation": 25.0,
            "distance": 8.0,
            "target": {"x": 0.0, "y": 0.5, "z": 0.0},
            "pan": {"x": 0.0, "y": 0.0, "z": 0.0},
            "damping": 0.2,
        },
        "primitives": {
            "box": {"scale": 1.2, "color": "#618ccc", "position": [-1.25, 0.5, 0.0]},
            "sphere": {"scale": 0.9, "color": "#c86f55", "position": [1.25, 0.65, 0.0]},
            "cylinder": {"scale": 1.0, "color": "#59bd88", "position": [0.0, 0.9, -1.25]},
        },
        "lighting": {
            "keyIntensity": 600.0,
            "fillIntensity": 280.0,
            "rimIntensity": 220.0,
            "ambient": {"color": "#0f171f"},
        },
    }

    merged = deepcopy(defaults)

    if settings_manager is not None:
        try:
            settings_payload = settings_manager.get("current.threeD", {})
        except Exception:
            settings_payload = {}
        if isinstance(settings_payload, Mapping):
            _deep_merge_dicts(merged, _coerce_mapping(settings_payload))

    if overrides:
        _deep_merge_dicts(merged, _coerce_mapping(overrides))

    return merged


def sync_three_d_state(
    window: Any,
    *,
    settings_manager: SettingsManager | None = None,
    overrides: Mapping[str, Any] | None = None,
    flush: bool = False,
) -> dict[str, Any]:
    """Queue a 3D payload for QML and optionally flush immediately."""

    payload = initial_three_d_payload(settings_manager, overrides=overrides)
    QMLBridge.queue_update(window, "threeD", payload)
    if flush:
        QMLBridge.flush_updates(window)
    return payload


def _deep_merge_dicts(target: dict[str, Any], source: Mapping[str, Any]) -> None:
    for key, value in source.items():
        if (
            key in target
            and isinstance(target[key], dict)
            and isinstance(value, Mapping)
        ):
            _deep_merge_dicts(target[key], value)
        else:
            target[key] = deepcopy(value)
