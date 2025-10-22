# MainWindow Module

## ?? Overview

**Module:** `src/ui/main_window.py`

**Purpose:** Main application window and UI controller

**Status:** ? Fully Functional

---

## ?? Responsibilities

1. **Window Management**
   - Create main window with panels
   - Manage dock widgets
   - Handle window events (show, resize, close)

2. **UI Coordination**
   - Connect panel signals
   - Route user input to simulation
   - Update UI from simulation state

3. **Python ? QML Integration**
   - Load QML 3D scene
   - Update QML properties
   - Invoke QML functions
   - Read QML state

4. **Simulation Control**
   - Start/stop/pause/reset
   - Parameter updates
   - Error handling

---

## ?? Class Diagram

```
???????????????????????????????????????????????
?          MainWindow                         ?
?          (QMainWindow)                      ?
???????????????????????????????????????????????
? - simulation_manager: SimulationManager     ?
? - geometry_converter: GeometryBridge        ?
? - _qml_root_object: QObject                 ?
? - current_snapshot: StateSnapshot           ?
?                                             ?
? PANELS:                                     ?
? - geometry_panel: GeometryPanel             ?
? - pneumo_panel: PneumoPanel                 ?
? - modes_panel: ModesPanel                   ?
? - road_panel: RoadPanel                     ?
? - chart_widget: ChartWidget                 ?
???????????????????????????????????????????????
? PUBLIC METHODS:                             ?
? + __init__(use_qml_3d: bool)                ?
? + show()                                    ?
? + close()                                   ?
?                                             ?
? PRIVATE METHODS:                            ?
? - _setup_central()                          ?
? - _setup_docks()                            ?
? - _setup_menus()                            ?
? - _connect_simulation_signals()             ?
? - _on_state_update(snapshot)                ?
? - _on_geometry_changed(params)              ?
? - _on_animation_changed(params)             ?
? - _update_3d_scene_from_snapshot(snapshot)  ?
???????????????????????????????????????????????
```

---

## ?? Key Methods

### **1. Initialization**

```python
def __init__(self, use_qml_3d: bool = True):
    """Initialize main window

    Args:
        use_qml_3d: Use Qt Quick 3D (True) or legacy OpenGL (False)
    """
    super().__init__()

    # Create simulation manager
    self.simulation_manager = SimulationManager(self)

    # Create geometry converter
    self.geometry_converter = create_geometry_converter()

    # Setup UI
    self._setup_central()      # QML 3D scene
    self._setup_docks()        # Control panels
    self._setup_menus()        # Menu bar
    self._setup_toolbar()      # Toolbar

    # Connect signals
    self._connect_simulation_signals()

    # Start render timer (60 FPS)
    self.render_timer = QTimer(self)
    self.render_timer.timeout.connect(self._update_render)
    self.render_timer.start(16)  # 16ms = 60 FPS
```

---

### **2. QML Scene Setup**

```python
def _setup_qml_3d_view(self):
    """Setup Qt Quick 3D visualization"""
    # Create QQuickWidget
    self._qquick_widget = QQuickWidget(self)
    self._qquick_widget.setResizeMode(
        QQuickWidget.ResizeMode.SizeRootObjectToView
    )

    # Load main.qml
    qml_path = Path("assets/qml/main.qml")
    qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
    self._qquick_widget.setSource(qml_url)

    # Get root object for property access
    self._qml_root_object = self._qquick_widget.rootObject()

    # Set as central widget
    self.setCentralWidget(self._qquick_widget)
```

---

### **3. Signal Routing**

```python
def _wire_panel_signals(self):
    """Connect panel signals to handlers"""

    # Geometry changes ? Update 3D scene
    self.geometry_panel.geometry_changed.connect(
        self._on_geometry_changed
    )

    # Animation changes ? Update animation params
    self.modes_panel.animation_changed.connect(
        self._on_animation_changed
    )

    # Simulation control ? Start/stop physics
    self.modes_panel.simulation_control.connect(
        self._on_sim_control
    )

    # Physics state ? Update UI
    self.simulation_manager.state_bus.state_ready.connect(
        self._on_state_update
    )
```

---

### **4. Geometry Update Handler**

```python
def _on_geometry_changed(self, geometry_params: dict):
    """Handle geometry parameter changes

    Args:
        geometry_params: Dict with geometry values
            {
                'frameLength': float,      # mm
                'frameHeight': float,      # mm
                'leverLength': float,      # mm
                'cylinderBodyLength': float,  # mm
                ...
            }
    """
    # Update QML scene via invokeMethod
    from PySide6.QtCore import QMetaObject, Q_ARG, Qt

    success = QMetaObject.invokeMethod(
        self._qml_root_object,
        "updateGeometry",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", geometry_params)
    )

    if not success:
        # Fallback: Set properties individually
        self._set_geometry_properties_fallback(geometry_params)
```

---

### **5. Animation Update Handler**

```python
def _on_animation_changed(self, animation_params: dict):
    """Handle animation parameter changes

    Args:
        animation_params: Dict with animation values
            {
                'amplitude': float,    # m
                'frequency': float,    # Hz
                'phase': float,        # degrees
                'lf_phase': float,     # degrees
                ...
            }
    """
    # Set QML properties directly
    if 'amplitude' in animation_params:
        # Convert amplitude from meters to degrees
        amplitude_deg = animation_params['amplitude'] * 1000 / 10
        self._qml_root_object.setProperty("userAmplitude", amplitude_deg)

    if 'frequency' in animation_params:
        self._qml_root_object.setProperty(
            "userFrequency",
            animation_params['frequency']
        )

    # ... (other parameters)
```

---

