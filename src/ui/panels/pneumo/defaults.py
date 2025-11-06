# -*- coding: utf-8 -*-
"""Default values and limits for the pneumatic panel."""

from __future__ import annotations

from typing import Any, Dict

PA_PER_BAR = 100_000.0
MM_PER_M = 1000.0

PRESSURE_UNIT_FACTORS = {
    "бар": PA_PER_BAR,
    "Па": 1.0,
    "кПа": 1_000.0,
    "МПа": 1_000_000.0,
}

DEFAULT_PNEUMATIC: Dict[str, Any] = {
    "pressure_units": "бар",
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
    "diagonal_coupling_dia": 0.8,  # мм
    "atmo_temp": 20.0,  # °C
    "thermo_mode": "ISOTHERMAL",
    "polytropic_heat_transfer_coeff": 45.0,  # Вт/(м²·К)
    "polytropic_exchange_area": 0.12,  # м²
    "leak_coefficient": 5e-08,  # кг/(с·Па·м²)
    "leak_reference_area": 0.0002,  # м²
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
POLY_HEAT_TRANSFER_LIMITS = {"min": 0.0, "max": 200.0, "step": 1.0, "decimals": 0}
POLY_EXCHANGE_AREA_LIMITS = {"min": 0.0, "max": 0.5, "step": 0.01, "decimals": 2}
LEAK_COEFFICIENT_LIMITS = {"min": 0.0, "max": 0.0001, "step": 0.000001, "decimals": 6}
LEAK_AREA_LIMITS = {"min": 0.0, "max": 0.005, "step": 0.0001, "decimals": 4}


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
    "diagonal_coupling_dia",
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp *value* into the inclusive range [minimum, maximum]."""

    return max(minimum, min(maximum, value))


def get_pressure_factor(units: str) -> float:
    """Return conversion factor from *units* to Паскали."""

    units_key = (units or "").strip()
    return PRESSURE_UNIT_FACTORS.get(units_key, PA_PER_BAR)


def convert_pressure_value(value: float, from_units: str, to_units: str) -> float:
    """Convert ``value`` between two pressure unit systems."""

    from_factor = get_pressure_factor(from_units)
    to_factor = get_pressure_factor(to_units)
    value_pa = float(value) * from_factor
    return value_pa / to_factor
