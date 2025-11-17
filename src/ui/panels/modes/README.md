# ModesPanel - Refactored Module

**Version:** v5.0.0
**Status:** ✅ **COMPLETE**
**Phase:** 4 of 4

---

## 📋 Overview

Модульная панель управления режимами симуляции с делегированием функциональности в специализированные вкладки.

**Original size:** ~580 lines
**Refactored coordinator:** ~150 lines (**-74%**)
**Total modules:** 8

---

## 🏗️ Architecture

```
src/ui/panels/modes/
├── panel_modes_refactored.py    150 lines (Coordinator)
├── control_tab.py               120 lines (Play/Pause/Stop/Reset)
├── simulation_tab.py            180 lines (Kinematics/Dynamics/Thermo + Presets)
├── physics_tab.py                90 lines (Springs/Dampers/Pneumatics toggles)
├── road_excitation_tab.py       220 lines (Amplitude/Frequency/Phases)
├── state_manager.py             150 lines (State + validation)
├── defaults.py                  100 lines (Constants + presets)
├── __init__.py                   50 lines (API + fallback)
└── README.md                          (This file)
```

**Total:** ~1060 lines (включая виджеты)
**Code reuse:** StandardSlider переиспользуется в road_excitation_tab

---

## 🎯 Features

### 1. **Control Tab** 🎮
- Play/Pause/Stop/Reset buttons
- Visual status indicator
- Keyboard shortcuts support (Space, R)
- Button state management

### 2. **Simulation Tab** ⚙️
- Quick presets selector (5 presets)
- Simulation type (Kinematics/Dynamics)
- Thermodynamic mode (Isothermal/Adiabatic)
- Auto-switch to "Custom" on manual change

### 3. **Physics Tab** 🔧
- Enable/disable physical components:
  - Springs (упругость)
  - Dampers (демпфирование)
  - Pneumatics (пневматика)
- Component info tooltips

### 4. **Road Excitation Tab** 🛣️
- Global parameters:
  - Amplitude (0-0.2 м)
  - Frequency (0.1-10 Гц)
  - Global phase (0-360°)
- Per-wheel phase offsets (FL, FR, RL, RR)

---

## 🔌 Public API

### ModesPanel

```python
from src.ui.panels.modes import ModesPanel

panel = ModesPanel(parent)

# Signals
panel.simulation_control.connect(...)      # str: "start", "stop", "pause", "reset"
panel.mode_changed.connect(...)            # (mode_type: str, new_mode: str)
panel.parameter_changed.connect(...)       # (param_name: str, value: float)
panel.physics_options_changed.connect(...) # dict
panel.animation_changed.connect(...)       # dict

# Methods
params = panel.get_parameters()            # dict
options = panel.get_physics_options()      # dict
panel.set_simulation_running(True/False)
errors = panel.validate_state()            # List[str]
```

### State Manager

```python
from src.ui.panels.modes import ModesStateManager

manager = ModesStateManager()

# Update state
manager.update_parameter('amplitude', 0.08)
manager.update_physics_option('include_springs', False)
manager.apply_preset(2)  # Full Dynamics

# Get state
params = manager.get_parameters()
options = manager.get_physics_options()
animation = manager.get_animation_parameters()

# Validation
errors = manager.validate_state()
warnings = manager.check_dependencies('sim_type', 'DYNAMICS')
```

---

## 📊 Mode Presets

| Index | Name | Sim Type | Thermo | Springs | Dampers | Pneumatics |
|-------|------|----------|--------|---------|---------|------------|
| 0 | Стандартный | Kinematics | Isothermal | ✅ | ✅ | ✅ |
| 1 | Только кинематика | Kinematics | Isothermal | ❌ | ❌ | ❌ |
| 2 | Полная динамика | Dynamics | Adiabatic | ✅ | ✅ | ✅ |
| 3 | Тест пневматики | Dynamics | Isothermal | ❌ | ❌ | ✅ |
| 4 | Пользовательский | (custom) | (custom) | (custom) | (custom) | (custom) |

