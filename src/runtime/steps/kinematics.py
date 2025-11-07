"""Kinematic helpers for physics step execution."""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np

from src.common.units import to_gauge_pressure
from src.pneumo.enums import Port, Wheel

from .context import LeverDynamicsConfig, PhysicsStepState


_WHEEL_KEY_MAP: Dict[Wheel, str] = {
    Wheel.LP: "LF",
    Wheel.PP: "RF",
    Wheel.LZ: "LR",
    Wheel.PZ: "RR",
}


def _solve_angle_for_displacement(
    lever_geom, target: float, initial_angle: float
) -> float:
    """Return angle that produces ``target`` displacement using Newton iterations."""

    angle = initial_angle
    for _ in range(12):
        displacement = lever_geom.angle_to_displacement(angle) - target
        if abs(displacement) < 1e-8:
            break
        derivative = lever_geom.mechanical_advantage(angle)
        if abs(derivative) < 1e-9:
            break
        angle -= displacement / derivative
        angle = float(np.clip(angle, -math.pi / 2.0, math.pi / 2.0))
    return angle


def _force_components(
    wheel: Wheel,
    theta: float,
    omega: float,
    lever_config: LeverDynamicsConfig,
    lever_geom,
    geom,
    cylinder,
    road_disp: float,
    road_vel: float,
    get_line_pressure,
) -> Tuple[float, float, float, float, float, float]:
    """Evaluate forces and resulting torque for a given lever state."""

    displacement = lever_geom.angle_to_displacement(theta)
    derivative = lever_geom.mechanical_advantage(theta)
    piston_velocity = omega * derivative

    spring_force = 0.0
    if lever_config.include_springs:
        spring_extension = displacement - road_disp - lever_config.spring_rest_position
        spring_force = -lever_config.spring_constant * spring_extension

    damper_force = 0.0
    if lever_config.include_dampers:
        relative_velocity = piston_velocity - road_vel
        damper_force = -lever_config.damper_coefficient * relative_velocity
        if abs(damper_force) < lever_config.damper_threshold:
            damper_force = 0.0

    pneumatic_force = 0.0
    if lever_config.include_pneumatics:
        head_pressure = get_line_pressure(wheel, Port.HEAD)
        rod_pressure = get_line_pressure(wheel, Port.ROD)
        area_head = geom.area_head(cylinder.spec.is_front)
        area_rod = geom.area_rod(cylinder.spec.is_front)
        pneumatic_force = head_pressure * area_head - rod_pressure * area_rod

    total_force = spring_force + damper_force + pneumatic_force
    torque = total_force * derivative
    return (
        torque,
        spring_force,
        damper_force,
        pneumatic_force,
        displacement,
        piston_velocity,
    )


