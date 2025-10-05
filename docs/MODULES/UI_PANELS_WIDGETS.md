# UI Panels & Widgets Documentation

## ?? Overview

**Modules:**
- `src/ui/panels/panel_geometry.py` - Geometry controls
- `src/ui/panels/panel_pneumo.py` - Pneumatic controls
- `src/ui/panels/panel_modes.py` - Simulation modes
- `src/ui/panels/panel_road.py` - Road profiles
- `src/ui/widgets/range_slider.py` - Custom slider
- `src/ui/widgets/knob.py` - Rotary knob

**Purpose:** User interface controls for simulation parameters

**Status:** ? Fully Functional

---

## ?? Complete Module List

### **UI Panels**
1. ? **GeometryPanel** - Frame, lever, cylinder geometry
2. ? **PneumoPanel** - Pressures, valves, thermodynamics
3. ? **ModesPanel** - Simulation type, animation, road excitation
4. ? **RoadPanel** - CSV loading, presets, wheel selection

### **UI Widgets**
1. ? **RangeSlider** - Custom slider with value display
2. ? **RotaryKnob** - Rotary control widget

---

## ?? GeometryPanel

### **Class Diagram**

```
???????????????????????????????????????????
?         GeometryPanel                   ?
?         (QWidget)                       ?
???????????????????????????????????????????
? Signals:                                ?
? - geometry_changed(dict)                ?
? - parameter_changed(str, float)         ?
???????????????????????????????????????????
? UI Elements:                            ?
? - wheelbase_spin: QDoubleSpinBox        ?
? - track_width_spin: QDoubleSpinBox      ?
? - frame_height_spin: QDoubleSpinBox     ?
? - lever_length_spin: QDoubleSpinBox     ?
? - cylinder_length_spin: QDoubleSpinBox  ?
? - rod_position_slider: RangeSlider      ?
? - bore_head_spin: QDoubleSpinBox        ?
? - bore_rod_spin: QDoubleSpinBox         ?
? - rod_diameter_spin: QDoubleSpinBox     ?
? - piston_thickness_spin: QDoubleSpinBox ?
???????????????????????????????????????????
? + get_parameters() ? dict              ?
? + set_parameters(dict)                 ?
???????????????????????????????????????????
```

### **Parameters**

```python
DEFAULT_GEOMETRY = {
    'wheelbase': 2.5,            # m
    'track_width': 0.3,          # m
    'frame_height': 0.65,        # m
    'lever_length': 0.4,         # m
    'cylinder_body_length': 0.25,# m
    'rod_position': 0.6,         # 0-1 (fraction on lever)
    'bore_head': 0.08,           # m
    'bore_rod': 0.08,            # m
    'rod_diameter': 0.035,       # m
    'piston_thickness': 0.025,   # m
}
```

### **Example Usage**

```python
from src.ui.panels import GeometryPanel

panel = GeometryPanel(parent_window)

# Connect signal
panel.geometry_changed.connect(lambda params: print(f"Geometry: {params}"))

# Get current values
geometry = panel.get_parameters()
print(f"Wheelbase: {geometry['wheelbase']} m")

# Set new values
panel.set_parameters({'wheelbase': 3.0, 'track_width': 0.35})
```

---

## ?? PneumoPanel

### **Class Diagram**

```
???????????????????????????????????????????
?         PneumoPanel                     ?
?         (QWidget)                       ?
???????????????????????????????????????????
? Signals:                                ?
? - mode_changed(str, str)                ?
? - parameter_changed(str, float)         ?
? - valve_position_changed(str, float)    ?
???????????????????????????????????????????
? UI Elements:                            ?
? - isothermal_radio: QRadioButton        ?
? - adiabatic_radio: QRadioButton         ?
? - receiver_pressure: QDoubleSpinBox     ?
? - supply_pressure: QDoubleSpinBox       ?
? - master_isolation_check: QCheckBox     ?
? - valve_sliders: Dict[str, RangeSlider] ?
???????????????????????????????????????????
? + get_parameters() ? dict              ?
? + set_valve_position(line, pos)        ?
???????????????????????????????????????????
```

### **Parameters**

