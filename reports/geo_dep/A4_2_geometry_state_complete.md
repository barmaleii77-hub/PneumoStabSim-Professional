# A-4.2: �������������� ��������� � ��������������� ������������� - ���������

## ? ����������� ������ A-4.2

### 1. ������ ������ GeometryState
**����**: `src/ui/geo_state.py`

**�������� �����������:**
- ? ���������������� ���������� ����� ��������������� �����������
- ? �������������� ��������� �������������� �����������
- ? ���������� � LeverKinematics � CylinderKinematics
- ? ������ stroke_max ����� �������� ���������� (�� ������ ��������� ��������)

### 2. �������������� �������
```python
def calculate_stroke_max_kinematic(self) -> float:
    """������ ������ ������������� ���� ����� ���������� ��������"""
    # ���������� LeverKinematics ��� ������� ����� ��������
    # ���������� CylinderKinematics ��� ������� ���� ������
    # ���������� ��������� ���������� �����������
```

**���������**: ������ stroke_max �������������� �� ������ ��� �������������� ����������� ��������, � ��� �������� �������������� ����������� ���� ��������.

### 3. ����������� ���������
```python
def validate_all_constraints(self) -> bool:
    # 1. �������������� ����������� (wheelbase vs lever)
    # 2. �������������� ����������� (stroke vs length)  
    # 3. �������������� ����������� (rod vs cylinder ratio)
    # 4. ? �����: �������������� ����������� (stroke vs kinematics)
```

### 4. ������� ������� ��������
- `create_default_geometry()` - ����������� ��������
- `create_light_commercial_geometry()` - ����� ������������
- `create_heavy_truck_geometry()` - ������ �������� (����� ���������)

---

## ?? ����������� ������

### ���������� � �����������:
```python
# � calculate_stroke_max_kinematic():
lever_kin = LeverKinematics(
    arm_length=self.lever_length,
    pivot_position=Point2(0.0, 0.0),
    pivot_offset_from_frame=self.frame_to_pivot,
    rod_attach_fraction=self.rod_position
)

# ������������ ��������� �� ������� �����
max_angle = self._calculate_max_lever_angle()  # �� wheelbase
state_pos = lever_kin.solve_from_angle(max_angle)
state_neg = lever_kin.solve_from_angle(-max_angle)

# ������ ���� �������� � ������� ��������
cyl_kin = CylinderKinematics(...)
stroke_range = abs(cyl_state_pos.stroke - cyl_state_neg.stroke)
```

### Fallback �����:
- ���� �������������� ������ ���������� ? ���������� �������������� ������
- ������������� ������������� ����� ������ ����������� � ���������� ����������

---

## ?? ������������ A-4.2

### �� A-4 (� GeometryPanel):
```python
# ������� �������������� �����������
min_cylinder_length = stroke + piston_thickness + 2 * dead_gap
```

**��������**: ��� ����������� ��������, �� ��������!

### ����� A-4.2 (� GeometryState):
```python  
# �������� �������������� �����������
stroke_max_kinematic = calculate_stroke_max_kinematic()  # ��������� wheelbase, lever_length, geometry
stroke_max_geometric = cylinder_length - piston - 2*gaps  # ������������ ����������� ��������

# �������� ����������� - ������� �� ����:
stroke_max = min(stroke_max_kinematic, stroke_max_geometric)
```

**���������**: Stroke ������ �������������� ��������� ������������� ��������, � �� ������ ��������� ��������!

---

## ?? ���������� � A-4.3

### ? ������:
- GeometryState � ��������������� ���������
- �������������� ��������� �����������
- ���������� � ������������� ��������������� ��������
- Fallback �� ���������� �������

### ?? ��������� ��� A-4.3:
**���������� GeometryState � GeometryPanel**

������:
1. �������� ������� �������� � GeometryPanel �� GeometryState
2. �������� �������������� ������������ ���������� � UI
3. ���������� �������������� ������� ������������
4. ������������� � ������������� preset'���

---

## ?? ������������

### ����� ������������:
- ? GeometryState �������� ��� ������
- ? �������������� ������ ������������� ���������  
- ? ��������� �������� ��� ���� ����� �����������
- ? Preset'� ������� ���������� ������������

### ������ A-4.2: **���������** ?

**��������� ��������**: A-4.3 - ���������� � GeometryPanel