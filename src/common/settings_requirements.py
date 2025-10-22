"""Список обязательных секций и ключей для файла настроек."""
from __future__ import annotations

from typing import Iterable, Tuple


NUMERIC_SIMULATION_KEYS: Tuple[str, ...] = (
    "physics_dt",
    "render_vsync_hz",
    "max_steps_per_frame",
    "max_frame_time",
)

NUMERIC_PNEUMATIC_KEYS: Tuple[str, ...] = (
    "receiver_volume",
)

BOOL_PNEUMATIC_KEYS: Tuple[str, ...] = (
    "master_isolation_open",
)

STRING_PNEUMATIC_KEYS: Tuple[str, ...] = (
    "volume_mode",
    "thermo_mode",
)

RECEIVER_VOLUME_LIMIT_KEYS: Tuple[str, ...] = (
    "min_m3",
    "max_m3",
)

REQUIRED_CURRENT_SECTIONS: Tuple[str, ...] = (
    "current.simulation",
    "current.pneumatic",
    "current.geometry",
    "current.pneumatic.receiver_volume_limits",
)


def iter_all_required_paths() -> Iterable[str]:
    """Перечислить все обязательные пути в current.*"""

    for section in REQUIRED_CURRENT_SECTIONS:
        yield section

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
