# ?? �������� ���� �� ������� �������� � ����������� �������

**����:** 3 ������ 2025
**������:** "� �� ���� ������������� �����"

---

## ? ������ �����������

### 1. **QML ���� (assets/qml/main.qml)** ? �������

**��������:**
```
Loading: C:\Users\User.GPC-01\source\repos\barmaleii77-hub\NewRepo2\assets\qml\main.qml
Exists: True
Status: Status.Ready
Root: QQuick3DViewport_QML_0
```

**�������� ����������:**
```qml
Model {
    id: sphere
    // ...
    NumberAnimation on eulerRotation.y {
        from: 0
        to: 360
        duration: 6000
        loops: Animation.Infinite
    }
}
```

? **�������� ��� - �������� �������**

---

### 2. **����������� QML � MainWindow** ? �������

**��� (main_window.py:124-157):**
```python
def _setup_central(self):
    # Create QQuickWidget for Qt Quick 3D content
    self._qquick_widget = QQuickWidget(self)

    # Set resize mode
    self._qquick_widget.setResizeMode(
        QQuickWidget.ResizeMode.SizeRootObjectToView
    )

    # Load QML file
    qml_path = Path("assets/qml/main.qml")
    self._qquick_widget.setSource(QUrl.fromLocalFile(...))

    # Set as central widget
    self.setCentralWidget(self._qquick_widget)
```

? **�������� ��� - QML ���������**

---

### 3. **��������� � ����������** ? �������

**��� (main_window.py:456-469):**
```python
# Render timer (UI thread ~60 FPS)
self.render_timer = QTimer(self)
self.render_timer.timeout.connect(self._update_render)
self.render_timer.start(16)  # ~60 FPS

@Slot()
def _update_render(self):
    if not self._qml_root_object:
        return

    # Update QML properties
    self._qml_root_object.setProperty("simulationText", sim_text)
    self._qml_root_object.setProperty("fpsText", fps_text)
```

? **�������� ��� - ������ �������**

---

## ?? ��������� ��������

### �������� #1: **����������� ������ �������� ��������**

**���-������ ��������� ����� ������������ �������:**
```python
# line 111-177: _setup_central() - ��������� QQuickWidget
# line 180-230: _setup_docks() - ��������� 5 dock panels
```

**������:**
- Geometry (Left)
- Pneumatics (Left)
- Charts (Right)
- Modes (Right)
- Road (Bottom)

**���������:** ����������� ������ ����� ���� **��������� ������** ��������!

---

### �������� #2: **����������� ������ �� ����������� ���������**

**��� (line 154):**
```python
self._qquick_widget.setMinimumSize(800, 600)
```

**��������:** ���� dock panels �������� ��� �����, ����������� ������ ��������� �� �������� ��� ����������.

---

### �������� #3: **������ ��� ��������� � �����**

**QML (main.qml:11):**
```qml
environment: SceneEnvironment {
    backgroundMode: SceneEnvironment.Color
    clearColor: "#101418"  // ����� ������ ����
}
```

**��������:** �� ������ ���� ���������� ������ ����� ����� ���� �� �����.

---

## ??? �����������

### ����������� #1: **��������� ��������� ������������ �������**

**������� A: ������ ������ �� ���������**
```python
# � _setup_docks():
self.geometry_dock.hide()
self.pneumo_dock.hide()
# ... etc
```

**������� B: ���������� ��������� splitter**
```python
# ������������ QSplitter ��� ���������� �����������
```

**������� C: ������� ����������� ������ ������**
```python
self._qquick_widget.setMinimumSize(1200, 800)
```

---

### ����������� #2: **�������� ���� ���� ��� ���������**

**����: assets/qml/main.qml**
```qml
environment: SceneEnvironment {
    backgroundMode: SceneEnvironment.Color
    clearColor: "#2a2a3e"  // ������� ��� ���������
    // ���
    clearColor: "#4a4a6e"  // ��� �������
}
```

---

### ����������� #3: **�������� ��������� ��������**

**�������� � main.qml:**
```qml
// Overlay indicator
Rectangle {
    anchors.centerIn: parent
    width: 100; height: 100
    color: "transparent"
    border.color: "#ff6b35"
    border.width: 2
    radius: 50

    Text {
        anchors.centerIn: parent
        text: "3D"
        color: "#ffffff"
        font.pixelSize: 24
    }

    RotationAnimation on rotation {
        from: 0; to: 360
        duration: 3000
        loops: Animation.Infinite
    }
}
```

---

## ?? �������� �����������

| ��������� | ������ | �������� | �������� |
|-----------|--------|----------|----------|
| **QML ����** | ? ������� | ? ��� | - |
| **��������** | ? ���������� | ? ��� | - |
| **�����������** | ? ������� | ? ��� | - |
| **���������** | ? ������� | ? ��� | - |
| **���������** | ?? �������� ����� | - | ������ ����������� |
| **��������** | ?? ������ | - | ������ ��� |

---

## ? ������������

### ����������� ��������:

1. **��������� ��������� �������:**
   - ������� ��� dock-������ (View menu)
   - ���������, ����� �� ����������� ������

2. **��������� ��������:**
   - �������� `clearColor` � main.qml �� ����� �������

3. **�������� debug ���������:**
   - �������� ����������� ������� � overlay

### ��� ��� ��������:

```python
# � app.py ��� test �������:
window.geometry_dock.hide()
window.pneumo_dock.hide()
window.charts_dock.hide()
window.modes_dock.hide()
window.road_dock.hide()
```

��� ������ �������� ����������� ������ � ���������.

---

## ?? ����������

**�������� � ����������� ������� �� ����������** ?

**��������:** ������ ����� **����������** - ����������� ������ �������� �������� ��� ��������� � �����.

**�������:** ������ ������ ��� �������� ���� ���� QML.

---

**������:** ? **�������� ��������, �� ����� ���� �� �����**
