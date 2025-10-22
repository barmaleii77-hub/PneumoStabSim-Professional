# ?? �����������: ����� ������ � Canvas (�������� �������)

**����:** 3 ������ 2025
**�������:** ������ � Canvas �����, �� ������ (����� ������ �� ������ ����)
**������:** ? **�������� ������� � ������**

---

## ?? ����������� ��������

### 1. ��������������� ������

**�������:** `diagnose_layout.py`

```
BEFORE SHOW:
  Window size: 1500x950
  QQuickWidget size: 800x600
  QQuickWidget minimum size: 0x0  ? ��������!
  QQuickWidget visible: False

AFTER SHOW:
  Window size: 1500x950
  Central widget size: 1500x950
  QQuickWidget size: 1500x950  ? ���������� ������
```

---

## ?? �������� �������

### �������� #1: ����������� ������ ����������� � Dock-��������

**��� � `src/ui/main_window.py:154`:**
```python
# Set minimum size for visibility
self._qquick_widget.setMinimumSize(800, 600)
```

**��� ����������:**

1. **����:** 1500x950
2. **Dock-������ ��������:**
   - Left (Geometry + Pneumatics): ~400px
   - Right (Charts + Modes): ~400px
   - Bottom (Road): ~200px
3. **������� ��� ������:** ~700x750px
4. **������� QQuickWidget:** 800x600

**���������:**
```
700px (��������) < 800px (�������)
? QMainWindow ������� ������
? ���������� scrollbar/overflow
? ����� ������ (������� �� ��������� ���������)
```

---

### �������� #2: ������ �� ����������� ���������

**������ 128:**
```python
self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
```

��� **���������**, �� ����������� ������ **��������������** �������������� ��������� �������!

---

## ??? �������

### ������� 1: ������ ����������� ������ (�������������)

**����:** `src/ui/main_window.py`

**������� ������ 153-154:**
```python
# Set minimum size for visibility
self._qquick_widget.setMinimumSize(800, 600)  # ? �������
```

**�����������:**
- `SizeRootObjectToView` ������������� ������������ QML ��� ������ �������
- ����������� ������ �� �����
- ��������� QQuickWidget �������������� � ���������� ������������

---

### ������� 2: ���������� ������� �������

**�������� ��:**
```python
# Set smaller minimum to allow dock panel flexibility
self._qquick_widget.setMinimumSize(400, 300)
```

**�����������:**
- ����������� ����������� ��������� 3D view
- �� ����������� � dock-��������
- ��������� ������������ ������������ �������

---

### ������� 3: ������ ������ �� ��������� (��� �����������)

**������ "Toggle Panels" �� toolbar:**
```python
def _toggle_all_panels(self, visible: bool):
    for dock in [...]:
        dock.setVisible(visible)
```

**��� ������������:**
1. ��������� ����������
2. ������ "Toggle Panels" ? ������ ������
3. 3D view ������ ���� �����
4. �������� ������ �����

---

## ?? �������������� �������

### �������� #3: ChartWidget ����� ���� ������ (��� ������)

**ChartWidget ��������� ���������:**
```python
# src/ui/charts.py:50-110
def _create_pressure_chart(self):
    chart = QChart()
    chart.setTitle("System Pressures")
    # ... �������� series � axes
```

**�� ������ ����������� ������ ��� ������� snapshot:**
```python
def update_from_snapshot(self, snapshot: StateSnapshot):
    if self.update_counter % self.update_interval != 0:
        return  # Throttling

    # Update data...
```

**��������:** ���� ��������� �� �������� ? ������� ������ ? ChartWidget ����� ��������� ��� "����� ������"

---

## ?? �������������� �����������

### �������� ���������

```python
# � main_window.py:_on_state_update
@Slot(object)
def _on_state_update(self, snapshot: StateSnapshot):
    self.current_snapshot = snapshot
    if snapshot:
        # Update labels...
    if self.chart_widget:
        self.chart_widget.update_from_snapshot(snapshot)  # ? ����������?
```

**���������:** �������� �� snapshots �� SimulationManager?

### �������� debug logging

```python
def _on_state_update(self, snapshot: StateSnapshot):
    print(f"DEBUG: Snapshot received - time={snapshot.simulation_time if snapshot else 'None'}")
    self.current_snapshot = snapshot
    # ...
```

---

## ? �����������

### ����������� #1: ������ ����������� ������ QQuickWidget

**����:** `src/ui/main_window.py`

