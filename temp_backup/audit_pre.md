# ?? ����-����� UI (��-0) - ����� Post-PROMPT#1

**����:** 2025-10-05 22:40  
**����:** ������������� ������� ��������� UI ����� �����������  
**������:** ? **�����ب�**

---

## ?? ��������� ������

### ������� ����
- ? `src/ui/main_window.py` - ������� ���� ���������� (776 �����)

### ������ ����������
- ? `src/ui/panels/panel_geometry.py` - ������ ��������� (500+ �����)
- ? `src/ui/panels/panel_pneumo.py` - ������ �������������
- ? `src/ui/panels/panel_modes.py` - ������ �������

### �������
- ? `src/ui/widgets/range_slider.py` - ������� � ����������
- ? `src/ui/widgets/knob.py` - �������� (������-������)
- ? `src/ui/accordion.py` - ��������� (������������, �� �� ������������)

### QML �����
- ? `assets/qml/main.qml` - ������� QML �����

---

## ?? ��������� ������

### 1. MainWindow (main_window.py)

**������� ���������:**

#### ������������ �������� (? ��� ����!)
```python
# ������ ~130-160
self.main_splitter = QSplitter(Qt.Orientation.Vertical)
self.main_splitter.setObjectName("MainSplitter")

# Top: 3D scene
self._qquick_widget  # QQuickWidget � main.qml

# Bottom: Charts (full width!)
self.chart_widget = ChartWidget(self)
```
**�����:** ? ������������ �������� ��� ����������

#### �������������� �������� (? ���!)
```python
# ������ ~153-159
central_container = QWidget()
central_layout = QHBoxLayout(central_container)

# ����������� �������� + ������� �� ��� QSplitter!
central_layout.addWidget(self.main_splitter, stretch=3)  # 75%
# ... ����� ����������� tab_widget, stretch=1  # 25%
```
**�����:** ? **��� ��������������� QSplitter** ����� left (scene+charts) � right (tabs)!  
**�����:** �������� � `QSplitter(Qt.Orientation.Horizontal)`

#### ������� (? ��� ����!)
```python
# ������ ~215-275
self.tab_widget = QTabWidget(self)
self.tab_widget.setObjectName("ParameterTabs")

# Tab 1: "���������" + QScrollArea ?
# Tab 2: "�������������" + QScrollArea ?
# Tab 3: "������ �������������" + QScrollArea ?
# Tab 4: "������������" (��������)
# Tab 5: "�������� ��������" (��������)
```
**�����:** ? ������� � �������� ���������� + QScrollArea ��� ����!

#### ������� (? �� �����!)
```python
# ������ ~148-149
self.chart_widget = ChartWidget(self)
self.main_splitter.addWidget(self.chart_widget)  # ����� ������������� ���������
```
**�����:** ? ������� ��� ����� �� ��� ������

---

### 2. GeometryPanel (panel_geometry.py)

**��������� �������� (������� - ������� ���������!):**

```python
# ������ ~139-167 - ���������� ��������� ��������:
self.bore_head_slider = RangeSlider(
    title="������� (����������� ������)"  # ? ���� ������
)

self.bore_rod_slider = RangeSlider(
    title="������� (�������� ������)"  # ? ���� ������
)

self.rod_diameter_slider = RangeSlider(
    title="������� �����"  # ? ��������
)

self.piston_rod_length_slider = RangeSlider(
    title="����� ����� ������"  # ? �������� (�� �������� �������������)
)

self.piston_thickness_slider = RangeSlider(
    title="������� ������"  # ? ��������
)
```

**����� ��������� (��-1):**
1. ? **������:** `bore_head_slider`, `bore_rod_slider`
2. ? **��������:** `cylinder_diameter_slider` (������ ������� ��������)
3. ? **��������:** `stroke_slider` (��� ������)
4. ? **��������:** `dead_gap_slider` (������ �����)
5. ? **��������:** `rod_diameter_slider`, `piston_thickness_slider`

**������� ��������� (�������):**

| �������� | ������� ������� | ������ ������� (��) | ��� | Decimals |
|----------|----------------|---------------------|-----|----------|
| wheelbase | ? � | ? � | 0.1 ? **0.001** | 1 ? **3** |
| track | ? � | ? � | 0.1 ? **0.001** | 1 ? **3** |
| frame_to_pivot | ? � | ? � | 0.05 ? **0.001** | 2 ? **3** |
| lever_length | ? � | ? � | 0.05 ? **0.001** | 2 ? **3** |
| rod_position | fraction (0-1) | ? OK | 0.05 ? **0.001** | 2 ? **3** |
| cylinder_length | ? � | ? � | 0.01 ? **0.001** | 2 ? **3** |
| bore_head | ? �� | **�** | 5.0 ? **0.001** | 0 ? **3** |
| bore_rod | ? �� | **�** | 5.0 ? **0.001** | 0 ? **3** |
| rod_diameter | ? �� | **�** | 2.5 ? **0.001** | 1 ? **3** |
| piston_rod_length | ? �� | **�** | 10.0 ? **0.001** | 0 ? **3** |
| piston_thickness | ? �� | **�** | 2.5 ? **0.001** | 1 ? **3** |

**�����:** ��� ��������� � ����������� ����� ��������� � �����!

---

### 3. PneumoPanel (panel_pneumo.py)

**������� �������� (�� ����):**

```python
# ����������� ��������:
- �������� �������: ? ���� �������� (Knob)
- ����������������� �������: ? ���� ��������
- ����������� ���������: ? ����
- �����-�����: ? ����������� (��������������/��������������)
- ������� ��������: ? ������� "������� �������� �������"
- ����� ��������� ������: ? �������
```

