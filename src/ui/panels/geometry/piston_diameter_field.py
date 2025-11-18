"""Slider specification for piston diameter."""

from __future__ import annotations

from .accordion_spec_factory import spec_from_limits


def build_piston_diameter_spec():
    return (
        "piston_diameter",
        spec_from_limits(
            "cyl_diam_m",
            telemetry_key="geometry.cyl_diameter",
            settings_key="cyl_diam_m",
        ),
    )


__all__ = ["build_piston_diameter_spec"]