### **6. State Update Handler (CRITICAL!)**

```python
def _update_3d_scene_from_snapshot(self, snapshot: StateSnapshot):
    """Update 3D scene with simulation state

    This is called 60 times per second from render timer!

    Args:
        snapshot: Current physics state
    """
    if not self._qml_root_object:
        return

    # Read animation parameters FROM QML
    # (These were set by _on_animation_changed)
    amplitude = self._qml_root_object.property("userAmplitude") or 8.0
    frequency = self._qml_root_object.property("userFrequency") or 1.0
    phase_global = self._qml_root_object.property("userPhaseGlobal") or 0.0

    # Calculate lever angles using animation formula
    import time
    t = time.time()
    omega = 2.0 * np.pi * frequency

    angles = {
        'fl': amplitude * np.sin(omega * t + np.deg2rad(phase_global)),
        'fr': amplitude * np.sin(omega * t + np.deg2rad(phase_global)),
        'rl': amplitude * np.sin(omega * t + np.deg2rad(phase_global)),
        'rr': amplitude * np.sin(omega * t + np.deg2rad(phase_global))
    }

    # Calculate piston positions using GeometryBridge
    piston_positions = {}
    for corner, angle in angles.items():
        coords = self.geometry_converter.get_corner_3d_coords(
            corner, angle, None
        )
        piston_positions[corner] = coords['pistonPositionMm']

    # Update QML: Set angles
    for corner, angle in angles.items():
        self._qml_root_object.setProperty(f"{corner}_angle", float(angle))

    # Update QML: Set piston positions
    QMetaObject.invokeMethod(
        self._qml_root_object,
        "updatePistonPositions",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", piston_positions)
    )
```

**WHY THIS WORKS:**
1. User changes amplitude slider ? `_on_animation_changed()` ? QML property updated
2. Every frame: `_update_render()` ? reads UPDATED amplitude from QML
3. Calculates new angles with current amplitude
4. Sends to QML ? smooth animation with user-controlled params!

---

## ?? Event Flow

### **User Changes Amplitude**

```
User drags slider
      ?
ModesPanel.amplitude_slider.valueEdited
      ?
ModesPanel.animation_changed.emit({'amplitude': 0.1})
      ?
MainWindow._on_animation_changed({'amplitude': 0.1})
      ?
QML.setProperty("userAmplitude", 10.0)  // Convert m?deg
      ?
      [QML property updated]
      ?
      [Next frame...]
      ?
MainWindow._update_render()
      ?
_update_3d_scene_from_snapshot()
      ?
amplitude = QML.property("userAmplitude")  // Read: 10.0
      ?
angle = 10.0 * sin(...)  // Use new amplitude!
      ?
QML.setProperty("fl_angle", angle)
      ?
      [QML recalculates j_rod from fl_angle]
      ?
      [3D scene updates with new amplitude!]
```

---

## ?? Configuration

### **Default Window Settings**

```python
SETTINGS_ORG = "PneumoStabSim"
SETTINGS_APP = "PneumoStabSimApp"

# Window geometry
resize(1200, 800)
setMinimumSize(1000, 700)

# Update rates
RENDER_FPS = 60      # UI update rate
PHYSICS_FPS = 1000   # Physics timestep
```

---

## ?? Error Handling

```python
def _on_physics_error(self, msg: str):
    """Handle physics errors

    Args:
        msg: Error message from physics engine
    """
    self.status_bar.showMessage(f"Physics Error: {msg}")
    self.logger.error(f"Physics engine error: {msg}")

    # Show critical error dialog
    if "CRITICAL" in msg.upper():
        QMessageBox.critical(
            self,
            "Physics Engine Error",
            f"Critical error:\n\n{msg}\n\n"
            "Simulation may be unstable."
        )
```

---

## ?? Performance Monitoring

```python
def _update_render(self):
    """Update UI (60 FPS)"""
    if not self._qml_root_object:
        return

    # Update status bar
    if self.current_snapshot:
        fps = 1.0 / self.current_snapshot.aggregates.physics_step_time
        self.fps_label.setText(f"Physics FPS: {fps:.1f}")

    # Update queue stats
    stats = self.simulation_manager.get_queue_stats()
    self.queue_label.setText(f"Queue: {stats['get_count']}/{stats['put_count']}")
```

---

## ?? Known Issues & Fixes

### **Issue 1: Animation params not updating**
**Problem:** `_update_3d_scene_from_snapshot()` used hardcoded values

**Fix:** Read from QML properties set by `_on_animation_changed()`

**Commit:** `adf8c82` (2025-01-05)

### **Issue 2: Log spam (60/sec)**
**Problem:** Logged amplitude every frame

**Fix:** Cache last params, log only on change

**Commit:** `c06c9d7` (2025-01-05)

---

## ?? Test Coverage

**Test Files:**
- `test_main_window.py` (unit tests)
- `test_qml_integration.py` (integration tests)

**Coverage:** ~70%

---

## ?? Dependencies

```python
from PySide6.QtWidgets import QMainWindow, QDockWidget, ...
from PySide6.QtCore import QTimer, Slot, Qt, QMetaObject
from PySide6.QtQuickWidgets import QQuickWidget

from .geometry_bridge import create_geometry_converter
from .panels import GeometryPanel, ModesPanel, ...
from ..runtime import SimulationManager, StateSnapshot
```

---

## ?? Future Enhancements

1. **Preset management** (save/load configurations)
2. **Multi-window support** (separate 3D views)
3. **Plugin system** (custom panels)
4. **Scripting interface** (Python console)

---

**Last Updated:** 2025-01-05
**Module Version:** 2.0.0
**Status:** Production Ready ?
