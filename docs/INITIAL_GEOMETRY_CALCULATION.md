# ��������� ��������� ��������

## ���������� ���ר�

### �������� ������
```
D_cylinder = 80 mm (������� ��������)
D_rod = 32 mm (������� �����)
L_body = 250 mm (����� ��������)
L_piston = 20 mm (������� ������)
```

### ������ ��������
```
A_head = ? ? (D_cylinder/2)? = ? ? 40? = 5027 mm?
A_rod_steel = ? ? (D_rod/2)? = ? ? 16? = 804 mm?
A_rod = A_head - A_rod_steel = 4223 mm? (����������� ������� �������� �������)
```

### ��������� ��������� ������ (V_head = V_rod)

**������� ��������� �������:**
```
V_head = V_rod
A_head ? L_head = A_rod ? L_rod
A_head ? L_head = A_rod ? (L_working - L_head)
L_head ? (A_head + A_rod) = A_rod ? L_working

L_head_0 = (A_rod ? L_working) / (A_head + A_rod)
```

**������:**
```
L_working = L_body - L_piston = 250 - 20 = 230 mm

L_head_0 = (4223 ? 230) / (5027 + 4223)
         = 970290 / 9250
         = 104.9 mm ? 105 mm

L_rod_0 = 230 - 105 = 125 mm
```

**�������� ��������� �������:**
```
V_head = 5027 ? 105 = 527835 mm?
V_rod = 4223 ? 125 = 527875 mm?
������� = 40 mm? (0.0075% - ������������ ����!)
```

### ������� ������
```
x_piston_0 = 105 mm �� ������ ��������
pistonRatio = 105 / 250 = 0.42 (42% �� ����� ��������)
```

### ��������� ��������� ������� (�������������!)

**����� ��������������� ���� ��� ����������� ���������:**
```
����� ������: L_lever = 315 mm

����� ������� (FL, RL):
j_rod = j_arm + (-315, 0, 0)

FL: (-150, 60, -1000) + (-315, 0, 0) = (-465, 60, -1000)
RL: (-150, 60, 1000) + (-315, 0, 0) = (-465, 60, 1000)

������ ������� (FR, RR):
j_rod = j_arm + (+315, 0, 0)

FR: (150, 60, -1000) + (315, 0, 0) = (465, 60, -1000)
RR: (150, 60, 1000) + (315, 0, 0) = (465, 60, 1000)
```

### ����� ����������

**����������� �� ��������� ���������:**
```
���������� �� j_tail �� j_rod (��� �������������� ������):

��� FL:
dx = j_rod.x - j_tail.x = -465 - (-100) = -365 mm
dy = j_rod.y - j_tail.y = 60 - 710 = -650 mm
L_total = ?(365? + 650?) = ?(133225 + 422500) = ?555725 = 745.5 mm

����������:
L_tail = 100 mm (���������)
L_cylinder = 250 mm (������ ��������)
L_piston_rod = L_total - L_tail - L_cylinder = 745.5 - 100 - 250 = 395.5 mm
```

## QML ��� (����������)

```qml
// ��������� ������� (�������������!)
property vector3d fl_j_arm: Qt.vector3d(-150, 60, -1000)
property vector3d fr_j_arm: Qt.vector3d(150, 60, -1000)
property vector3d rl_j_arm: Qt.vector3d(-150, 60, 1000)
property vector3d rr_j_arm: Qt.vector3d(150, 60, 1000)

property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)
property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)
property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)
property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)

// ��������� j_rod (����� ������������ ��� angle=0!)
property vector3d fl_j_rod_0: Qt.vector3d(-465, 60, -1000)
property vector3d fr_j_rod_0: Qt.vector3d(465, 60, -1000)
property vector3d rl_j_rod_0: Qt.vector3d(-465, 60, 1000)
property vector3d rr_j_rod_0: Qt.vector3d(465, 60, 1000)

// ������� � ��������� ��������� ��ڨ���
property real pistonPositionMm: 105.0  // mm �� ������ ��������
property real pistonRatio: 0.42        // 42% �� ����� ��������

// ����� ����� ������ (��������� �� ���������)
property real pistonRodLength: 395.5   // mm
```

## �����!

1. **������� �� � �������� ��������!** �� ������ � ����������� ������� ��-�� ������ �����!
2. **����� ������ ������������** � ����������� ��������� (�� ��� �����!)
3. **��� ���������� �����������** �� ���������� ���������, � �� ��������!
4. **����� ���������� �������** �� ������������ j_tail � j_rod_0!
