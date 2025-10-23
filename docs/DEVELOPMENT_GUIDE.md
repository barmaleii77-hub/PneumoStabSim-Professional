# PneumoStabSim - Development Guide

## ??? Development Environment Setup

### **Prerequisites**

| Software | Version | Purpose |
|----------|---------|---------|
| Python |3.13.x | Runtime |
| Git |2.x | Version control |
| Visual Studio Code | Latest | IDE (recommended) |
| Qt Creator |6.x | QML editing (optional) |

---

## ?? Installation Steps

### **1. Clone Repository**

```sh
git clone https://github.com/barmaleii77-hub/PneumoStabSim-Professional.git
cd PneumoStabSim-Professional
```

### **2. Create Virtual Environment**

```sh
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### **3. Install Dependencies**

```sh
pip install --upgrade pip
pip install -r requirements.txt
```

**Core Dependencies:**

```
PySide6==6.10.0 # Qt6.10 bindings
PySide6-Addons==6.10.0 # Qt Quick3D tooling
numpy==1.26.4 # Math operations
scipy==1.11.4 # Physics integration
```

### **4. Verify Installation**

```sh
# Check Python version
python --version # Should be3.13.x

# Check PySide6
python -c "from PySide6 import QtCore; print(QtCore.qVersion())"
# Should print:6.10.x

# Check Qt Quick3D
python -c "from PySide6.QtQuick3D import QQuick3DGeometry; print('OK')"
# Should print: OK (Qt6.10 runtime)
```

---

## 🎯 IDE Integration (Visual Studio Code & Visual Studio2022)

### VS Code quick start

1. **Open workspace** – launch `PneumoStabSim.code-workspace`. It pins the interpreter to `${workspaceFolder}/.venv` (Python3.13) and exports Qt6.10 paths for both Windows and Linux terminals.
2. **Verify interpreter** – the status bar should show `.venv (3.13)`. If not, run the command palette (`Ctrl+Shift+P`) → *Python: Select Interpreter* → choose the `.venv` entry.
3. **Qt tooling** – install recommended extensions when prompted (PySide6/Qt language server, Python tooling). `qt.qmlls` automatically resolves through the virtual environment once `PySide6`6.10 is installed.
4. **Launch profiles** – use the updated `.vscode/launch.json` entries:
 - *App: PneumoStabSim (Qt6.10)* – regular GUI start with Qt variables.
 - *Tests: Smoke suite (pytest -k smoke)* – executes the reduced regression suite.
 - *Diagnostics: QML asset scan* – runs `qml_diagnostic.py` for quick asset sanity checks.

### Visual Studio2022 (Python workload)

1. Open `PneumoStabSim.slnx`. The solution references both `.pyproj` files and the shared launch profiles in `Properties/launchSettings.json`.
2. Visual Studio automatically binds to `.venv\Scripts\python.exe` (Python3.13). If the environment is missing, create it via the *Python Environments* panel using the3.13 base interpreter.
3. Use the **Debug Targets** dropdown to select:
 - *PneumoStabSim (App)* – launches `app.py` with Qt6.10 paths.
 - *Smoke tests (pytest -k smoke)* – console smoke validations.
 - *QML diagnostics* – runs the project level QML check.
4. The `.pyproj` files export `QML*_PATH` and `QT_PLUGIN_PATH` so PySide66.10 assets resolve without manual tweaks.

---

## ??? Project Structure Deep Dive

### **Source Code Organization**

```
src/
??? common/ # Shared utilities (NO business logic!)
? ??? logging.py # Centralized logging setup
? ??? csv_export.py # Data export utilities
? ??? config.py # Configuration management
?
??? core/ # Domain primitives (pure Python, no Qt!)
? ??? geometry.py # FrameConfig, basic types
?
??? mechanics/ # Physics calculations (pure functions)
? ??? kinematics.py # CylinderKinematics class
? ??? dynamics.py # RigidBody3DOF (future)
?
??? physics/ # ODE integration (SciPy-based)
? ??? odes.py # Right-hand side functions (f_rhs)
? ??? integrator.py # solve_ivp wrapper
?
??? pneumo/ # Pneumatic gas system
? ??? enums.py # Wheel, Line, ThermoMode enums
? ??? network.py # GasNetwork class
? ??? system.py # PneumaticSystem class
? ??? sim_time.py # Time stepping utilities
?
??? road/ # Road excitation generation
? ??? engine.py # RoadInput class
?
??? runtime/ # Simulation runtime (threading!)
? ??? state.py # StateSnapshot, StateBus
? ??? sync.py # LatestOnlyQueue, thread safety
? ??? sim_loop.py # PhysicsWorker, SimulationManager
?
??? ui/ # User interface (Qt-dependent)
    ??? main_window.py         # MainWindow (QMainWindow)
    ??? geometry_bridge.py     # 2D?3D coordinate converter
    ??? custom_geometry.py     # QQuick3DGeometry subclasses
    ??? panels/               # UI control panels
    ?   ??? __init__.py
    ?   ??? panel_geometry.py  # GeometryPanel
    ?   ??? panel_pneumo.py    # PneumoPanel
    ?   ??? panel_modes.py     # ModesPanel
    ?   ??? panel_road.py      # RoadPanel
    ??? widgets/              # Custom Qt widgets
        ??? range_slider.py    # RangeSlider
        ??? knob.py           # RotaryKnob
