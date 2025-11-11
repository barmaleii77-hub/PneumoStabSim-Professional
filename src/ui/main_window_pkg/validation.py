from __future__ import annotations

import math
from typing import Any, Mapping

from ..panels.modes.defaults import (
    DEFAULT_PHYSICS_OPTIONS,
    PARAMETER_RANGES,
    SIMULATION_TYPES,
    THERMO_MODES,
)

__all__ = [
    "clamp_parameter_value",
    "normalise_mode_value",
    "sanitize_physics_payload",
]


_RANGE_ALIASES: dict[str, str] = {
    "phase_global": "phase",
    "phase": "phase",
    "lf_phase": "wheel_phase",
    "rf_phase": "wheel_phase",
    "lr_phase": "wheel_phase",
    "rr_phase": "wheel_phase",
    "smoothingDurationMs": "smoothing_duration_ms",
    "smoothingAngleSnapDeg": "smoothing_angle_snap_deg",
    "smoothingPistonSnapM": "smoothing_piston_snap_m",
}

_NON_NEGATIVE_NUMERIC_KEYS = {
    "spring_constant",
    "damper_coefficient",
    "damper_force_threshold_n",
    "lever_inertia_multiplier",
}


def _to_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(numeric) or math.isinf(numeric):
        return None
    return numeric


def clamp_parameter_value(name: str, value: Any) -> float | None:
    """Clamp numeric parameter to metadata-defined range."""

    numeric = _to_float(value)
    if numeric is None:
        return None

    alias = _RANGE_ALIASES.get(name, name)
    range_info = PARAMETER_RANGES.get(alias)
    if not range_info:
        return numeric

    minimum = _to_float(range_info.get("min"))
    maximum = _to_float(range_info.get("max"))

    if minimum is not None and numeric < minimum:
        numeric = minimum
    if maximum is not None and numeric > maximum:
        numeric = maximum
    return numeric


def normalise_mode_value(mode_type: str, value: str | None) -> str | None:
    """Normalise mode strings to canonical uppercase values."""

    if not value:
        return None

    normalized = str(value).strip().upper()
    if not normalized:
        return None

    mode_key = (mode_type or "").strip().lower()
    if mode_key == "sim_type":
        allowed = {key.upper(): key for key in SIMULATION_TYPES.keys()}
        return allowed.get(normalized, None)
    if mode_key == "thermo_mode":
        allowed = {key.upper(): key for key in THERMO_MODES.keys()}
        return allowed.get(normalized, None)
    return normalized


def sanitize_physics_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Sanitize physics toggle payload coming from QML."""

    sanitized: dict[str, Any] = {}
    for key, default in DEFAULT_PHYSICS_OPTIONS.items():
        if key not in payload:
            continue
        raw_value = payload[key]
        if isinstance(default, bool):
            sanitized[key] = bool(raw_value)
            continue
        numeric = _to_float(raw_value)
        if numeric is None:
            numeric = float(default)
        if key in _NON_NEGATIVE_NUMERIC_KEYS and numeric < 0:
            numeric = 0.0
        sanitized[key] = numeric
    return sanitized