**����������� �������� (��-5):**

1. ? **���:** ������� "������������ ���/����"
2. ? **���:** ������� "������������ �������"
3. ? **���:** �������� "����� ��������, �"

---

### 4. ModesPanel (panel_modes.py)

**������� ��������:**

```python
# �������� �����������:
- ���������� ���������: ? RangeSlider, units="�"
- ���������� �������: ? RangeSlider, units="��"
- ���������� ����: ? RangeSlider, units="�"
- ���� �� ������: ? 4x RangeSlider (��, ��, ��, ��)
```

**�����:** ? �� � �������, ������� UI ��� ����

---

### 5. Accordion (accordion.py)

**������:**

```python
# ���� ������������ � src/ui/accordion.py
# �� �� ������������ � main_window.py!

class AccordionWidget(QScrollArea):
    """Accordion widget with multiple collapsible sections"""
    # ... ���������� ����
```

**�����:** ? ��������� �� ������������ (���� ������ ��� �����������)

---

## ? �������� ������ ��-0

### ��� ��� ���� (�� �������)
1. ? ������������ �������� (�����/�������)
2. ? ������� � �������� ����������
3. ? QScrollArea � ������ �������
4. ? ������� ����� �� ��� ������
5. ? ��������� �� ������������

### ��� ����� ��������/��������

#### ��-1: ��������� ��������
- ? ������ `bore_head`, `bore_rod` (���������� ��������)
- ? �������� `cyl_diam_m` (������ �������)
- ? �������� `stroke_m` (��� ������)
- ? �������� `dead_gap_m` (������ �����)
- ? ��� �����: ������� **�**, ��� **0.001**, decimals **3**

#### ��-2: ������� ���������
- ? ��� �������� ��������� ? **�**
- ? ��� ? **0.001 �**
- ? Decimals ? **3**
- ? �������� �������� (�� ? �)

#### ��-3: �������������� ��������
- ? **��������:** `QSplitter(Qt.Horizontal)` �����:
  - ����� �����: ������������ �������� (����� + �������)
  - ������ �����: QTabWidget (������)
- ? objectName: `"split_main_h"`
- ? ����������/�������������� ����� QSettings

#### ��-5: ������-��������
- ? �������� ������� "������������ ���/����"
- ? �������� ������� "������������ �������"
- ? �������� �������� "����� ��������, �" (�����, 0-100�, ������ 20�)

---

## ?? ������ ������ �������� (tree_pre.txt)

```
QMainWindow "PneumoStabSim"
??? QWidget central_container
?   ??? QHBoxLayout
?   ?   ??? QSplitter "MainSplitter" (Vertical) ? ? ��� ����
?   ?   ?   ??? QQuickWidget (3D scene)
?   ?   ?   ??? ChartWidget (graphics)
?   ?   ??? QTabWidget "ParameterTabs" ? ? ��� ����
?   ?       ??? QScrollArea "���������" ? ? ��� ����
?   ?       ?   ??? GeometryPanel
?   ?       ??? QScrollArea "�������������" ? ? ��� ����
?   ?       ?   ??? PneumoPanel
?   ?       ??? QScrollArea "������ �������������" ? ? ��� ����
?   ?       ?   ??? ModesPanel
?   ?       ??? QWidget "������������" (stub)
?   ?       ??? QWidget "�������� ��������" (stub)
??? QToolBar "�������"
??? QMenuBar
?   ??? QMenu "����"
?   ??? QMenu "���������"
?   ??? QMenu "���"
??? QStatusBar

MISSING: QSplitter(Horizontal) ����� left � right!
```

---

## ?? ��������� ��������� (������� ��������)

### ����
| �������� | �������� | ������� | �������� |
|----------|----------|---------|----------|
| wheelbase | 3.2 | � | 2.0 - 4.0 |
| track | 1.6 | � | 1.0 - 2.5 |

### ��������
| �������� | �������� | ������� | �������� |
|----------|----------|---------|----------|
| frame_to_pivot | 0.6 | � | 0.3 - 1.0 |
| lever_length | 0.8 | � | 0.5 - 1.5 |
| rod_position | 0.6 | fraction | 0.3 - 0.9 |

### ������� (������� ���������!)
| �������� | �������� | ������� | �������� | ������ |
|----------|----------|---------|----------|--------|
| cylinder_length | 0.5 | � | 0.3 - 0.8 | ? OK |
| bore_head | 80.0 | **��** ? | 50 - 150 | ? **������** |
| bore_rod | 80.0 | **��** ? | 50 - 150 | ? **������** |
| rod_diameter | 35.0 | **��** ? | 20 - 60 | ? **��������� � �** |
| piston_rod_length | 200.0 | **��** ? | 100 - 500 | ? **��������� � �** |
| piston_thickness | 25.0 | **��** ? | 10 - 50 | ? **��������� � �** |

---

## ?? ���������� � ��-1

### ����� ��� ���������
1. `src/ui/panels/panel_geometry.py` (������ bore_head/bore_rod, �������� cyl_diam/stroke/dead_gap)
2. `tests/ui/test_geometry_ui.py` (����� �� ����� ���������)

### ��������� ���������
- ? ������: 2 �������� (bore_head, bore_rod)
- ? ��������: 3 �������� (cyl_diam_m, stroke_m, dead_gap_m)
- ? ��������: ���/decimals ��� ���� �������� ����������

---

**����� ��������:** 2025-10-05 22:50  
**��������� ���:** ��-1 (���������� ���������� ��������)  
**���������:**
- `reports/ui/audit_pre.md` (���� ����)
- `artifacts/ui/tree_pre.txt` (����� ������)
- `artifacts/ui/widget_tree_pre.json` (����� ������)
