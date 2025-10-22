# PneumoStabSim v2.0.0 - Quick Reference

## ?? Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Run tests
python test_correct_kinematics.py
```

---

## ?? Project Structure

```
PneumoStabSim/
??? app.py                 # ? START HERE
??? src/
?   ??? ui/
?   ?   ??? main_window.py        # Main controller
?   ?   ??? geometry_bridge.py    # Kinematics
?   ??? runtime/
?   ?   ??? sim_loop.py           # Physics thread
?   ??? ...
??? assets/qml/
?   ??? main.qml                  # 3D scene
??? docs/                          # Full documentation
?   ??? PROJECT_OVERVIEW.md
?   ??? ARCHITECTURE.md
?   ??? MODULES/
??? tests/
```

---

## ?? User Interface

### **Controls**

**3D View:**
- **LMB + Drag**: Rotate camera
- **RMB + Drag**: Pan view
- **Mouse Wheel**: Zoom
- **R**: Reset view
- **Double-Click**: Auto-fit

**Simulation:**
- **Start**: Begin animation
- **Stop**: Stop animation
- **Pause**: Pause/resume
- **Reset**: Return to initial state

### **Parameters**

**Geometry Panel:**
- Frame dimensions (wheelbase, height)
- Lever length
- Cylinder length

**Modes Panel:**
- **Amplitude**: 0-0.2m (lever swing)
- **Frequency**: 0.1-10 Hz (oscillation speed)
- **Phase**: 0-360° (timing offset)
- **Per-Wheel Phase**: Individual corner control

---

## ?? Key Features

? **Real-time 3D visualization** (Qt Quick 3D + D3D11)
? **Correct mechanical kinematics** (GeometryBridge)
? **User-controllable animation** (amplitude, frequency, phase)
? **4-corner independent suspension** (FL, FR, RL, RR)
? **Transparent cylinders** (see pistons inside!)
? **Constant rod length** (realistic constraint)

---

## ?? Documentation

| Document | Description |
|----------|-------------|
| [Project Overview](docs/PROJECT_OVERVIEW.md) | High-level summary |
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [Python?QML API](docs/PYTHON_QML_API.md) | Integration guide |
| [GeometryBridge](docs/MODULES/GEOMETRY_BRIDGE.md) | Kinematics module |
| [MainWindow](docs/MODULES/MAIN_WINDOW.md) | UI controller |
| [Status Report](docs/REPORTS/STATUS_2025_01_05.md) | Current status |

---

## ?? Troubleshooting

### **3D scene not visible?**
- Check console for "rhi: backend: D3D11"
- Ensure PySide6-Addons installed
- Try: `pip install --upgrade PySide6 PySide6-Addons`

### **Animation not working?**
- Click "Start" button
- Check "isRunning" in console output
- Verify ModesPanel parameters not zero

### **Piston stuck?**
- This was a bug, fixed in v2.0.0
- Pull latest code: `git pull origin master`

---

## ?? Testing

```bash
# Test kinematics
python test_correct_kinematics.py

# Manual control
python test_piston_movement.py

# Geometry calculations
python test_geometry_bridge.py
```

---

## ?? Current Status

**Version:** 2.0.0 (Qt Quick 3D Release)
**Status:** ? Core Features Complete
**Next:** Physics integration

**See:** [Status Report](docs/REPORTS/STATUS_2025_01_05.md) for details

---

## ?? Contributing

1. Read [Architecture](docs/ARCHITECTURE.md)
2. Check [Module Docs](docs/MODULES/)
3. Write tests
4. Submit PR

---

## ?? License

See [LICENSE](LICENSE)

---

**Questions?** Check the [full documentation](docs/) first!
