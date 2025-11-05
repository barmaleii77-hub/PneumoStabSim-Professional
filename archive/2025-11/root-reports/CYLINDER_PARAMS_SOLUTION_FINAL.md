# ✅ ФИНАЛЬНОЕ РЕШЕНИЕ: Параметры цилиндра Python↔QML

**Дата:** 10 января 2026
**Статус:** ✅ **ИСПРАВЛЕНО И ГОТОВО К ТЕСТИРОВАНИЮ**

---

## 🎯 ЧТО СДЕЛАНО

### 1. Добавлены QML свойства для параметров цилиндра

**Файл:** `assets/qml/main.qml`

**Добавлено:**
```qml
// ✅ НОВЫЕ СВОЙСТВА С СУФФИКСОМ M (основные!)
property real userCylDiamM: 80           // мм - диаметр цилиндра
property real userStrokeM: 300           // мм - ход поршня
property real userDeadGapM: 5            // мм - мертвый зазор
property real userRodDiameterM: 35       // мм - диаметр штока
property real userPistonRodLengthM: 200  // мм - длина штока поршня
property real userPistonThicknessM: 25   // мм - толщина поршня
```

### 2. Обновлена функция обработки геометрии

**Файл:** `assets/qml/main.qml` → `applyGeometryUpdates()`

**Добавлено:**
```qml
// Обработка cylDiamM
if (params.cylDiamM !== undefined) {
    userCylDiamM = params.cylDiamM
    userBoreHead = params.cylDiamM  // Обратная совместимость
    userBoreRod = params.cylDiamM
}

// Обработка rodDiameterM
if (params.rodDiameterM !== undefined) {
    userRodDiameterM = params.rodDiameterM
    userRodDiameter = params.rodDiameterM  // Обратная совместимость
}

// ... и т.д. для всех параметров
```

### 3. Исправлен обработчик в Python

**Файл:** `src/ui/main_window.py` → `_on_geometry_changed_qml()`

**Изменено:** Вместо вызова `updateGeometry()` используется **прямая установка свойств**:

```python
# Параметры цилиндра с суффиксом M
if 'cylDiamM' in geometry_params:
    value = float(geometry_params['cylDiamM'])
    self._qml_root_object.setProperty("userCylDiamM", value)
    self._qml_root_object.setProperty("userBoreHead", value)  # Совместимость
    self._qml_root_object.setProperty("userBoreRod", value)
    print(f"   ✅ userCylDiamM = {value} мм")

# ... аналогично для остальных параметров ...

# Принудительное обновление виджета
if self._qquick_widget:
    self._qquick_widget.update()
```

---

## 🧪 КАК ПРОТЕСТИРОВАТЬ

### Вариант 1: Ручное тестирование (РЕКОМЕНДУЕТСЯ)

**Шаги:**

1. **Запустите приложение:**
   ```powershell
   py app.py
   ```

2. **Откройте вкладку "Геометрия"**

3. **Измените слайдер "Диаметр цилиндра":**
   - Подвиньте слайдер с 80мм на 90мм
   - Посмотрите на 3D сцену

4. **ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:**
   - ✅ Цилиндры должны стать **толще**
   - ✅ В консоли должно появиться:
     ```
     🔧 Устанавливаем свойства напрямую в QML...
        ✅ userCylDiamM = 90.0 мм
     📊 Статус: Геометрия успешно обновлена
     ```

5. **Проверьте другие параметры:**
   - Диаметр штока (должен изменить толщину штоков)
   - Толщина поршня (должна изменить размер поршней)
   - Длина штока поршня (должна изменить расстояние от поршня до шарнира)

---

### Вариант 2: Автоматический тест (С ЗАДЕРЖКАМИ)

