# ?? ����������� �����������: ������ ����� � ��������� �������

**����:** 3 ������ 2025, 12:00 UTC
**��������:**
1. ? ������ ����� ������ 3D ��������
2. ? ������ �������� �� �������� (������ 101325 Pa)
3. ? Frame heave = 293 ����� (��������� �������!)

**������:** ?? **����������� ������ �������**

---

## ?? ����������� ���������

### ��������: `diagnose_simulation.py`

**���������� �� 10 ������:**
```
Total states received: 783 ? (��������� ��������)

Sim time: 7.730s
Step: 7730
Frame heave: 293.087975m  ? ��������! (������ ���� ~0.0m)
Frame roll: 0.000000rad   ? (�� ����������)
Frame pitch: 0.000000rad  ? (�� ����������)

A1 pressure: 101325.0Pa   ? (�����������, �� ��������)
B1 pressure: 101325.0Pa   ?
A2 pressure: 101325.0Pa   ?
B2 pressure: 101325.0Pa   ?
Tank pressure: 101325.0Pa ?
```

---

## ?? �������� �������

### �������� #1: ��������� ������� (heave = 293m)

**����:** `src/physics/odes.py:98-130`

**���:**
```python
def assemble_forces(...):
    # ...
    for i, wheel_name in enumerate(wheel_names):
        # ...

        # TODO: Calculate pneumatic cylinder force
        F_cyl_axis = 0.0  # ? ��������! ������ 0

        # TODO: Calculate spring force
        F_spring_axis = 0.0  # ? ��������! ������ 0

        # TODO: Calculate damper force
        F_damper_axis = 0.0  # ? ��������! ������ 0
```

**��� ����������:**
```python
# � f_rhs():
F_suspension_total = np.sum(vertical_forces)  # = 0 (��� ���� = 0)
F_gravity = params.M * params.g  # ? 9810 N (����)

d2Y = (F_gravity + F_suspension_total) / params.M
    = (9810 + 0) / 1000
    = 9.81 m/s?  # ��������� �������!
```

**���������:**
- ������ ������ � ���������� ���������� �������
- �� 7.7 ������: heave ? 0.5 * g * t? = 0.5 * 9.81 * 7.7? ? **291 �����** ?

---

### �������� #2: �������� �� ��������

**����:** `src/runtime/sim_loop.py:228-241`

**���:**
```python
# Line states (placeholder)
for line in [Line.A1, Line.B1, Line.A2, Line.B2]:
    line_state = LineState(line=line)
    # TODO: Get actual line state from gas network  ? �� �����������!
    snapshot.lines[line] = line_state

# Tank state (placeholder)
snapshot.tank = TankState()  # ? ��������� � ���������� ����������
```

**��� ����������:**
```python
# � LineState.__init__():
self.pressure = 101325.0  # ����������� �������� (������)

# � TankState.__init__():
self.pressure = 101325.0  # ����������� �������� (������)
```

**���������:**
- ������ snapshot ������� ����� ������� � ��������� ���������
- ������� ���� �� ����������
- �������� ������ 101325 Pa (1 ���)

---

### �������� #3: ������ ����� (QML �� ����������)

**��������� �������:**

**A. QML ����� ���������, �� �� �����������**

�������� � `main_window.py:456-469`:
```python
@Slot()
def _update_render(self):
    if not self._qml_root_object:
        return  # ? ���� root = None, ��������� �� ��������

    # Update QML properties...
```

**���������:** ���������� �� `self._qml_root_object`?

**B. QML ����� ������ ��� (��������� � ������)**

� `assets/qml/main.qml:11`:
```qml
environment: SceneEnvironment {
    clearColor: "#101418"  // ����� ������
}
```

**C. 3D ������� ��� ������**

� `main.qml:21-27`:
```qml
PerspectiveCamera {
    position: Qt.vector3d(0, 1.5, 5)
    eulerRotation.x: -15
}
```

---

## ? ����������� (���������)

### ����������� #1: �������� ���� �������� (��������)

**����:** `src/physics/odes.py`

**�������� ������� ������� � �������:**

```python
def assemble_forces(system: Any, gas: Any, y: np.ndarray,
                   params: RigidBody3DOF) -> Tuple[np.ndarray, float, float]:
    """Assemble forces and moments from suspension system"""
    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y

    wheel_names = ['LP', 'PP', 'LZ', 'PZ']
    vertical_forces = np.zeros(4)

    # TEMPORARY: Add basic spring/damper until pneumatics connected
    k_spring = 50000.0  # N/m (spring constant)
    c_damper = 2000.0   # N�s/m (damping coefficient)

    for i, wheel_name in enumerate(wheel_names):
        x_i, z_i = params.attachment_points.get(wheel_name, (0.0, 0.0))

        # Calculate wheel vertical position relative to frame
        # Y is heave (positive down), so suspension compression is Y
        compression = Y  # Simplified

        # Spring force (resists compression, acts upward = negative)
        F_spring = -k_spring * compression

        # Damper force (resists velocity, acts upward if moving down)
        F_damper = -c_damper * dY

        # Pneumatic force (TODO: get from gas network)
        F_pneumatic = 0.0

        # Total vertical force (positive downward)
        F_total = F_spring + F_damper + F_pneumatic
        vertical_forces[i] = F_total

    # Calculate moments
    tau_x = 0.0
    tau_z = 0.0

    for i, wheel_name in enumerate(wheel_names):
        x_i, z_i = params.attachment_points.get(wheel_name, (0.0, 0.0))
        tau_x += vertical_forces[i] * z_i
        tau_z += vertical_forces[i] * x_i

    return vertical_forces, tau_x, tau_z
```

**������:**
- ? ������ ����� ������������ �� ����� ���������
- ? Heave stabil��������� ����� 0
- ? ������ heave ������� ���������

