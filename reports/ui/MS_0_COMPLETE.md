# ?? ��-0: ����-����� �����ب�

**����:** 2025-10-05 23:00  
**������:** ? **�����ب�**  
**��������� ���:** ��-1 (���������� ���������� ��������)

---

## ? ��� �������

### ��������� �������
- ? `reports/ui/audit_pre.md` - ��������� ����� UI
- ? `artifacts/ui/tree_pre.txt` - ������ �������� (��������� ������)
- ?? `artifacts/ui/widget_tree_pre.json` - �� ������ (������ �������� �������)

### ������������������ �����
- ? `src/ui/main_window.py` (776 �����)
- ? `src/ui/panels/panel_geometry.py` (500+ �����)
- ? `src/ui/widgets/range_slider.py`
- ? `src/ui/accordion.py` (�� ������������)

---

## ?? �������� �������

### 1. ������������ ��������: ? ��� ����������

```python
# main_window.py, ������ ~130-160
self.main_splitter = QSplitter(Qt.Orientation.Vertical)
self.main_splitter.addWidget(self._qquick_widget)  # 3D scene
self.main_splitter.addWidget(self.chart_widget)    # Charts
```

**�����:** �� ������� ��������� � ��-3!

### 2. �������������� ��������: ? �����������

```python
# main_window.py, ������ ~153-159
central_layout = QHBoxLayout(central_container)
central_layout.addWidget(self.main_splitter, stretch=3)  # 75%
# ... �����: central_layout.addWidget(self.tab_widget, stretch=1)  # 25%
```

**�����:** ��������� QSplitter(Horizontal) � ��-3!

### 3. �������: ? ��� �����������

```python
# main_window.py, ������ ~215-275
self.tab_widget = QTabWidget()
# 5 ������� � �������� ����������
# Tab 1-3: QScrollArea ?
# Tab 4-5: ��������
```

**�����:** ��������� ������� ���������!

### 4. ��������� ��������: ? ������� ���������

**������� ��������� (panel_geometry.py):**
```python
bore_head_slider    # 50-150 �� ? ������
bore_rod_slider     # 50-150 �� ? ������
rod_diameter_slider # 20-60 �� ? 0.020-0.060 �
piston_rod_length_slider  # 100-500 �� ? 0.100-0.500 �
piston_thickness_slider   # 10-50 �� ? 0.010-0.050 �
```

**����� ��������:**
```python
cyl_diam_m   # 0.030-0.150 � (������ �������)
stroke_m     # 0.100-0.500 � (��� ������)
dead_gap_m   # 0.000-0.020 � (������ �����)
```

### 5. ������� ���������: ? ����������� � ��

| �������� | ������ | ����� |
|----------|--------|-------|
| wheelbase | �, ��� 0.1, dec=1 | �, ��� **0.001**, dec=**3** |
| track | �, ��� 0.1, dec=1 | �, ��� **0.001**, dec=**3** |
| bore_head | **��**, ��� 5.0 | **������** |
| bore_rod | **��**, ��� 5.0 | **������** |
| rod_diameter | **��**, ��� 2.5 | **�**, ��� **0.001**, dec=**3** |
| piston_rod_length | **��**, ��� 10.0 | **�**, ��� **0.001**, dec=**3** |
| piston_thickness | **��**, ��� 2.5 | **�**, ��� **0.001**, dec=**3** |

**�����:** 5 ���������� ����� �������������� �� ? �!

### 6. ������-��������: ? �����������

**������������� �������� (panel_pneumo.py):**
- ? ������� "������������ ���/����"
- ? ������� "������������ �������"
- ? �������� "����� ��������, �" (�����, 0-100, ������ 20)

**�����:** ��������� 3 ����� �������� � ��-5!

### 7. ���������: ? �� ������������

```python
# src/ui/accordion.py - ���� ����������
class AccordionWidget(QScrollArea):
    """Accordion widget with multiple collapsible sections"""
    # ... ���������� ����
```

```python
# src/ui/main_window.py - �� �������������
# Accordion �� ������������ ����� � ����
```

**�����:** ? ��������� �� ������������ (���� ����������)!

---

## ?? ������� ����������

