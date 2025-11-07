"""Validation helpers for geometry configuration used in tests.

The production project defines a comprehensive JSON-schema for the vehicle
geometry parameters.  Recreating that entire stack is unnecessary for the
unit tests shipped with this kata – they only need a lightweight validator that
ensures required keys are present and the numeric values remain within a sane
range.  This module provides a compact, dependency-free implementation that is
compatible with the expectations of :mod:`tests.unit.test_geometry_schema`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Mapping


class GeometryValidationError(ValueError):
    """Raised when supplied geometry settings are invalid."""


_POSITIVE_FLOAT_FIELDS: dict[str, float] = {
    "wheelbase": 1e-6,
    "track": 1e-6,
    "frame_to_pivot": 1e-6,
    "lever_length": 1e-6,
    "rod_position": 1e-6,
    "cylinder_length": 1e-6,
    "cyl_diam_m": 1e-6,
    "stroke_m": 1e-6,
    "rod_diameter_m": 1e-6,
    "rod_diameter_rear_m": 1e-6,
    "piston_rod_length_m": 1e-6,
    "piston_thickness_m": 1e-6,
    "frame_height_m": 1e-6,
    "frame_beam_size_m": 1e-6,
    "tail_rod_length_m": 1e-6,
}

_NON_NEGATIVE_FIELDS = {"dead_gap_m"}

_BOOLEAN_FIELDS = {"interference_check", "link_rod_diameters"}

_ALL_FIELDS = set(_POSITIVE_FLOAT_FIELDS) | _NON_NEGATIVE_FIELDS | _BOOLEAN_FIELDS


@dataclass(slots=True)
class GeometrySettings:
    """Container for validated geometry settings used by the tests."""

    values: dict[str, Any]

    def to_config_dict(self) -> dict[str, Any]:
        return dict(self.values)


def _as_float(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GeometryValidationError(f"Field '{field}' must be a number")
    return float(value)


def validate_geometry_settings(payload: Mapping[str, Any]) -> GeometrySettings:
    """Validate geometry payload and return a structured representation."""

    missing = _ALL_FIELDS - payload.keys()
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise GeometryValidationError(f"Missing required geometry keys: {missing_list}")

    validated: dict[str, Any] = {}

    for field, minimum in _POSITIVE_FLOAT_FIELDS.items():
        value = _as_float(payload[field], field)
        if value <= minimum:
            raise GeometryValidationError(
                f"Field '{field}' must be greater than {minimum}"  # pragma: no cover - defensive guard
            )
        validated[field] = value

    for field in _NON_NEGATIVE_FIELDS:
        value = _as_float(payload[field], field)
        if value < 0.0:
            raise GeometryValidationError(f"Field '{field}' must be non-negative")
        validated[field] = value

    for field in _BOOLEAN_FIELDS:
        value = payload[field]
        if not isinstance(value, bool):
            raise GeometryValidationError(f"Field '{field}' must be a boolean")
        validated[field] = value

    return GeometrySettings(validated)


__all__ = ["validate_geometry_settings", "GeometryValidationError", "GeometrySettings"]
