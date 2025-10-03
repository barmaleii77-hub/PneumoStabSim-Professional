"""
Runtime state management and signal bus
Provides snapshot-based state sharing between physics and UI threads
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
import numpy as np
from PySide6.QtCore import QObject, Signal, Qt

# Import pneumatic enums - use absolute import when possible
try:
    from pneumo.enums import Line, Wheel, Port
except ImportError:
    # Fallback for relative import
    try:
        from ..pneumo.enums import Line, Wheel, Port
    except ImportError:
        # Create minimal enums for testing
        from enum import Enum
        class Line(Enum):
            A1 = "A1"
            B1 = "B1"
            A2 = "A2"
            B2 = "B2"
        
        class Wheel(Enum):
            LP = "LP"
            PP = "PP"
            LZ = "LZ"
            PZ = "PZ"
        
        class Port(Enum):
            HEAD = "HEAD"
            ROD = "ROD"


@dataclass
class WheelState:
    """State of a single wheel/suspension point"""
    wheel: Wheel
    lever_angle: float = 0.0           # Lever angle (rad)
    piston_position: float = 0.0       # Piston position (m)
    piston_velocity: float = 0.0       # Piston velocity (m/s)
    
    # Cylinder volumes
    vol_head: float = 0.0              # Head side volume (m?)
    vol_rod: float = 0.0               # Rod side volume (m?)
    
    # Joint coordinates
    joint_x: float = 0.0               # Joint X coordinate (m)
    joint_y: float = 0.0               # Joint Y coordinate (m)
    joint_z: float = 0.0               # Joint Z coordinate (m)
    
    # Forces
    force_pneumatic: float = 0.0       # Net pneumatic force (N)
    force_spring: float = 0.0          # Spring force (N)
    force_damper: float = 0.0          # Damper force (N)
    
    # Road input
    road_excitation: float = 0.0       # Road input (m)


@dataclass
class LineState:
    """State of a pneumatic line"""
    line: Line
    
    # Gas state (TEMPORARY: different initial pressures for visibility)
    pressure: float = 150000.0         # Pressure (Pa) - 1.5 bar for lines
    temperature: float = 293.15        # Temperature (K)
    mass: float = 0.0                  # Gas mass (kg)
    volume: float = 0.0                # Total volume (m?)
    
    # Valve states and flows
    cv_atmo_open: bool = False         # Atmosphere check valve open
    cv_tank_open: bool = False         # Tank check valve open
    flow_atmo: float = 0.0             # Flow from atmosphere (kg/s)
    flow_tank: float = 0.0             # Flow to tank (kg/s)


@dataclass
class TankState:
    """State of receiver tank"""
    pressure: float = 200000.0         # Pressure (Pa) - 2.0 bar for tank
    temperature: float = 293.15        # Temperature (K)
    mass: float = 0.0                  # Gas mass (kg)
    volume: float = 0.0005             # Volume (m?)
    
    # Relief valve states
    relief_min_open: bool = False      # Min pressure relief open
    relief_stiff_open: bool = False    # Stiffness relief open
    relief_safety_open: bool = False   # Safety relief open
    
    flow_min: float = 0.0              # Min relief flow (kg/s)
    flow_stiff: float = 0.0            # Stiffness relief flow (kg/s)
    flow_safety: float = 0.0           # Safety relief flow (kg/s)


@dataclass
class FrameState:
    """State of vehicle frame (3-DOF rigid body)"""
    # Position (Y-down coordinate system)
    heave: float = 0.0                 # Vertical position (m, positive down)
    roll: float = 0.0                  # Roll angle (rad, positive = right down)
    pitch: float = 0.0                 # Pitch angle (rad, positive = nose down)
    
    # Velocity
    heave_rate: float = 0.0            # Vertical velocity (m/s)
    roll_rate: float = 0.0             # Roll rate (rad/s)
    pitch_rate: float = 0.0            # Pitch rate (rad/s)
    
    # Acceleration
    heave_accel: float = 0.0           # Vertical acceleration (m/s?)
    roll_accel: float = 0.0            # Roll acceleration (rad/s?)
    pitch_accel: float = 0.0           # Pitch acceleration (rad/s?)
    
    # Forces and moments
    total_force_z: float = 0.0         # Total vertical force (N)
    total_moment_x: float = 0.0        # Total pitch moment (N?m)
    total_moment_z: float = 0.0        # Total roll moment (N?m)


@dataclass
class SystemAggregates:
    """Aggregated system metrics for diagnostics and plotting"""
    # Energy metrics
    kinetic_energy: float = 0.0        # Total kinetic energy (J)
    potential_energy: float = 0.0      # Total potential energy (J)
    pneumatic_energy: float = 0.0      # Stored pneumatic energy (J)
    
    # Mass flow metrics
    total_flow_in: float = 0.0         # Total inflow (kg/s)
    total_flow_out: float = 0.0        # Total outflow (kg/s)
    net_flow: float = 0.0              # Net flow (kg/s)
    
    # Valve activity counters
    valve_switches: int = 0            # Total valve state changes
    relief_activations: int = 0        # Relief valve activations
    
    # Performance metrics
    physics_step_time: float = 0.0     # Last physics step time (s)
    integration_steps: int = 0         # Integration steps taken
    integration_failures: int = 0      # Integration failures


@dataclass
class StateSnapshot:
    """Complete system state snapshot for thread-safe sharing"""
    # Timing
    timestamp: float = field(default_factory=time.perf_counter)  # Absolute time
    simulation_time: float = 0.0       # Simulation time (s)
    dt_physics: float = 0.001          # Physics timestep used (s)
    step_number: int = 0               # Physics step counter
    
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
    thermo_mode: str = "ISOTHERMAL"    # "ISOTHERMAL" or "ADIABATIC"
    
    def __post_init__(self):
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
            Dictionary mapping wheel names to 3D positions
        """
        positions = {}
        
        for wheel, state in self.wheels.items():
            # Convert to string keys for easier access
            wheel_name = wheel.value  # LP, PP, LZ, PZ
            positions[wheel_name] = np.array([
                state.joint_x,
                state.joint_y,
                state.joint_z
            ])
        
        return positions
    
    def get_pressure_array(self) -> np.ndarray:
        """Get line pressures as array for plotting
        
        Returns:
            Array of pressures [A1, B1, A2, B2] in Pa
        """
        return np.array([
            self.lines[Line.A1].pressure,
            self.lines[Line.B1].pressure,
            self.lines[Line.A2].pressure,
            self.lines[Line.B2].pressure
        ])
    
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
                self.frame.heave, self.frame.roll, self.frame.pitch,
                self.frame.heave_rate, self.frame.roll_rate, self.frame.pitch_rate
            ]
            
            if not all(np.isfinite(v) for v in frame_values):
                return False
            
            # Check reasonable angle limits (±45 degrees)
            if abs(self.frame.roll) > 0.785 or abs(self.frame.pitch) > 0.785:
                return False
            
            # Check line pressures (must be positive, reasonable range)
            for line_state in self.lines.values():
                if line_state.pressure <= 0 or line_state.pressure > 1e7:  # 0 to 100 bar
                    return False
                if not np.isfinite(line_state.pressure):
                    return False
            
            # Check tank pressure
            if self.tank.pressure <= 0 or not np.isfinite(self.tank.pressure):
                return False
            
            return True
            
        except Exception:
            return False


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
    set_physics_dt = Signal(float)       # Change physics timestep
    set_thermo_mode = Signal(str)        # "ISOTHERMAL" or "ADIABATIC"
    set_master_isolation = Signal(bool)  # Master isolation valve
    
    # Road input signals
    load_road_profile = Signal(str)      # Load CSV road profile
    set_road_preset = Signal(str)        # Set road preset by name
    
    # Diagnostic signals
    physics_error = Signal(str)          # Physics thread error
    performance_update = Signal(object)  # Performance metrics
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Connect all signals to use queued connections for thread safety
        self.state_ready.connect(self._on_state_ready, Qt.QueuedConnection)
    
    def _on_state_ready(self, snapshot: StateSnapshot):
        """Internal handler for state updates (for debugging/logging)"""
        # This runs in UI thread due to queued connection
        pass  # Override in subclasses if needed


# Export main classes
__all__ = [
    'StateSnapshot', 'FrameState', 'WheelState', 'LineState', 'TankState',
    'SystemAggregates', 'StateBus'
]