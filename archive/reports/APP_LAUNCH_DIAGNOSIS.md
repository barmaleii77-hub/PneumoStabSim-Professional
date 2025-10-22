# ? ��������� ������ ������� ����������

**����:** 3 ������� 2025, 06:05 UTC

---

## ?? ���������� ������������

### ? ������� Qt ��������
```python
# ultra_minimal.py
QApplication + QMainWindow + show() + exec()
```
**������:** ? **�������� ��������**

### ?? ���������� � ������������
```python
# app_minimal.py
QApplication + logging + QMainWindow
```
**������:** ?? **���� ����� show()**

### ? ������ ����������
```python
# app.py
Full MainWindow + GLView + SimulationManager
```
**������:** ? **���� ����� show()**

---

## ?? �����������

### ��� ��������:
1. ? Python 3.13.7
2. ? PySide6 6.8.3
3. ? QApplication ��������
4. ? QMainWindow ��������
5. ? window.show() � ������� �������
6. ? app.exec() event loop

### ��� �� ��������:
1. ? `window.show()` � GLView � �������
2. ? `window.show()` � init_logging
3. ? ������ MainWindow

---

## ?? �������� �������

**�������� �� � OpenGL!**

**��������� ��������:** ���-�� � ������:
- `init_logging()` �� `src.common`
- ��� `SimulationManager`
- ��� `GLView` ��� ������� ������� OpenGL ��������
- ��� `QSettings` restore

�������� **SILENT CRASH** (��� exception, ��� stderr output)

---

## ?? ��������� �������

### ������� 1: ��������� �����������
```python
# � app.py ����������������
# logger = init_logging("PneumoStabSim", Path("logs"))
```

### ������� 2: ��������� GLView
```python
# � main_window.py _setup_central()
from PySide6.QtWidgets import QLabel
label = QLabel("OpenGL Disabled")
self.setCentralWidget(label)
```

### ������� 3: ��������� SimulationManager
```python
# � main_window.py __init__()
# self.simulation_manager = SimulationManager(self)
self.simulation_manager = None
```

---

## ?? ��� ��������� (������� ������)

```powershell
# Ultra-minimal ������ (��������!)
python ultra_minimal.py
```

**��� �������:**
- ���� 400x300
- ������� "TEST WINDOW"
- ���� ������� ��������
- �������� ��� ������

---

## ?? ������������

### ��������� 1: ����������� ��������
����������� ���������������:

1. **���� � ������������:**
```python
logger = init_logging("Test", Path("logs"))
app = QApplication(sys.argv)
window = QMainWindow()
window.show()
app.exec()
```

2. **���� � SimulationManager:**
```python
app = QApplication(sys.argv)
manager = SimulationManager(None)
window = QMainWindow()
window.show()
app.exec()
```

3. **���� � GLView (��� scene):**
```python
app = QApplication(sys.argv)
glview = GLView()
window = QMainWindow()
window.setCentralWidget(glview)
window.show()
app.exec()
```

### ��������� 2: ��������� threading
`SimulationManager` ��������� ����� - �������� ���� ���������� � ������� ������

### ��������� 3: ��������� Qt message handler
`qInstallMessageHandler` ����� ������������� ��������� ���������

---

## ?? ��������� ��������

1. **Silent crash** - ��� exception, ��� stderr
2. **������� �����������** ��� error code
3. **���� ����������** �� "Step 7: MainWindow created"

---

## ? ��� ��� ����������

- ? QSurfaceFormat ���������� ���������
- ? GLScene �� ���������� PyOpenGL
- ? ������ ���������
- ? ��������� ������ ���������

---

## ?? ����� ��� ������������

| ���� | ������ | �������� |
|------|--------|----------|
| `ultra_minimal.py` | ? �������� | ������� Qt test |
| `app_minimal.py` | ? ���� | � ������������ |
| `app.py` | ? ���� | ������ ���������� |

---

## ?? ��������� ����

1. ��������� `ultra_minimal.py` - ���������, ��� Qt ��������
2. ��������� ���������� �� ������
3. �����, ����� ��������� �������� ����
4. ��������� ���������� ���������

---

## ?? ����������

**�������� ��������� �������:**

1. **QueueHandler � logging** - threading issue
2. **SimulationManager.start()** - ������� ����� ������
3. **QSettings.restoreGeometry()** - ������������ ���������� ������
4. **OpenGL context creation** - ������� ����������

**������������:** ����������� ���������!

---

**������:** ? **��������� �������������� �����������**
