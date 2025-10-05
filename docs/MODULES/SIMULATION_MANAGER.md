# SimulationManager & PhysicsWorker Module

## ?? Overview

**Module:** `src/runtime/sim_loop.py`

**Purpose:** Manage physics simulation in separate thread with thread-safe communication

**Status:** ? Fully Functional

---

## ?? Responsibilities

### **SimulationManager (Main Thread)**
1. **Thread Management**
   - Create and control PhysicsWorker thread
   - Start/stop/pause simulation
   - Monitor worker health

2. **State Communication**
   - Provide StateBus for signals
   - Route state snapshots to UI
   - Handle error messages

3. **Queue Management**
   - Maintain LatestOnlyQueue
   - Provide thread-safe state access
   - Track queue statistics

### **PhysicsWorker (Background Thread)**
1. **Physics Loop**
   - Fixed timestep execution (1ms)
   - ODE integration
   - State snapshot creation

2. **System Updates**
   - Update kinematics
   - Update gas network
   - Apply road excitation

3. **Error Handling**
   - Catch integration failures
   - Emit error signals
   - Graceful degradation

---

## ?? Class Diagram

```
???????????????????????????????????????????
?       SimulationManager                 ?
?       (Main Thread)                     ?
???????????????????????????????????????????
? - state_bus: StateBus                   ?
? - physics_worker: PhysicsWorker         ?
? - snapshot_queue: LatestOnlyQueue       ?
? - logger: Logger                        ?
???????????????????????????????????????????
? + start()                               ?
? + stop()                                ?
? + pause()                               ?
? + reset()                               ?
? + get_queue_stats() ? dict             ?
???????????????????????????????????????????
         ?
         ? creates & manages
         ?
???????????????????????????????????????????
?       PhysicsWorker                     ?
?       (QThread)                         ?
???????????????????????????????????????????
? - running: bool                         ?
? - paused: bool                          ?
? - physics_timer: QTimer                 ?
? - integrator: ODEIntegrator             ?
? - kinematics: CylinderKinematics        ?
? - gas_network: GasNetwork               ?
? - road_input: RoadInput                 ?
???????????????????????????????????????????
? + run()                                 ?
? - _execute_physics_step(dt)            ?
? - _create_state_snapshot() ? Snapshot  ?
? - _handle_integration_error(e)         ?
???????????????????????????????????????????
```

---

## ?? API Reference

### **SimulationManager**

```python
class SimulationManager:
    """Manage physics simulation thread and state communication"""
    
    def __init__(self, parent: QObject):
        """Initialize simulation manager
        
        Args:
            parent: Parent QObject (usually MainWindow)
        """
        self.state_bus = StateBus()  # Signal emitter
        self.snapshot_queue = LatestOnlyQueue()  # Thread-safe queue
        self.physics_worker = PhysicsWorker(self)  # Background thread
    
    def start(self):
        """Start physics simulation thread"""
        if not self.physics_worker.isRunning():
            self.physics_worker.start()
            self.state_bus.simulation_started.emit()
    
    def stop(self):
        """Stop physics simulation thread"""
        if self.physics_worker.isRunning():
            self.physics_worker.running = False
            self.physics_worker.wait(1000)  # Wait 1 second
            self.state_bus.simulation_stopped.emit()
    
    def pause(self, paused: bool):
        """Pause/resume simulation
        
        Args:
            paused: True to pause, False to resume
        """
        self.physics_worker.paused = paused
        self.state_bus.simulation_paused.emit(paused)
    
    def reset(self):
        """Reset simulation to initial state"""
        self.stop()
        # Reset all systems
        self.physics_worker.reset_state()
        self.state_bus.simulation_reset.emit()
    
    def get_queue_stats(self) -> dict:
        """Get queue statistics
        
        Returns:
            Dictionary with queue metrics
        """
        return {
            'size': self.snapshot_queue.qsize(),
            'put_count': self.snapshot_queue.put_count,
            'get_count': self.snapshot_queue.get_count,
            'dropped': self.snapshot_queue.dropped_count
        }
```

### **PhysicsWorker**

