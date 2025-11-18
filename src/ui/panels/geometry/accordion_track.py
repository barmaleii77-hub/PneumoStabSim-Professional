"""Slider spec for track width control in the geometry accordion."""

from __future__ import annotations

from typing import Mapping


def track_spec() -> Mapping[str, object]:
    """Return declarative configuration for the track width slider."""

    return {
        "attr": "track_width",
        "slider": {
            "key": "track_width",
            "label": "Track Width (B)",
            "min_value": 1.0,
            "max_value": 2.5,
            "step": 0.01,
            "decimals": 3,
            "unit": "m",
            "allow_range_edit": True,
            "default": 1.8,
            "settings_key": "track",
            "telemetry_key": "geometry.track",
        },
    }