```python
DEFAULT_PNEUMATIC = {
    'thermo_mode': 'ISOTHERMAL',
    'receiver_pressure': 600000,  # Pa (6 bar)
    'supply_pressure': 700000,    # Pa (7 bar)
    'master_isolation_open': True,
    'valve_positions': {
        'supply_fl_head': 0.0,
        'supply_fl_rod': 0.0,
        'exhaust_fl_head': 0.0,
        'exhaust_fl_rod': 0.0,
        # ... (all 16 valves)
    }
}
```

---

## ?? ModesPanel

### **Class Diagram**

```
???????????????????????????????????????????
?         ModesPanel                      ?
?         (QWidget)                       ?
???????????????????????????????????????????
? Signals:                                ?
? - simulation_control(str)               ?
? - mode_changed(str, str)                ?
? - parameter_changed(str, float)         ?
? - animation_changed(dict)               ?
???????????????????????????????????????????
? UI Elements:                            ?
? - start_button: QPushButton             ?
? - stop_button: QPushButton              ?
? - pause_button: QPushButton             ?
? - reset_button: QPushButton             ?
? - kinematics_radio: QRadioButton        ?
? - dynamics_radio: QRadioButton          ?
? - amplitude_slider: RangeSlider         ?
? - frequency_slider: RangeSlider         ?
? - phase_slider: RangeSlider             ?
? - lf/rf/lr/rr_phase_sliders             ?
???????????????????????????????????????????
? + get_parameters() ? dict              ?
? + set_simulation_running(bool)          ?
???????????????????????????????????????????
```

### **Animation Parameters**

```python
DEFAULT_ANIMATION = {
    'amplitude': 0.05,    # m
    'frequency': 1.0,     # Hz
    'phase': 0.0,         # degrees (global)
    'lf_phase': 0.0,      # degrees (per-wheel)
    'rf_phase': 0.0,
    'lr_phase': 0.0,
    'rr_phase': 0.0,
}
```

### **Example: Animation Control**

```python
from src.ui.panels import ModesPanel

panel = ModesPanel(parent_window)

# Connect animation signal
panel.animation_changed.connect(
    lambda params: print(f"Animation: A={params['amplitude']}m F={params['frequency']}Hz")
)

# Connect simulation control
panel.simulation_control.connect(
    lambda cmd: print(f"Simulation command: {cmd}")
)

# Change amplitude
panel.amplitude_slider.set_value(0.1)  # 0.1m = 100mm
```

---

## ?? RoadPanel

### **Class Diagram**

```
???????????????????????????????????????????
?         RoadPanel                       ?
?         (QWidget)                       ?
???????????????????????????????????????????
? Signals:                                ?
? - load_csv_profile(str)                 ?
? - apply_preset(str)                     ?
? - apply_to_wheels(str, List[str])       ?
? - clear_profiles()                      ?
???????????????????????????????????????????
? UI Elements:                            ?
? - preset_combo: QComboBox               ?
? - browse_button: QPushButton            ?
? - wheel_checkboxes: Dict[str, QCheckBox]?
? - apply_button: QPushButton             ?
? - clear_button: QPushButton             ?
???????????????????????????????????????????
? + get_active_wheels() ? List[str]      ?
? + load_csv_file(path: str)             ?
???????????????????????????????????????????
```

### **Road Presets**

```python
ROAD_PRESETS = {
    'smooth': {
        'amplitude': 0.01,  # 10mm
        'frequency': 0.5,   # Hz
        'type': 'sine'
    },
    'rough': {
        'amplitude': 0.05,  # 50mm
        'frequency': 2.0,
        'type': 'sine'
    },
    'pothole': {
        'amplitude': 0.1,   # 100mm
        'frequency': 0.2,
        'type': 'step'
    },
    'belgian_paving': {
        'file': 'assets/road/belgian.csv'
    }
}
```

---

## ?? RangeSlider Widget

### **Features**

- Horizontal slider with integrated value display
- Unit labels (mm, m, degrees, Hz, etc.)
- Decimal precision control
- Min/max range
- Step size
- Real-time value updates

### **API**