```python
class PhysicsWorker(QThread):
    """Background thread for physics simulation"""
    
    # Signals
    state_ready = Signal(object)  # StateSnapshot
    error_occurred = Signal(str)  # Error message
    
    def __init__(self, manager: SimulationManager):
        """Initialize physics worker
        
        Args:
            manager: Parent simulation manager
        """
        super().__init__()
        self.manager = manager
        self.running = False
        self.paused = False
        
        # Physics systems
        self.integrator = ODEIntegrator()
        self.kinematics = CylinderKinematics()
        self.gas_network = GasNetwork()
        self.road_input = RoadInput()
        
        # Timing
        self.dt = 0.001  # 1ms timestep
        self.simulation_time = 0.0
    
    def run(self):
        """Main physics loop (runs in thread)"""
        self.running = True
        
        # Create timer for fixed timestep
        self.physics_timer = QTimer()
        self.physics_timer.setInterval(1)  # 1ms
        self.physics_timer.timeout.connect(self._physics_step)
        self.physics_timer.start()
        
        # Start event loop
        self.exec()
    
    def _physics_step(self):
        """Execute single physics timestep"""
        if self.paused or not self.running:
            return
        
        try:
            # Execute physics
            self._execute_physics_step(self.dt)
            
            # Create snapshot
            snapshot = self._create_state_snapshot()
            
            # Emit to main thread (Qt.QueuedConnection)
            self.state_ready.emit(snapshot)
            
            # Update time
            self.simulation_time += self.dt
            
        except Exception as e:
            self._handle_integration_error(e)
    
    def _execute_physics_step(self, dt: float):
        """Execute physics calculations
        
        Args:
            dt: Timestep in seconds
        """
        # 1. Get road excitation
        road_inputs = self.road_input.get_wheel_excitation(
            self.simulation_time
        )
        
        # 2. Update kinematics
        self.kinematics.update_from_angles(road_inputs)
        
        # 3. Update gas network
        self.gas_network.apply_valves_and_flows(dt)
        
        # 4. Integrate dynamics
        self.integrator.step(dt)
    
    def _create_state_snapshot(self) -> StateSnapshot:
        """Create state snapshot for UI
        
        Returns:
            StateSnapshot with current physics state
        """
        return StateSnapshot(
            simulation_time=self.simulation_time,
            step_number=int(self.simulation_time / self.dt),
            corners={
                'fl': self._get_corner_state('fl'),
                'fr': self._get_corner_state('fr'),
                'rl': self._get_corner_state('rl'),
                'rr': self._get_corner_state('rr')
            },
            gas_network=self.gas_network.get_state(),
            aggregates=self._compute_aggregates()
        )
    
    def _handle_integration_error(self, error: Exception):
        """Handle physics integration errors
        
        Args:
            error: Exception that occurred
        """
        error_msg = f"Physics error: {str(error)}"
        self.error_occurred.emit(error_msg)
        
        # Log but continue
        import logging
        logging.getLogger(__name__).error(error_msg)
```

---

## ?? Threading Architecture

```
???????????????????????????????????????????????????????
?                  MAIN THREAD (UI)                   ?
?                                                     ?
?  SimulationManager                                  ?
?  ?? state_bus (signals)                            ?
?  ?? snapshot_queue (LatestOnlyQueue)               ?
?  ?? physics_worker (QThread)                       ?
?                                                     ?
?  Responsibilities:                                  ?
?  - UI updates (60 Hz)                              ?
?  - User input handling                             ?
?  - QML rendering                                   ?
?  - State snapshot consumption                      ?
?                                                     ?
???????????????????????????????????????????????????????
                  ?
                  ? QThread boundary
                  ? (Qt.QueuedConnection)
                  ?
???????????????????????????????????????????????????????
?             PHYSICS THREAD (Worker)                 ?
?                                                     ?
?  PhysicsWorker (QThread)                           ?
?  ?? physics_timer (1ms)                            ?
?  ?? integrator (ODE solver)                        ?
?  ?? kinematics (CylinderKinematics)                ?
?  ?? gas_network (GasNetwork)                       ?
?  ?? road_input (RoadInput)                         ?
?                                                     ?
?  Responsibilities:                                  ?
?  - Physics calculations (1000 Hz)                  ?
?  - ODE integration                                 ?
?  - State snapshot creation                         ?
?  - Error handling                                  ?
?                                                     ?
???????????????????????????????????????????????????????
```

---

## ?? Data Flow

### **Simulation Start**

```
User clicks "Start"
      ?
MainWindow._on_sim_control("start")
      ?
SimulationManager.start()
      ?
PhysicsWorker.start()  [Thread starts]
      ?
PhysicsWorker.run()
      ?
Create QTimer (1ms interval)
      ?
      [Physics loop begins]
      ?
PhysicsWorker._physics_step()  [Every 1ms]
      ?
?? Get road inputs
?? Update kinematics
?? Update gas network
?? Integrate dynamics
?? Create StateSnapshot
?? Emit state_ready signal
      ?
      [Qt.QueuedConnection]
      ?
MainWindow._on_state_update(snapshot)
      ?
Update UI (3D view, charts, status)
```

