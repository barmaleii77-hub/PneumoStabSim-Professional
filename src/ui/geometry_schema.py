"""Validation helpers for geometry configuration payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class GeometryValidationError(ValueError):
    """Raised when geometry settings contain invalid values."""


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


@dataclass(slots=True)
class GeometrySettings:
    """Validated geometry configuration payload."""

    data: dict[str, Any]

    def to_config_dict(self) -> dict[str, Any]:
        return dict(self.data)


def validate_geometry_settings(payload: Mapping[str, Any]) -> GeometrySettings:
    """Validate and normalise the geometry configuration payload."""

    if not isinstance(payload, Mapping):
        raise GeometryValidationError("Payload must be a mapping")

    data: dict[str, Any] = {}

    for field, minimum in _NUMERIC_FIELDS.items():
        if field not in payload:
            raise GeometryValidationError(f"Missing required field: {field}")

        value = payload[field]
        if not isinstance(value, (int, float)):
            raise GeometryValidationError(f"{field} must be numeric")

        numeric_value = float(value)
        if numeric_value < minimum:
            raise GeometryValidationError(f"{field} must be >= {minimum}")

        data[field] = numeric_value

    for field in _BOOLEAN_FIELDS:
        if field not in payload:
            raise GeometryValidationError(f"Missing required field: {field}")

        value = payload[field]
        if not isinstance(value, bool):
            raise GeometryValidationError(f"{field} must be a boolean")
        data[field] = value

    return GeometrySettings(data)


__all__ = [
    "GeometrySettings",
    "GeometryValidationError",
    "validate_geometry_settings",
]
