# PneumoStabSim - Troubleshooting Guide

## ?? Common Issues and Solutions

This guide covers common problems you might encounter and their solutions.

---

## ?? Installation & Setup Issues

### **Issue 1: "No module named 'PySide6'"**

**Symptoms:**
```
ModuleNotFoundError: No module named 'PySide6'
```

**Cause:** PySide6 not installed

**Solution:**
```bash
pip install PySide6 PySide6-Addons
```

**Verify:**
```bash
python -c "import PySide6; print(PySide6.__version__)"
# Should print: 6.6.1 (or higher)
```

---

### **Issue 2: "Qt Quick 3D module not found"**

**Symptoms:**
```
qrc:/qt-project.org/imports/QtQuick3D/...
QQmlApplicationEngine failed to load component
```

**Cause:** PySide6-Addons not installed (Qt Quick 3D is in Addons!)

**Solution:**
```bash
pip install PySide6-Addons
```

**Verify:**
```bash
python -c "from PySide6.QtQuick3D import QQuick3DGeometry; print('OK')"
# Should print: OK
```

---

### **Issue 3: "ImportError: DLL load failed"**

**Symptoms:**
```
ImportError: DLL load failed while importing QtCore
```

**Cause:** Missing Visual C++ Redistributable (Windows)

**Solution:**
1. Download [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Install and restart

---

## ??? Visualization Issues

### **Issue 4: "3D scene is blank/black"**

**Symptoms:**
- Window opens but 3D view is black
- No error messages

**Diagnostic:**
```bash
# Check console for RHI backend
python app.py 2>&1 | findstr "rhi:"
```

**Expected:**
```
rhi: backend: D3D11
```

**If not D3D11:**

**Solution 1:** Force D3D11 backend
```python
# In app.py (BEFORE PySide6 import!)
os.environ["QSG_RHI_BACKEND"] = "d3d11"
```

**Solution 2:** Update graphics drivers
- NVIDIA: GeForce Experience
- AMD: Radeon Software
- Intel: Intel Graphics Command Center

**Solution 3:** Try OpenGL backend (fallback)
```python
os.environ["QSG_RHI_BACKEND"] = "opengl"
```

---

### **Issue 5: "QML errors: 'Cannot read property of undefined'"**

**Symptoms:**
```
qml: TypeError: Cannot read property 'x' of undefined
```

**Cause:** Accessing property before it's initialized

**Solution:**
```qml
// BAD: Direct access (might be undefined)
position: j_arm

// GOOD: Safe access with default
position: typeof j_arm !== 'undefined' ? j_arm : Qt.vector3d(0,0,0)

// BETTER: Initialize in declaration
property vector3d j_arm: Qt.vector3d(0, 0, 0)
```

---

### **Issue 6: "Models not visible in 3D scene"**

**Symptoms:**
- 3D scene loads but models invisible
- Camera controls work

**Diagnostic:**
```qml
// Add to Model
onVisibleChanged: console.log("Model visible:", visible)
onPositionChanged: console.log("Model position:", position)
```

**Common Causes:**

**1. Position outside camera view**
```qml
// Check if position is reasonable
Model {
    position: Qt.vector3d(0, 300, 1000)  // Should be near origin
}
```

**2. Scale too small/large**
```qml
// Scale should be visible (0.1 - 100)
Model {
    scale: Qt.vector3d(1, 1, 1)  // Start with 1:1:1
}
```

**3. Material not set**
```qml
// MUST have material!
Model {
    source: "#Cube"
    materials: PrincipledMaterial {
        baseColor: "#ff0000"  // Bright color for testing
    }
}
```

---

## ?? Animation Issues

### **Issue 7: "Animation not working"**

**Symptoms:**
- Start button clicked
- No movement in 3D scene

**Diagnostic Steps:**

**1. Check isRunning property:**
```python
# In Python
is_running = self._qml_root_object.property("isRunning")
print(f"isRunning: {is_running}")
# Should print: True
```

**2. Check timer running:**
```qml
// In QML
Timer {
    running: isRunning
    onRunningChanged: console.log("Timer running:", running)
}
```

**3. Check angles updating:**
```qml
onFl_angleChanged: console.log("FL angle:", fl_angle)
```

**Solution:**
```python
# Ensure isRunning is set in _on_sim_control
def _on_sim_control(self, command: str):
    if command == "start":
        self._qml_root_object.setProperty("isRunning", True)
        print("? Animation STARTED")
```

---

### **Issue 8: "Parameters don't change animation"**

**Symptoms:**
- Change amplitude slider
- Animation stays the same

**Diagnostic:**
```python
# Add logging in _on_animation_changed
def _on_animation_changed(self, params):
    print(f"?? Animation params received: {params}")

    amplitude = params.get('amplitude', 0.05)
    print(f"   Setting userAmplitude = {amplitude}")

    self._qml_root_object.setProperty("userAmplitude", amplitude)

    # Verify
    actual = self._qml_root_object.property("userAmplitude")
    print(f"   Actual value in QML: {actual}")
```

**Common Causes:**

**1. Signal not connected:**
```python
# In _wire_panel_signals()
self.modes_panel.animation_changed.connect(self._on_animation_changed)
print("? animation_changed signal connected")
```

**2. Property name mismatch:**
```python
# Python uses 'amplitude' (meters)
# QML uses 'userAmplitude' (degrees)
# Need conversion!
amplitude_deg = params['amplitude'] * 1000 / 10
```

---

## ?? Physics/Kinematics Issues

### **Issue 9: "Piston moves in wrong direction"**

**Symptoms:**
- Lever rotates up
- Piston moves down (or vice versa)

**Cause:** Sign error in calculation

**Check GeometryBridge:**
```python
# CORRECT formula
piston_position = (cylinder_length / 2.0) + delta_distance

# WRONG formula (bug!)
piston_position = (cylinder_length / 2.0) - delta_distance
```

**Solution:** See `docs/MODULES/GEOMETRY_BRIDGE.md` section "Piston Position Calculation"

---

### **Issue 10: "Rod length changes during animation"**

**Symptoms:**
- Rod stretches/compresses
- Length not constant

**Cause:** j_rod calculated OUTSIDE component, angle applied TWICE

**Solution:** Move j_rod calculation INSIDE SuspensionCorner
```qml
component SuspensionCorner: Node {
    property vector3d j_arm
    property vector3d j_tail
    property real leverAngle

    // CALCULATE j_rod here (not outside!)
    property real baseAngle: (j_arm.x < 0) ? 180 : 0
    property real totalAngle: baseAngle + leverAngle

    property vector3d j_rod: Qt.vector3d(
        j_arm.x + leverLength * Math.cos(totalAngle * Math.PI / 180),
        j_arm.y + leverLength * Math.sin(totalAngle * Math.PI / 180),
        j_arm.z
    )
}
```

---

## ?? Threading Issues

### **Issue 11: "QObject: Cannot create children in different thread"**

**Symptoms:**
```
QObject: Cannot create children for a parent that is in a different thread
```

**Cause:** Creating Qt objects in wrong thread

**Solution:** Use Qt.QueuedConnection
```python
# Cross-thread signal connections MUST use QueuedConnection
bus.state_ready.connect(
    self._on_state_update,
    Qt.ConnectionType.QueuedConnection  # CRITICAL!
)
```

---

### **Issue 12: "Application freezes"**

**Symptoms:**
- UI stops responding
- No error messages

**Cause:** Blocking operation in UI thread

**Diagnostic:**
```python
# Check thread ID
import threading
thread_id = threading.current_thread().ident
print(f"Current thread: {thread_id}")
print(f"Main thread: {QApplication.instance().thread().currentThreadId()}")
```

**Solution:** Move heavy computation to worker thread
```python
class PhysicsWorker(QThread):
    def run(self):
        # Heavy physics calculations here
        while self.running:
            self.compute_frame()
```

---

## ?? Performance Issues

### **Issue 13: "Low FPS / choppy animation"**

**Symptoms:**
- Animation stutters
- FPS < 30

**Diagnostic:**
```python
# Add FPS counter
import time

class FPSCounter:
    def __init__(self):
        self.frames = 0
        self.start_time = time.time()

    def tick(self):
        self.frames += 1
        elapsed = time.time() - self.start_time
        if elapsed > 1.0:
            fps = self.frames / elapsed
            print(f"FPS: {fps:.1f}")
            self.frames = 0
            self.start_time = time.time()

# In _update_render():
self.fps_counter.tick()
```

**Solutions:**

**1. Reduce update frequency:**
```python
# Update at 30 FPS instead of 60
self.render_timer.start(33)  # 33ms = ~30 FPS
```

**2. Optimize QML:**
```qml
// Use property bindings (efficient!)
position: Qt.vector3d(x, y, z)

// NOT JavaScript (slow!)
position: calculatePosition()
```

**3. Profile bottlenecks:**
```bash
python -m cProfile -o profile.stats app.py
# Analyze with snakeviz:
pip install snakeviz
snakeviz profile.stats
```

---

## ?? Debugging Tools

### **Enable Verbose Logging**

```python
# In app.py
logging.basicConfig(
    level=logging.DEBUG,  # Show ALL logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### **QML Debugging**

```bash
# Environment variables
export QML_IMPORT_TRACE=1      # Trace QML imports
export QT_LOGGING_RULES="qt.qml*=true"  # Enable QML logging
export QSG_INFO=1              # Show RHI backend info
```

### **Memory Profiling**

```python
import tracemalloc

tracemalloc.start()

# Run application
app.exec()

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("Top 10 memory consumers:")
for stat in top_stats[:10]:
    print(stat)
```

---

## ?? Reporting Bugs

### **Information to Include**

1. **Environment:**
   ```bash
   python --version
   pip list | grep -E "PySide6|numpy|scipy"
   ```

2. **Steps to reproduce:**
   ```
   1. Open app.py
   2. Click "Start" button
   3. Change amplitude to 0.15
   4. Observe: Piston moves in wrong direction
   ```

3. **Expected vs Actual:**
   ```
   Expected: Piston extends (moves up)
   Actual: Piston retracts (moves down)
   ```

4. **Logs:**
   ```
   Attach console output
   Attach logs/PneumoStabSim_YYYYMMDD_HHMMSS.log
   ```

5. **Screenshots/Video:**
   - Screenshot of 3D view
   - Recording of issue (use OBS Studio)

---

## ?? Getting Help

### **Resources**

1. **Documentation:**
   - `docs/PROJECT_OVERVIEW.md` - Start here
   - `docs/ARCHITECTURE.md` - System design
   - `docs/DEVELOPMENT_GUIDE.md` - Development tips

2. **Code Examples:**
   - `tests/` - Working test examples
   - `docs/MODULES/` - Module documentation

3. **Community:**
   - GitHub Issues: Report bugs
   - GitHub Discussions: Ask questions

### **Before Asking**

? Check this troubleshooting guide
? Search existing GitHub issues
? Read relevant module documentation
? Try minimal reproducible example

---

## ?? Known Issues (Workarounds)

### **Windows: Console shows "???" instead of emoji**

**Workaround:**
```python
# Already handled in app.py
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
```

### **Linux: Qt Quick 3D crashes**

**Workaround:** Use OpenGL backend
```python
os.environ["QSG_RHI_BACKEND"] = "opengl"
```

### **macOS: Window doesn't appear**

**Workaround:**
```python
# Force window to front
window.raise_()
window.activateWindow()
```

---

**Last Updated:** 2025-01-05
**Maintainer:** Development Team
**Status:** Living Document

**Found a new issue?** Please contribute to this guide!
