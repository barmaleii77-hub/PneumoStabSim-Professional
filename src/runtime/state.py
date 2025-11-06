"""Runtime state dataclasses and Qt signal bus helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

try:
    from PySide6.QtCore import QObject, Signal, Qt
except ImportError:  # pragma: no cover - headless environments
    QObject = None  # type: ignore[assignment]
    Signal = None  # type: ignore[assignment]
    Qt = None  # type: ignore[assignment]

from src.pneumo.enums import Line, Wheel


@dataclass
class WheelState:
    """State of a single wheel/suspension point"""

    wheel: Wheel
    lever_angle: float = 0.0  # Lever angle (rad)
    piston_position: float = 0.0  # Piston position (m)
    piston_velocity: float = 0.0  # Piston velocity (m/s)

    # Cylinder volumes
    vol_head: float = 0.0  # Head side volume (m3)
    vol_rod: float = 0.0  # Rod side volume (m3)
    vol_head_min: float = 0.0
    vol_head_max: float = 0.0
    vol_rod_min: float = 0.0
    vol_rod_max: float = 0.0
    lever_angle_min: Optional[float] = None
    lever_angle_max: Optional[float] = None

    # Joint coordinates
    joint_x: float = 0.0  # Joint X coordinate (m)
    joint_y: float = 0.0  # Joint Y coordinate (m)
    joint_z: float = 0.0  # Joint Z coordinate (m)

    # Forces
    force_pneumatic: float = 0.0  # Net pneumatic force (N)
    force_spring: float = 0.0  # Spring force (N)
    force_damper: float = 0.0  # Damper force (N)

    # Road input
    road_excitation: float = 0.0  # Road input (m)

    # Mechanical stops
    stop_head_engaged: bool = False
    stop_rod_engaged: bool = False
    stop_head_penetration: float = 0.0
    stop_rod_penetration: float = 0.0


@dataclass
class LineState:
    """State of a pneumatic line"""

    line: Line

    pressure: float = 0.0  # Pressure (Pa)
    temperature: float = 0.0  # Temperature (K)
    mass: float = 0.0  # Gas mass (kg)
    volume: float = 0.0  # Total volume (m3)
    pressure_min: Optional[float] = None
    pressure_max: Optional[float] = None
    volume_min: Optional[float] = None
    volume_max: Optional[float] = None
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None

    # Valve states and flows
    cv_atmo_open: bool = False  # Atmosphere check valve open
    cv_tank_open: bool = False  # Tank check valve open
    flow_atmo: float = 0.0  # Flow from atmosphere (kg/s)
    flow_tank: float = 0.0  # Flow to tank (kg/s)


@dataclass
class TankState:
    """State of receiver tank"""

    pressure: float = 0.0  # Pressure (Pa)
    temperature: float = 0.0  # Temperature (K)
    mass: float = 0.0  # Gas mass (kg)
    volume: float = 0.0  # Volume (m3)
    pressure_min: Optional[float] = None
    pressure_max: Optional[float] = None
    volume_min: Optional[float] = None
    volume_max: Optional[float] = None

    # Relief valve states
    relief_min_open: bool = False  # Min pressure relief open
    relief_stiff_open: bool = False  # Stiffness relief open
    relief_safety_open: bool = False  # Safety relief open

    flow_min: float = 0.0  # Min relief flow (kg/s)
    flow_stiff: float = 0.0  # Stiffness relief flow (kg/s)
    flow_safety: float = 0.0  # Safety relief flow (kg/s)


@dataclass
class FrameState:
    """State of vehicle frame (3-DOF rigid body)"""

    # Position (Y-down coordinate system)
    heave: float = 0.0  # Vertical position (m, positive down)
    roll: float = 0.0  # Roll angle (rad, positive = right down)
    pitch: float = 0.0  # Pitch angle (rad, positive = nose down)

    # Velocity
    heave_rate: float = 0.0  # Vertical velocity (m/s)
    roll_rate: float = 0.0  # Roll rate (rad/s)
    pitch_rate: float = 0.0  # Pitch rate (rad/s)

    # Acceleration
    heave_accel: float = 0.0  # Vertical acceleration (m/s2)
    roll_accel: float = 0.0  # Roll acceleration (rad/s2)
    pitch_accel: float = 0.0  # Pitch acceleration (rad/s2)

    # Forces and moments
    total_force_z: float = 0.0  # Total vertical force (N)
    total_moment_x: float = 0.0  # Total pitch moment (N*m)
    total_moment_z: float = 0.0  # Total roll moment (N*m)


@dataclass
class SystemAggregates:
    """Aggregated system metrics for diagnostics and plotting"""

    # Energy metrics
    kinetic_energy: float = 0.0  # Total kinetic energy (J)
    potential_energy: float = 0.0  # Total potential energy (J)
    pneumatic_energy: float = 0.0  # Stored pneumatic energy (J)

    # Mass flow metrics
    total_flow_in: float = 0.0  # Total inflow (kg/s)
    total_flow_out: float = 0.0  # Total outflow (kg/s)
    net_flow: float = 0.0  # Net flow (kg/s)

    # Valve activity counters
    valve_switches: int = 0  # Total valve state changes
    relief_activations: int = 0  # Relief valve activations

    # Performance metrics
    physics_step_time: float = 0.0  # Last physics step time (s)
    integration_steps: int = 0  # Integration steps taken
    integration_failures: int = 0  # Integration failures


@dataclass
class StateSnapshot:
    """Complete system state snapshot for thread-safe sharing"""

    # Timing
    timestamp: float = field(default_factory=time.perf_counter)  # Absolute time
    simulation_time: float = 0.0  # Simulation time (s)
    dt_physics: float = 0.001  # Physics timestep used (s)
    step_number: int = 0  # Physics step counter

    # Frame dynamics
    frame: FrameState = field(default_factory=FrameState)

    # Wheel/suspension states
    wheels: Dict[Wheel, WheelState] = field(default_factory=dict)

    # Pneumatic line states
    lines: Dict[Line, LineState] = field(default_factory=dict)

    # Tank state
    tank: TankState = field(default_factory=TankState)

    # System-wide metrics
    aggregates: SystemAggregates = field(default_factory=SystemAggregates)

    # Configuration state
    master_isolation_open: bool = False
    thermo_mode: str = "ISOTHERMAL"  # "ISOTHERMAL" or "ADIABATIC"

    def __post_init__(self) -> None:
        """Initialize wheel and line dictionaries if empty"""
        if not self.wheels:
            for wheel in [Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ]:
                self.wheels[wheel] = WheelState(wheel=wheel)

        if not self.lines:
            for line in [Line.A1, Line.B1, Line.A2, Line.B2]:
                self.lines[line] = LineState(line=line)

    def get_wheel_positions(self) -> Dict[str, np.ndarray]:
        """Get wheel positions as numpy arrays for rendering

        Returns:
        Dictionary mapping wheel names to3D positions
        """
        positions: Dict[str, np.ndarray] = {}

        for wheel, state in self.wheels.items():
            # Convert to string keys for easier access
            wheel_name = wheel.value  # LP, PP, LZ, PZ
            joint_position = [state.joint_x, state.joint_y, state.joint_z]
            positions[wheel_name] = np.array(joint_position)

        return positions

    def get_pressure_array(self) -> np.ndarray:
        """Get line pressures as array for plotting

        Returns:
        Array of pressures [A1, B1, A2, B2] in Pa
        """
        line_pressures = [
            self.lines[Line.A1].pressure,
            self.lines[Line.B1].pressure,
            self.lines[Line.A2].pressure,
            self.lines[Line.B2].pressure,
        ]
        return np.array(line_pressures)

    def get_flow_array(self) -> np.ndarray:
        """Get total flows as array for plotting

        Returns:
        Array of flows [inflow, outflow, tank_relief] in kg/s
        """
        total_inflow = sum(line.flow_atmo for line in self.lines.values())
        total_outflow = sum(line.flow_tank for line in self.lines.values())
        tank_relief = self.tank.flow_min + self.tank.flow_stiff + self.tank.flow_safety

        return np.array([total_inflow, total_outflow, tank_relief])

    def validate(self) -> bool:
        """Validate snapshot for reasonable values

        Returns:
        True if snapshot appears valid
        """
        try:
            # Check frame state for NaN/inf
            frame_values = [
                self.frame.heave,
                self.frame.roll,
                self.frame.pitch,
                self.frame.heave_rate,
                self.frame.roll_rate,
                self.frame.pitch_rate,
            ]

            if not all(np.isfinite(v) for v in frame_values):
                return False

            # Check reasonable angle limits (~45 degrees)
            if abs(self.frame.roll) > 0.785 or abs(self.frame.pitch) > 0.785:
                return False

            # Check line pressures (must be positive, reasonable range)
            for line_state in self.lines.values():
                if not np.isfinite(line_state.pressure) or not np.isfinite(
                    line_state.volume
                ):
                    return False

                if line_state.pressure <= 0.0:
                    return False

                if line_state.volume <= 0.0:
                    return False

                if (
                    line_state.pressure_min is not None
                    and line_state.pressure < line_state.pressure_min * 0.999
                ):
                    return False

                if (
                    line_state.pressure_max is not None
                    and line_state.pressure > line_state.pressure_max * 1.001
                ):
                    return False

                if (
                    line_state.volume_min is not None
                    and line_state.volume < line_state.volume_min * 0.999
                ):
                    return False

                if (
                    line_state.volume_max is not None
                    and line_state.volume > line_state.volume_max * 1.001
                ):
                    return False

            # Check tank pressure
            if not np.isfinite(self.tank.pressure) or not np.isfinite(self.tank.volume):
                return False

            if self.tank.pressure <= 0 or self.tank.volume <= 0:
                return False

            if (
                self.tank.pressure_min is not None
                and self.tank.pressure < self.tank.pressure_min * 0.999
            ):
                return False

            if (
                self.tank.pressure_max is not None
                and self.tank.pressure > self.tank.pressure_max * 1.001
            ):
                return False

            if (
                self.tank.volume_min is not None
                and self.tank.volume < self.tank.volume_min * 0.999
            ):
                return False

            if (
                self.tank.volume_max is not None
                and self.tank.volume > self.tank.volume_max * 1.001
            ):
                return False

            # Wheel volumes and lever angles
            for wheel_state in self.wheels.values():
                if not np.isfinite(wheel_state.lever_angle):
                    return False
                if (
                    wheel_state.lever_angle_min is not None
                    and wheel_state.lever_angle < wheel_state.lever_angle_min - 1e-6
                ):
                    return False
                if (
                    wheel_state.lever_angle_max is not None
                    and wheel_state.lever_angle > wheel_state.lever_angle_max + 1e-6
                ):
                    return False
                if not np.isfinite(wheel_state.vol_head) or not np.isfinite(
                    wheel_state.vol_rod
                ):
                    return False
                if wheel_state.vol_head <= 0 or wheel_state.vol_rod <= 0:
                    return False
                if (
                    wheel_state.vol_head_min > 0
                    and wheel_state.vol_head < wheel_state.vol_head_min * 0.999
                ):
                    return False
                if (
                    wheel_state.vol_head_max > 0
                    and wheel_state.vol_head > wheel_state.vol_head_max * 1.001
                ):
                    return False
                if (
                    wheel_state.vol_rod_min > 0
                    and wheel_state.vol_rod < wheel_state.vol_rod_min * 0.999
                ):
                    return False
                if (
                    wheel_state.vol_rod_max > 0
                    and wheel_state.vol_rod > wheel_state.vol_rod_max * 1.001
                ):
                    return False

            return True

        except Exception:
            return False


if QObject is not None and Signal is not None and Qt is not None:

    class StateBus(QObject):
        """Signal bus for thread-safe state communication

        Provides Qt signals for communicating between physics and UI threads.
        All signals use queued connections for thread safety.
        """

        # Main state signal - emitted from physics thread
        state_ready = Signal(object)  # StateSnapshot

        # Control signals - emitted from UI thread
        start_simulation = Signal()
        stop_simulation = Signal()
        reset_simulation = Signal()
        pause_simulation = Signal()

        # Configuration signals
        set_physics_dt = Signal(float)  # Change physics timestep
        set_thermo_mode = Signal(str)  # "ISOTHERMAL" or "ADIABATIC"
        set_master_isolation = Signal(bool)  # Master isolation valve
        set_receiver_volume = Signal(
            float, str
        )  # NEW: Set receiver volume (m3) and mode ('MANUAL'/'GEOMETRIC')

        # Road input signals
        load_road_profile = Signal(str)  # Load CSV road profile
        set_road_preset = Signal(str)  # Set road preset by name

        # Diagnostic signals
        physics_error = Signal(str)  # Physics thread error
        performance_update = Signal(object)  # Performance metrics

        def __init__(self, parent=None):
            super().__init__(parent)

            # Connect all signals to use queued connections for thread safety
            self.state_ready.connect(self._on_state_ready, Qt.QueuedConnection)

        def _on_state_ready(self, snapshot: StateSnapshot) -> None:
            """Internal handler for state updates (for debugging/logging)"""
            # This runs in UI thread due to queued connection
            pass  # Override in subclasses if needed

else:

    class _UnavailableSignal:
        """Placeholder that mirrors ``PySide6.Signal`` for headless tests."""

        def __init__(self, *_signature: object) -> None:
            self.signature = _signature

        def connect(self, *_args: object, **_kwargs: object) -> None:
            raise RuntimeError("PySide6 is required to use Qt signals.")

        def emit(self, *_args: object, **_kwargs: object) -> None:
            raise RuntimeError("PySide6 is required to use Qt signals.")

    class StateBus:  # type: ignore[override]
        """Fallback placeholder when Qt bindings are unavailable."""

        state_ready = _UnavailableSignal(object)
        start_simulation = _UnavailableSignal()
        stop_simulation = _UnavailableSignal()
        reset_simulation = _UnavailableSignal()
        pause_simulation = _UnavailableSignal()
        set_physics_dt = _UnavailableSignal(float)
        set_thermo_mode = _UnavailableSignal(str)
        set_master_isolation = _UnavailableSignal(bool)
        set_receiver_volume = _UnavailableSignal(float, str)
        load_road_profile = _UnavailableSignal(str)
        set_road_preset = _UnavailableSignal(str)
        physics_error = _UnavailableSignal(str)
        performance_update = _UnavailableSignal(object)

        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise ImportError(
                "PySide6 is not installed; StateBus is unavailable in this environment."
            )


# Export main classes
__all__ = [
    "StateSnapshot",
    "FrameState",
    "WheelState",
    "LineState",
    "TankState",
    "SystemAggregates",
    "StateBus",
]
