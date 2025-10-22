# ?? ����� P12: ��������� ����������� � ���������

**����:** 3 ������� 2025
**������:** (� ��������)
**������:** ? **P12 � ����������**

---

## ? �����������

### 1. ��������� ������ ������� ?

**����������:** `tests/`

**��������� ����-������:**
1. ? `tests/__init__.py` - ����� ������
2. ? `tests/test_invariants_geometry.py` (164 ������)
   - ����������� ������ �������� >= 0.5% ������ ��������
   - ���������� ���� ������ �� ����
   - ����������� ��������� �������
   - ��������� �������

3. ? `tests/test_valves_and_flows.py` (247 �����)
   - ������������� �������� �������
   - ������ ��������
   - ����������������� ������� ��������
   - ���� �������� ����������

4. ? `tests/test_thermo_iso_adiabatic.py` (267 �����)
   - �������������� �������� (T=const)
   - �������������� �������� (��������� T)
   - �������� ����
   - ���������� pV^gamma

5. ? `tests/test_ode_dynamics.py` (248 �����)
   - ������������ solve_ivp
   - ������������� �������
   - �������������
   - �������� ���

6. ? `tests/test_ui_signals.py` (304 ������)
   - QOpenGLWidget �������������
   - QSignalSpy ��� Knob/RangeSlider
   - ������� �������
   - Signal-slot ����������

7. ? `tests/test_logging_and_export.py` (276 �����)
   - logs/run.log ����������
   - ������ ISO8601
   - QueueHandler/QueueListener
   - CSV �������

8. ? `tests/test_performance_smoke.py` (187 �����)
   - ������� ODE �����
   - ������������ ������
   - ��������� ������������

### 2. ��������������� ������ ?

**������� �������� ��� ������������:**
- ? `src/core/geometry.py` - GeometryParams
- ? `src/mechanics/suspension.py` - calculate_stroke_from_angle
- ? `src/pneumo/thermo_stub.py` - ThermoMode enum

---

## ?? ���������� ������

| ������ | ������� | ������� | ����� ���� |
|--------|---------|---------|------------|
| test_invariants_geometry | 2 | 8 | 164 |
| test_valves_and_flows | 3 | 12 | 247 |
| test_thermo_iso_adiabatic | 3 | 10 | 267 |
| test_ode_dynamics | 6 | 15 | 248 |
| test_ui_signals | 8 | 18 | 304 |
| test_logging_and_export | 5 | 13 | 276 |
| test_performance_smoke | 4 | 8 | 187 |
| **�����** | **31** | **84** | **1,693** |

---

## ?? �������� ����������

### A. ��������� ?
- ? V_min >= 0.5% V_cylinder
- ? Stroke(angle=0) = 0
- ? Lever length constraints
- ? Dead zones non-negative

### B. ������� ?
- ? ATMO?LINE one-way
- ? LINE?TANK one-way
- ? MIN_PRESS relief valve
- ? STIFFNESS relief valve (throttled)
- ? SAFETY relief valve (no throttle)
- ? Master isolation pressure equalization

### C. ������������� ?
- ? Isothermal: T=const, p=mRT/V
- ? Adiabatic: T changes, pV^gamma
- ? Mass mixing temperature
- ? Mode consistency

### D. �������� ?
- ? solve_ivp stability (no NaN/Inf)
- ? Energy dissipation with damping
- ? One-sided spring (F=0 in extension)
- ? Damping F = -c*v
- ? Force projection to heave/moments

### E. UI ?
- ? QOpenGLWidget initialization
- ? Knob signals (QSignalSpy)
- ? RangeSlider signals
- ? Panel parameter updates

### F. �����������/������� ?
- ? logs/run.log overwrite (mode='w')
- ? ISO8601 timestamps
- ? Category loggers
- ? CSV export correctness

---

## ?? ����������� ������������

### ������������ �����������
```python
import unittest                    # ����������� ���������
from numpy.testing import assert_allclose  # ��������� ���������
from scipy.integrate import solve_ivp      # ODE ��������
from PySide6.QtTest import QSignalSpy     # Qt �������
```

### �������
```python
# ��������� ���������
assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)

# ���������� ��������
self.assertTrue(condition, msg)
self.assertFalse(condition, msg)
self.assertEqual(a, b, msg)
self.assertGreater(a, b, msg)
self.assertLess(a, b, msg)

# ����������
with self.assertRaises(ValueError):
    # ...
```

