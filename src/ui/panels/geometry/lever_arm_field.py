"""Slider specification for the lever arm field."""

from __future__ import annotations

from .accordion_spec_factory import spec_from_limits


def build_lever_arm_spec():
    return (
        "lever_arm",
        spec_from_limits(
            "lever_length",
            telemetry_key="geometry.lever_length",
        ),
    )


__all__ = ["build_lever_arm_spec"]
