"""
Physics simulation loop with fixed timestep
Runs in dedicated QThread with QTimer for precise timing
"""

import time
import logging
from typing import Optional, Dict, Any
import numpy as np

from PySide6.QtCore import QObject, QTimer, Signal, Slot, Qt
from PySide6.QtCore import QThread

from .state import StateSnapshot, StateBus, FrameState, WheelState, LineState, TankState, SystemAggregates
from .sync import LatestOnlyQueue, PerformanceMetrics, TimingAccumulator, ThreadSafeCounter

# Import physics and simulation modules
from ..physics.odes import RigidBody3DOF, create_initial_conditions, f_rhs
from ..physics.integrator import step_dynamics, PhysicsLoopConfig, create_default_rigid_body
from ..pneumo.enums import Wheel, Line, ThermoMode
from ..road.engine import RoadInput


class PhysicsWorker(QObject):
    """Physics simulation worker running in dedicated thread
    
    Handles fixed-timestep physics simulation with road inputs,
    pneumatic system, and 3-DOF frame dynamics.
    """
    
    # Signals emitted to UI thread
    state_ready = Signal(object)       # StateSnapshot
    error_occurred = Signal(str)       # Error message
    performance_update = Signal(object) # PerformanceMetrics
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Physics configuration
        self.dt_physics = 0.001         # 1ms physics timestep
        self.vsync_render_hz = 60.0     # Target render rate
        
        # Simulation state
        self.is_running = False
        self.is_configured = False
        self.simulation_time = 0.0
        self.step_counter = 0
        
        # Physics objects (will be initialized in configure)
        self.rigid_body: Optional[RigidBody3DOF] = None
        self.road_input: Optional[RoadInput] = None
        self.pneumatic_system: Optional[Any] = None
        self.gas_network: Optional[Any] = None
        
        # Current physics state
        self.physics_state: np.ndarray = np.zeros(6)  # [Y, ?z, ?x, dY, d?z, d?x]
        
        # Simulation modes
        self.thermo_mode = ThermoMode.ISOTHERMAL
        self.master_isolation_open = False
        
        # Threading objects (created in target thread)
        self.physics_timer: Optional[QTimer] = None
        
        # Performance monitoring
        self.performance = PerformanceMetrics()
        self.timing_accumulator = TimingAccumulator(self.dt_physics)
        self.step_time_samples = []
        
        # Thread safety
        self.error_counter = ThreadSafeCounter()
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
    def configure(self, dt_phys: float = 0.001, vsync_render_hz: float = 60.0):
        """Configure physics parameters"""
        self.dt_physics = dt_phys
        self.vsync_render_hz = vsync_render_hz
        
        # Update timing accumulator
        self.timing_accumulator = TimingAccumulator(self.dt_physics)
        self.performance.target_dt = self.dt_physics
        
        # Create default physics objects
        self._initialize_physics_objects()
        
        self.is_configured = True
        self.logger.info(f"Physics configured: dt={dt_phys*1000:.3f}ms, render={vsync_render_hz:.1f}Hz")
    
    def _initialize_physics_objects(self):
        """Initialize physics simulation objects"""
        try:
            # Create 3-DOF rigid body
            self.rigid_body = create_default_rigid_body()
            
            # Initialize physics state (at rest)
            self.physics_state = create_initial_conditions()
            
            # TODO: Initialize pneumatic system and gas network
            # For now, create minimal stubs
            self.pneumatic_system = None  # Will be set up later
            self.gas_network = None
            
            # TODO: Initialize road input
            # For now, create minimal stub
            self.road_input = None
            
            self.logger.info("Physics objects initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize physics objects: {e}")
            raise
    
    @Slot()
    def start_simulation(self):
        """Start physics simulation (called from UI thread)"""
        if not self.is_configured:
            self.error_occurred.emit("Physics worker not configured")
            return
        
        if self.is_running:
            self.logger.warning("Simulation already running")
            return
        
        # Create timer in this thread (will be moved to physics thread)
        if self.physics_timer is None:
            self.physics_timer = QTimer()
            self.physics_timer.timeout.connect(self._physics_step)
            self.physics_timer.setSingleShot(False)
        
        # Start timer with high precision
        timer_interval_ms = max(1, int(self.dt_physics * 1000))  # At least 1ms
        self.physics_timer.start(timer_interval_ms)
        
        self.is_running = True
        self.timing_accumulator.reset()
        
        self.logger.info(f"Physics simulation started, timer interval: {timer_interval_ms}ms")
    
    @Slot()
    def stop_simulation(self):
        """Stop physics simulation"""
        if self.physics_timer:
            self.physics_timer.stop()
        
        self.is_running = False
        self.logger.info("Physics simulation stopped")
    
    @Slot()
    def reset_simulation(self):
        """Reset simulation to initial state"""
        self.simulation_time = 0.0
        self.step_counter = 0
        
        if self.rigid_body:
            self.physics_state = create_initial_conditions()
        
        self.timing_accumulator.reset()
        self.performance = PerformanceMetrics()
        self.performance.target_dt = self.dt_physics
        
        self.logger.info("Simulation reset to initial state")
    
    @Slot()
    def pause_simulation(self):
        """Pause/unpause simulation"""
        if self.is_running:
            self.stop_simulation()
        else:
            self.start_simulation()
    
    @Slot(str)
    def set_thermo_mode(self, mode: str):
        """Set thermodynamic mode"""
        if mode == "ISOTHERMAL":
            self.thermo_mode = ThermoMode.ISOTHERMAL
        elif mode == "ADIABATIC":
            self.thermo_mode = ThermoMode.ADIABATIC
        else:
            self.error_occurred.emit(f"Unknown thermo mode: {mode}")
            return
        
        self.logger.info(f"Thermo mode set to: {mode}")
    
    @Slot(bool)
    def set_master_isolation(self, open: bool):
        """Set master isolation valve state"""
        self.master_isolation_open = open
        self.logger.info(f"Master isolation: {'OPEN' if open else 'CLOSED'}")
    
    @Slot(float)
    def set_physics_dt(self, dt: float):
        """Change physics timestep"""
        if dt <= 0 or dt > 0.1:  # Reasonable limits
            self.error_occurred.emit(f"Invalid physics dt: {dt}")
            return
        
        old_dt = self.dt_physics
        self.dt_physics = dt
        self.timing_accumulator = TimingAccumulator(dt)
        self.performance.target_dt = dt
        
        # Restart timer if running
        if self.is_running and self.physics_timer:
            self.physics_timer.stop()
            timer_interval_ms = max(1, int(dt * 1000))
            self.physics_timer.start(timer_interval_ms)
        
        self.logger.info(f"Physics dt changed: {old_dt*1000:.3f}ms ? {dt*1000:.3f}ms")
    
    @Slot()
    def _physics_step(self):
        """Single physics simulation step (called by QTimer)"""
        if not self.is_running:
            return
        
        step_start_time = time.perf_counter()
        
        try:
            # Use timing accumulator to determine number of steps
            steps_to_take = self.timing_accumulator.update()
            
            for _ in range(steps_to_take):
                self._execute_physics_step()
            
            # Update performance metrics
            step_end_time = time.perf_counter()
            step_time = step_end_time - step_start_time
            self.performance.update_step_time(step_time)
            
            # Emit performance update periodically
            if self.step_counter % 100 == 0:  # Every 100 steps
                self.performance_update.emit(self.performance.get_summary())
            
            # Create and emit state snapshot
            snapshot = self._create_state_snapshot()
            if snapshot and snapshot.validate():
                self.state_ready.emit(snapshot)
            else:
                self.error_counter.increment()
                if self.error_counter.get() > 10:  # Too many invalid states
                    self.error_occurred.emit("Too many invalid state snapshots")
                    self.stop_simulation()
        
        except Exception as e:
            self.logger.error(f"Physics step failed: {e}")
            self.error_occurred.emit(f"Physics step error: {str(e)}")
            self.stop_simulation()
    
    def _execute_physics_step(self):
        """Execute single physics timestep"""
        # 1. Get road inputs
        road_excitations = self._get_road_inputs()
        
        # 2. Update geometry/kinematics
        # TODO: Update lever angles, piston positions, volumes
        
        # 3. Update gas system
        # TODO: Update pressures due to volume changes
        # TODO: Apply valve flows
        
        # 4. Integrate 3-DOF dynamics
        if self.rigid_body:
            try:
                # Use placeholder system/gas for now
                result = step_dynamics(
                    y0=self.physics_state,
                    t0=self.simulation_time,
                    dt=self.dt_physics,
                    params=self.rigid_body,
                    system=self.pneumatic_system,
                    gas=self.gas_network,
                    method="Radau"
                )
                
                if result.success:
                    self.physics_state = result.y_final
                else:
                    self.performance.integration_failures += 1
                    self.logger.warning(f"Integration failed: {result.message}")
            
            except Exception as e:
                self.performance.integration_failures += 1
                self.logger.error(f"Integration error: {e}")
        
        # Update simulation time and step counter
        self.simulation_time += self.dt_physics
        self.step_counter += 1
    
    def _get_road_inputs(self) -> Dict[str, float]:
        """Get road excitation for all wheels"""
        if self.road_input:
            try:
                return self.road_input.get_wheel_excitation(self.simulation_time)
            except Exception as e:
                self.logger.warning(f"Road input error: {e}")
        
        # Return zero excitation as fallback
        return {'LF': 0.0, 'RF': 0.0, 'LR': 0.0, 'RR': 0.0}
    
    def _create_state_snapshot(self) -> Optional[StateSnapshot]:
        """Create current state snapshot"""
        try:
            snapshot = StateSnapshot()
            
            # Basic timing info
            snapshot.simulation_time = self.simulation_time
            snapshot.dt_physics = self.dt_physics
            snapshot.step_number = self.step_counter
            
            # Frame state from physics integration
            if len(self.physics_state) >= 6:
                Y, phi_z, theta_x, dY, dphi_z, dtheta_x = self.physics_state
                
                snapshot.frame = FrameState(
                    heave=float(Y),
                    roll=float(phi_z),
                    pitch=float(theta_x),
                    heave_rate=float(dY),
                    roll_rate=float(dphi_z),
                    pitch_rate=float(dtheta_x)
                )
            
            # Road excitations
            road_excitations = self._get_road_inputs()
            
            # Wheel states
            for wheel in [Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ]:
                wheel_state = WheelState(wheel=wheel)
                
                # Add road excitation
                wheel_key = wheel.value  # LP, PP, LZ, PZ
                if wheel_key in road_excitations:
                    wheel_state.road_excitation = road_excitations[wheel_key]
                
                # TODO: Add actual wheel state from pneumatic system
                
                snapshot.wheels[wheel] = wheel_state
            
            # Line states (placeholder)
            for line in [Line.A1, Line.B1, Line.A2, Line.B2]:
                line_state = LineState(line=line)
                # TODO: Get actual line state from gas network
                snapshot.lines[line] = line_state
            
            # Tank state (placeholder)
            snapshot.tank = TankState()
            
            # System aggregates
            snapshot.aggregates = SystemAggregates(
                physics_step_time=self.performance.avg_step_time,
                integration_steps=self.step_counter,
                integration_failures=self.performance.integration_failures
            )
            
            # Configuration
            snapshot.master_isolation_open = self.master_isolation_open
            snapshot.thermo_mode = self.thermo_mode.name if hasattr(self.thermo_mode, 'name') else str(self.thermo_mode)
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to create state snapshot: {e}")
            return None