def compute_kinematics(state: PhysicsStepState, road_inputs: Dict[str, float]) -> None:
    """Update pneumatic system and wheel states from road excitation."""

    dt = float(state.dt)
    lever_config = state.lever_config
    inertia = max(lever_config.lever_inertia, 1e-6)

    results: Dict[Wheel, Dict[str, float]] = {}
    lever_angles: Dict[Wheel, float] = {}

    for wheel, key in _WHEEL_KEY_MAP.items():
        road_disp = float(road_inputs.get(key, 0.0))
        prev_disp = float(state.prev_road_inputs.get(key, road_disp))

        cylinder = state.pneumatic_system.cylinders[wheel]
        lever_geom = cylinder.spec.lever_geom
        lever_length = max(lever_geom.L_lever, 1e-6)

        ratio = float(np.clip(road_disp / lever_length, -0.999, 0.999))
        prev_ratio = float(np.clip(prev_disp / lever_length, -0.999, 0.999))
        theta_road = math.asin(ratio)
        theta_prev = math.asin(prev_ratio)
        x_road = lever_geom.angle_to_displacement(theta_road)
        x_prev = lever_geom.angle_to_displacement(theta_prev)
        road_velocity = (x_road - x_prev) / dt if dt > 0.0 else 0.0

        wheel_state = state.wheel_states[wheel]
        theta0 = float(wheel_state.lever_angle)
        omega0 = float(getattr(wheel_state, "lever_angular_velocity", 0.0))

        if dt > 0.0:

            def _acc(theta: float, omega: float) -> float:
                torque, *_ = _force_components(
                    wheel,
                    theta,
                    omega,
                    lever_config,
                    lever_geom,
                    cylinder.spec.geometry,
                    cylinder,
                    x_road,
                    road_velocity,
                    state.get_line_pressure,
                )
                return torque / inertia

            k1_theta = omega0
            k1_omega = _acc(theta0, omega0)

            k2_theta = omega0 + 0.5 * dt * k1_omega
            k2_omega = _acc(theta0 + 0.5 * dt * k1_theta, omega0 + 0.5 * dt * k1_omega)

            k3_theta = omega0 + 0.5 * dt * k2_omega
            k3_omega = _acc(theta0 + 0.5 * dt * k2_theta, omega0 + 0.5 * dt * k2_omega)

            k4_theta = omega0 + dt * k3_omega
            k4_omega = _acc(theta0 + dt * k3_theta, omega0 + dt * k3_omega)

            theta_new = theta0 + (dt / 6.0) * (
                k1_theta + 2.0 * k2_theta + 2.0 * k3_theta + k4_theta
            )
            omega_new = omega0 + (dt / 6.0) * (
                k1_omega + 2.0 * k2_omega + 2.0 * k3_omega + k4_omega
            )
        else:  # pragma: no cover - zero dt guard
            theta_new = theta0
            omega_new = omega0

        geom = cylinder.spec.geometry
        max_displacement = geom.L_travel_max / 2.0
        displacement = lever_geom.angle_to_displacement(theta_new)
        clamped = False
        if displacement > max_displacement:
            theta_new = _solve_angle_for_displacement(
                lever_geom, max_displacement, theta_new
            )
            omega_new = 0.0
            clamped = True
        elif displacement < -max_displacement:
            theta_new = _solve_angle_for_displacement(
                lever_geom, -max_displacement, theta_new
            )
            omega_new = 0.0
            clamped = True

        (
            _torque,
            spring_force,
            damper_force,
            pneumatic_force,
            displacement,
            piston_velocity,
        ) = _force_components(
            wheel,
            theta_new,
            omega_new,
            lever_config,
            lever_geom,
            geom,
            cylinder,
            x_road,
            road_velocity,
            state.get_line_pressure,
        )

        if clamped:
            piston_velocity = 0.0

        lever_angles[wheel] = theta_new
        state.last_road_inputs[key] = road_disp
        results[wheel] = {
            "angle": theta_new,
            "angular_velocity": omega_new,
            "spring_force": spring_force,
            "damper_force": damper_force,
            "pneumatic_force": pneumatic_force,
            "piston_velocity": piston_velocity,
            "road_displacement": road_disp,
        }

    state.pneumatic_system.update_system_from_lever_angles(lever_angles)

    for wheel, metrics in results.items():
        cylinder = state.pneumatic_system.cylinders[wheel]
        piston_pos = float(cylinder.x)
        prev_pos = state.prev_piston_positions.get(wheel, piston_pos)
        piston_vel = (piston_pos - prev_pos) / dt if dt > 0.0 else 0.0
        state.prev_piston_positions[wheel] = piston_pos

        geom = cylinder.spec.geometry
        rod_x, rod_y = cylinder.spec.lever_geom.rod_joint_pos(metrics["angle"])
        wheel_state = state.wheel_states[wheel]
        wheel_state.lever_angle = metrics["angle"]
        wheel_state.lever_angular_velocity = metrics["angular_velocity"]
        wheel_state.piston_position = piston_pos
        wheel_state.piston_velocity = piston_vel
        wheel_state.vol_head = cylinder.vol_head()
        wheel_state.vol_rod = cylinder.vol_rod()
        wheel_state.joint_x = 0.0
        wheel_state.joint_y = rod_x
        wheel_state.joint_z = geom.Z_axle + rod_y
        wheel_state.road_excitation = metrics["road_displacement"]

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
        wheel_state.force_spring = metrics["spring_force"]
        wheel_state.force_damper = metrics["damper_force"]
