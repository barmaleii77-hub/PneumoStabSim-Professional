# ��-3: ���������� ������ dependency resolution

## ��������� ?

����: 2024-01-XX  
������: **���������**

### ����
�������� ������ `_check_dependencies()` � `_resolve_conflict()` ��� ������ � ������ ���������������� ����������� � �� ��������.

### ���������

#### 1. �������������� ����������� (�� �������)
**��:**
```python
max_lever_reach = wheelbase / 2.0 - 0.1  # 0.1� clearance
message: f'�������: {frame_to_pivot + lever_length:.2f}�'
```

**�����:**
```python  
max_lever_reach = wheelbase / 2.0 - 0.100  # 100mm clearance explicit
message: f'�������: {frame_to_pivot + lever_length:.3f}�'  # 3 decimals for SI
```

#### 2. �������������� ����������� (��������������� ���������)
**��:**
```python
rod_diameter = self.parameters['rod_diameter']  # mm
min_bore = min(bore_head, bore_rod)             # mm  
```

**�����:**
```python
rod_diameter = self.parameters['rod_diam_m']    # meters
cyl_diameter = self.parameters['cyl_diam_m']    # meters (unified)
# Both head and rod use same diameter now!
```

#### 3. Stroke constraints (����� ������)
**���������:**
```python
if param_name in ['stroke_m', 'cylinder_length', 'piston_thickness_m', 'dead_gap_m']:
    min_cylinder_length = stroke + piston_thickness + 2 * dead_gap
    # Detailed breakdown in error message
```

#### 4. 3D Scene ��������� (��������� �� ? ��)
**���������:**
```python
geometry_3d = {
    'boreHead': self.parameters.get('cyl_diam_m', 0.080) * 1000,  # m -> mm
    'boreRod': self.parameters.get('cyl_diam_m', 0.080) * 1000,   # Same as boreHead!
    'strokeLength': self.parameters.get('stroke_m', 0.300) * 1000,  # m -> mm
    # ... ��� ��������� ��������� �������������� �� �� � ��
}
```

#### 5. ������� (��������� ��� ��������������� ����������)
**���������:**
```python
presets = {
    0: {  # ����������� ��������
        'cyl_diam_m': 0.080, 'rod_diam_m': 0.035, 'stroke_m': 0.300,
        'cylinder_length': 0.500, 'piston_thickness_m': 0.020, 'dead_gap_m': 0.005
    },
    # ... ��� ������� ��������� ��� ����� ����������
}
```

### ���������

#### ��������������� ������ dependency resolution:
- ? **�������������� �����������** �������� � �� ��������� � ��������� 0.001�
- ? **�������������� �����������** ���������� unified `cyl_diam_m` ��������  
- ? **Stroke constraints** ������������ ��� ����� ���������
- ? **3D Scene ���������** ��������� ����������� �� ? ��
- ? **�������** ��������� ��� ���� ����� ����������

#### ���������������:
- ��� ������� � �� �������� (�����)
- �������� 0.001� (1��) �����
- ��������������� ������� ��������
- ��������� ��������� �� �������

### ����� ��������

1. `src/ui/panels/panel_geometry.py`
   - `_check_dependencies()` - ��������� ������� ��� ��������������� ����������
   - `_on_parameter_changed()` - ��������� ������ emit geometry_changed  
   - `_on_preset_changed()` - ������� ��������� ��� ����� ����������

2. `tests/ui/test_ms3_dependency.py` - ����� ��� ��������� ��-3

### ���������

- ? ���������� ��� ������  
- ? ������ ������ �������
- ? Dependency check �������� ���������
- ? �������������� ����������� � �� ��������
- ? �������������� ����������� � ���������������� �����������
- ? Stroke constraints � ����� �������

### ��������� ���

**��-4:** �������� comprehensive ������ ��� ����� ������������ � ��������� ���������.

---
**������:** ��-3 �������� �������. Dependency resolution ������� ��� ��������������� ���������� ��.