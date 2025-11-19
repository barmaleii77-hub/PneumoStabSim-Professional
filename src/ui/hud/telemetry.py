"""Headless-friendly helpers for camera HUD telemetry."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any
from collections.abc import Mapping

__all__ = ["CameraHudTelemetry"]


def _current_timestamp() -> str:
    """Return an ISO 8601 timestamp in UTC with millisecond precision."""

    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(numeric):
        return default
    return numeric


class CameraHudTelemetry:
    """Normalise camera payloads exposed to QML overlays."""

    def _extract_scalar(
        self, payload: Mapping[str, Any], keys: tuple[str, ...], default: float = 0.0
    ) -> float:
        for key in keys:
            if key in payload:
                return _coerce_float(payload.get(key), default)
        return default

    def _vector_component(
        self, payload: Mapping[str, Any], base: str, axis: str, default: float = 0.0
    ) -> float:
        explicit_key = f"{base}_{axis}"
        if explicit_key in payload:
            return _coerce_float(payload.get(explicit_key), default)

        vector = payload.get(base)
        if isinstance(vector, Mapping):
            for candidate in (axis, axis.upper()):
                if candidate in vector:
                    return _coerce_float(vector[candidate], default)

        if isinstance(vector, (tuple, list)):
            index_map = {"x": 0, "y": 1, "z": 2}
            idx = index_map.get(axis)
            if idx is not None and len(vector) > idx:
                return _coerce_float(vector[idx], default)

        return default

    def build(self, payload: Mapping[str, Any] | None) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            return {}

        preset_id = payload.get("orbitPresetId") or payload.get("orbitPreset")
        preset_label = payload.get("orbitPresetLabel")
        preset_default = payload.get("orbitPresetDefault")
        preset_version = payload.get("orbitPresetVersion")

        snapshot = {
            "timestamp": _current_timestamp(),
            "distance": _coerce_float(
                payload.get("orbit_distance", payload.get("distance")), 0.0
            ),
            "yawDeg": _coerce_float(payload.get("orbit_yaw", payload.get("yaw")), 0.0),
            "pitchDeg": _coerce_float(
                payload.get("orbit_pitch", payload.get("pitch")), 0.0
            ),
            "panX": self._vector_component(payload, "pan", "x", 0.0),
            "panY": self._vector_component(payload, "pan", "y", 0.0),
            "panZ": self._vector_component(payload, "pan", "z", 0.0),
            "pivot": {
                "x": self._vector_component(payload, "orbit_target", "x", 0.0),
                "y": self._vector_component(payload, "orbit_target", "y", 0.0),
                "z": self._vector_component(payload, "orbit_target", "z", 0.0),
            },
            "fov": _coerce_float(payload.get("fov", payload.get("field_of_view")), 0.0),
            "speed": _coerce_float(payload.get("speed"), 0.0),
            "nearPlane": self._extract_scalar(
                payload, ("near", "clip_near", "nearPlane"), 0.0
            ),
            "farPlane": self._extract_scalar(
                payload, ("far", "clip_far", "farPlane"), 0.0
            ),
            "autoRotate": bool(payload.get("auto_rotate")),
            "autoRotateSpeed": _coerce_float(payload.get("auto_rotate_speed"), 0.0),
            "inertiaEnabled": bool(payload.get("orbit_inertia_enabled", False)),
            "inertia": _coerce_float(payload.get("orbit_inertia"), 0.0),
            "rotateSmoothing": _coerce_float(
                payload.get("orbit_rotate_smoothing"), 0.0
            ),
            "panSmoothing": _coerce_float(payload.get("orbit_pan_smoothing"), 0.0),
            "zoomSmoothing": _coerce_float(payload.get("orbit_zoom_smoothing"), 0.0),
            "friction": _coerce_float(payload.get("orbit_friction"), 0.0),
            "motionSettlingMs": _coerce_float(
                payload.get("motion_settling_ms", payload.get("motionSettlingMs")), 0.0
            ),
            "rotationDampingMs": _coerce_float(
                payload.get(
                    "rotation_damping_ms",
                    payload.get("rotationDampingMs", payload.get("rotation_damping")),
                ),
                0.0,
            ),
            "panDampingMs": _coerce_float(
                payload.get(
                    "pan_damping_ms",
                    payload.get("panDampingMs", payload.get("pan_damping")),
                ),
                0.0,
            ),
            "distanceDampingMs": _coerce_float(
                payload.get(
                    "distance_damping_ms",
                    payload.get(
                        "distanceDampingMs",
                        payload.get("distance_damping"),
                    ),
                ),
                0.0,
            ),
        }

        if preset_id is not None:
            snapshot["presetId"] = preset_id
        if preset_label is not None:
            snapshot["presetLabel"] = preset_label
        if preset_default is not None:
            snapshot["orbitPresetDefault"] = preset_default
        if preset_version is not None:
            snapshot["orbitPresetVersion"] = preset_version

        return snapshot
