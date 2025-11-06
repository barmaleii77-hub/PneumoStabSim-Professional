"""Gas network helpers for physics step execution."""

from __future__ import annotations

from typing import Dict

from src.common.units import PA_ATM
from src.pneumo.enums import Line, Port
from src.pneumo.gas_state import apply_instant_volume_change

from .context import PhysicsStepState


def _compute_penetration_volume(state: PhysicsStepState, line_name: Line) -> float:
    penetration_volume = 0.0
    line = state.pneumatic_system.lines[line_name]
    for wheel, port in line.endpoints:
        cylinder = state.pneumatic_system.cylinders[wheel]
        geom = cylinder.spec.geometry
        if port == Port.HEAD:
            penetration = cylinder.penetration_head
            if penetration > 0.0:
                penetration_volume += (
                    geom.area_head(cylinder.spec.is_front) * penetration
                )
        else:
            penetration = cylinder.penetration_rod
            if penetration > 0.0:
                penetration_volume += (
                    geom.area_rod(cylinder.spec.is_front) * penetration
                )
    return penetration_volume


def update_gas_state(state: PhysicsStepState) -> None:
    """Synchronise gas network with mechanical configuration."""

    line_volumes = state.pneumatic_system.get_line_volumes()
    corrected_volumes: Dict[Line, float] = {}
    for line_name, volume_info in line_volumes.items():
        total_volume = float(volume_info.get("total_volume"))
        penetration_volume = _compute_penetration_volume(state, line_name)
        corrected_volumes[line_name] = max(total_volume - penetration_volume, 1e-9)

    state.gas_network.master_isolation_open = state.master_isolation_open
    state.gas_network.update_pressures_with_explicit_volumes(
        corrected_volumes, state.thermo_mode
    )

    state.gas_network.tank.mode = state.receiver_mode
    if abs(state.gas_network.tank.V - state.receiver_volume) > 1e-9:
        apply_instant_volume_change(
            state.gas_network.tank,
            state.receiver_volume,
            gamma=state.gas_network.tank.gamma,
        )

    state.gas_network.apply_valves_and_flows(state.dt, state.logger)
    state.gas_network.enforce_master_isolation(state.logger)

    for line_name, gas_state in state.gas_network.lines.items():
        line_state = state.line_states[line_name]
        line_state.pressure = gas_state.p
        line_state.temperature = gas_state.T
        line_state.mass = gas_state.m
        line_state.volume = gas_state.V_curr
        pneumo_line = state.pneumatic_system.lines[line_name]
        try:
            line_state.cv_atmo_open = pneumo_line.cv_atmo.is_open(PA_ATM, gas_state.p)
        except Exception:
            line_state.cv_atmo_open = False
        try:
            line_state.cv_tank_open = pneumo_line.cv_tank.is_open(
                gas_state.p, state.gas_network.tank.p
            )
        except Exception:
            line_state.cv_tank_open = False
        line_state.flow_atmo = 0.0
        line_state.flow_tank = 0.0

    tank_state = state.gas_network.tank
    state.tank_state.pressure = tank_state.p
    state.tank_state.temperature = tank_state.T
    state.tank_state.mass = tank_state.m
    state.tank_state.volume = tank_state.V
