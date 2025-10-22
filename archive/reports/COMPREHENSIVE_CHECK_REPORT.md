# ?? ������ �������� ������� - ��������� ��������

**���� ��������:** 3 ������� 2025
**������:** ? **������� ����������� ������**

---

## ? ����������� ��������

### 1. ���������� ��� OpenGL �� ���˨�

**�����, ������� ������ ���� ������� �������� �������� �� Qt Quick 3D:**

- ? `src/ui/gl_view.py` - **�Ѩ �٨ ����������** (330+ ����� OpenGL ����)
- ? `src/ui/gl_scene.py` - stub ������, �� ������ ���� �������
- ? �������� `src/ui/hud.py` - ���� ���������� QPainter ������ OpenGL

**������ ��������:**
- ������� OpenGL ������������ (QOpenGLWidget, QOpenGLFunctions)
- ����� �������� ��������� � Qt Quick RHI
- ������ � ����������� ��� ������

**��������:** ������� ��� �����

---

### 2. Crash � `_reset_ui_layout()` ��-�� None docks

**����:** `src/ui/main_window.py`
**������:** ~540

```python
def _reset_ui_layout(self):
    for dock in [self.geometry_dock, self.pneumo_dock, self.charts_dock,
                 self.modes_dock, self.road_dock]:
        dock.show()  # ? CRASH! dock is None
```

**��������:**
- ��� ���� ����������� � `None` � `_setup_docks()`
- ����� `.show()` �� `None` ? `AttributeError`

**�����������:**
```python
def _reset_ui_layout(self):
    for dock in [self.geometry_dock, self.pneumo_dock, self.charts_dock,
                 self.modes_dock, self.road_dock]:
        if dock:  # ? �������� ��������
            dock.show()
    self.status_bar.showMessage("UI layout reset")
```

---

### 3. View Menu ���������� � None docks

**����:** `src/ui/main_window.py`
**�����:** `_setup_menus()`

```python
view_menu = menubar.addMenu("View")
for dock, title in [
    (self.geometry_dock, "Geometry"),  # ? None
    (self.pneumo_dock, "Pneumatics"),  # ? None
    ...
]:
    act = QAction(title, self, checkable=True, checked=True)
    act.toggled.connect(lambda checked, d=dock: d.setVisible(checked))  # ? CRASH!
```

**��������:**
- Lambda ����������� `None`
- ��� toggle ? `d.setVisible(checked)` ? `AttributeError`

**�����������:**
```python
view_menu = menubar.addMenu("View")
for dock, title in [
    (self.geometry_dock, "Geometry"),
    (self.pneumo_dock, "Pneumatics"),
    (self.charts_dock, "Charts"),
    (self.modes_dock, "Modes"),
    (self.road_dock, "Road Profiles")
]:
    if dock:  # ? �������� ��������
        act = QAction(title, self, checkable=True, checked=True)
        act.toggled.connect(lambda checked, d=dock: d.setVisible(checked))
        view_menu.addAction(act)
```

**���** ������ �� ��������� View menu ���� ���� ���������.

---

## ?? ������� ��������

### 4. �������� ��������: �������� �������� ����� � OpenGL

**�����:**
- `test_p9_opengl.py` - ����� ��� OpenGL (��������)
- `test_with_surface_format.py` - OpenGL �����
- `check_opengl.py` - �������� OpenGL

**��������:**
- ������������� � `*.old.py` ��� �������
- ������� ����� ����� ��� Qt Quick 3D

---

### 5. ������������ �� ���������

**�����:**
- `P9_P10_REPORT.md` - ��������� OpenGL ������ (�������)
- `P10_STATUS_COMPLETE.md` - ��� HUD ������ OpenGL

**��������:**
- �������� ����������: "DEPRECATED: Migrated to Qt Quick 3D"
- ������� ����� `QTQUICK3D_ARCHITECTURE.md`

---

### 6. ����������� ���������� simulation ? QML

**��������:**
� `_update_render()` ����������� ������ 2 ��������:
```python
self._qml_root_object.setProperty("simulationText", sim_text)
self._qml_root_object.setProperty("fpsText", fps_text)
```

**�����������:**
- ���������� ������ (distance, pitch, yaw)
- �������� �� ������ ������ ���������
- ������������ ����������

**��������:**
- ��������� QML properties
- �������� ������ ���������� 3D ��������

---

## ? ��� �������� ���������

1. ? `app.py` - ��������� ������������� RHI backend
2. ? `assets/qml/main.qml` - �������� Qt Quick 3D �����
3. ? `MainWindow._setup_central()` - ��������� ���������� QQuickView
4. ? `MainWindow.showEvent()` - SimulationManager �������� ����� show()
5. ? ��� �������� OpenGL � MainWindow
6. ? Qt Quick 3D ����������� �����������

---

## ?? ���� �����������

### ��������� 1 (��������):
1. ? ������� `src/ui/gl_view.py`
2. ? ������� `src/ui/gl_scene.py`
3. ? ��������� `_reset_ui_layout()` - �������� �� None
4. ? ��������� View menu - �������� �� None

### ��������� 2 (�����):
5. �������������/������� OpenGL �����
6. �������� DEPRECATED ������� � ������ ������
7. ������� `QTQUICK3D_ARCHITECTURE.md`

### ��������� 3 (����������):
8. ��������� QML integration
9. �������� ����� ��� Qt Quick 3D
10. ��������������� QML API

---

## ?? �������������� �����������

�������� �������������� ����������� ����������� �������...

---

**������ ����� �����������:** ����� ��������� ����� ���������� ���������
