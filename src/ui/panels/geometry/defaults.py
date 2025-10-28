# -*- coding: utf-8 -*-
"""
Geometry panel default values and presets
Константы и пресеты для панели геометрии
"""

from typing import Dict, Any

# =============================================================================
# DEFAULT GEOMETRY VALUES
# =============================================================================

DEFAULT_GEOMETRY: Dict[str, Any] = {
    # Frame dimensions (м)
    "wheelbase": 3.2,  # База (колёсная база)
    "track": 1.6,  # Колея (расстояние между колёсами)
    "frame_height_m": 0.65,  # Высота рамы
    "frame_beam_size_m": 0.12,  # Толщина балки рамы
    "frame_length_m": 0.80,  # Визуальная длина рамы для 3D-сцены
    # Suspension geometry (м)
    "frame_to_pivot": 0.6,  # Расстояние рама → ось рычага
    "lever_length": 0.8,  # Длина рычага
    "lever_length_m": 0.15,  # Длина рычага в визуализаторе
    "rod_position": 0.6,  # Положение крепления штока (доля 0..1)
    # Cylinder dimensions (м)
    "cylinder_length": 0.5,  # Длина цилиндра
    "cyl_diam_m": 0.080,  # Диаметр цилиндра
    "stroke_m": 0.300,  # Ход поршня
    "dead_gap_m": 0.005,  # Мёртвый зазор
    "cylinder_body_length_m": 0.30,  # Длина корпуса цилиндра в сцене
    # Rod and piston dimensions (м)
    "rod_diameter_m": 0.035,  # Диаметр штока
    "rod_diameter_rear_m": 0.035,  # Диаметр штока (задний контур)
    "piston_rod_length_m": 0.200,  # Длина штока поршня
    "piston_thickness_m": 0.025,  # Толщина поршня
    "tail_rod_length_m": 0.100,  # Длина заднего штока
    # Visual joint scale factors (dimensionless)
    # Options (bool)
    "interference_check": True,  # Проверять пересечения
    "link_rod_diameters": False,  # Связать диаметры штоков
}

# =============================================================================
# GEOMETRY PRESETS
# =============================================================================

GEOMETRY_PRESETS: Dict[str, Dict[str, Any]] = {
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

PARAMETER_LIMITS: Dict[str, Dict[str, float]] = {
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

PARAMETER_METADATA: Dict[str, Dict[str, str]] = {
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


def get_preset(preset_key: str) -> Dict[str, Any]:
    """Get preset by key

    Args:
        preset_key: Preset identifier (e.g., 'standard_truck')

    Returns:
        Preset dictionary (empty if not found)
    """
    return GEOMETRY_PRESETS.get(preset_key, {})


def get_preset_by_index(index: int) -> Dict[str, Any]:
    """Get preset by combo box index

    Args:
        index: Combo box index (0-3)

    Returns:
        Preset dictionary
    """
    preset_key = PRESET_INDEX_MAP.get(index, "custom")
    return get_preset(preset_key)


def get_parameter_limits(param_name: str) -> Dict[str, float]:
    """Get parameter limits

    Args:
        param_name: Parameter name

    Returns:
        Dictionary with min, max, step, decimals
    """
    return PARAMETER_LIMITS.get(
        param_name, {"min": 0.0, "max": 10.0, "step": 0.01, "decimals": 2}
    )


def get_parameter_metadata(param_name: str) -> Dict[str, str]:
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