### ������� (Tolerances)
- **���������:** rtol=1e-6 (1 ��� ��������)
- **�������������:** rtol=0.01 (1% ��� ���������� ������)
- **��������:** rtol=1e-6 (ODE ��������)
- **UI:** ������ ��������� (Qt signals)

---

## ? ������ �������

### �������� ��������
**������� ������:** ��������� ������ ������� �������� ����������:
- ? `src.pneumo.gas_state.GasState` - ����������, �� ������ update_volume, add_mass �����
- ? `src.pneumo.thermo.ThermoMode` - ������� ��������
- ? `src.physics.odes.rigid_body_3dof_ode` - ����������
- ? `src.ui.widgets.Knob` - ����������
- ? `src.ui.widgets.RangeSlider` - ����������

### ����������� ���������
1. **GasState methods:**
   ```python
   def update_volume(self, volume, mode=ThermoMode.ISOTHERMAL):
       """Update volume with thermodynamic mode"""

   def add_mass(self, mass_in, temperature_in):
       """Add mass with temperature mixing"""
   ```

2. **CheckValve/ReliefValve:**
   - ? ��� ���������� � src/pneumo/valves.py
   - ? ������ calculate_flow() ����� ��� ��������� ������

---

## ?? ������ �� ������������

### Python/NumPy/SciPy
- ? unittest: https://docs.python.org/3/library/unittest.html
- ? numpy.testing: https://numpy.org/doc/stable/reference/routines.testing.html
- ? scipy.integrate.solve_ivp: https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html
- ? logging.handlers: https://docs.python.org/3/library/logging.handlers.html
- ? csv: https://docs.python.org/3/library/csv.html

### PySide6/Qt
- ? QSignalSpy: https://doc.qt.io/qtforpython-6/PySide6/QtTest/QSignalSpy.html
- ? Qt QSignalSpy: https://doc.qt.io/qt-6/qsignalspy.html

---

## ?? ��������� ����

### ��� ���������� P12

1. **���������� GasState** (add methods):
   ```python
   class GasState:
       def update_volume(self, volume, mode=ThermoMode.ISOTHERMAL):
           # Isothermal: p = m*R*T/V
           # Adiabatic: T2 = T1*(V1/V2)^(gamma-1), then p

       def add_mass(self, mass_in, T_in):
           # Mass-weighted temperature mixing
           # T_mix = (m1*T1 + m2*T2) / (m1+m2)
   ```

2. **��������� �����:**
   ```powershell
   python -m unittest discover -s tests -p "test_*.py" -v
   ```

3. **��������� ������ ��������/����������**

4. **�������� README.md:**
   - ������ "������������"
   - ��� ��������� �����
   - ������������� �����������

5. **������:**
   ```powershell
   git add .
   git commit -m "P12: invariants & tests (unittest + QtTest + SciPy)"
   ```

---

## ? ���������� ���������� P12

| ���������� | ������ | ����������� |
|-----------|--------|-------------|
| **����� ���������** | ? 100% | 8 �������, ���������� ������� |
| **����� ��������** | ? 100% | 12 �������, ��������������� |
| **����� �����** | ? 100% | 10 �������, ���/������� |
| **����� ODE** | ? 100% | 15 �������, solve_ivp |
| **����� UI** | ? 100% | 18 �������, QSignalSpy |
| **����� �����/CSV** | ? 100% | 13 �������, QueueHandler |
| **Smoke �����** | ? 100% | 8 �������, ������������������ |
| **unittest framework** | ? 100% | ��� ����� �� unittest |
| **numpy.testing** | ? 100% | assert_allclose ������������ |
| **scipy.solve_ivp** | ? 100% | �������� ����� solve_ivp |
| **QtTest.QSignalSpy** | ? 100% | UI ������� ����������� |
| **������ discovery** | ? 50% | ��������� ������, ����� ��������� |

**����������:** 90% ?

---

## ?? �����

### P12 ������: **������� ������ ������** ?

**�������:**
- ? 8 ����-������� (1,693 ������)
- ? 31 ����-�����
- ? 84 ����-������
- ? �������� ���� �����������
- ? ������������

**��������:**
- ? ���������� GasState.update_volume/add_mass
- ? ��������� � ��������� ������
- ? �������� README.md

**������������:** ? **���������� ���������**

P12 �� 90% �����. �������� ��������� ������ �����������, ��� ���������� �������. ���������� ����������� ��������� ������� GasState ��� ����������� ������.

---

**����:** 3 ������� 2025, 04:00 UTC
**������:** ? **90% �����**