---

### ����������� #2: ���������������� �������� (���������)

**����:** `src/runtime/state.py`

**�������� ��������� ��������:**

```python
@dataclass
class LineState:
    line: Line
    pressure: float = 150000.0  # 1.5 bar ������ 1.0 bar
    temperature: float = 293.15
    mass: float = 0.001
    # ...

@dataclass
class TankState:
    pressure: float = 200000.0  # 2.0 bar ������ 1.0 bar
    temperature: float = 293.15
    mass: float = 1.0
    # ...
```

**������:**
- ? ������ �������� ������� ������ �������� ��� �����/����
- ??  ��������� ������� - ����� ���������� ������� ����

---

### ����������� #3: ��������� QML ���������

**�������� debug � `main_window.py`:**

```python
def _update_render(self):
    if not self._qml_root_object:
        print("??  QML root object is None!")  # DEBUG
        return

    # Debug: print first time
    if not hasattr(self, '_debug_printed'):
        print(f"? QML root object: {self._qml_root_object}")
        print(f"  width: {self._qml_root_object.property('width')}")
        print(f"  height: {self._qml_root_object.property('height')}")
        self._debug_printed = True

    # Update properties...
```

---

### ����������� #4: �������� ���� ���� QML (�����������)

**����:** `assets/qml/main.qml`

**�������� �� ����� ������� ���:**

```qml
environment: SceneEnvironment {
    backgroundMode: SceneEnvironment.Color
    clearColor: "#2a2a3e"  // ������� ��� ��������� (���� #101418)
    antialiasingMode: SceneEnvironment.MSAA
    antialiasingQuality: SceneEnvironment.High
}
```

---

## ?? ��������� �����������

| � | ����������� | ��������� | ������ |
|---|-------------|-----------|--------|
| **1** | �������� ���� �������� | ?? �������� | ��������� ��������� ������� |
| **2** | ���������������� �������� | ??  ����� | ������� ������ �������� |
| **3** | Debug QML ���������� | ?? ����� | ������� ������� ������ ����� |
| **4** | �������� ��� QML | ?? ����������� | ������� ��������� |

---

## ?? ��� ��������� �����������

### ��� 1: ��������� ����������� #1 (���� ��������)

```powershell
# ������� ����
code src/physics/odes.py

# �������� assemble_forces() �� ��� ����
# ���������
```

### ��� 2: ��������� �����������

```powershell
.\env\Scripts\python.exe diagnose_simulation.py
```

**��������� ���������:**
```
State #100
  Frame heave: 0.049m  ? (����� 0, ���������)
  Frame roll: 0.002rad ? (��������� ���������)
  Frame pitch: 0.001rad ?
```

### ��� 3: ��������� ����������

```powershell
.\env\Scripts\python.exe app.py
```

**���������:**
1. ? ������ "Dynamics" ? ������� ���������� ��������� heave
2. ? ������ "Pressures" ? ������� ���������� ����� (���� ����������� #2 ���������)

---

## ?? �������������� �������

### ������ �������� �� ����������� (�������������� �������)

**����:** `src/ui/charts.py:234-246`

**���:**
```python
def _update_pressure_data(self, snapshot: StateSnapshot):
    # Line pressures
    for line_name, line_state in snapshot.lines.items():
        buffer_key = line_name.value  # A1, B1, A2, B2
        if buffer_key in self.pressure_buffers:
            self.pressure_buffers[buffer_key].append(line_state.pressure)
```

**��������:** ���� ��� �������� = 101325, ������ ����� ������� ������ (�� "�� ��������", � "����������")

**��������:** ���������� �� ������ - ���� ����� ����, �� �������, ��� ������������ ��������.

---

## ?? ������

### ��������� ��������, ��:

1. ? **������ �����������:**
   - ��� ��� �������� ? ��������� �������
   - ����� �������� ��������� �������/��������

2. ? **���������� �� ����������:**
   - �������� ������ ��������� (101325 Pa)
   - ����� ���������������� ������� ����

3. ? **QML ����� �� �����������:**
   - ����� ��������� `_qml_root_object`
   - ��������, ������ ��� ���������

### ��� ��������:

- ? SimulationManager �������
- ? Physics worker ���������� states (~78 states/sec)
- ? State bus �������� snapshots � UI
- ? ChartWidget �������� ������
- ? QTimer ��������

### ��� �� ��������:

- ? ���� �������� (������ 0)
- ? ������� ���� (placeholders)
- ? 3D �������� (������ �����)

---

## ?? ��������� ����

### ���������� (��������):

1. **�������� ��������� ���� ��������** (����������� #1)
   - ��������� ��������� �������
   - ������� ������������ ��������

2. **��������� QML ���������** (����������� #3)
   - ��������, ������ ������ �����
   - �������� debug logging

### � ��������� �����:

3. **���������� ������� ����**
   - ������� GasNetwork � PhysicsWorker
   - ���������������� ��������
   - ��������� � _execute_physics_step()

4. **���������� �������������� �������**
   - ������� PneumaticSystem
   - ������� � ������� �����
   - ��������� ���� ���������

---

## ?? ����� ��� �����������

| ���� | �������� | ��������� |
|------|----------|-----------|
| `src/physics/odes.py` | �������� ���� �������� | ?? �������� |
| `src/runtime/state.py` | �������� ��������� �������� | ??  ����� |
| `src/ui/main_window.py` | Debug QML ���������� | ?? ����� |
| `assets/qml/main.qml` | �������� clearColor | ?? ����������� |

---

**���� ���������� �����������:** 3 ������ 2025, 12:00 UTC
**������:** ?? **����������� �������� ������� ������������ �����������**

?? **���������� �� ������������� ��� �����������!** ??