class SimulationManager(QObject):
    """High-level simulation manager
    
    Manages PhysicsWorker in separate thread and provides
    unified interface for UI interaction.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create physics thread and worker
        self.physics_thread = QThread()
        self.physics_worker = PhysicsWorker()
        
        # Move worker to physics thread
        self.physics_worker.moveToThread(self.physics_thread)
        
        # Create state bus for communication
        self.state_bus = StateBus()
        
        # Create state queue for latest-only semantics
        self.state_queue = LatestOnlyQueue()
        
        # Connect signals
        self._connect_signals()
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def _connect_signals(self):
        """Connect signals between components"""
        # Physics worker signals
        self.physics_worker.state_ready.connect(
            self._on_state_ready, Qt.QueuedConnection)
        self.physics_worker.error_occurred.connect(
            self._on_physics_error, Qt.QueuedConnection)
        
        # State bus control signals
        self.state_bus.start_simulation.connect(
            self.physics_worker.start_simulation, Qt.QueuedConnection)
        self.state_bus.stop_simulation.connect(
            self.physics_worker.stop_simulation, Qt.QueuedConnection)
        self.state_bus.reset_simulation.connect(
            self.physics_worker.reset_simulation, Qt.QueuedConnection)
        self.state_bus.pause_simulation.connect(
            self.physics_worker.pause_simulation, Qt.QueuedConnection)
        
        # Configuration signals
        self.state_bus.set_physics_dt.connect(
            self.physics_worker.set_physics_dt, Qt.QueuedConnection)
        self.state_bus.set_thermo_mode.connect(
            self.physics_worker.set_thermo_mode, Qt.QueuedConnection)
        self.state_bus.set_master_isolation.connect(
            self.physics_worker.set_master_isolation, Qt.QueuedConnection)
        
        # Thread lifecycle
        self.physics_thread.started.connect(self._on_thread_started)
        self.physics_thread.finished.connect(self._on_thread_finished)
    
    def start(self):
        """Start simulation manager"""
        if not self.physics_thread.isRunning():
            # Configure physics worker
            self.physics_worker.configure()
            
            # Start physics thread
            self.physics_thread.start()
            
            self.logger.info("Simulation manager started")
    
    def stop(self):
        """Stop simulation manager"""
        if self.physics_thread.isRunning():
            # Stop simulation first
            self.state_bus.stop_simulation.emit()
            
            # Quit thread gracefully
            self.physics_thread.quit()
            self.physics_thread.wait(5000)  # Wait up to 5 seconds
            
            if self.physics_thread.isRunning():
                self.logger.warning("Physics thread did not stop gracefully")
                self.physics_thread.terminate()
                self.physics_thread.wait(1000)
            
            self.logger.info("Simulation manager stopped")
    
    def get_latest_state(self) -> Optional[StateSnapshot]:
        """Get latest state snapshot without blocking"""
        return self.state_queue.get_nowait()
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get state queue statistics"""
        return self.state_queue.get_stats()
    
    @Slot(object)
    def _on_state_ready(self, snapshot):
        """Handle state ready from physics worker"""
        # Put in latest-only queue
        self.state_queue.put_nowait(snapshot)
        
        # Re-emit through state bus
        self.state_bus.state_ready.emit(snapshot)
    
    @Slot(str)
    def _on_physics_error(self, error_msg):
        """Handle physics error"""
        self.logger.error(f"Physics error: {error_msg}")
        self.state_bus.physics_error.emit(error_msg)
    
    @Slot()
    def _on_thread_started(self):
        """Handle physics thread started"""
        self.logger.info("Physics thread started successfully")
    
    @Slot()
    def _on_thread_finished(self):
        """Handle physics thread finished"""
        self.logger.info("Physics thread finished")


# Export main classes
__all__ = ['PhysicsWorker', 'SimulationManager']