"""Kinematic helpers for physics step execution."""

from __future__ import annotations

from typing import Dict

import numpy as np

from src.common.units import to_gauge_pressure
from src.pneumo.enums import Port, Wheel

from .context import PhysicsStepState


_WHEEL_KEY_MAP: Dict[Wheel, str] = {
    Wheel.LP: "LF",
    Wheel.PP: "RF",
    Wheel.LZ: "LR",
    Wheel.PZ: "RR",
}


def compute_kinematics(
    state: PhysicsStepState, road_inputs: Dict[str, float]
) -> Dict[Wheel, float]:
    """Update pneumatic system and wheel states from road excitation."""

    state.last_road_inputs.update({k: float(v) for k, v in road_inputs.items()})

    lever_angles: Dict[Wheel, float] = {}
    for wheel, key in _WHEEL_KEY_MAP.items():
        excitation = float(road_inputs.get(key, 0.0))
        cylinder = state.pneumatic_system.cylinders[wheel]
        lever = cylinder.spec.lever_geom
        lever_length = max(lever.L_lever, 1e-6)
        angle = float(np.clip(excitation / lever_length, -0.5, 0.5))
        lever_angles[wheel] = angle

    state.pneumatic_system.update_system_from_lever_angles(lever_angles)

    for wheel, angle in lever_angles.items():
        cylinder = state.pneumatic_system.cylinders[wheel]
        piston_pos = float(cylinder.x)
        prev_pos = state.prev_piston_positions.get(wheel, 0.0)
        piston_vel = (piston_pos - prev_pos) / state.dt if state.dt > 0 else 0.0
        state.prev_piston_positions[wheel] = piston_pos

        geom = cylinder.spec.geometry
        rod_x, rod_y = cylinder.spec.lever_geom.rod_joint_pos(angle)
        wheel_state = state.wheel_states[wheel]
        wheel_state.lever_angle = angle
        wheel_state.piston_position = piston_pos
        wheel_state.piston_velocity = piston_vel
        wheel_state.vol_head = cylinder.vol_head()
        wheel_state.vol_rod = cylinder.vol_rod()
        wheel_state.joint_x = 0.0
        wheel_state.joint_y = rod_x
        wheel_state.joint_z = geom.Z_axle + rod_y
        wheel_state.road_excitation = state.last_road_inputs.get(
            _WHEEL_KEY_MAP[wheel], 0.0
        )

        wheel_state.stop_head_penetration = cylinder.penetration_head
        wheel_state.stop_rod_penetration = cylinder.penetration_rod
        wheel_state.stop_head_engaged = cylinder.penetration_head > 1e-9
        wheel_state.stop_rod_engaged = cylinder.penetration_rod > 1e-9

        head_pressure = state.get_line_pressure(wheel, Port.HEAD)
        rod_pressure = state.get_line_pressure(wheel, Port.ROD)
        head_pressure_gauge = to_gauge_pressure(head_pressure)
        rod_pressure_gauge = to_gauge_pressure(rod_pressure)
        area_head = geom.area_head(cylinder.spec.is_front)
        area_rod = geom.area_rod(cylinder.spec.is_front)
        wheel_state.force_pneumatic = (
            head_pressure_gauge * area_head - rod_pressure_gauge * area_rod
        )

    return lever_angles
