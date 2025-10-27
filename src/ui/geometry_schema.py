"""Validation helpers for geometry configuration payloads.

The production application relies on Qt widgets which are unavailable inside
the execution environment used by the unit tests. The helpers defined here are
pure-Python so they can be exercised without requiring the GUI stack.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Mapping


class GeometryValidationError(ValueError):
    """Raised when a geometry payload fails validation."""


@dataclass(frozen=True)
class GeometrySettings:
    """Typed container for validated geometry parameters."""

    wheelbase: float
    track: float
    frame_to_pivot: float
    lever_length: float
    rod_position: float
    cylinder_length: float
    cyl_diam_m: float
    stroke_m: float
    dead_gap_m: float
    rod_diameter_m: float
    piston_rod_length_m: float
    piston_thickness_m: float
    frame_height_m: float
    frame_beam_size_m: float
    tail_rod_length_m: float
    tail_mount_offset_m: float
    joint_tail_scale: float
    joint_arm_scale: float
    joint_rod_scale: float
    interference_check: bool
    link_rod_diameters: bool

    def to_config_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation compatible with the app."""

        return {field.name: getattr(self, field.name) for field in fields(self)}


_NUMERIC_FIELDS: dict[str, float] = {
    "wheelbase": 0.0,
    "track": 0.0,
    "frame_to_pivot": 0.0,
    "lever_length": 0.0,
    "rod_position": 0.0,
    "cylinder_length": 0.0,
    "cyl_diam_m": 0.0,
    "stroke_m": 0.0,
    "dead_gap_m": 0.0,
    "rod_diameter_m": 0.0,
    "piston_rod_length_m": 0.0,
    "piston_thickness_m": 0.0,
    "frame_height_m": 0.0,
    "frame_beam_size_m": 0.0,
    "tail_rod_length_m": 0.0,
    "tail_mount_offset_m": 0.0,
    "joint_tail_scale": 0.0,
    "joint_arm_scale": 0.0,
    "joint_rod_scale": 0.0,
}

_BOOLEAN_FIELDS = {"interference_check", "link_rod_diameters"}
_FRACTIONAL_FIELDS = {"rod_position"}
_STRICT_POSITIVE = {
    "wheelbase",
    "track",
    "frame_to_pivot",
    "lever_length",
    "cylinder_length",
    "cyl_diam_m",
    "stroke_m",
    "rod_diameter_m",
    "piston_rod_length_m",
    "piston_thickness_m",
    "frame_height_m",
    "frame_beam_size_m",
    "tail_rod_length_m",
    "joint_tail_scale",
    "joint_arm_scale",
    "joint_rod_scale",
}


def _coerce_number(name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise GeometryValidationError(f"Field '{name}' must be a number, got boolean")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise GeometryValidationError(f"Field '{name}' must be a number") from exc

    if name in _STRICT_POSITIVE and number <= 0.0:
        raise GeometryValidationError(f"Field '{name}' must be greater than zero")

    minimum = _NUMERIC_FIELDS.get(name, 0.0)
    if number < minimum:
        raise GeometryValidationError(
            f"Field '{name}' must be greater than or equal to {minimum}"
        )

    if name in _FRACTIONAL_FIELDS and not 0.0 < number <= 1.0:
        raise GeometryValidationError(
            f"Field '{name}' must be within the open interval (0, 1]"
        )

    return number


def _coerce_bool(name: str, value: Any) -> bool:
    if isinstance(value, bool):
        return value

    raise GeometryValidationError(f"Field '{name}' must be a boolean")


def validate_geometry_settings(payload: Mapping[str, Any]) -> GeometrySettings:
    """Validate a geometry payload and return a typed representation.

    The helper performs type conversion, applies range checks and guarantees
    that no unexpected keys are present.  A ``GeometryValidationError`` is
    raised whenever the payload cannot be normalised.
    """

    if not isinstance(payload, Mapping):
        raise GeometryValidationError("Geometry settings payload must be a mapping")

    expected_keys = set(_NUMERIC_FIELDS) | _BOOLEAN_FIELDS

    missing = expected_keys - payload.keys()
    if missing:
        missing_keys = ", ".join(sorted(missing))
        raise GeometryValidationError(f"Missing geometry fields: {missing_keys}")

    unexpected = set(payload.keys()) - expected_keys
    if unexpected:
        unexpected_keys = ", ".join(sorted(unexpected))
        raise GeometryValidationError(
            f"Unexpected geometry fields provided: {unexpected_keys}"
        )

    numeric_values = {
        key: _coerce_number(key, payload[key]) for key in _NUMERIC_FIELDS
    }
    bool_values = {key: _coerce_bool(key, payload[key]) for key in _BOOLEAN_FIELDS}

    return GeometrySettings(**numeric_values, **bool_values)


__all__ = [
    "GeometrySettings",
    "GeometryValidationError",
    "validate_geometry_settings",
]
