"""Slider specification for rod diameter (front linkage)."""

from __future__ import annotations

from .accordion_spec_factory import spec_from_limits


def build_rod_diameter_spec():
    return (
        "rod_diameter",
        spec_from_limits(
            "rod_diameter_m",
            telemetry_key="geometry.rod_diameter",
            settings_key="rod_diameter_m",
        ),
    )


__all__ = ["build_rod_diameter_spec"]
