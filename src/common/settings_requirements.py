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
    "receiver_diameter",
    "receiver_length",
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
    "polytropic_heat_transfer_coeff",
    "polytropic_exchange_area",
    "leak_coefficient",
    "leak_reference_area",
)

BOOL_PNEUMATIC_KEYS: tuple[str, ...] = ("master_isolation_open",)

STRING_PNEUMATIC_KEYS: tuple[str, ...] = (
    "volume_mode",
    "thermo_mode",
    "pressure_units",
)

RECEIVER_VOLUME_LIMIT_KEYS: tuple[str, ...] = (
    "min_m3",
    "max_m3",
)

NUMERIC_MODES_KEYS: tuple[str, ...] = (
    "amplitude",
    "frequency",
    "phase",
    "lf_phase",
    "rf_phase",
    "lr_phase",
    "rr_phase",
    "ambient_temperature_c",
)

STRING_MODES_KEYS: tuple[str, ...] = (
    "sim_type",
    "thermo_mode",
    "mode_preset",
    "road_profile",
    "custom_profile_path",
)

BOOL_MODES_KEYS: tuple[str, ...] = ("check_interference",)

REQUIRED_CURRENT_SECTIONS: tuple[str, ...] = (
    "current.simulation",
    "current.pneumatic",
    "current.geometry",
    "current.pneumatic.receiver_volume_limits",
    "current.modes",
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

    for key in NUMERIC_MODES_KEYS:
        yield f"current.modes.{key}"

    for key in STRING_MODES_KEYS:
        yield f"current.modes.{key}"

    for key in BOOL_MODES_KEYS:
        yield f"current.modes.{key}"
