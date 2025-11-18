"""Slider spec for wheelbase control in the geometry accordion."""

from __future__ import annotations

from typing import Mapping


def wheelbase_spec() -> Mapping[str, object]:
    """Return declarative configuration for the wheelbase slider."""

    return {
        "attr": "wheelbase",
        "slider": {
            "key": "wheelbase",
            "label": "Wheelbase (L)",
            "min_value": 2.0,
            "max_value": 5.0,
            "step": 0.01,
            "decimals": 3,
            "unit": "m",
            "allow_range_edit": True,
            "default": 3.0,
            "settings_key": "wheelbase",
            "telemetry_key": "geometry.wheelbase",
        },
    }