### **State Snapshot Flow**

```
PhysicsWorker (1000 Hz)
      ?
      ?? Create StateSnapshot
      ?
      ?? Put in LatestOnlyQueue
      ?     (Old snapshots dropped!)
      ?
      ?? Emit state_ready signal
            ?
            [Qt.QueuedConnection]
            ?
MainWindow (60 Hz)
      ?
      ?? Get latest snapshot from queue
      ?
      ?? Update 3D scene
      ?
      ?? Update charts
      ?
      ?? Update status bar
```

---

## ?? Configuration

### **Timing Parameters**

```python
# Physics timestep (fixed)
PHYSICS_DT = 0.001  # 1ms (1000 Hz)

# UI update rate
UI_UPDATE_INTERVAL = 16  # 16ms (~60 Hz)

# Queue size (latest-only)
SNAPSHOT_QUEUE_SIZE = 1  # Only keep latest
```

### **Thread Safety**

```python
# CORRECT: Cross-thread signal connection
state_bus.state_ready.connect(
    main_window._on_state_update,
    Qt.ConnectionType.QueuedConnection  # CRITICAL!
)

# WRONG: Direct connection (crashes!)
state_bus.state_ready.connect(
    main_window._on_state_update,
    Qt.ConnectionType.DirectConnection  # DON'T DO THIS!
)
```

---

## ?? Example Usage

### **Basic Simulation Control**

```python
from src.runtime.sim_loop import SimulationManager
from PySide6.QtWidgets import QMainWindow

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Create simulation manager
        self.sim_manager = SimulationManager(self)
        
        # Connect signals
        self.sim_manager.state_bus.state_ready.connect(
            self._on_state_update,
            Qt.QueuedConnection
        )
        
        self.sim_manager.state_bus.physics_error.connect(
            self._on_physics_error,
            Qt.QueuedConnection
        )
    
    def start_simulation(self):
        """Start simulation"""
        self.sim_manager.start()
    
    def stop_simulation(self):
        """Stop simulation"""
        self.sim_manager.stop()
    
    def _on_state_update(self, snapshot):
        """Handle state snapshot"""
        print(f"Time: {snapshot.simulation_time:.3f}s")
        print(f"Step: {snapshot.step_number}")
    
    def _on_physics_error(self, error_msg):
        """Handle physics error"""
        print(f"ERROR: {error_msg}")
```

---

## ?? Known Issues & Fixes

### **Issue 1: Thread not stopping**

**Problem:** `worker.wait()` hangs forever

**Cause:** Event loop not exiting

**Solution:**
```python
def stop(self):
    self.physics_worker.running = False
    self.physics_worker.quit()  # Exit event loop
    self.physics_worker.wait(1000)  # Wait max 1 second
```

### **Issue 2: State snapshots delayed**

**Problem:** UI shows old data

**Cause:** Queue not being consumed fast enough

**Solution:** Use `LatestOnlyQueue` (drops old snapshots)

---

## ?? Test Coverage

**Test File:** `tests/test_sim_loop.py`

**Test Cases:**
1. ? SimulationManager creation
2. ? Thread start/stop
3. ? State snapshot emission
4. ? Error handling
5. ? Pause/resume
6. ? Queue statistics

**Coverage:** ~75%

---

## ?? Dependencies

```python
from PySide6.QtCore import QThread, QTimer, QObject, Signal, Qt
from .state import StateSnapshot, StateBus
from .sync import LatestOnlyQueue
from ..physics.integrator import ODEIntegrator
from ..mechanics.kinematics import CylinderKinematics
from ..pneumo.network import GasNetwork
from ..road.engine import RoadInput
```

---

## ?? Configuration

### **Default Physics Settings**

```python
DEFAULT_PHYSICS_CONFIG = {
    'timestep': 0.001,           # 1ms
    'integrator': 'Radau',       # Stiff ODE solver
    'max_steps': 10000,          # Per integration
    'tolerance': 1e-6,           # Integration tolerance
}
```

---

## ?? Future Enhancements

1. **Variable timestep** - Adaptive integration
2. **Multi-threading** - Parallel corner calculations
3. **State recording** - Save/replay simulations
4. **Checkpointing** - Resume from saved state

---

## ?? References

- **Threading:** [Qt Threading Basics](https://doc.qt.io/qt-6/thread-basics.html)
- **ODE Integration:** [SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)
- **State Management:** `src/runtime/state.py`

---

**Last Updated:** 2025-01-05  
**Module Version:** 2.0.0  
**Status:** Production Ready ?
