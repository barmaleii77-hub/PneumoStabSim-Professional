"""Shared context for physics step helper functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict
import logging

import numpy as np

from src.physics.odes import RigidBody3DOF
from src.pneumo.enums import Line, Port, ReceiverVolumeMode, ThermoMode, Wheel
from src.pneumo.network import GasNetwork
from src.runtime.state import LineState, TankState, WheelState
from src.runtime.sync import PerformanceMetrics


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
    prev_piston_positions: Dict[Wheel, float]
    wheel_states: Dict[Wheel, WheelState]
    line_states: Dict[Line, LineState]
    tank_state: TankState
    last_road_inputs: Dict[str, float]
    latest_frame_accel: np.ndarray
    prev_frame_velocities: np.ndarray
    performance: PerformanceMetrics
    logger: logging.Logger
    get_line_pressure: Callable[[Wheel, Port], float]
