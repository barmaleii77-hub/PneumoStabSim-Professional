# Python ? QML API Documentation

## Overview

PneumoStabSim uses a bidirectional communication system between Python physics engine and QML 3D visualization.

**Architecture:**
```
Python Physics Engine (CylinderKinematics)
         ?
  StateSnapshot (runtime)
         ?
  GeometryBridge (2D?3D + piston positions)
         ?
  MainWindow._update_3d_scene_from_snapshot()
         ?
  QML Properties & Functions
         ?
  3D Visualization (main.qml)
```

---

## ?? Python ? QML Communication

### 1. Geometry Parameters (Static)

**Function:** `updateGeometry(params)`

**Called from:** `MainWindow._on_geometry_changed()`

**Parameters:**
```javascript
{
    frameLength: float,        // mm - Frame longitudinal length
    frameHeight: float,        // mm - Horn height
    frameBeamSize: float,      // mm - Beam cross-section size
    leverLength: float,        // mm - Lever arm length
    cylinderBodyLength: float, // mm - Cylinder working length
    trackWidth: float,         // mm - Distance between left/right corners
    frameToPivot: float,       // mm - Distance from frame centerline to pivot
    rodPosition: float,        // 0..1 - Rod attachment position on lever
    boreHead: float,           // mm - Head bore diameter
    boreRod: float,            // mm - Rod bore diameter
    rodDiameter: float,        // mm - Piston rod diameter
    pistonThickness: float     // mm - Piston thickness
}
```

**Example (Python):**
```python
geometry_params = {
    'frameLength': 2500.0,
    'frameHeight': 650.0,
    'frameBeamSize': 120.0,
    'leverLength': 400.0,
    'cylinderBodyLength': 570.0,
    # ... other parameters
}

QMetaObject.invokeMethod(
    self._qml_root_object,
    "updateGeometry",
    Qt.ConnectionType.DirectConnection,
    Q_ARG("QVariant", geometry_params)
)
```

---

### 2. Piston Positions (Dynamic - Real-time Physics!)

**Function:** `updatePistonPositions(positions)`

**Called from:** `MainWindow._update_3d_scene_from_snapshot()`

**Parameters:**
```javascript
{
    fl: float,  // mm - Front Left piston position (from cylinder start)
    fr: float,  // mm - Front Right piston position
    rl: float,  // mm - Rear Left piston position
    rr: float   // mm - Rear Right piston position
}
```

**Calculation (Python - GeometryBridge):**
```python
# From CylinderState
stroke_mm = cylinder_state.stroke * 1000.0  # m to mm
max_stroke_mm = cylinder_body_length * 0.8  # 80% of cylinder
piston_ratio = 0.5 + (stroke_mm / (2 * max_stroke_mm))  # 0..1
piston_ratio = np.clip(piston_ratio, 0.1, 0.9)
piston_position_mm = piston_ratio * cylinder_body_length
```

**Example (Python):**
```python
piston_positions = {
    'fl': 125.5,  # mm
    'fr': 132.8,
    'rl': 118.3,
    'rr': 140.1
}

QMetaObject.invokeMethod(
    self._qml_root_object,
    "updatePistonPositions",
    Qt.ConnectionType.DirectConnection,
    Q_ARG("QVariant", piston_positions)
)
```

---

### 3. Animation Parameters

**Function:** `updateAnimation(angles)`

**Parameters:**
```javascript
{
    fl: float,  // degrees - Front Left lever angle
    fr: float,  // degrees - Front Right lever angle
    rl: float,  // degrees - Rear Left lever angle
    rr: float   // degrees - Rear Right lever angle
}
```

**Example (Python):**
```python
angles = {'fl': 5.2, 'fr': -3.1, 'rl': 2.8, 'rr': -1.5}

QMetaObject.invokeMethod(
    self._qml_root_object,
    "updateAnimation",
    Qt.ConnectionType.DirectConnection,
    Q_ARG("QVariant", angles)
)
```

---

## ?? QML ? Python Communication

### Signals (Future Implementation)

**Planned:**
- `cameraPositionChanged(x, y, z)` - Camera moved by user
- `cornerSelected(corner_id)` - User clicked on a corner
- `visualizationModeChanged(mode)` - User changed view mode

---

## ?? QML Properties (Read/Write from Python)

### Geometry Properties
```javascript
property real userFrameLength: 2000.0      // mm
property real userFrameHeight: 650.0       // mm
property real userBeamSize: 120.0          // mm
property real userLeverLength: 315.0       // mm
property real userCylinderLength: 250.0    // mm
property real userTrackWidth: 300.0        // mm
property real userFrameToPivot: 150.0      // mm
property real userRodPosition: 0.6         // 0..1
property real userBoreHead: 80.0           // mm
property real userBoreRod: 80.0            // mm
property real userRodDiameter: 35.0        // mm
property real userPistonThickness: 25.0    // mm
```

### Animation Properties
```javascript
property real userAmplitude: 8.0           // degrees
property real userFrequency: 1.0           // Hz
property real userPhaseGlobal: 0.0         // degrees
property real userPhaseFL: 0.0             // degrees
property real userPhaseFR: 0.0             // degrees
property real userPhaseRL: 0.0             // degrees
property real userPhaseRR: 0.0             // degrees
property bool isRunning: false             // Animation on/off
```

