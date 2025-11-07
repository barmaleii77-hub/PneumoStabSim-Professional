"""Geometry panel default values and presets.

This module must not introduce hard-coded geometry defaults. Instead we source
them from :mod:`config/app_settings.json` so the UI, the Python bridge and the
QtQuick scene always share a single canonical baseline.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict


logger = logging.getLogger(__name__)


_REPO_ROOT = Path(__file__).resolve().parents[4]
_SETTINGS_FILE = _REPO_ROOT / "config" / "app_settings.json"


def _load_geometry_defaults() -> dict[str, Any]:
    """Load geometry defaults from the application settings file.

    If the configuration is unavailable or malformed we fall back to the
    previous constants to keep the UI usable while still emitting a warning so
    the issue can be diagnosed quickly.
    """

    try:
        with _SETTINGS_FILE.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        logger.error("Geometry defaults file is missing: %%s", _SETTINGS_FILE)
        return _LEGACY_DEFAULT_GEOMETRY.copy()
    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse geometry defaults from %%s: %%s",
            _SETTINGS_FILE,
            exc,
        )
        return _LEGACY_DEFAULT_GEOMETRY.copy()

    defaults_snapshot = payload.get("defaults_snapshot", {})
    geometry_defaults = defaults_snapshot.get("geometry")
    if not isinstance(geometry_defaults, dict) or not geometry_defaults:
        logger.error(
            "defaults_snapshot.geometry section is missing or empty in %%s",
            _SETTINGS_FILE,
        )
        return _LEGACY_DEFAULT_GEOMETRY.copy()

    result: dict[str, Any] = dict(geometry_defaults)

    mesh_defaults = (
        defaults_snapshot.get("graphics", {}).get("quality", {}).get("mesh", {})
    )
    if isinstance(mesh_defaults, dict):
        for key in ("cylinder_segments", "cylinder_rings"):
            if mesh_defaults.get(key) is not None and key not in result:
                result[key] = mesh_defaults[key]

    for key, value in _LEGACY_DEFAULT_GEOMETRY.items():
        result.setdefault(key, value)

    return result


# Legacy defaults retained solely as a safety net when the JSON configuration
# cannot be read. Keeping them private ensures call sites only use
# ``DEFAULT_GEOMETRY`` which is populated from the live configuration whenever
# possible.
_LEGACY_DEFAULT_GEOMETRY: dict[str, Any] = {
    "wheelbase": 3.2,
    "track": 1.6,
    "frame_height_m": 0.65,
    "frame_beam_size_m": 0.12,
    "frame_length_m": 0.80,
    "frame_to_pivot": 0.6,
    "lever_length": 0.8,
    "lever_length_m": 0.15,
    "rod_position": 0.6,
    "cylinder_length": 0.5,
    "cyl_diam_m": 0.080,
    "stroke_m": 0.300,
    "dead_gap_m": 0.005,
    "cylinder_body_length_m": 0.30,
    "rod_diameter_m": 0.035,
    "rod_diameter_rear_m": 0.035,
    "piston_rod_length_m": 0.200,
    "piston_thickness_m": 0.025,
    "tail_rod_length_m": 0.100,
    "interference_check": True,
    "link_rod_diameters": False,
    "cylinder_segments": 64,
    "cylinder_rings": 8,
}


DEFAULT_GEOMETRY: dict[str, Any] = _load_geometry_defaults()

# =============================================================================
# GEOMETRY PRESETS
# =============================================================================

GEOMETRY_PRESETS: dict[str, dict[str, Any]] = {
    "standard_truck": {
        "name": "Стандартный грузовик",
        "wheelbase": 3.2,
        "track": 1.6,
        "lever_length": 0.8,
        "cyl_diam_m": 0.080,
        "rod_diameter_m": 0.035,
        "rod_diameter_rear_m": 0.035,
    },
    "light_commercial": {
        "name": "Лёгкий коммерческий",
        "wheelbase": 2.8,
        "track": 1.4,
        "lever_length": 0.7,
        "cyl_diam_m": 0.065,
        "rod_diameter_m": 0.028,
        "rod_diameter_rear_m": 0.028,
    },
    "heavy_truck": {
        "name": "Тяжёлый грузовик",
        "wheelbase": 3.8,
        "track": 1.9,
        "lever_length": 0.95,
        "cyl_diam_m": 0.100,
        "rod_diameter_m": 0.045,
        "rod_diameter_rear_m": 0.045,
    },
    "custom": {
        "name": "Пользовательский",
        # Empty - user defined
    },
}

# Preset list for combo box
PRESET_NAMES = [
    "Стандартный грузовик",
    "Лёгкий коммерческий",
    "Тяжёлый грузовик",
    "Пользовательский",
]

# Mapping preset index -> preset key
PRESET_INDEX_MAP = {
    0: "standard_truck",
    1: "light_commercial",
    2: "heavy_truck",
    3: "custom",
}

# =============================================================================
# PARAMETER CONSTRAINTS
# =============================================================================

PARAMETER_LIMITS: dict[str, dict[str, float]] = {
    "wheelbase": {"min": 2.0, "max": 4.0, "step": 0.001, "decimals": 3},
    "track": {"min": 1.0, "max": 2.5, "step": 0.001, "decimals": 3},
    "frame_to_pivot": {"min": 0.3, "max": 1.0, "step": 0.001, "decimals": 3},
    "lever_length": {"min": 0.5, "max": 1.5, "step": 0.001, "decimals": 3},
    "rod_position": {"min": 0.3, "max": 0.9, "step": 0.001, "decimals": 3},
    "cylinder_length": {"min": 0.3, "max": 0.8, "step": 0.001, "decimals": 3},
    "cyl_diam_m": {"min": 0.030, "max": 0.150, "step": 0.001, "decimals": 3},
    "stroke_m": {"min": 0.100, "max": 0.500, "step": 0.001, "decimals": 3},
    "dead_gap_m": {"min": 0.000, "max": 0.020, "step": 0.001, "decimals": 3},
    "rod_diameter_m": {"min": 0.020, "max": 0.060, "step": 0.001, "decimals": 3},
    "rod_diameter_rear_m": {"min": 0.020, "max": 0.060, "step": 0.001, "decimals": 3},
    "piston_rod_length_m": {"min": 0.100, "max": 0.500, "step": 0.001, "decimals": 3},
    "piston_thickness_m": {"min": 0.010, "max": 0.050, "step": 0.001, "decimals": 3},
}

# =============================================================================
# PARAMETER METADATA
# =============================================================================

PARAMETER_METADATA: dict[str, dict[str, str]] = {
    "wheelbase": {
        "title": "База (колёсная)",
        "units": "м",
        "description": "Расстояние между передней и задней осями",
        "group": "frame",
    },
    "track": {
        "title": "Колея",
        "units": "м",
        "description": "Расстояние между левыми и правыми колёсами",
        "group": "frame",
    },
    "frame_to_pivot": {
        "title": "Расстояние рама → ось рычага",
        "units": "м",
        "description": "Расстояние от центра рамы до оси вращения рычага",
        "group": "suspension",
    },
    "lever_length": {
        "title": "Длина рычага",
        "units": "м",
        "description": "Длина рычага подвески",
        "group": "suspension",
    },
    "rod_position": {
        "title": "Положение крепления штока (доля)",
        "units": "",
        "description": "Относительное положение крепления штока на рычаге (0..1)",
        "group": "suspension",
    },
    "cylinder_length": {
        "title": "Длина цилиндра",
        "units": "м",
        "description": "Рабочая длина пневматического цилиндра",
        "group": "cylinder",
    },
    "cyl_diam_m": {
        "title": "Диаметр цилиндра",
        "units": "м",
        "description": "Внутренний диаметр цилиндра",
        "group": "cylinder",
    },
    "stroke_m": {
        "title": "Ход поршня",
        "units": "м",
        "description": "Максимальный ход поршня в цилиндре",
        "group": "cylinder",
    },
    "dead_gap_m": {
        "title": "Мёртвый зазор",
        "units": "м",
        "description": "Зазор между поршнем и торцом цилиндра",
        "group": "cylinder",
    },
    "rod_diameter_m": {
        "title": "Диаметр штока",
        "units": "м",
        "description": "Диаметр штока поршня",
        "group": "cylinder",
    },
    "rod_diameter_rear_m": {
        "title": "Диаметр штока (задняя ось)",
        "units": "м",
        "description": "Диаметр штока поршня для заднего контура",
        "group": "cylinder",
    },
    "piston_rod_length_m": {
        "title": "Длина штока поршня",
        "units": "м",
        "description": "Длина выдвигающегося штока",
        "group": "cylinder",
    },
    "piston_thickness_m": {
        "title": "Толщина поршня",
        "units": "м",
        "description": "Толщина поршня в цилиндре",
        "group": "cylinder",
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_preset(preset_key: str) -> dict[str, Any]:
    """Get preset by key

    Args:
        preset_key: Preset identifier (e.g., 'standard_truck')

    Returns:
        Preset dictionary (empty if not found)
    """
    return GEOMETRY_PRESETS.get(preset_key, {})


def get_preset_by_index(index: int) -> dict[str, Any]:
    """Get preset by combo box index

    Args:
        index: Combo box index (0-3)

    Returns:
        Preset dictionary
    """
    preset_key = PRESET_INDEX_MAP.get(index, "custom")
    return get_preset(preset_key)


def get_parameter_limits(param_name: str) -> dict[str, float]:
    """Get parameter limits

    Args:
        param_name: Parameter name

    Returns:
        Dictionary with min, max, step, decimals
    """
    return PARAMETER_LIMITS.get(
        param_name, {"min": 0.0, "max": 10.0, "step": 0.01, "decimals": 2}
    )


def get_parameter_metadata(param_name: str) -> dict[str, str]:
    """Get parameter metadata

    Args:
        param_name: Parameter name

    Returns:
        Dictionary with title, units, description, group
    """
    return PARAMETER_METADATA.get(
        param_name,
        {"title": param_name, "units": "", "description": "", "group": "other"},
    )


# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Hydraulic constraints
MAX_ROD_TO_CYLINDER_RATIO = 0.8  # Rod diameter must be < 80% of cylinder diameter
WARNING_ROD_TO_CYLINDER_RATIO = 0.7  # Warning threshold

# Geometric constraints
MIN_FRAME_CLEARANCE = 0.1  # Minimum clearance from frame edge (м)