### ��-1: ��������� �������� ? �� �����
- [ ] ������ bore_head_slider, bore_rod_slider
- [ ] �������� cyl_diam_m (������ �������)
- [ ] �������� stroke_m (��� ������)
- [ ] �������� dead_gap_m (������ �����)
- [ ] ��� �����: �, ��� 0.001, decimals 3
- [ ] �����: test_geometry_ui.py

### ��-2: ������� �� ? �� �����
- [ ] rod_diameter: �� ? �
- [ ] piston_rod_length: �� ? �
- [ ] piston_thickness: �� ? �
- [ ] ��� ��������: ��� 0.001, decimals 3
- [ ] �������� �������� (�� ? �)
- [ ] �����: test_steps_units.py

### ��-3: �������������� �������� ? �� �����
- [ ] ������� QSplitter(Horizontal)
- [ ] objectName "split_main_h"
- [ ] ����� �����: MainSplitter (vertical)
- [ ] ������ �����: ParameterTabs
- [ ] ����������/�������������� ����� QSettings
- [ ] �����: test_layout_splitters.py

### ��-4: �������/��������� ? ��� ����
- [x] ������� ��������� �������
- [x] QScrollArea � ������ �������
- [x] ���������� �����������
- [ ] �����: test_tabs_scroll_ru.py

### ��-5: ������-�������� ? �� �����
- [ ] ������� "������������ ���/����"
- [ ] ������� "������������ �������"
- [ ] �������� "����� ��������, �"
- [ ] �����: test_pneumo_ui.py

### ��-6: �������/����������� ?? �������� ����
- [x] _on_geometry_changed ����������
- [x] geometry_changed ������ ���������
- [ ] ����������� ��������� � logs/ui/ui_params.log
- [ ] ������� ui_state.json
- [ ] �����: test_signals_logging.py

### ��-7: ��������� �������� ? �� �����
- [ ] ������� ���� ���� UI-����������
- [ ] ����� summary_ui_post.md
- [ ] �����: test_final_ui_sweep.py

### ��-8: ����-����� ? �� �����
- [ ] audit_post.md
- [ ] tree_post.txt
- [ ] widget_tree_post.json
- [ ] diff_prompt_all_microsteps.patch
- [ ] Git commit + push

---

## ?? ���������� ��-0

### ������ ����������������
- main_window.py: 776 �����
- panel_geometry.py: 500+ �����
- range_slider.py: 400+ �����
- accordion.py: 200+ �����

### ���������� �������
- ����� ��������: 11
- � �� (�): 6
- � ��: 5 ?
- ������� ���������: 8

### ��������� UI
- �������: 5 (3 �������� + 2 ��������)
- QScrollArea: 3 ?
- ����������: 1 (vertical) ?, 1 (horizontal) ?
- �����������: 0 ?

---

## ?? ���������� � ��-1

### ���������� �����
1. `src/ui/panels/panel_geometry.py` - ������� ����
2. `tests/ui/test_geometry_ui.py` - ����� ���� ������

### ��������� ���������
- ? �������: 2 �������� (bore_head, bore_rod)
- ? ��������: 3 �������� (cyl_diam_m, stroke_m, dead_gap_m)
- ? ��������: 5 ��������� (�� ? �)
- ? ��������: _set_default_values(), _connect_signals()

### ����������� ��������
- ? RangeSlider ������ �����
- ? QGroupBox ����������� ������
- ? ������� parameter_changed, geometry_updated ������

---

## ?? ��������� ��������

1. **��-1** (���������):
   - ������������� `panel_geometry.py`
   - ������ bore_head/bore_rod
   - �������� cyl_diam_m/stroke_m/dead_gap_m
   - ������� �����

2. **��-2** (����� ��-1):
   - �������������� �� ? �
   - �������� ���/decimals
   - ����������� �������

3. **��-3** (����� ��-2):
   - �������� �������������� ��������
   - QSettings ��� ����������

---

**����� ��-0 ��������:** 2025-10-05 23:00  
**����� ����������:** 20 �����  
**���������� � ��-1:** ? 100%  

**���������:**
- ? `reports/ui/audit_pre.md`
- ? `artifacts/ui/tree_pre.txt`
- ?? `artifacts/ui/widget_tree_pre.json` (�� ������ ��-�� ������)

?? **����� ���������� � ��-1!**
