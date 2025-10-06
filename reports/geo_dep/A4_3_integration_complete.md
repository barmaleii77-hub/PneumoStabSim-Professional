# A-4.3: ���������� GEOMETRYSTATE � GEOMETRYPANEL - ���������

## ? ����������� ������ A-4.3

### 1. ������ ���������� GeometryState � GeometryPanel

**��������� � `src/ui/panels/panel_geometry.py`:**
- ? ������ � ������������� GeometryState
- ? Fallback ����� ��� ������������� (���� GeometryState ����������)
- ? �������������� ����������� ����������� �������������� �������

```python
# A-4.3: Import GeometryState for kinematic constraints
try:
    from ..geo_state import GeometryState, create_default_geometry, create_light_commercial_geometry
    GEOMETRY_STATE_AVAILABLE = True
except ImportError:
    GEOMETRY_STATE_AVAILABLE = False
    print("Warning: GeometryState not available, using legacy validation")
```

### 2. �������������� ��������� � �������� �������

**����� �����������:**
- ? �������������� �������� �������������� ����������� ��� ��������� ����������
- ? ����� �������������� �������� � UI (stroke_max, max_lever_angle)
- ? �������������� ��������� ����������� ��������
- ? ��������� ��������� �� ������� � ������������

```python
def _apply_ui_change_with_geometry_state(self, param_name: str, value: float):
    """A-4.3: Apply UI change using GeometryState for validation and normalization"""
    
    # Update GeometryState parameter
    setattr(self.geo_state, param_name, value)
    
    # Validate constraints
    is_valid = self.geo_state.validate_all_constraints()
    errors, warnings = self.geo_state.get_validation_results()
    
    if errors:
        # Show kinematic constraint violations with auto-correction option
```

### 3. ����������� UI � �������������� �����������

**����� �������� ����������:**
- ? ��������� ������ ���������� "(A-4.3: Kinematic Constraints)"
- ? ������������ ����������� �������������� ��������
- ? Stroke slider ���������� ������������ �������������� ���
- ? Checkbox ��� ���������/���������� �������������� �����������
- ? ����������� ������ ��������� � �������������� ���������

```python
# A-4.3: Kinematic info display
self.kinematic_info_label = QLabel("Kinematic limits: calculating...")

# Enhanced stroke slider with kinematic limits
stroke_title = "Stroke"
if GEOMETRY_STATE_AVAILABLE:
    stroke_max_km = computed['stroke_max_kinematic']
    stroke_title += f" (max: {stroke_max_km*1000:.0f}mm kinematic)"
```

### 4. ����� ������� � �������������� ����������

**���������� �������:**
- ? Standard Truck ? `create_default_geometry()`
- ? Light Commercial ? `create_light_commercial_geometry()`  
- ? Heavy Truck ? `create_heavy_truck_geometry()` (�������� � geo_state.py)
- ? Custom ? ��������� ������� ���������

```python
if index == 0:  # Standard truck
    self.geo_state = create_default_geometry()
elif index == 1:  # Light commercial
    self.geo_state = create_light_commercial_geometry()
elif index == 2:  # Heavy truck
    self.geo_state = create_heavy_truck_geometry()
```

### 5. ������� ������������� (Legacy + A-4.3)

**������� fallback:**
- ? ���� GeometryState �������� ? ���������� �������������� �����������
- ? ���� GeometryState ���������� ? ���������� legacy ���������
- ? ������� ������� ����� �������� ��� ������ ����������������

---

## ?? ����� ����������� A-4.3

### �� A-4 (Legacy):
```python
# ������� �������� ��������� ��������
min_cylinder_length = stroke + piston_thickness + 2 * dead_gap
if cylinder_length < min_cylinder_length:
    errors.append("Cylinder too short")
```

### ����� A-4.3 (Kinematic):
```python
# ����������� �������������� ���������
is_valid = self.geo_state.validate_all_constraints()
errors, warnings = self.geo_state.get_validation_results()

# ����� �������������� ��������:
# � Max stroke (kinematic): 287mm
# � Max lever angle: 38.7�
# � Current stroke: 300mm
# ? Stroke exceeds kinematic limit: 300.0mm > 287.3mm
```

### �������������� ���������:
```python
normalized_value, corrections = self.geo_state.normalize_parameter('stroke_m', 0.600)
# corrections = ["Stroke limited to kinematic maximum: 287mm"]
```

---

## ?? ���������� A-4.3

### ? ������������ ���������:
1. **���������� ������������**: ������ UI ������������� �������� ��������� ����������� ������������ ��������
2. **�������� �����������**: ������ ������� �������������� ����������� ������������ �������� �������������� �������
3. **�������������� ���������**: ������� ���������� � ��������� �������� �����������
4. **��������� ������**: ������������ �����, ������ ����������� ���������� ���������� ����������

### ? �������������� ����������:
- **�������������� �����������**: 4 ���� (wheelbase, lever, cylinder, hydraulic)
- **�������������� ���������**: 3 ���� (stroke, rod diameter, lever length)
- **����� ���������**: Legacy + Kinematic (������� �������)
- **Preset'�� � �����������**: 3 (Standard, Light, Heavy)

### ? ���������������� ����:
- ����� �������� ������� �������� � �������� �������
- �������� ���������� ������ �������� ����������
- ����� ������� �������������� ��������� ��� ������ �����������
- ���������� ��������� ���������� �������

---

## ?? ������������ A-4.3

### ����������� ��������:
1. ? **������ �������**: GeometryState ������������� ��� ������
2. ? **Fallback �����**: ��� ������������� GeometryState ���������� legacy
3. ? **�������������� �������**: LeverKinematics � CylinderKinematics �������������
4. ? **UI ����������**: ������������ ����������� �������������� ��������
5. ? **���������**: ����������� �������� ���� ����� �����������

### ������ ����������:
```bash
get_errors(["src/ui/panels/panel_geometry.py", "src/ui/geo_state.py"])
# Result: No errors found ?
```

---

## ?? ��������� � A-0 (Pre-audit)

### ���� � A-0:
- 11 ��������� � ������� ����������
- ��������� ������� (��/�)
- ���������� ��������� ��������
- ������ �������������� �����������

### ����� � A-4.3:
- ? 11 ��������� � �������������� ����������
- ? ��������������� �� ������� (��� � ������)
- ? ��������������� ��������� ��������
- ? �������������� + �������������� + �������������� �����������
- ? �������������� ������������ ����������
- ? �������� ���������� ������� ��������

---

## ?? A-4: �������������� ����������� - ��������� ���������

### ����������� ���������:
- ? **A-4.1**: ������ �������� ���������
- ? **A-4.2**: �������� GeometryState � ��������������� ���������  
- ? **A-4.3**: ���������� GeometryState � GeometryPanel

### ����������� ����:
1. **�������� �������������� �����������** ������ ���������� ��������������
2. **�������������� ���������** ����������� ����������
3. **��������� ���������� �������** ��� ������ ����� ����������
4. **��������� ���������** � ����������� �����������

### ���������� � ������������:
- ? ������ �������� ������������� (fallback �����)
- ? ��� ������ ����������
- ? ���������� � ������������� �������� ����������
- ? ����������� ��������� ���� ����������

**������ A-4**: **���������** ???

������ ��������� ������ ���������� �������� ������ �������� ��� ����������� ����������!