---

## 🔧 Parameter Ranges

### Road Excitation

| Parameter | Min | Max | Default | Step | Unit |
|-----------|-----|-----|---------|------|------|
| amplitude | 0.0 | 0.2 | 0.05 | 0.001 | м |
| frequency | 0.1 | 10.0 | 1.0 | 0.1 | Гц |
| phase | 0.0 | 360.0 | 0.0 | 15.0 | ° |
| wheel_phase | 0.0 | 360.0 | 0.0 | 15.0 | ° |

---

## 🎬 Animation Parameters

ModesPanel экспортирует параметры анимации для передачи в QML:

```python
animation_params = {
    'amplitude': 0.05,     # м
    'frequency': 1.0,      # Гц
    'phase': 0.0,          # ° (global)
    'lf_phase': 0.0,       # ° (Left Front)
    'rf_phase': 0.0,       # ° (Right Front)
    'lr_phase': 0.0,       # ° (Left Rear)
    'rr_phase': 0.0        # ° (Right Rear)
}
```

---

## ✅ Validation

StateManager выполняет валидацию:

### Checked constraints:
- Simulation type in `['KINEMATICS', 'DYNAMICS']`
- Thermo mode in `['ISOTHERMAL', 'ADIABATIC']`
- Amplitude: 0.0 ≤ A ≤ 0.2 м
- Frequency: 0.1 ≤ f ≤ 10.0 Гц
- All phases: 0° ≤ φ ≤ 360°

### Dependency warnings:
- Kinematics + Pneumatics enabled → warning
- Dynamics + all components disabled → warning
- High amplitude + high frequency → resonance warning

---

## 🧪 Testing

### Unit Tests

```bash
python tests/test_modes_panel_refactored.py
```

**Tests:**
- State manager initialization
- Parameter validation
- Preset application
- Signal emission
- Tab coordination

### Integration Test

```bash
python tests/test_modes_panel_integration.py
```

**Tests:**
- Full panel initialization
- Tab switching
- Parameter changes propagation
- Simulation control workflow

---

## 🔄 Backward Compatibility

**Fallback mechanism:**
- If refactored version fails to import → falls back to original `panel_modes.py`
- API fully compatible with original version
- All signals preserved
- All methods preserved

**Check version:**
```python
from src.ui.panels.modes import get_version_info, is_refactored

print(get_version_info())
print(f"Using refactored: {is_refactored()}")
```

---

## 📝 Usage Example

```python
from PySide6.QtWidgets import QApplication, QMainWindow
from src.ui.panels.modes import ModesPanel

app = QApplication([])
window = QMainWindow()

# Create panel
modes_panel = ModesPanel()

# Connect signals
modes_panel.simulation_control.connect(
    lambda cmd: print(f"Simulation: {cmd}")
)
modes_panel.animation_changed.connect(
    lambda params: print(f"Animation: {params}")
)

# Get state
print("Parameters:", modes_panel.get_parameters())
print("Physics:", modes_panel.get_physics_options())

# Validate
errors = modes_panel.validate_state()
if errors:
    print("Errors:", errors)

window.setCentralWidget(modes_panel)
window.show()
app.exec()
```

---

## 🐛 Known Issues

**None** - All features working as expected.

---

## 🚀 Future Enhancements

1. **Recording tab** - Animation recording/playback
2. **Road profiles** - Load CSV road profiles
3. **Visualization** - Live phase diagram
4. **Presets import/export** - Save/load custom presets

---

## 📚 References

- **Original:** `src/ui/panels/panel_modes.py`
- **State Manager:** `state_manager.py`
- **Defaults:** `defaults.py`
- **Documentation:** `REFACTORING_PHASE4_MODESPANEL_COMPLETE.md`

---

**Author:** GitHub Copilot
**Date:** 2025-01-XX
**Version:** v5.0.0
**Status:** ✅ Production Ready
