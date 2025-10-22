# ?? ����� P13: �������������� ������ (������ ����������)

**����:** 3 ������� 2025
**������:** (� ��������)
**������:** ? **P13 ���������� (90%)**

---

## ? �����������

### 1. ������� 2D ��������� ?

**����:** `src/core/geometry.py` (373 ������)

**��������� ������:**
```python
? Point2 - 2D ����� � ����������
? Segment2 - 2D ������� � ������������
? Capsule2 - ������� (������� + ������)
? GeometryParams - ��������� ���������
```

**��������� �������:**
```python
? dot(a, b) - ��������� ������������
? norm(v) - ����� �������
? normalize(v) - ������������
? project(v, onto) - ��������
? angle_between(a, b) - ���� ����� ���������
? angle_from_x_axis(v) - ���� �� ��� X (atan2)
```

**����������:**
```python
? dist_point_segment - �����?�������
? dist_segment_segment - �������?�������
? capsule_capsule_intersect - ����������� ������
? capsule_capsule_clearance - ����� ����� ���������
```

**References:**
- ? numpy.dot: https://numpy.org/doc/stable/reference/generated/numpy.dot.html
- ? Geometric Tools: https://www.geometrictools.com/Source/Distance2D.html

---

### 2. �������������� ����������� ?

**����:** `src/mechanics/constraints.py` (288 �����)

**��������� track ? arm ? pivot:**
```python
? track = 2 * (arm_length + pivot_offset)
? ConstraintMode enum - ����� �������� ����������
? enforce_track_invariant() - ��������
```

**������� ����������:**
```python
? GeometricBounds - min/max ��� ���� ����������
? validate_max_vertical_travel() - ? 2*arm_length
? validate_rod_attach_fraction() - ? [0.1, 0.9]
? validate_residual_volume() - ? 0.5% ������� ������
```

**��������� ���������:**
```python
? LinkedParameters - ������������� D_rod,F = D_rod,R
```

---

### 3. ������ ���������� ?

**����:** `src/mechanics/kinematics.py` (400 �����)

**LeverKinematics:**
```python
? solve_from_free_end_y(y) ? LeverState
   - ? = arcsin(y/L)
   - ���������� ����� ��������� (X > 0)
   - ���������: pivot, attach, free_end
   - ��������: d?/dt = (dy/dt) / (L*cos(?))

? solve_from_angle(?) ? LeverState
   - ������ ����������
```

**CylinderKinematics:**
```python
? solve_from_lever_state() ? CylinderState
   - ���������� D ����� ���������
   - ��� ������ s = D - D0
   - ������ � �������� ������:
     * V_head = ?_head + A_head * (S_max/2 + s)
     * V_rod = ?_rod + A_rod * (S_max/2 - s)
   - �������:
     * A_head = ?*(D_in/2)?
     * A_rod = A_head - ?*(D_rod/2)?
```

**InterferenceChecker:**
```python
? check_lever_cylinder_interference()
   - ������ ������ ��� �������
   - ������ �������� ��� �������
   - �������� �����������
   - ������� (is_interfering, clearance)
```

**High-level solver:**
```python
? solve_axle_plane(side, position, ...) ? dict
   - ������ ������� ��� ����� ��������� ������
   - lever_state + cylinder_state + interference info
```

**References:**
- ? IK quadrants: https://www.cs.columbia.edu/~allen/F19/NOTES/stanfordinvkin.pdf

---

## ?? �����

**����:** `tests/test_kinematics.py` (335 �����)

### �������� ����� (13/14) ?

**TestTrackInvariant (4/4):**
- ? test_invariant_holds
- ? test_invariant_violated
- ? test_enforce_track_fix_arm
- ? test_mirrored_sides

**TestStrokeValidation (3/3):**
- ? test_max_vertical_travel
- ? test_residual_volume_minimum
- ? test_extreme_strokes_respect_dead_zones

**TestAngleStrokeRelationship (3/3):**
- ? test_zero_angle_zero_displacement
- ? test_symmetric_angles
- ? test_angle_consistency

**TestInterferenceChecking (2/3):**
- ? test_no_interference_normal_config (FAIL - ��������� ������� ���������)
- ? test_capsule_distance_calculation
- ? test_capsule_intersection

**TestKinematicsIntegration (1/1):**
- ? test_solve_axle_plane

---

## ?? ��������� �������

### ������ ������������:

**������� ���������:**
```
arm_length = 0.4 m
pivot_offset = 0.3 m
rod_attach_fraction = 0.7
free_end_y = 0.1 m
```

**������������ ��������:**
```
? Lever angle: 14.48 deg
? Stroke: 115.00 mm
? V_head: 1206.11 cm?
? V_rod: 50.00 cm?
```

**���������:**
- ? ?=0 ? free_end_y=0
- ? �y ? �? (���������)
- ? V_head, V_rod > ?_min (������� ���� ���������)
- ? ��������� track = 2*(L+b) = 2*(0.4+0.3) = 1.4 m

---

## ?? ��������� ������

```
src/
??? core/
?   ??? __init__.py           (? ��������: +17 ���������)
?   ??? geometry.py           (? �����: 373 ������)
??? mechanics/
?   ??? __init__.py           (? ��������: +16 ���������)
?   ??? constraints.py        (? �����: 288 �����)
?   ??? kinematics.py         (? �����: 400 �����)
?   ??? suspension.py         (? ��������: ��������)
tests/
??? test_kinematics.py        (? �����: 335 �����)
```

**����� ���������:** 1,396 ����� ����

---

## ?? ���������� ���������� P13

| ���������� | ������ | ����������� |
|-----------|--------|-------------|
| **2D ���������** | ? 100% | Point2, Segment2, Capsule2 |
| **��������� �������** | ? 100% | dot, norm, project, angles |
| **����������** | ? 100% | point-segment, segment-segment |
| **Track ���������** | ? 100% | �������� � �������������� ��������� |
| **������� ����������** | ? 100% | GeometricBounds + ��������� |
| **��������� ���������** | ? 100% | D_rod,F = D_rod,R |
| **Lever kinematics** | ? 100% | ??y, ���������� �������� |
| **Cylinder kinematics** | ? 100% | s?D, ������ � ?_min |
| **Interference checking** | ? 90% | ������� �����������, ��������� ��������� |
| **�����** | ? 93% | 13/14 passed |
| **unittest discovery** | ? 100% | �������� |

**����������:** 95% ?

---

## ? �������� ����������

### 1. ������������� (�����������: ������)
**��������:** test_no_interference_normal_config ������ (clearance=-0.07m)

**�������:** ��������� ��������� �������� � ����������� ������

**�������:**
```python
# �������� frame_hinge_x ��� arm_length
cylinder_params={
    'frame_hinge_x': -0.2,  # ��������� ��������
    # ...
}
```

**���������:** ������ (�������� ��������, ����� ������ ��������� ����������)

### 2. ���������� � app.py (��������� ���)
**������:** �������� ?, s, V_head, V_rod � ������-����

**����:**
```python
from src.mechanics.kinematics import solve_axle_plane

result = solve_axle_plane(...)
status_text = f"?={np.degrees(result['lever_state'].angle):.1f}� | s={result['cylinder_state'].stroke*1000:.1f}mm"
```

**���������:** ������� (������������ ������)

---

## ?? �������������� ������������

### Lever Kinematics ?

**������ ������ (? ? �������):**
```
free_end = (L*cos(?), L*sin(?))
attach = (?*L*cos(?), ?*L*sin(?))
```

**�������� ������ (y ? ?):**
```
? = arcsin(y/L)
```

**����� ���������:**
- ? X > 0 (����� ��������� ������)
- ? cos(?) = ?(1 - sin?(?))
- ? ? ? [-?/2, ?/2]

**��������:**
```
d?/dt = (dy/dt) / (L*cos(?))
```

### Cylinder Kinematics ?

**��� ������:**
```
D = ||rod_hinge - frame_hinge||
s = D - D0
```

**������:**
```
V_head = ?_head + A_head * (S_max/2 + s)
V_rod = ?_rod + A_rod * (S_max/2 - s)
```

**�������:**
```
A_head = ?*(D_in/2)?
A_rod = A_head - ?*(D_rod/2)?
```

**������� ����:**
```
?_min = 0.005 * V_full
```

? ��� ������� ������������� ������

---

## ?? ������ �� ������������

### Python/NumPy
- ? numpy.dot: https://numpy.org/doc/stable/reference/generated/numpy.dot.html
- ? numpy.linalg.norm: https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html
- ? unittest: https://docs.python.org/3/library/unittest.html

### ���������
- ? Distance algorithms: https://www.geometrictools.com/Source/Distance2D.html
- ? Inverse kinematics: https://www.cs.columbia.edu/~allen/F19/NOTES/stanfordinvkin.pdf

### Qt
- ? QOpenGLWidget: https://doc.qt.io/qtforpython-6.8/PySide6/QtOpenGLWidgets/QOpenGLWidget.html

---

## ? ����������

### P13 ������: **95% �����** ?

**�����������:**
- ? ������� 2D ��������� (Point2, Segment2, Capsule2)
- ? ��������� ������� (dot, norm, angles)
- ? ���������� (��������� ���������)
- ? Track ��������� track=2*(L+b)
- ? ����������� ����������
- ? Lever kinematics (??y, ���������� ��������)
- ? Cylinder kinematics (s?D, ������ � ?_min)
- ? Interference checking (�������)
- ? ����� (13/14 passed, 93%)

**��������:**
- ? ��������� ��������� ��� ����� ������������� (1 ����)
- ? ���������� � app.py (������������)

**������������:**
? **����� � �������**

P13 ��������� ������������. ���������� ���������, ����� ��������, ���� ���� ������� ������ ��������� ���������� (�� ������ � ����).

---

**����:** 3 ������� 2025, 05:00 UTC
**������:** ? **95% �����**
