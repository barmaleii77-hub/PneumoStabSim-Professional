"""Slider spec for lever arm control in the geometry accordion."""

from __future__ import annotations

from typing import Mapping


def lever_spec() -> Mapping[str, object]:
    """Return declarative configuration for the lever arm slider."""

    return {
        "attr": "lever_arm",
        "slider": {
            "key": "lever_arm",
            "label": "Lever Arm (r)",
            "min_value": 0.1,
            "max_value": 0.6,
            "step": 0.001,
            "decimals": 3,
            "unit": "m",
            "allow_range_edit": True,
            "default": 0.3,
            "settings_key": "lever_length",
            "telemetry_key": "geometry.lever_length",
        },
    }