```

---

## ?? Code Style Guide

### **Python Style**

**Follow PEP 8 with these additions:**

```python
# 1. Type hints everywhere (Python 3.11+)
def calculate_piston_position(
    lever_angle: float,
    cylinder_length: float
) -> float:
    """Calculate piston position from lever angle

    Args:
        lever_angle: Lever rotation in degrees
        cylinder_length: Cylinder body length in mm

    Returns:
        Piston position from cylinder start (mm)
    """
    # Implementation...
    return position

# 2. Explicit imports (no wildcards!)
from PySide6.QtCore import Qt, QTimer, Slot
# NOT: from PySide6.QtCore import *

# 3. Docstrings for public methods
class GeometryBridge:
    """Convert 2D kinematics to 3D coordinates

    This class bridges the gap between 2D mechanical
    calculations and 3D visualization coordinates.
    """

    def get_corner_3d_coords(self, corner: str) -> dict:
        """Get 3D coordinates for suspension corner

        Args:
            corner: Corner identifier ('fl', 'fr', 'rl', 'rr')

        Returns:
            Dictionary with 3D coordinate arrays
        """
        pass

# 4. Constants in UPPER_CASE
DEFAULT_CYLINDER_LENGTH = 0.25  # meters
MAX_PISTON_RATIO = 0.9

# 5. Private methods start with _
def _internal_calculation(self):
    """Internal helper method"""
    pass
```

### **QML Style**

```qml
// 1. Components start with Capital letter
component SuspensionCorner: Node {
    // Properties BEFORE functions
    property real leverAngle: 0.0
    property vector3d position: Qt.vector3d(0, 0, 0)

    // Functions use camelCase
    function updatePosition(newPos) {
        position = newPos
    }

    // Models INSIDE component
    Model {
        source: "#Cube"
        materials: PrincipledMaterial {
            baseColor: "#ff0000"
        }
    }
}

// 2. Comments for complex calculations
// Calculate piston position from lever angle
// Formula: pos = center + delta
// Where delta = (tail_to_rod - baseline_distance)
property real pistonPos: calculatePistonPosition()

// 3. Use Qt.vector3d() for vectors (not array!)
property vector3d correct: Qt.vector3d(1.0, 2.0, 3.0)
// NOT: property var wrong: [1.0, 2.0, 3.0]
```

## Python ↔ QML Binding Review Checklist

- [ ] **Контексты:** новые `context.setContextProperty` добавлены до `setSource`, отражены в `docs/PYTHON_QML_API.md` и сопровождаются проверкой в QML. 【F:src/ui/main_window/ui_setup.py†L94-L144】【F:docs/PYTHON_QML_API.md†L11-L52】
- [ ] **Карта обновлений:** категории и методы синхронизированы между `QMLBridge.QML_UPDATE_METHODS` и QML (`apply*Updates`). 【F:src/ui/main_window/qml_bridge.py†L60-L105】【F:assets/qml/main.qml†L90-L166】
- [ ] **Batched payload:** `applyBatchedUpdates` умеет обрабатывать новые ключи, а `_prepare_for_qml` корректно сериализует Python-структуры. 【F:assets/qml/main.qml†L18-L166】【F:src/ui/main_window/qml_bridge.py†L279-L321】
- [ ] **ACK и логирование:** `SignalsRouter` подключает QML-сигналы, `QMLBridge.handle_qml_ack` и `EventLogger` обновлены, если менялась структура ответов. 【F:src/ui/main_window/signals_router.py†L215-L233】【F:src/ui/main_window/qml_bridge.py†L360-L434】
- [ ] **Симуляция:** изменения в `StateSnapshot` отражены в `_snapshot_to_payload` и QML-обработчиках (`apply3DUpdates`/`applySimulationUpdates`). 【F:src/ui/main_window/qml_bridge.py†L195-L279】【F:assets/qml/main.qml†L90-L166】
- [ ] **Документация:** разделы `docs/PYTHON_QML_API.md` и `docs/python_qml_bridge.md` обновлены описанием новых точек привязки. 【F:docs/PYTHON_QML_API.md†L1-L121】【F:docs/python_qml_bridge.md†L1-L84】

---

## ?? Testing Strategy

### **Test Pyramid**

```
        /\
       /  \      E2E Tests (few)
      /????\     - Full app integration
     /??????\
    /????????\   Integration Tests (some)
   /??????????\  - Module interactions
  /????????????\
 /??????????????\ Unit Tests (many)
 /????????????????\ - Individual functions
