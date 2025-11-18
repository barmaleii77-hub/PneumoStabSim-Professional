"""Список обязательных секций и ключей для файла настроек."""

from __future__ import annotations
from collections.abc import Iterable


NUMERIC_SIMULATION_KEYS: tuple[str, ...] = (
    "physics_dt",
    "render_vsync_hz",
    "max_steps_per_frame",
    "max_frame_time",
)

NUMERIC_PNEUMATIC_KEYS: tuple[str, ...] = (
    "receiver_volume",
    "tank_pressure_pa",
    "relief_pressure_pa",
    "cv_atmo_dp",
    "cv_tank_dp",
    "cv_atmo_dia",
    "cv_tank_dia",
    "relief_min_pressure",
    "relief_stiff_pressure",
    "relief_safety_pressure",
    "throttle_min_dia",
    "throttle_stiff_dia",
    "diagonal_coupling_dia",
    "atmo_temp",
    "dead_zone_head_m3",
    "dead_zone_rod_m3",
    "polytropic_heat_transfer_coeff",
    "polytropic_exchange_area",
    "leak_coefficient",
    "leak_reference_area",
)

BOOL_PNEUMATIC_KEYS: tuple[str, ...] = ("master_isolation_open",)

STRING_PNEUMATIC_KEYS: tuple[str, ...] = (
    "volume_mode",
    "thermo_mode",
)

RECEIVER_VOLUME_LIMIT_KEYS: tuple[str, ...] = (
    "min_m3",
    "max_m3",
)

LINE_PRESSURE_KEYS: tuple[str, ...] = (
    "a1_pa",
    "b1_pa",
    "a2_pa",
    "b2_pa",
)

CHAMBER_VOLUME_KEYS: tuple[str, ...] = (
    "head_m3",
    "rod_m3",
)

REQUIRED_CURRENT_SECTIONS: tuple[str, ...] = (
    "current.simulation",
    "current.pneumatic",
    "current.geometry",
    "current.road",
    "current.advanced",
    "current.pneumatic.receiver_volume_limits",
)


def iter_all_required_paths() -> Iterable[str]:
    """Перечислить все обязательные пути в current.*"""

    yield from REQUIRED_CURRENT_SECTIONS

    for key in NUMERIC_SIMULATION_KEYS:
        yield f"current.simulation.{key}"

    for key in NUMERIC_PNEUMATIC_KEYS:
        yield f"current.pneumatic.{key}"

    for key in BOOL_PNEUMATIC_KEYS:
        yield f"current.pneumatic.{key}"

    for key in STRING_PNEUMATIC_KEYS:
        yield f"current.pneumatic.{key}"

    for key in RECEIVER_VOLUME_LIMIT_KEYS:
        yield f"current.pneumatic.receiver_volume_limits.{key}"

    for key in LINE_PRESSURE_KEYS:
        yield f"current.pneumatic.line_pressures.{key}"

    for key in CHAMBER_VOLUME_KEYS:
        yield f"current.pneumatic.chamber_volumes.{key}"