**������ 153-154 ? �������:**
```python
            # Set minimum size for visibility
            self._qquick_widget.setMinimumSize(800, 600)  # ? ������� ��� ������
```

**����� �����������:**
```python
            print("    ? QML loaded successfully")

            # �������: setMinimumSize(800, 600)

            # Set as central widget (QQuickWidget IS a QWidget, no container needed!)
            self.setCentralWidget(self._qquick_widget)
```

---

### ����������� #2: �������� debug logging (�����������)

**����:** `src/ui/main_window.py`

**� ����� `_on_state_update` ��������:**
```python
@Slot(object)
def _on_state_update(self, snapshot: StateSnapshot):
    # DEBUG
    if snapshot and self.update_counter % 100 == 0:  # ������ 100 ����������
        print(f"DEBUG: State update - time={snapshot.simulation_time:.3f}s, step={snapshot.step_number}")

    self.current_snapshot = snapshot
    # ...
```

---

### ����������� #3: �������� ��������� Chart Widget

**����:** `src/ui/charts.py`

**�������� ������� ���� ��� QChart:**
```python
def _create_pressure_chart(self):
    chart = QChart()
    chart.setTitle("System Pressures")
    chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)

    # ADD: Set background color to distinguish from empty state
    chart.setBackgroundBrush(QColor(30, 30, 40))  # �����-����� ���
    chart.setTitleBrush(QColor(255, 255, 255))    # ����� ���������

    # ...
```

---

## ?? ��������� �����������

| ��������� | ����������� | ������ |
|-----------|-------------|--------|
| **1 (��������)** | ������ `setMinimumSize(800, 600)` | �������� ����� ������ |
| **2 (�����)** | �������� ��� ��� QChart | ������� ��������� �������� |
| **3 (�����������)** | Debug logging | ������� ������� |

---

## ?? ��� ��������� �����������

### ��� 1: ��������� ����������� #1

```powershell
# ������� ����
code src/ui/main_window.py

# ����� ������ 154 � �������:
# self._qquick_widget.setMinimumSize(800, 600)

# ���������
```

### ��� 2: ��������� ����������

```powershell
.\env\Scripts\python.exe app.py
```

### ��� 3: ���������

1. ? ���� ����������� 1500x950
2. ? ������ ����� �����/������/�����
3. ? ����������� ������� (QQuickWidget) �� ����� ����� ������
4. ? 3D ����� ����� (����� ���� ������� ��������)
5. ? ������ "Toggle Panels" ? 3D view �� ���� �����

### ��� 4: ��������� �������

1. ������ "Start" �� toolbar
2. ������� ������ "Charts" (������)
3. ������������� ����� ��������� (Pressures, Dynamics, Flows)
4. ? ������� ������ ������������ (����� �� ������ ����)

---

## ?? ������ ��������� ������� "����� ������"

### ���� �������� �� ������ ����� ����������� #1:

**������� A: QML �� �����������**
```
��������: ���������� ������� �� ������ QML
�������: ��������� assets/qml/main.qml ����������
```

**������� B: Qt Quick 3D �� ���������������**
```
��������: ���������� "qsbc file is for a different Qt version"
�������: ������� ��� Qt Quick
  rm -rf ~/AppData/Local/python/cache/q3dshadercache-*
```

**������� C: ������� ����� (��� ������)**
```
��������: ��������� ��������� ("Start")
�������: ��������� 2-3 ������� ��� ���������� ������
```

**������� D: ������������ ���� ����**
```
��������: ���������� �� ����� � main.qml:
  clearColor: "#101418"  (����� ������)
�������: �������� �� ����� �������:
  clearColor: "#2a2a3e"
```

---

## ? �������� �������

### �������� ��������: **setMinimumSize ����������� � dock-��������**

**��������:**
1. ? ������� `setMinimumSize(800, 600)` �� main_window.py:154
2. ? �������� ��� ��� QChart (�����������)
3. ? ������������ "Toggle Panels" ��� ��������� 3D

**���������:**
- ����������� ������ ������������ � ���������� ������������
- ��� ����� ����� ��� overflow
- ������ � 3D view �������� ���������

---

## ?? �����

**�������� ����������������:**
- ����������� ������ QQuickWidget (800x600) ����������� � dock-��������
- �������� overflow � ����� ������

**�������:**
- ������ `setMinimumSize`
- ���������� �� `SizeRootObjectToView` ��� ��������������� ��������� �������

**������:** ? **������ � �����������**

---

**����:** 3 ������ 2025
**����� �����������:** ~15 �����
**������:** ? **�������� ������**
