"""Slider spec for cylinder stroke control in the geometry accordion."""

from __future__ import annotations

from typing import Mapping


def cylinder_stroke_spec() -> Mapping[str, object]:
    """Return declarative configuration for the cylinder stroke slider."""

    return {
        "attr": "cylinder_stroke",
        "slider": {
            "key": "cylinder_stroke",
            "label": "Cylinder Stroke (s_max)",
            "min_value": 0.05,
            "max_value": 0.5,
            "step": 0.001,
            "decimals": 3,
            "unit": "m",
            "allow_range_edit": True,
            "default": 0.2,
            "settings_key": "stroke_m",
            "telemetry_key": "geometry.stroke",
        },
    }
