"""Slider specification for the track width field."""

from __future__ import annotations

from .accordion_spec_factory import spec_from_limits


def build_track_width_spec():
    return (
        "track_width",
        spec_from_limits(
            "track",
            telemetry_key="geometry.track",
            settings_key="track",
        ),
    )


__all__ = ["build_track_width_spec"]