```python
class RangeSlider(QWidget):
    """Custom slider with value display"""
    
    # Signal emitted when value changes
    valueEdited = Signal(float)
    
    def __init__(
        self,
        minimum: float = 0.0,
        maximum: float = 100.0,
        value: float = 50.0,
        step: float = 1.0,
        decimals: int = 1,
        units: str = "",
        title: str = ""
    ):
        """Initialize range slider"""
        ...
    
    def value(self) -> float:
        """Get current value"""
        return self._value
    
    def set_value(self, value: float):
        """Set value programmatically"""
        self._value = np.clip(value, self.minimum, self.maximum)
        self._update_display()
        self.valueEdited.emit(self._value)
```

### **Example**

```python
from src.ui.widgets import RangeSlider

# Create slider
amplitude_slider = RangeSlider(
    minimum=0.0,
    maximum=0.2,
    value=0.05,
    step=0.005,
    decimals=3,
    units="m",
    title="Amplitude"
)

# Connect signal
amplitude_slider.valueEdited.connect(
    lambda val: print(f"Amplitude changed to {val:.3f}m")
)

# Add to layout
layout.addWidget(amplitude_slider)
```

---

## ?? RotaryKnob Widget

### **Features**

- Rotary dial control
- Mouse drag to rotate
- Visual feedback
- Angle snapping
- Value range mapping

### **API**

```python
class RotaryKnob(QWidget):
    """Rotary knob control"""
    
    valueChanged = Signal(float)
    
    def __init__(
        self,
        minimum: float = 0.0,
        maximum: float = 100.0,
        value: float = 50.0,
        snap_angle: float = 15.0  # degrees
    ):
        """Initialize rotary knob"""
        ...
    
    def value(self) -> float:
        """Get current value"""
        return self._value
    
    def paintEvent(self, event):
        """Custom painting (dial + indicator)"""
        ...
```

---

## ?? Signal Flow

### **Geometry Change**

```
User changes wheelbase spinbox
      ?
GeometryPanel.wheelbase_spin.valueChanged
      ?
GeometryPanel._on_parameter_changed()
      ?
Collect all geometry parameters
      ?
GeometryPanel.geometry_changed.emit(params)
      ?
MainWindow._on_geometry_changed(params)
      ?
Update QML: updateGeometry(params)
      ?
3D scene rebuilds with new geometry
```

### **Animation Control**

```
User changes amplitude slider
      ?
ModesPanel.amplitude_slider.valueEdited
      ?
ModesPanel._on_parameter_changed('amplitude', value)
      ?
Collect all animation parameters
      ?
ModesPanel.animation_changed.emit(params)
      ?
MainWindow._on_animation_changed(params)
      ?
Set QML properties (userAmplitude, userFrequency, etc.)
      ?
Animation updates in real-time
```

---

## ?? Configuration

### **Panel Sizes**

```python
PANEL_SIZES = {
    'geometry_min_width': 200,
    'geometry_max_width': 350,
    'pneumo_min_width': 200,
    'pneumo_max_width': 350,
    'modes_min_width': 300,
    'modes_max_width': 500,
    'road_min_height': 150,
    'road_max_height': 250,
}
```

### **Widget Styles**

```python
SLIDER_STYLE = """
QSlider::groove:horizontal {
    border: 1px solid #999999;
    height: 8px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #B1B1B1, stop:1 #c4c4c4);
}
QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
        stop:0 #b4b4b4, stop:1 #8f8f8f);
    border: 1px solid #5c5c5c;
    width: 18px;
    margin: -2px 0;
    border-radius: 3px;
}
"""
```

---

## ?? Test Coverage

**Test Files:**
- `tests/test_panels.py`
- `tests/test_widgets.py`

**Coverage:** ~70%

---

## ?? References

- **Qt Widgets:** [Qt Widgets Documentation](https://doc.qt.io/qt-6/qtwidgets-index.html)
- **Signals/Slots:** [Qt Signals & Slots](https://doc.qt.io/qt-6/signalsandslots.html)
- **Custom Widgets:** [Qt Custom Widgets](https://doc.qt.io/qt-6/designer-creating-custom-widgets.html)

---

**Last Updated:** 2025-01-05  
**Module Version:** 2.0.0  
**Status:** Production Ready ?
