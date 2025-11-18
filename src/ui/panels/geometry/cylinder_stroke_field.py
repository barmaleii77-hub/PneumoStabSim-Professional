"""Slider specification for cylinder stroke."""

from __future__ import annotations

from .accordion_spec_factory import spec_from_limits


def build_cylinder_stroke_spec():
    return (
        "cylinder_stroke",
        spec_from_limits(
            "stroke_m",
            telemetry_key="geometry.stroke",
            settings_key="stroke_m",
        ),
    )


__all__ = ["build_cylinder_stroke_spec"]
