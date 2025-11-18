"""Slider specification for the wheelbase field."""

from __future__ import annotations

from .accordion_spec_factory import spec_from_limits


def build_wheelbase_spec():
    return (
        "wheelbase",
        spec_from_limits(
            "wheelbase",
            telemetry_key="geometry.wheelbase",
        ),
    )


__all__ = ["build_wheelbase_spec"]
