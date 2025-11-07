"""Factory helpers that provide deterministic default configurations.

The original application bundled a large JSON snapshot with hundreds of
hard-coded values. During the refactor that introduced the modular
``src`` package that file was accidentally removed which broke both the
runtime bootstrap code and a sizeable portion of the legacy regression
tests. The helpers below recreate a compact, well documented
configuration that covers all required components:

* geometry definitions for the pneumatic cylinders and frame
* valve configuration for the diagonal line layout
* receiver state with sensible thermodynamic parameters
* convenience accessors used by smoke tests and fixtures

The values are intentionally conservative (typical light truck geometry
and moderate pressures) which keeps the analytical checks in the tests
stable while still producing realistic numbers for manual experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar
from collections.abc import Mapping

from config.constants import (
    get_pneumo_gas_constants,
    get_pneumo_master_isolation_default,
    get_pneumo_receiver_constants,
    get_pneumo_valve_constants,
)
from src.common.units import PA_ATM, T_AMBIENT
from src.pneumo.cylinder import CylinderSpec
from src.pneumo.enums import (
    CheckValveKind,
    Line,
    ReceiverVolumeMode,
    ThermoMode,
    Wheel,
)
from src.pneumo.geometry import CylinderGeom, FrameGeom, LeverGeom
from src.pneumo.network import GasNetwork
from src.pneumo.gas_state import create_line_gas_state, create_tank_gas_state
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.valves import CheckValve

EnumType = TypeVar("EnumType", bound=Enum)


def _require_value(payload: Mapping[str, Any], key: str, path: str) -> Any:
    """Return a value from ``payload`` or raise an informative error."""

    if key not in payload:
        raise KeyError(f"Missing '{path}.{key}' in config/app_settings.json")
    return payload[key]


def _enum_from_config(
    enum_cls: type[EnumType], value: object, *, path: str
) -> EnumType:
    """Return an enum value using case-insensitive lookups."""

    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        key = value.upper()
        try:
            return enum_cls[key]
        except KeyError as exc:
            raise ValueError(
                f"Invalid value '{value}' for {path} in config/app_settings.json"
            ) from exc
    raise TypeError(
        f"{path} must be a string or {enum_cls.__name__}, got {type(value).__name__}"
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _create_default_geometry() -> tuple[FrameGeom, LeverGeom, CylinderGeom]:
    """Return a validated set of geometry primitives.

    The numbers reflect a mid-sized commercial chassis. They satisfy all
    invariants enforced by :mod:`src.pneumo.geometry` and are intentionally
    symmetrical which simplifies many analytical calculations in the tests.
    """

    frame = FrameGeom(L_wb=3.4)

    lever = LeverGeom(
        L_lever=0.75,
        rod_joint_frac=0.45,
        d_frame_to_lever_hinge=0.42,
    )

    cylinder = CylinderGeom(
        D_in_front=0.11,
        D_in_rear=0.11,
        D_out_front=0.13,
        D_out_rear=0.13,
        L_inner=0.46,
        t_piston=0.025,
        D_rod=0.035,
        link_rod_diameters_front_rear=True,
        L_dead_head=0.018,
        L_dead_rod=0.02,
        residual_frac_min=0.01,
        Y_tail=0.45,
        Z_axle=0.55,
    )

    return frame, lever, cylinder


def _create_line_valves() -> dict[Line, dict]:
    """Create check valve configuration for every pneumatic line."""

    valve_defaults = get_pneumo_valve_constants()
    delta_open = float(_require_value(valve_defaults, "delta_open_pa", "pneumo.valves"))
    d_eq = float(
        _require_value(valve_defaults, "equivalent_diameter_m", "pneumo.valves")
    )

    def _check_valve(kind: CheckValveKind) -> CheckValve:
        return CheckValve(kind=kind, delta_open=delta_open, d_eq=d_eq)

    line_defaults: dict[Line, dict] = {}
    for line in (Line.A1, Line.B1, Line.A2, Line.B2):
        line_defaults[line] = {
            "cv_atmo": _check_valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _check_valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        }

    return line_defaults


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_default_system_configuration() -> dict:
    """Return a fully validated default system configuration."""

    frame_geom, lever_geom, cylinder_geom = _create_default_geometry()

    cylinder_specs = {
        Wheel.LP: CylinderSpec(cylinder_geom, True, lever_geom),
        Wheel.PP: CylinderSpec(cylinder_geom, True, lever_geom),
        Wheel.LZ: CylinderSpec(cylinder_geom, False, lever_geom),
        Wheel.PZ: CylinderSpec(cylinder_geom, False, lever_geom),
    }

    receiver_defaults = get_pneumo_receiver_constants()
    receiver_spec = ReceiverSpec(
        V_min=float(
            _require_value(receiver_defaults, "volume_min_m3", "pneumo.receiver")
        ),
        V_max=float(
            _require_value(receiver_defaults, "volume_max_m3", "pneumo.receiver")
        ),
    )
    receiver_state = ReceiverState(
        spec=receiver_spec,
        V=float(
            _require_value(receiver_defaults, "initial_volume_m3", "pneumo.receiver")
        ),
        p=float(
            _require_value(receiver_defaults, "initial_pressure_pa", "pneumo.receiver")
        ),
        T=float(
            _require_value(
                receiver_defaults, "initial_temperature_k", "pneumo.receiver"
            )
        ),
        mode=_enum_from_config(
            ReceiverVolumeMode,
            _require_value(receiver_defaults, "volume_mode", "pneumo.receiver"),
            path="pneumo.receiver.volume_mode",
        ),
    )

    return {
        "frame_geom": frame_geom,
        "lever_geom": lever_geom,
        "cylinder_geom": cylinder_geom,
        "cylinder_specs": cylinder_specs,
        "line_configs": _create_line_valves(),
        "receiver": receiver_state,
        "master_isolation_open": get_pneumo_master_isolation_default(),
    }


def create_default_gas_network(system) -> GasNetwork:
    """Create a gas network with atmospheric initial conditions."""

    line_volumes = system.get_line_volumes()

    line_states = {
        line: create_line_gas_state(line, PA_ATM, T_AMBIENT, volume)
        for line, volume in line_volumes.items()
    }

    gas_defaults = get_pneumo_gas_constants()
    tank_state = create_tank_gas_state(
        V_initial=float(
            _require_value(gas_defaults, "tank_volume_initial_m3", "pneumo.gas")
        ),
        p_initial=float(
            _require_value(gas_defaults, "tank_pressure_initial_pa", "pneumo.gas")
        ),
        T_initial=float(
            _require_value(gas_defaults, "tank_temperature_initial_k", "pneumo.gas")
        ),
        mode=_enum_from_config(
            ReceiverVolumeMode,
            _require_value(gas_defaults, "tank_volume_mode", "pneumo.gas"),
            path="pneumo.gas.tank_volume_mode",
        ),
    )

    return GasNetwork(
        lines=line_states,
        tank=tank_state,
        system_ref=system,
        master_isolation_open=False,
    )


def get_default_lever_angles() -> dict[Wheel, float]:
    """Return zeroed lever angles for all wheels."""

    return {wheel: 0.0 for wheel in Wheel}


def get_default_gas_parameters() -> dict:
    """Return time-integration parameters for gas simulations."""

    gas_defaults = get_pneumo_gas_constants()
    thermo_mode_enum = _enum_from_config(
        ThermoMode,
        _require_value(gas_defaults, "thermo_mode", "pneumo.gas"),
        path="pneumo.gas.thermo_mode",
    )

    return {
        "dt": float(_require_value(gas_defaults, "time_step_s", "pneumo.gas")),
        "thermo_mode": thermo_mode_enum,
        "total_time": float(_require_value(gas_defaults, "total_time_s", "pneumo.gas")),
    }


@dataclass
class SystemWithDefaults:
    """Convenience wrapper combining system and gas network defaults."""

    system: object
    gas_network: GasNetwork


def create_system_with_gas_network() -> SystemWithDefaults:
    """Create a pneumatic system and matching gas network in one call."""

    config = create_default_system_configuration()
    system = create_standard_diagonal_system(
        cylinder_specs=config["cylinder_specs"],
        line_configs=config["line_configs"],
        receiver=config["receiver"],
        master_isolation_open=config["master_isolation_open"],
    )

    gas_network = create_default_gas_network(system)
    return SystemWithDefaults(system=system, gas_network=gas_network)


__all__ = [
    "create_default_system_configuration",
    "create_default_gas_network",
    "get_default_lever_angles",
    "get_default_gas_parameters",
    "create_system_with_gas_network",
    "SystemWithDefaults",
]