### Physics Properties (NEW!)
```javascript
property real userPistonPositionFL: 125.0  // mm - FROM PYTHON PHYSICS!
property real userPistonPositionFR: 125.0  // mm
property real userPistonPositionRL: 125.0  // mm
property real userPistonPositionRR: 125.0  // mm
```

### Direct Property Access (Python)
```python
# Set property
self._qml_root_object.setProperty("isRunning", True)

# Get property
is_running = self._qml_root_object.property("isRunning")
```

---

## ?? Data Flow Examples

### Example 1: Start Simulation
```python
# Python (MainWindow._on_sim_control)
def _on_sim_control(self, command: str):
    if command == "start":
        bus.start_simulation.emit()
        self.is_simulation_running = True

        # Update QML
        if self._qml_root_object:
            self._qml_root_object.setProperty("isRunning", True)
```

### Example 2: Update from Physics Snapshot
```python
# Python (MainWindow._update_3d_scene_from_snapshot)
def _update_3d_scene_from_snapshot(self, snapshot):
    # Extract data from physics engine
    piston_positions = {}
    for corner in ['fl', 'fr', 'rl', 'rr']:
        corner_data = snapshot.corners[corner]
        cylinder_state = corner_data.cylinder_state

        # Use GeometryBridge to calculate 3D position
        corner_3d = self.geometry_converter.get_corner_3d_coords(
            corner,
            corner_data.lever_angle,
            cylinder_state  # Physics data!
        )

        piston_positions[corner] = corner_3d['pistonPositionMm']

    # Send to QML
    QMetaObject.invokeMethod(
        self._qml_root_object,
        "updatePistonPositions",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", piston_positions)
    )
```

### Example 3: User Changes Geometry in UI
```python
# Python (GeometryPanel.geometry_changed signal)
geometry_params = {
    'frameLength': self.wheelbase_spin.value() * 1000,  # m to mm
    'leverLength': self.lever_length_spin.value() * 1000,
    # ... other parameters
}

# Send to QML
QMetaObject.invokeMethod(
    main_window._qml_root_object,
    "updateGeometry",
    Qt.ConnectionType.DirectConnection,
    Q_ARG("QVariant", geometry_params)
)
```

---

## ?? Visualization Details

### Coordinate System
- **X-axis:** Transverse (left/right) - Red
- **Y-axis:** Vertical (up/down) - Green
- **Z-axis:** Longitudinal (front/rear) - Blue
- **Origin:** Frame center, beam bottom

### Piston Position Convention
- **0 mm:** Cylinder start (near tail rod)
- **pistonPositionMm:** Absolute position from cylinder start
- **lCylinder:** Cylinder end (where rod exits)
- **Valid range:** 10% to 90% of cylinder length (safety limits)

### Example Calculation
```
Cylinder length: 250mm
Piston position: 125mm (center)
Ratio: 0.5

Stroke +50mm (extension):
  Position: 125 + 50 = 175mm
  Ratio: 0.7

Stroke -50mm (retraction):
  Position: 125 - 50 = 75mm
  Ratio: 0.3
```

---

## ? Performance Considerations

### Update Frequency
- **Geometry:** ~1 Hz (user changes)
- **Piston positions:** ~60 Hz (physics simulation)
- **Animation:** ~60 Hz (smooth visualization)

### Optimization
- Use `DirectConnection` for synchronous updates
- Batch multiple property updates in single function call
- Avoid property updates if value hasn't changed

---

## ?? Debugging

### Enable QML Console Logging
```python
os.environ["QT_LOGGING_RULES"] = "js.debug=true;qt.qml.debug=true"
```

### Check Function Calls
```javascript
// In QML function
function updatePistonPositions(positions) {
    console.log("?? Received:", JSON.stringify(positions))
    // ... update logic
}
```

### Verify from Python
```python
# Check if function exists
from PySide6.QtCore import QMetaObject
meta = self._qml_root_object.metaObject()
for i in range(meta.methodCount()):
    method = meta.method(i)
    name = method.name().data().decode('utf-8')
    if 'updatePiston' in name:
        print(f"Found method: {name}")
```

---

## ?? References

- **GeometryBridge:** `src/ui/geometry_bridge.py`
- **MainWindow:** `src/ui/main_window.py`
- **QML Scene:** `assets/qml/main.qml`
- **CylinderKinematics:** `src/mechanics/kinematics.py`

---

## ? Integration Checklist

- [x] QML receives geometry parameters from Python
- [x] QML receives piston positions from Python physics
- [x] QML receives animation parameters from Python
- [x] Python can start/stop animation
- [x] Python can update real-time physics data
- [x] GeometryBridge converts 2D kinematics to 3D
- [x] Piston positions calculated from CylinderState.stroke
- [ ] QML signals back to Python (future)
- [ ] User interaction events (future)

---

**Status:** ? **FULLY INTEGRATED**

Python physics engine ? QML 3D visualization working!
