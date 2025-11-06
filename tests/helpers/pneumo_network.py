"""Shared helpers for constructing pneumatic gas network fixtures."""

from __future__ import annotations

from typing import Dict, Tuple

from src.common.units import PA_ATM, T_AMBIENT
from src.pneumo.cylinder import CylinderSpec
from src.pneumo.enums import CheckValveKind, Line, ReceiverVolumeMode, Wheel
from src.pneumo.gas_state import create_line_gas_state, create_tank_gas_state
from src.pneumo.geometry import CylinderGeom, LeverGeom
from src.pneumo.network import GasNetwork
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.pneumo.system import PneumaticSystem, create_standard_diagonal_system
from src.pneumo.valves import CheckValve


def _default_lever_geometry() -> LeverGeom:
    return LeverGeom(
        L_lever=0.75,
        rod_joint_frac=0.45,
        d_frame_to_lever_hinge=0.42,
    )


def _default_cylinder_geometry() -> CylinderGeom:
    return CylinderGeom(
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


def _build_line_valves(
    delta_open: float = 5_000.0, diameter: float = 0.008
) -> Dict[Line, Dict[str, CheckValve]]:
    def _valve(kind: CheckValveKind) -> CheckValve:
        return CheckValve(kind=kind, delta_open=delta_open, d_eq=diameter)

    return {
        line: {
            "cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        }
        for line in (Line.A1, Line.B1, Line.A2, Line.B2)
    }


def build_default_system_and_network(
    *,
    delta_open: float = 5_000.0,
    valve_diameter: float = 0.008,
) -> Tuple[PneumaticSystem, GasNetwork]:
    """Construct the canonical pneumatic system and gas network for tests."""

    lever_geom = _default_lever_geometry()
    cylinder_geom = _default_cylinder_geometry()

    cylinder_specs = {
        wheel: CylinderSpec(cylinder_geom, wheel in (Wheel.LP, Wheel.PP), lever_geom)
        for wheel in (Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ)
    }

    line_configs = _build_line_valves(delta_open=delta_open, diameter=valve_diameter)

    receiver_state = ReceiverState(
        spec=ReceiverSpec(V_min=0.0018, V_max=0.0045),
        V=0.003,
        p=PA_ATM,
        T=T_AMBIENT,
        mode=ReceiverVolumeMode.ADIABATIC_RECALC,
    )

    system = create_standard_diagonal_system(
        cylinder_specs=cylinder_specs,
        line_configs=line_configs,
        receiver=receiver_state,
        master_isolation_open=False,
    )
    system.update_system_from_lever_angles({wheel: 0.0 for wheel in Wheel})

    volumes = {
        line: info["total_volume"] for line, info in system.get_line_volumes().items()
    }
    line_states = {
        line: create_line_gas_state(line, PA_ATM, T_AMBIENT, volume)
        for line, volume in volumes.items()
    }
    tank_state = create_tank_gas_state(
        V_initial=0.0035,
        p_initial=PA_ATM,
        T_initial=T_AMBIENT,
        mode=ReceiverVolumeMode.ADIABATIC_RECALC,
    )

    gas_network = GasNetwork(
        lines=line_states,
        tank=tank_state,
        system_ref=system,
        master_isolation_open=False,
    )
    return system, gas_network


__all__ = ["build_default_system_and_network"]
