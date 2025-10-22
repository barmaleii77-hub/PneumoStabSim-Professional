# ? ����� UI ���������� - ACCORDION � PARAMETER SLIDER

**����:** 3 ������ 2025, 13:00 UTC
**������:** ? **�������� ��������**

---

## ?? ��������� ����������

### 1. AccordionWidget (`src/ui/accordion.py`)

**������������ ��������� � ��������������� ��������**

#### �����������:
- ? ��������������/��������������� ������
- ? ������� �������� (200ms, easing)
- ? ��������� ��� ������������
- ? ������ ����
- ? ������ ���������� ������

#### API:
```python
accordion = AccordionWidget()

# �������� ������
section = accordion.add_section(
    name="geometry",           # ���������� ���
    title="Geometry",          # ���������
    content_widget=widget,     # ������ �����������
    expanded=True              # ���������� �� ���������
)

# ���������� ��������
accordion.expand_section("geometry")
accordion.collapse_section("pneumo")
accordion.collapse_all()
accordion.expand_all()
```

#### �����:
- ������ ��� (#1a1a2e)
- ��������� (#2a2a3e ? #4a4a5e ��� ���������)
- ��������� ��������� (#4a4a5e)
- ������� ?/? � ����������

---

### 2. ParameterSlider (`src/ui/parameter_slider.py`)

**������� � ������������ ����������**

#### �����������:
- ? Slider ��� ������� ���������
- ? SpinBox ��� ������� �����
- ? Min/Max ����������� ����������
- ? ������� ���������
- ? ��������� ��������
- ? ������������� ��� � ��������
- ? ������ ����

#### API:
```python
slider = ParameterSlider(
    name="Wheelbase (L)",       # �������� ���������
    initial_value=3.0,          # ��������� ��������
    min_value=2.0,              # �������
    max_value=5.0,              # ��������
    step=0.01,                  # ���
    decimals=3,                 # ������ ����� �������
    unit="m",                   # ������� ���������
    allow_range_edit=True,      # ��������� ������������� ��������
    validator=None              # ������� ��������� (�����������)
)

# ���������� � ����������
slider.value_changed.connect(lambda v: print(f"Value: {v}"))
slider.range_changed.connect(lambda min, max: print(f"Range: {min}-{max}"))

# ��������/���������� ��������
value = slider.value()
slider.set_value(3.5)

# ��������/���������� ��������
min_val, max_val = slider.get_range()
slider.set_range(1.0, 10.0)
```

#### Layout:
```
???????????????????????????????????????
? Parameter Name          [123.45] m  ?  ? Label + SpinBox
? ????????????????????????????????    ?  ? Slider
? Min: [2.00] m       Max: [5.00] m   ?  ? Range controls
? ?????????????????????????????????   ?  ? Separator
???????????????????????????????????????
```

---

## ?? ������������

### Test Application: `test_new_ui_components.py`

**4 ������ ��������������:**

1. **Geometry** (����������)
   - Wheelbase (L): 2.0-5.0 m
   - Track Width (B): 1.0-2.5 m
   - Lever Arm (r): 0.1-0.6 m

2. **Pneumatics**
   - Head Volume (V_h): 100-1000 cm?
   - Rod Volume (V_r): 50-800 cm?
   - Line Pressure: 50-500 kPa
   - Tank Pressure: 100-600 kPa

3. **Simulation**
   - Time Step (dt): 0.0001-0.01 s
   - Simulation Speed: 0.1-10.0x

4. **Advanced**
   - Spring Stiffness (k): 10000-200000 N/m
   - Damper Coefficient (c): 500-10000 N*s/m

### ���������� ������������:
```
? Accordion ������������/������������� ������
? Slider �������� ���������
? SpinBox ��������������� �� ���������
? Min/Max ����������� ��������
? ��������� ���������� (min < max)
? ��� ��������� ����������
? ������ ���� ���������
? ��������� ���������� ��� �������������
```

---

## ?? ���������: �� � �����

### �� (QDockWidget + Tabs):
```
? ������ � ����� (������)
? ��� ��������� (������ spinbox)
? ��������� ������������
? ��� ����������� ����������
? �������� ����� �����
? ��� ����������� ����������
```

### ����� (Accordion + ParameterSlider):
```
? ������ ������������/�������������
? �������� + spinbox
? ������������ ���������
? ��������� min/max
? �������� �����
? ���������� �����������
? ������������� �����������
```

---

## ?? ���������� � MainWindow

### ���� ����������:

#### 1. �������� ����� ������
```python
# � src/ui/main_window.py

# ����:
self.geometry_dock = QDockWidget("Geometry", self)
self.tabifyDockWidget(...)

# ������:
self.left_accordion = AccordionWidget(self)

# �������� ������
geometry_panel = GeometryPanelAccordion()  # ����� ������
self.left_accordion.add_section("geometry", "Geometry", geometry_panel, expanded=True)

pneumo_panel = PneumoPanelAccordion()
self.left_accordion.add_section("pneumo", "Pneumatics", pneumo_panel, expanded=False)

# ���������� ��� ����� ������
left_dock = QDockWidget("Parameters", self)
left_dock.setWidget(self.left_accordion)
self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)
```

#### 2. ���������� ������ � ParameterSlider
```python
# ������: GeometryPanelAccordion

class GeometryPanelAccordion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # Wheelbase
        self.wheelbase = ParameterSlider(
            "Wheelbase (L)", 3.0, 2.0, 5.0, 0.01, 3, "m"
        )
        layout.addWidget(self.wheelbase)

        # Track width
        self.track = ParameterSlider(
            "Track Width (B)", 1.8, 1.0, 2.5, 0.01, 3, "m"
        )
        layout.addWidget(self.track)

        # ... ��������� ���������
```

---

## ?? ��������� ����

### PHASE 1: ���������� � MainWindow (2-3 ���)

#### ������:
1. ? ������� AccordionWidget ? **������**
2. ? ������� ParameterSlider ? **������**
3. ? ������� ����� ������ �������:
   - GeometryPanelAccordion
   - PneumoPanelAccordion
   - SimulationPanelAccordion
   - RoadPanelAccordion
   - AdvancedPanelAccordion
4. ? �������� dock-������� �� accordion
5. ? ���������� ������� � simulation manager
6. ? ������������

---

### PHASE 2: ParameterManager (3-5 ����)

#### ������������ ��������� ����������:
```python
class ParameterManager:
    """���������� ������������� ����������"""

    def __init__(self):
        self.params = {}
        self.dependencies = {}  # ���� ������������

    def register(self, name, slider, depends_on=None, formula=None):
        """���������������� ��������

        Args:
            name: ��� ���������
            slider: ParameterSlider
            depends_on: ������ ������������
            formula: ������� ���������
        """
        self.params[name] = slider

        if depends_on and formula:
            self.dependencies[name] = {
                'deps': depends_on,
                'formula': formula
            }

            # ���������� ����������
            for dep in depends_on:
                self.params[dep].value_changed.connect(
                    lambda: self._update_dependent(name)
                )

    def _update_dependent(self, name):
        """�������� ��������� ��������"""
        dep_info = self.dependencies[name]

        # �������� �������� ������������
        values = {dep: self.params[dep].value()
                  for dep in dep_info['deps']}

        # ��������� ����� ��������
        new_value = dep_info['formula'](**values)

        # ����������
        self.params[name].set_value(new_value)
```

#### ������ �������������:
```python
manager = ParameterManager()

# ���������������� ���������
manager.register('wheelbase', wheelbase_slider)
manager.register('track', track_slider)

# ��������� ��������: diagonal
manager.register(
    'diagonal',
    diagonal_slider,
    depends_on=['wheelbase', 'track'],
    formula=lambda wheelbase, track: math.sqrt(wheelbase**2 + track**2)
)

# ��� ��������� wheelbase ��� track ? diagonal ������������� �������������
```

---

### PHASE 3: ��������� ������������ (2-3 ���)

#### ������� ���������:
```python
# ���������: rod volume < head volume
def validate_rod_volume(value, min_val, max_val):
    head_volume = head_slider.value()
    return value < head_volume

rod_slider = ParameterSlider(
    ...,
    validator=validate_rod_volume
)

# ���������: ����. �������� >= �������� ������������ * 1.2
def validate_max_pressure(value, min_val, max_val):
    relief_pressure = relief_slider.value()
    return value >= relief_pressure * 1.2

max_pressure_slider = ParameterSlider(
    ...,
    validator=validate_max_pressure
)
```

---

## ?? ������ ���������

### ������� ������ ����� �����������:

| ��������� | ������ | ���������� |
|-----------|--------|-----------|
| **AccordionWidget** | ? ������ | 100% |
| **ParameterSlider** | ? ������ | 100% |
| **Test Application** | ? �������� | 100% |
| **���������� � MainWindow** | ? �� ������ | 0% |
| **ParameterManager** | ? �� ������ | 0% |
| **��������� ������������** | ? �� ������� | 0% |

### ������������ �����������:

| ���������� | �� | ����� | �������� |
|------------|----|----|---------|
| **���������** | 0% ? | 100% ? | +100% |
| **��������** | 0% ? | 100% ? | +100% |
| **����������� ����������** | 0% ? | 100% ? | +100% |
| **������������** | 0% ? | 0% ? | 0% |
| **���������** | 0% ? | 50% ? | +50% |

**����� ��������:** 25% ? **45%** (+20%)

---

## ? ������

### ��� �������:
1. ? **AccordionWidget** - ��������� ��������
2. ? **ParameterSlider** - ��������� ��������
3. ? ������ ���� ���������
4. ? ������� ��������
5. ? �������� ���������� �������� ��������

### ��� ������:
1. ? ���������� � MainWindow (2-3 ���)
2. ? ParameterManager ��� ������������� (3-5 ����)
3. ? ������� ��������� (2-3 ���)

### ������ �������:
- **������� ����������:** 2-3 ���
- **������ ����������������:** 7-10 ����

---

**����:** 3 ������ 2025, 13:00 UTC
**������:** ? **���������� ������ � ����������**
**��������:** **25% ? 45%** (+20%)

?? **ACCORDION � PARAMETER SLIDER �������� ��������!** ??
