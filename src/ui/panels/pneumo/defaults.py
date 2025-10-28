# -*- coding: utf-8 -*-
"""Default values and limits for the pneumatic panel."""

from __future__ import annotations

from typing import Any, Dict

PA_PER_BAR = 100_000.0
MM_PER_M = 1000.0

DEFAULT_PNEUMATIC: Dict[str, Any] = {
    "pressure_units": "Па",
    "volume_mode": "MANUAL",
    "receiver_volume": 0.02,  # м³
    "receiver_diameter": 0.200,  # м
    "receiver_length": 0.500,  # м
    "cv_atmo_dp": 0.02,  # бар
    "cv_tank_dp": 0.02,  # бар
    "cv_atmo_dia": 3.0,  # мм
    "cv_tank_dia": 3.0,  # мм
    "relief_min_pressure": 2.5,  # бар
    "relief_stiff_pressure": 15.0,  # бар
    "relief_safety_pressure": 50.0,  # бар
    "throttle_min_dia": 1.0,  # мм
    "throttle_stiff_dia": 1.5,  # мм
    "atmo_temp": 20.0,  # °C
    "thermo_mode": "ISOTHERMAL",
    "master_isolation_open": False,
    "receiver_volume_limits": {"min_m3": 0.001, "max_m3": 1.0},
}

PRESSURE_UNITS = [
    ("бар (bar)", "бар"),
    ("Па (Pa)", "Па"),
    ("кПа (kPa)", "кПа"),
    ("МПа (MPa)", "МПа"),
]

RECEIVER_MANUAL_LIMITS = {"min": 0.001, "max": 1.0, "step": 0.001, "decimals": 3}
RECEIVER_DIAMETER_LIMITS = {"min": 0.050, "max": 0.500, "step": 0.001, "decimals": 3}
RECEIVER_LENGTH_LIMITS = {"min": 0.100, "max": 2.000, "step": 0.001, "decimals": 3}
PRESSURE_DROP_LIMITS = {"min": 0.001, "max": 0.100, "step": 0.001, "decimals": 3}
RELIEF_PRESSURE_LIMITS = {"min": 1.0, "max": 100.0, "step": 0.5, "decimals": 1}
VALVE_DIAMETER_LIMITS = {"min": 1.0, "max": 10.0, "step": 0.1, "decimals": 1}
THROTTLE_DIAMETER_LIMITS = {"min": 0.5, "max": 3.0, "step": 0.1, "decimals": 1}


STORAGE_PRESSURE_KEYS = {
    "cv_atmo_dp",
    "cv_tank_dp",
    "relief_min_pressure",
    "relief_stiff_pressure",
    "relief_safety_pressure",
}

STORAGE_DIAMETER_KEYS_MM = {
    "cv_atmo_dia",
    "cv_tank_dia",
    "throttle_min_dia",
    "throttle_stiff_dia",
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp *value* into the inclusive range [minimum, maximum]."""

    return max(minimum, min(maximum, value))