**Создайте файл `test_cylinder_visual.py`:**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Визуальный тест параметров цилиндра
Проверяет обновление через визуальные изменения
"""
import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

print("🔬 ВИЗУАЛЬНЫЙ ТЕСТ: Параметры цилиндра")

from src.ui.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow(use_qml_3d=True)
window.show()

def test_sequence():
    print("\n⏳ Начало теста...")
    time.sleep(2)  # Даём время на загрузку QML

    geometry_panel = window.geometry_panel
    qml_root = window._qml_root_object

    if not qml_root:
        print("❌ QML недоступен!")
        QTimer.singleShot(1000, app.quit)
        return

    print("\n" + "=" * 60)
    print("ТЕСТ 1: Диаметр цилиндра 80мм → 100мм")
    print("=" * 60)

    # Читаем начальное значение
    initial = qml_root.property("userCylDiamM")
    print(f"Начальное значение: {initial} мм")

    # Изменяем слайдер
    geometry_panel.cyl_diam_m_slider.value_spinbox.setValue(0.100)  # 100мм

    # Ждём обработки
    time.sleep(0.5)
    QApplication.processEvents()

    # Читаем новое значение
    updated = qml_root.property("userCylDiamM")
    print(f"Новое значение: {updated} мм")

    if abs(updated - 100.0) < 0.1:
        print("✅ ТЕСТ ПРОЙДЕН: Диаметр обновился!")
    else:
        print(f"❌ ТЕСТ ПРОВАЛЕН: Ожидалось 100мм, получено {updated}мм")

    print("\n👀 ВИЗУАЛЬНО ПРОВЕРЬТЕ: Цилиндры должны стать толще!")
    print("⏳ Закрытие через 15 секунд...")

    QTimer.singleShot(15000, app.quit)

QTimer.singleShot(2000, test_sequence)
sys.exit(app.exec())
```

**Запуск:**
```powershell
py test_cylinder_visual.py
```

---

## 📊 СТАТУС ПАРАМЕТРОВ

| Параметр Python | QML свойство | Визуальный эффект | Статус |
|-----------------|--------------|-------------------|--------|
| `cyl_diam_m` | `userCylDiamM` | Толщина цилиндра | ✅ |
| `rod_diameter_m` | `userRodDiameterM` | Толщина штоков | ✅ |
| `piston_thickness_m` | `userPistonThicknessM` | Высота поршней | ✅ |
| `piston_rod_length_m` | `userPistonRodLengthM` | Длина штоков поршня | ✅ |
| `stroke_m` | `userStrokeM` | (Не используется визуально) | ✅ |
| `dead_gap_m` | `userDeadGapM` | (Не используется визуально) | ✅ |

---

## 🔍 ДИАГНОСТИКА ПРОБЛЕМ

### Если параметры НЕ ОБНОВЛЯЮТСЯ:

**1. Проверьте консоль при изменении слайдера:**

Должно быть:
```
🔺 MainWindow: Получен сигнал geometry_changed от панели
   Параметры (15): ['frameLength', 'cylDiamM', ...]
🔧 Устанавливаем свойства напрямую в QML...
   ✅ userCylDiamM = 90.0 мм
```

Если этого НЕТ:
- ❌ Сигнал `geometry_changed` не подключен
- **Решение:** Проверить `_wire_panel_signals()` в `main_window.py`

**2. Проверьте, что используется `main.qml`, а не `main_simple.qml`:**

```python
# В main_window.py должно быть:
qml_path = Path("assets/qml/main.qml")  # ✅ ПРАВИЛЬНО

# НЕ должно быть:
qml_path = Path("assets/qml/main_simple.qml")  # ❌ НЕПРАВИЛЬНО (нет 3D)
```

**3. Проверьте QML свойства вручную:**

Добавьте в QML временный Text для отладки:
```qml
Text {
    anchors.top: parent.top
    anchors.right: parent.right
    text: "CylDiam: " + userCylDiamM + "мм"
    color: "#00ff00"
    font.pixelSize: 20
    z: 1000
}
```

Если значение **НЕ ИЗМЕНЯЕТСЯ** при движении слайдера:
- ❌ Свойства не обновляются
- **Решение:** Проверить `_on_geometry_changed_qml()` в `main_window.py`

---

## ✅ ОЖИДАЕМОЕ ПОВЕДЕНИЕ

**Когда пользователь двигает слайдер "Диаметр цилиндра":**

```
1. UI: Пользователь двигает слайдер → 90мм
   ↓
2. GeometryPanel: valueEdited сигнал → _on_parameter_changed()
   ↓
3. GeometryPanel: Обновляет parameters['cyl_diam_m'] = 0.090
   ↓
4. GeometryPanel: Вызывает _get_fast_geometry_update()
   ↓
5. GeometryPanel: geometry_changed.emit({'cylDiamM': 90.0, ...})
   ↓
6. MainWindow: _on_geometry_changed_qml({'cylDiamM': 90.0, ...})
   ↓
7. MainWindow: setProperty("userCylDiamM", 90.0)
   ↓
8. QML: userCylDiamM изменяется на 90.0
   ↓
9. QML: OptimizedSuspensionCorner использует userBoreHead (= userCylDiamM)
   ↓
10. 3D Scene: Цилиндры становятся толще!
```

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

1. ✅ **Запустите приложение вручную** и проверьте слайдеры
2. ✅ **Проверьте консоль** на наличие сообщений об обновлении
3. ✅ **Визуально проверьте** изменения в 3D сцене
4. ✅ **Если всё работает** - создайте коммит:
   ```bash
   git add assets/qml/main.qml src/ui/main_window.py
   git commit -m "FIX: Add cylinder parameters to QML and enable direct property updates

   - Added userCylDiamM, userStrokeM, userDeadGapM QML properties
   - Added userRodDiameterM, userPistonRodLengthM, userPistonThicknessM
   - Updated applyGeometryUpdates() to handle new parameters
   - Modified _on_geometry_changed_qml() to set properties directly
   - All cylinder parameters now update 3D scene in real-time"
   ```

---

## 📝 ТЕХНИЧЕСКАЯ ИНФОРМАЦИЯ

### Маппинг параметров (финальная версия):

| Python (метры) | Python (мм в dict) | QML property | Визуализация |
|----------------|-------------------|--------------|--------------|
| `cyl_diam_m: 0.080` | `cylDiamM: 80.0` | `userCylDiamM: 80` | `userBoreHead: 80` |
| `rod_diameter_m: 0.035` | `rodDiameterM: 35.0` | `userRodDiameterM: 35` | `userRodDiameter: 35` |
| `piston_thickness_m: 0.025` | `pistonThicknessM: 25.0` | `userPistonThicknessM: 25` | `userPistonThickness: 25` |
| `piston_rod_length_m: 0.200` | `pistonRodLengthM: 200.0` | `userPistonRodLengthM: 200` | `userPistonRodLength: 200` |
| `stroke_m: 0.300` | `strokeM: 300.0` | `userStrokeM: 300` | - |
| `dead_gap_m: 0.005` | `deadGapM: 5.0` | `userDeadGapM: 5` | - |

**Примечание:** Параметры с "старыми" именами (`userBoreHead`, `userRodDiameter`, и т.д.) обновляются **автоматически** для обратной совместимости.

---

**Отчёт создан:** 10 января 2026
**Статус:** ✅ **ГОТОВО К ТЕСТИРОВАНИЮ**
**Рекомендация:** Запустить `py app.py` и проверить слайдеры вручную 🚀

**Следующий шаг:** Ручное тестирование изменения параметров цилиндра в UI
