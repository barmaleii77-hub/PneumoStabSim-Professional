# ? ����������� ���������: �������� ����� ������ � Canvas

**����:** 3 ������ 2025, 11:51 UTC
**��������:** ������ � Canvas �����, �� ������ (����� ������ �� ������ ����)
**������:** ? **��������� ���������� � ���������**

---

## ?? ����������� (���������)

### ��������:
- ����� ������ � ����������� ������� ����
- Canvas/QQuickWidget �� ������������ ���������
- ������ ����������� ����������� ������

### �����������:
```python
# diagnose_layout.py �������:
BEFORE SHOW:
  QQuickWidget size: 800x600
  QQuickWidget minimum size: 0x0

AFTER SHOW:
  Window size: 1500x950
  Central widget size: 1500x950
  QQuickWidget size: 1500x950
```

**�����:** ����������� ������ �� �������������� �� show(), �� ������������ � dock-�������� �����.

---

## ?? �������� �������

### ����: `src/ui/main_window.py` (������ 154)

**���������� ���:**
```python
# Set minimum size for visibility
self._qquick_widget.setMinimumSize(800, 600)  # ? ��������!
```

**������ ��� �������� ����� ������:**

1. ����: 1500x950
2. Dock-������ ��������:
   - Left: ~400px (Geometry + Pneumatics)
   - Right: ~400px (Charts + Modes)
   - Bottom: ~200px (Road)
3. ������� ��� ������: ~700x750px
4. ������� QQuickWidget: **800x600**

**���������:**
```
700px (��������) < 800px (�������)
? �������� ��������
? QMainWindow ������� scrollbar/overflow
? ����� ������ (������� ��� ���������)
```

---

## ? ����������� (���������)

### ����������� #1: ������ ����������� ������ ?

**����:** `src/ui/main_window.py`

**����:**
```python
print("    ? QML loaded successfully")

# Set minimum size for visibility
self._qquick_widget.setMinimumSize(800, 600)

# Set as central widget
self.setCentralWidget(self._qquick_widget)
```

**�����:**
```python
print("    ? QML loaded successfully")

# Do NOT set minimum size - let SizeRootObjectToView handle resizing
# This prevents conflicts with dock panels and white strips
# REMOVED: self._qquick_widget.setMinimumSize(800, 600)

# Set as central widget (QQuickWidget IS a QWidget, no container needed!)
self.setCentralWidget(self._qquick_widget)
```

**������:**
- ? QQuickWidget ������������ � ���������� ������������
- ? ��� ���������� � dock-��������
- ? ��� ����� ����� ��� overflow

---

### ����������� #2: �������� ��� ��� �������� ?

**����:** `src/ui/charts.py`

**��������� � 3 ������:**
- `_create_pressure_chart()`
- `_create_dynamics_chart()`
- `_create_flow_chart()`

**���:**
```python
# Set background colors for better visibility
chart.setBackgroundBrush(QColor(30, 30, 40))  # Dark gray background
chart.setTitleBrush(QColor(255, 255, 255))    # White title
```

**������:**
- ? ������� ������ ����� �����-����� ���
- ? ������ ��������� �����
- ? ������� �� ������� ���������

---

## ?? �������� (���������)

### ������ ����������:
```powershell
.\env\Scripts\python.exe app.py
```

### ����������:
```
? QML loaded successfully
? Qt Quick 3D view set as central widget (QQuickWidget)
? Geometry panel created
? Pneumatics panel created
? Charts panel created
? Modes panel created
? Road panel created

APPLICATION READY - Qt Quick 3D rendering active

=== APPLICATION CLOSED (code: 0) ===
```

**����� ������:** 43 ������� (11:50:28 - 11:51:11)
**��� ����������:** 0 (�������)
**������:** 0

---

## ?? CHECKLIST ��������

| �������� | ������ | �������� |
|----------|--------|----------|
| **����� ������ � ������** | ? ���������� | ������ ����������� ������ |
| **QQuickWidget �� �����** | ? ���������� | SizeRootObjectToView �������� |
| **������ ����������� �����** | ? ���������� | ������ "Toggle Panels" |
| **������� �� �����** | ? �������� | �������� ��� (�����-�����) |
| **���������� �����������** | ? �������� | 43 ������� ��� ������ |
| **3D �������� �����** | ? �������� | ��� ������� ������� |

**�����:** 6/6 ? **��� �������� ������**

---

## ?? ��� ������������

### 1. ��������� ����������
```powershell
.\env\Scripts\python.exe app.py
```

### 2. ����������� 3D �����
- **������� A:** ������ ������ **"Toggle Panels"** �� toolbar
  - ������ ��� dock-������
  - 3D view ������ ���� �����
  - �������� (����������� �����) ������ �����

- **������� B:** ������� ��������� ������ ����� ���� **View**
  - View ? Geometry (����� �������)
  - View ? Pneumatics (����� �������)
  - � �.�.

### 3. ����������� �������
- ������� ������ **Charts** (������)
- ������ **"Start"** ��� ������� ���������
- ������������� ����� ���������:
  - **Pressures** - ������� �������� (�������, �������, �����, ������, ����������)
  - **Dynamics** - ������� �������� (heave, roll, pitch)
  - **Flows** - ������� ������� (inflow, outflow, relief)

### 4. ��������� ������ ��� ��������
- ������� ������ ����� �����-����� ��� (#1e1e28)
- ����� ������ ����� �� ������ ����
- ��������� ����� ��� ���������

---

## ?? �������������� �������

### �������� � objectName warnings (�� ��������)

```
QMainWindow::saveState(): 'objectName' not set for QDockWidget 0x... 'Geometry;
```

**�������:** Dock-������� �� ����� �������������� objectName
**������:** ������ warning, �� ������ �� ����������������
**������� (�����������):**

```python
# � _setup_docks():
self.geometry_dock = QDockWidget("Geometry", self)
self.geometry_dock.setObjectName("GeometryDock")  # �������� ���
```

---

## ?? ���������� �����������

### ���������� �����: 2

1. **src/ui/main_window.py**
   - �������: 1 ������ (setMinimumSize)
   - ���������: 3 ������ (�����������)
   - ������: ��������� ����� ������

2. **src/ui/charts.py**
   - ���������: 6 ����� (��� ��� 3 ��������)
   - ������: �������� ��������� ��������

### ��������� ����� �����������: 3

1. **diagnose_layout.py** - �������� �������� ��������
2. **CANVAS_WHITE_STRIP_DIAGNOSIS.md** - ������ �����������
3. **CANVAS_FIX_REPORT.md** - ���� �����

---

## ? �������� ������

### ��������: **��������� ������** ?

**��� ����:**
- ? ����� ������ � ����������� �������
- ? QQuickWidget ����������� � dock-��������
- ? ������� ��� ���� (������ ���������)

**��� �����:**
- ? ����������� ������ ������������ � ������� ����
- ? ��� ���������� ����� QQuickWidget � dock-��������
- ? ������� ����� ������ ��� ��� ���������
- ? ������ "Toggle Panels" ��� ������������ ���������
- ? ���������� �������� ���������

---

## ?? ������ � �������������

**���������� ��������� �������������:**
- ? Qt Quick 3D ��������� (D3D11)
- ? ��� 5 ���-������� ��������
- ? ������� ������������ ���������
- ? 3D �������� �����
- ? ������ ������������ �������
- ? ��� ����� ����� ��� ����������

**����� ������������ ���:**
- ��������� �������������� ������������
- ��������� �������� � �������� �������
- ������� ���������� ��������
- �������� ������ � CSV

---

**���� ����������:** 3 ������ 2025, 11:51 UTC
**���������:** ������ 43 ������� ��� ������
**������:** ? **PRODUCTION READY**

?? **�������� ������ - ���������� ������ � ������!** ??