```

### **Unit Tests**

**Test PURE functions first:**

```python
# test_geometry_bridge.py
import pytest
from src.ui.geometry_bridge import GeometryBridge

def test_piston_position_calculation():
    """Test piston position from lever angle"""
    bridge = GeometryBridge()

    # Test center position (0� angle)
    coords = bridge.get_corner_3d_coords('fl', lever_angle=0.0)
    assert abs(coords['pistonPositionMm'] - 125.0) < 1.0

    # Test extended (positive angle)
    coords = bridge.get_corner_3d_coords('fl', lever_angle=5.0)
    assert coords['pistonPositionMm'] > 125.0

    # Test retracted (negative angle)
    coords = bridge.get_corner_3d_coords('fl', lever_angle=-5.0)
    assert coords['pistonPositionMm'] < 125.0
```

### **Integration Tests**

**Test module interactions:**

```python
# test_qml_integration.py
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def test_qml_property_update(qtbot):
    """Test Python?QML property updates"""
    window = MainWindow()
    qtbot.addWidget(window)

    # Set amplitude in Python
    window._qml_root_object.setProperty("userAmplitude", 15.0)

    # Read back
    value = window._qml_root_object.property("userAmplitude")
    assert value == 15.0
```

### **Manual Tests**

**Create test scripts for visual verification:**

```python
# test_piston_movement.py
"""Manual test: Control pistons with sliders"""

class PistonTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create sliders
        self.fl_slider = QSlider(Qt.Horizontal)
        self.fl_slider.setRange(25, 225)  # 10%-90%
        self.fl_slider.valueChanged.connect(self.update_piston)

    def update_piston(self, value):
        # Update QML
        positions = {'fl': float(value)}
        QMetaObject.invokeMethod(
            self.qml_root,
            "updatePistonPositions",
            Qt.DirectConnection,
            Q_ARG("QVariant", positions)
        )
```

---

## ?? Debugging Techniques

### **Python Debugging**

```python
# 1. Use logging (not print!)
import logging
logger = logging.getLogger(__name__)

def complex_function(param):
    logger.debug(f"Input: {param}")
    result = calculate(param)
    logger.info(f"Result: {result}")
    return result

# 2. Breakpoints in VS Code
# Just click left of line number!

# 3. Interactive debugging
import pdb; pdb.set_trace()  # Python 3.6+
breakpoint()  # Python 3.7+
```

### **QML Debugging**

```qml
// 1. console.log() is your friend
onClicked: {
    console.log("Button clicked!")
    console.log("Value:", someProperty)
}

// 2. Check property changes
onFlAngleChanged: {
    console.log("FL angle changed to:", fl_angle)
}

// 3. Validate calculations
property real calculated: {
    var result = someComplexCalc()
    console.log("Calculated:", result)
    return result
}
```

### **Thread Debugging**

```python
# Always log thread ID for threading issues
import threading

def worker_function():
    thread_id = threading.current_thread().ident
    logger.info(f"Worker running in thread {thread_id}")
```

---

## ?? Performance Profiling

### **Python Profiling**

```python
# Using cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
run_simulation(10.0)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### **QML Profiling**

```bash
# Enable QML profiler
export QML_PROFILER=1
python app.py

# In Qt Creator:
# Analyze ? QML Profiler ? Load QML Trace
```

---

## ?? Common Development Tasks

### **Adding a New Panel**

