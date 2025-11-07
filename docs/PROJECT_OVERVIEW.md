# PneumoStabSim - Project Overview

## ?? Project Summary

**PneumoStabSim** - Pneumatic Stabilizer Simulator
- **Version:** 2.0.0 (Qt Quick 3D)
- **Language:** Python 3.11+
- **Framework:** PySide6 (Qt 6)
- **3D Rendering:** Qt Quick 3D (RHI/Direct3D 11)
- **Purpose:** Simulate pneumatic suspension system with 4-corner independent control

---

## ?? Project Structure

```
PneumoStabSim/
??? app.py                          # Main application entry point
??? src/                            # Source code
?   ??? common/                     # Common utilities
?   ?   ??? logging.py             # Logging setup
?   ?   ??? csv_export.py          # Data export
?   ?   ??? config.py              # Configuration
?   ??? core/                       # Core domain logic
?   ?   ??? geometry.py            # Basic geometry types
?   ??? mechanics/                  # Physics & kinematics
?   ?   ??? kinematics.py          # Cylinder kinematics
?   ?   ??? dynamics.py            # Body dynamics
?   ??? physics/                    # Physics simulation
?   ?   ??? odes.py                # ODE definitions
?   ?   ??? integrator.py          # Numerical integration
?   ??? pneumo/                     # Pneumatic system
?   ?   ??? enums.py               # Enumerations
?   ?   ??? network.py             # Gas network
?   ?   ??? system.py              # Pneumatic system
?   ?   ??? sim_time.py            # Time stepping
?   ??? road/                       # Road excitation
?   ?   ??? engine.py              # Road input generator
?   ??? runtime/                    # Simulation runtime
?   ?   ??? state.py               # State management
?   ?   ??? sync.py                # Synchronization
?   ?   ??? sim_loop.py            # Simulation loop
?   ??? ui/                         # User interface
?       ??? main_window.py         # Main window
?       ??? geometry_bridge.py     # 2D?3D converter
?       ??? custom_geometry.py     # Custom 3D shapes
?       ??? panels/                # UI panels
?       ?   ??? panel_geometry.py  # Geometry controls
?       ?   ??? panel_pneumo.py    # Pneumatic controls
?       ?   ??? panel_modes.py     # Simulation modes
?       ?   ??? panel_road.py      # Road profiles
?       ??? widgets/               # Custom widgets
?           ??? range_slider.py    # Range slider
?           ??? knob.py            # Rotary knob
??? assets/                         # Assets
?   ??? qml/                       # QML files
?       ??? main.qml               # Main 3D scene
?       ??? components/            # QML components
??? docs/                           # Documentation
?   ??? PROJECT_OVERVIEW.md        # This file
?   ??? ARCHITECTURE.md            # System architecture
?   ??? PYTHON_QML_API.md          # Python?QML API
?   ??? MODULES/                   # Module documentation
?   ??? REPORTS/                   # Status reports
??? tests/                          # Test files
??? logs/                           # Log files

```

---

## ??? Architecture Overview

### **High-Level Architecture**

```
┌──────────────────────────────┐
│        Application UI        │
│ Panels, widgets (PySide6)    │
└──────────────┬───────────────┘
               │ Python↔QML bridge
               ▼
┌──────────────────────────────┐
│   Qt Quick 3D Scene Graph    │
│ QML components + frame graph │
└──────────────┬───────────────┘
               │ RHI selection (configure_qt_environment)
               ▼
┌──────────────┼───────────────┐
│ OpenGL (desktop) │ Vulkan ICD │
│  QSG_RHI_BACKEND │ VK_ICD_*   │
└──────────────┬──┴───────┬────┘
               │          │
       ┌───────▼───┐  ┌───▼────────┐
       │ GPU driver │  │ Software GL│
       │  (native)  │  │ Mesa/ANGLE │
       └───────┬────┘  └────┬──────┘
               │            │
     ┌─────────▼────────┐ ┌─▼────────────┐
     │ Framebuffer / D3D│ │ Offscreen FBO │
     │ Windows/Linux UI │ │ CI/headless   │
     └──────────────────┘ └──────────────┘
```

---

## ?? Key Technologies

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| GUI Framework | PySide6 | 6.x |
| 3D Rendering | Qt Quick 3D | - |
| Graphics API | Direct3D 11 (RHI) | - |
| Physics | SciPy | 1.11+ |
| Math | NumPy | 1.24+ |
| Logging | Python logging | Standard |

---

## ?? Current Status (v2.0.0)

### ? **Completed Features**

| Feature | Status | Module |
|---------|--------|--------|
| 3D Visualization | ? Working | `assets/qml/main.qml` |
| Geometry Calculations | ? Working | `src/ui/geometry_bridge.py` |
| Python?QML Integration | ? Working | `src/ui/main_window.py` |
| Animation Controls | ? Working | `src/ui/panels/panel_modes.py` |
| Piston Kinematics | ? Working | `src/ui/geometry_bridge.py` |
| Rod Length Constraint | ? Working | `assets/qml/main.qml` |
| Parameter UI Controls | ? Working | All panels |
| Logging System | ? Working | `src/common/logging.py` |

### ?? **In Progress**

| Feature | Status | Next Steps |
|---------|--------|-----------|
| Full Physics Integration | ?? Partial | Connect CylinderKinematics |
| Pneumatic Simulation | ?? Partial | Integrate GasNetwork |
| Road Excitation | ?? Partial | Connect RoadInput |
| Data Export | ?? Partial | Add CSV export |

### ?? **Planned Features**

- [ ] Real-time physics simulation (ODE integration)
- [ ] Pneumatic gas network simulation
- [ ] Road profile loading from CSV
- [ ] Advanced visualization modes
- [ ] Performance profiling
- [ ] Unit tests

---

## ?? Quick Start

### **1. Installation**

```bash
pip install -r requirements.txt
```

### **2. Run Application**

```bash
python app.py
```

### **3. Test Kinematics**

```bash
python test_correct_kinematics.py
```

---

## ?? Documentation Index

### **Core Documentation**
- [Architecture Guide](ARCHITECTURE.md) - System design & patterns
- [Python?QML API](PYTHON_QML_API.md) - Integration reference
- [Module Reference](MODULES/) - Per-module documentation
- [Status Reports](REPORTS/) - Progress tracking

### **Module Documentation**
- [GeometryBridge](MODULES/GEOMETRY_BRIDGE.md) -2D?3D conversion
- [SimulationManager](MODULES/SIMULATION_MANAGER.md) - Physics loop
- [MainWindow](MODULES/MAIN_WINDOW.md) - UI controller
- [QML Scene](MODULES/QML_SCENE.md) -3D visualization

### **Development Guides**
- [Development Setup](DEV_SETUP.md) - Development environment
- [Testing Guide](TESTING.md) - Test procedures
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

## ?? Delivery Governance

- **Weekly readiness sync:** Tuesdays11:00 (UTC+3). Track compatibility, signal synchronization, configuration, CI, and code-style readiness using the0?3 scoring matrix described in the [Development Guide](DEVELOPMENT_GUIDE.md#-coordination--rituals).
- **Kanban board:** GitHub Projects workspace `Stability Delivery` with epics per readiness stream. Tasks must live in the active sprint column and link to their acceptance checklists.
- **Decision history:** All architectural and infrastructure agreements are logged in [DECISIONS_LOG.md](DECISIONS_LOG.md) and reviewed during the weekly sync.

---

## ?? Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## ?? License

See [LICENSE](../LICENSE) for details.

---

**Last Updated:**2025-02-15
**Project Status:** Active Development
**Version:**2.0.0 (Qt Quick3D Release)
