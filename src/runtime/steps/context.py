"""Shared context for physics step helper functions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from src.physics.odes import RigidBody3DOF
from src.pneumo.enums import Line, Port, ReceiverVolumeMode, ThermoMode, Wheel
from src.pneumo.network import GasNetwork
from src.runtime.state import LineState, TankState, WheelState
from src.runtime.sync import PerformanceMetrics


@dataclass
class LeverDynamicsConfig:
    """Configuration bundle for lever dynamics integration."""

    include_springs: bool = True
    include_dampers: bool = True
    include_pneumatics: bool = True
    spring_constant: float = 0.0
    damper_coefficient: float = 0.0
    damper_threshold: float = 0.0
    spring_rest_position: float = 0.0
    lever_inertia: float = 1.0
    integrator_method: str = "rk4"


@dataclass
class PhysicsStepState:
    """Aggregated state passed to physics step helpers."""

    dt: float
    pneumatic_system: Any
    gas_network: GasNetwork
    rigid_body: RigidBody3DOF | None
    physics_state: np.ndarray
    simulation_time: float
    master_isolation_open: bool
    thermo_mode: ThermoMode
    receiver_volume: float
    receiver_mode: ReceiverVolumeMode
    prev_piston_positions: dict[Wheel, float]
    wheel_states: dict[Wheel, WheelState]
    line_states: dict[Line, LineState]
    tank_state: TankState
    last_road_inputs: dict[str, float]
    prev_road_inputs: dict[str, float]
    latest_frame_accel: np.ndarray
    prev_frame_velocities: np.ndarray
    performance: PerformanceMetrics
    logger: logging.Logger
    get_line_pressure: Callable[[Wheel, Port], float]
    lever_config: LeverDynamicsConfig
