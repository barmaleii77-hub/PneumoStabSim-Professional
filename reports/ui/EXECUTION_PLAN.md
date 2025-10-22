# PROMPT #1 EXECUTION PLAN

## STATUS: AUDIT COMPLETE ?

### ��� 0: ������˨���� �������� ?
- ? ������� �����: reports/ui/, artifacts/ui/
- ? �����: reports/ui/ui_audit_pre.md
- ? JSON ������: artifacts/ui/widget_tree_pre.json
- ? �����������: reports/ui/ui_prompt1.log

### ��������� ��������:
1. **����:** ��� ������ �� ���������� ? ����� �������
2. **LAYOUT:** Charts � ������ ���� ? ������ ���� ����� �� ��� ������
3. **SCROLL:** ��� QScrollArea � ��������
4. **COMBOBOXES:** ���� ���������� �������
5. **ACCORDIONS:** ? ��� (������!)

### ��������� ���� (�� ����������):

## ��� 1: ���������������� �������� ����
**����:** `src/ui/main_window.py`

### 1.1 ������� ������������ ��������
```python
# ����: docks �����/������
# �����: QSplitter(Qt.Vertical)
#   - ����: 3D �����
#   - ���: ������� (�� ��� ������)
```

### 1.2 ����������� panels � QTabWidget
```python
# ������� QTabWidget ������ (������ �����):
tab_widget = QTabWidget()
tab_widget.addTab(scroll_geometry, "���������")
tab_widget.addTab(scroll_pneumo, "�������������")
tab_widget.addTab(scroll_modes, "������ �������������")
tab_widget.addTab(scroll_viz, "������������")
tab_widget.addTab(scroll_road, "�������� ��������")
```

### 1.3 �������� ������ ������ � QScrollArea
```python
scroll_area = QScrollArea()
scroll_area.setWidgetResizable(True)
scroll_area.setWidget(panel)
```

## ��� 2: ������ �����������
**�����:** ��� ������ + main_window.py

### 2.1 ��������� ����/�����
- "Geometry" ? "���������"
- "Pneumatics" ? "�������������"
- "Charts" ? "�������"
- "Simulation & Modes" ? "������ �������������"
- "Road Profiles" ? "�������� ��������"

### 2.2 ����
- "File" ? "����"
- "Road" ? "������" (������ ��� �������������)
- "Parameters" ? "���������"
- "View" ? "���"

### 2.3 Toolbar
- "Start" ? "�����"
- "Stop" ? "����"
- "Pause" ? "�����"
- "Reset" ? "�����"

### 2.4 Status Bar
- "Sim Time" ? "�����"
- "Steps" ? "����"
- "Physics FPS" ? "FPS ������"
- "RT" ? "��" (�������� �����)
- "Queue" ? "�������"

### 2.5 ������� ���������
- mm (����������)
- m (�����)
- bar (����)
- � (�������)
- ��? (���������� ����������)

## ��� 3: ������� ����� �� ��� ������
**����:** `src/ui/main_window.py`

```python
# ������� ������������ ��������:
splitter = QSplitter(Qt.Vertical)
splitter.addWidget(qquick_widget)  # 3D �����
splitter.addWidget(chart_widget)   # �������
splitter.setStretchFactor(0, 3)    # ����� 60%
splitter.setStretchFactor(1, 2)    # ������� 40%
```

## ��� 4: ������ ROAD PANEL
**�����:** `src/ui/main_window.py`, `src/ui/panels/panel_road.py`

- �� ��������� RoadPanel � �������
- ������� �������� "�������� ��������" (������ �������)
- ������ ���� "Road" ��� �������������

## ��� 5: ����������� � ��������
**����� ����:** `src/ui/ui_logger.py`

```python
# ���������� ������ ��������� ��������:
# timestamp | widget_path | objectName | label | old_value | new_value
```

## ��� 6: ���������
**����:** `tests/ui/test_ui_layout.py`

```python
def test_tabs_exist(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    # ��������� ������� �������
    tab_widget = window.findChild(QTabWidget)
    assert tab_widget is not None
    assert tab_widget.count() == 5
    assert tab_widget.tabText(0) == "���������"
    # ...
```

## ��� 7: ������������������ �����
- ��������� ����� ? `ui_audit_post.md`
- ���� ������ ? `widget_tree_post.json`
- ������� ����� ? `summary_prompt1.md`

## ��� 8: ����������
```bash
git checkout -b feature/ui-rus-tabs-layout
git add .
git commit -m "UI: Russian labels, tabs layout, charts bottom; no accordions; scroll areas; value tracing (PROMPT #1)"
git push origin feature/ui-rus-tabs-layout
```

## �������� ����������:
? ��� ������ � �������� (QTabWidget)
? ������� ����� �� ��� ������ (������������ splitter)
? ��� �����������
? ���� UI �� �������
? ��������/�������� ���������
? ���������� ��� ������������
? ��������� ������
? ������ � ���� �������
? ������/��� ���������

## ������� ������:
**STEP:** 0 (Audit) COMPLETE ?
**NEXT:** Step 1 (Restructure main window) ? READY TO START

---
**����� ������:** 2025-10-05 19:00
**����� ��������:** 2025-10-05 19:05
