# A-4.1: ������ �������� ��������� �������������� �����������

## ?? ���������� �������

### ? ��������� ����������:

**1. �������������� ������ ����������:**
- `src/mechanics/kinematics.py` - ������ ���������� LeverKinematics � CylinderKinematics
- `tests/test_kinematics.py` - ����������� ����� ����������
- ���������� ����������� � Point2, LeverState, CylinderState

**2. GeometryPanel ����������:**
- `src/ui/panels/panel_geometry.py` - ������ � ������� ����������
- ��������������� ��������� �������� (cyl_diam_m, rod_diam_m, stroke_m)
- �������� �������� ������������

### ? ����������� ����������:

**1. GeometryState �����������:**
- ��� ������ `src/ui/geo_state.py`
- ��� centralized state management
- ��� �������������� ������������

**2. ������������ �������������� �����������:**
- � GeometryPanel ���� ������ ������� ��������
- ��� ������� ������� stroke_max ����� ����������
- ����������� ��������� �������������� �����

**3. ��� ���������� ����� UI � �����������:**
- GeometryPanel �� ���������� LeverKinematics
- ��� ��������������� ������� stroke_max
- ����������� ����������� ������ ��� ���������

---

## ?? ������� ���������� stroke_max

### � GeometryPanel._validate_geometry():
```python
stroke = self.parameters['stroke_m']
cylinder_length = self.parameters['cylinder_length']
piston_thickness = self.parameters['piston_thickness_m']
dead_gap = self.parameters['dead_gap_m']

min_cylinder_length = stroke + piston_thickness + 2 * dead_gap
```

**��������**: ��� �������������� ����������� ��������, �� �������������� ����������� ��������!

### ��� ������ ����:
```python
# �������������� ������ ������������� ����:
lever_kinematics = LeverKinematics(...)
max_lever_angle = calculate_max_lever_angle(wheelbase, lever_geometry)
stroke_max_kinematic = calculate_stroke_from_angle(lever_kinematics, max_lever_angle)

# �������� �����������:
stroke <= min(stroke_max_kinematic, stroke_max_cylinder)
```

---

## ??? ���� A-4.2: �������� GeometryState � �����������

### ��� 1: ������� GeometryState
```python
# src/ui/geo_state.py
@dataclass
class GeometryState:
    # �������� ���������
    wheelbase: float = 3.200
    lever_length: float = 0.800
    frame_to_pivot: float = 0.600
    # ... ������ ���������

    # �������������� �����������
    def calculate_stroke_max_kinematic(self) -> float:
        """������ �������������� ������ stroke_max"""
        # ���������� LeverKinematics ��� �������

    def validate_kinematic_constraints(self) -> List[str]:
        """�������� ���� �������������� �����������"""
```

### ��� 2: ���������� � GeometryPanel
```python
# � GeometryPanel.__init__():
self.geo_state = GeometryState()

# � _on_parameter_changed():
corrections = self.geo_state.apply_kinematic_corrections(param_name, value)
```

### ��� 3: �������������� �������
```python
def calculate_max_lever_angle(wheelbase: float, lever_geometry: float) -> float:
    """������������ ���� �������� ������ ��� �����������"""

def calculate_stroke_from_lever_angle(kinematics: LeverKinematics, angle: float) -> float:
    """������ ���� �������� �� ���� ������"""
```

---

## ?? ���������� A-4:

**������� ���������:**
1. ? �������� GeometryState � ��������������� ��������
2. ? ���������� LeverKinematics � UI
3. ? ������ ������ stroke_max ����� ����������

**������� ���������:**
4. ������� ����������� �������
5. �������� ����������� ���������
6. �������������� ��������� ����������

**������ ���������:**
7. ������������ �������������� �����������
8. ����������� ���������� ��������

---

## ?? A-4.2: �������� ����������

**��������� ���**: �������� GeometryState � �������� ��������������� ���������

**����� ��� ��������/���������:**
1. `src/ui/geo_state.py` - ����� ������ (�������)
2. `src/ui/panels/panel_geometry.py` - ���������� (��������)
3. `test_a4_kinematics.py` - ����� (�������)

**����� � ���������� A-4.2** ?