1. **Create panel file:**
```python
# src/ui/panels/panel_mynew.py
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

class MyNewPanel(QWidget):
    # Define signals
    parameter_changed = Signal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
```

2. **Register in __init__.py:**
```python
# src/ui/panels/__init__.py
from .panel_mynew import MyNewPanel
__all__ = [..., 'MyNewPanel']
```

3. **Add to MainWindow:**
```python
# src/ui/main_window.py
from .panels import MyNewPanel

def _setup_docks(self):
    # Create dock
    self.mynew_dock = QDockWidget("My New Panel", self)
    self.mynew_panel = MyNewPanel(self)
    self.mynew_dock.setWidget(self.mynew_panel)
    self.addDockWidget(Qt.LeftDockWidgetArea, self.mynew_dock)
```

### **Adding QML Property**

1. **In main.qml:**
```qml
Item {
    id: root

    // Add property
    property real userNewParameter: 10.0
}
```

2. **In Python:**
```python
# Read
value = self._qml_root_object.property("userNewParameter")

# Write
self._qml_root_object.setProperty("userNewParameter", 15.0)
```

---

## ?? Troubleshooting Common Issues

### **Issue: "QML module not found"**

**Symptoms:**
```
qrc:/qt-project.org/imports/QtQuick3D/...
module "QtQuick3D" is not installed
```

**Solution:**
```bash
pip install --upgrade PySide6-Addons
```

### **Issue: "Property binding loop"**

**Symptoms:**
```
QML TypeError: Cannot read property of undefined
Binding loop detected for property "someProperty"
```

**Cause:** Circular dependency in property bindings

**Solution:**
```qml
// BAD: Circular binding
property real a: b + 1
property real b: a - 1

// GOOD: Use function
property real a: 10
property real b: calculateB()

function calculateB() {
    return a - 1
}
```

### **Issue: "Thread safety violation"**

**Symptoms:**
```
QObject: Cannot create children for a parent in different thread
```

**Solution:**
```python
# Use Qt.QueuedConnection for cross-thread signals
bus.state_ready.connect(
    self._on_state_update,
    Qt.QueuedConnection  # NOT DirectConnection!
)
```

---

## ?? Git Workflow

### **Branching Strategy**

```
master (production)
  ?? develop (integration)
       ?? feature/new-panel
       ?? feature/physics-integration
       ?? bugfix/piston-direction
       ?? docs/api-reference
```

### **Commit Message Format**

```
TYPE: Short description (50 chars max)

PROBLEM:
- What was broken/missing

SOLUTION:
- How you fixed it

CHANGES:
- File changes
- API changes
```

**Types:**
- `FIX:` - Bug fix
- `ADD:` - New feature
- `REFACTOR:` - Code refactoring
- `DOCS:` - Documentation
- `TEST:` - Tests
- `PERF:` - Performance improvement

**Example:**
```
FIX: Piston direction inverted in GeometryBridge

PROBLEM:
- Piston moved opposite to lever rotation
- Used "center - delta" instead of "center + delta"

SOLUTION:
- Changed formula to "center + delta"
- Added unit test to prevent regression

CHANGES:
- src/ui/geometry_bridge.py: Fixed sign
- tests/test_geometry_bridge.py: Added test case
```

---

## ?? Security Considerations

### **No secrets in code!**

```python
# BAD: Hardcoded credentials
API_KEY = "sk_live_123456789"

# GOOD: Environment variables
import os
API_KEY = os.getenv("PNEUMO_API_KEY")
```

### **Input validation**

```python
def set_amplitude(self, value: float):
    # Validate range
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"Amplitude must be 0-1, got {value}")

    self._amplitude = value
```

---

## ?? Recommended Reading

### **Python**
- [PEP 8 Style Guide](https://pep8.org/)
- [Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [Threading Best Practices](https://docs.python.org/3/library/threading.html)

### **Qt/QML**
- [Qt Quick 3D Documentation](https://doc.qt.io/qt-6/qtquick3d-index.html)
- [Qt Quick Best Practices](https://doc.qt.io/qt-6/qtquick-bestpractices.html)
- [PySide6 Examples](https://doc.qt.io/qtforpython-6/)

### **Physics**
- [SciPy ODE Tutorial](https://docs.scipy.org/doc/scipy/tutorial/integrate.html)
- [NumPy Basics](https://numpy.org/doc/stable/user/basics.html)

---

**Last Updated:** 2025-01-05
**Maintainer:** Development Team
**Status:** Living Document (update as needed!)
