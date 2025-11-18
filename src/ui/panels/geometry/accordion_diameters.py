"""Slider specs for piston and rod diameter controls in the geometry accordion."""

from __future__ import annotations

from typing import Iterable, Mapping


def diameter_specs() -> Iterable[Mapping[str, object]]:
    """Yield declarative configurations for piston and rod diameters."""

    yield {
        "attr": "piston_diameter",
        "slider": {
            "key": "piston_diameter",
            "label": "Piston Diameter (D_p)",
            "min_value": 0.03,
            "max_value": 0.15,
            "step": 0.001,
            "decimals": 3,
            "unit": "m",
            "allow_range_edit": True,
            "default": 0.08,
            "settings_key": "cyl_diam_m",
            "telemetry_key": "geometry.cyl_diameter",
        },
    }

    yield {
        "attr": "rod_diameter",
        "slider": {
            "key": "rod_diameter",
            "label": "Rod Diameter (D_r)",
            "min_value": 0.01,
            "max_value": 0.10,
            "step": 0.001,
            "decimals": 3,
            "unit": "m",
            "allow_range_edit": True,
            "default": 0.04,
            "settings_key": "rod_diameter_m",
            "telemetry_key": "geometry.rod_diameter",
        },
    }
