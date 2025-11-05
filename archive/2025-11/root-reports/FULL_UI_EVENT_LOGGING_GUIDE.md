# 🚀 Полное руководство по логированию UI событий

## 📋 Что нового

### ✅ Добавлено логирование для:

1. **QCheckBox** - клики на чекбоксы
2. **LabeledSlider** - изменения слайдеров
3. **QComboBox** - выбор в выпадающих списках
4. **ColorButton** - выбор цвета
5. **Мышь в QML** - drag, zoom, rotate на 3D канве

---

## 🔧 Как интегрировать

### **Шаг 1: Импорт в panel_graphics.py**

```python
# В начале файла
from src.common.event_logger import get_event_logger
from src.common.logging_slider_wrapper import create_logging_slider, LoggingColorButton
```

### **Шаг 2: Инициализация в __init__**

```python
def __init__(self, parent: QWidget | None = None):
    super().__init__(parent)

    # ... существующий код ...

    # ✅ НОВОЕ: Инициализируем event logger
    self.event_logger = get_event_logger()
```

### **Шаг 3: Применение к слайдерам**

#### ❌ БЫЛО:
```python
brightness = LabeledSlider("Яркость", 0.0, 10.0, 0.05, decimals=2)
brightness.valueChanged.connect(lambda v: self._update_lighting("key", "brightness", v))
self._lighting_controls["key.brightness"] = brightness
grid.addWidget(brightness, 0, 0, 1, 2)
```

#### ✅ СТАЛО:
```python
# Создаем слайдер с логированием
brightness_slider, brightness_logging = create_logging_slider(
    title="Яркость",
    minimum=0.0,
    maximum=10.0,
    step=0.05,
    widget_name="key.brightness",  # Уникальное имя для лога
    decimals=2,
    parent=self
)

# Подключаем к wrapper'у (логирование автоматическое)
brightness_logging.valueChanged.connect(
    lambda v: self._update_lighting("key", "brightness", v)
)

self._lighting_controls["key.brightness"] = brightness_slider
grid.addWidget(brightness_slider, 0, 0, 1, 2)
```

### **Шаг 4: Применение к чекбоксам**

#### ❌ БЫЛО:
```python
fog_enabled = QCheckBox("Включить туман", self)
fog_enabled.stateChanged.connect(
    lambda state: self._update_environment("fog_enabled", state == Qt.Checked)
)
```

#### ✅ СТАЛО:
```python
fog_enabled = QCheckBox("Включить туман", self)

def on_fog_changed(state: int):
    checked = (state == Qt.Checked)

    # 1️⃣ Логируем клик
    self.event_logger.log_user_click(
        widget_name="fog_enabled",
        widget_type="QCheckBox",
        value=checked,
        text="Включить туман"
    )

    # 2️⃣ Обрабатываем
    self._update_environment("fog_enabled", checked)

fog_enabled.stateChanged.connect(on_fog_changed)
```

### **Шаг 5: Применение к комбобоксам**

```python
mode_combo = QComboBox(self)
mode_combo.addItem("Сплошной цвет", "color")
mode_combo.addItem("Skybox / HDR", "skybox")

# Сохраняем предыдущее значение
previous_mode = [None]

def on_mode_changed(index: int):
    new_mode = mode_combo.currentData()

    # Логируем выбор
    self.event_logger.log_user_combo(
        combo_name="background_mode",
        old_value=previous_mode[0],
        new_value=new_mode,
        index=index,
        text=mode_combo.currentText()
    )

    previous_mode[0] = new_mode
    self._update_environment("background_mode", new_mode)

mode_combo.currentIndexChanged.connect(on_mode_changed)
```

### **Шаг 6: Интеграция мыши в QML**

В `main.qml`:

```qml
import QtQuick
import QtQuick3D
import "components"

View3D {
    id: view3D
    anchors.fill: parent

    // ... существующий код ...

    // ✅ НОВОЕ: Логирование мыши
    MouseEventLogger {
        id: mouseLogger
        enableLogging: true
        componentName: "main.qml"
        z: -1  // Под остальными элементами

        // Обработчики уже встроены в компонент
    }

    // ... остальной код ...
}
```

---

## 📊 Пример вывода диагностики

После применения всех изменений при выходе из приложения:

```
============================================================
🔍 ДИАГНОСТИКА ЛОГОВ И СОБЫТИЙ
============================================================

📊 Анализ всех логов...
   ✅ Основной лог: 1,234 строк

🎨 Анализ синхронизации графики...
   ✅ Синхронизация: 98.5%

👤 Анализ пользовательской сессии...
   ✅ Активность: 45 действий

🔗 Анализ событий Python↔QML...
   📁 События экспортированы: logs/events_20241215_153045.json
   Всего сигналов: 67
   Синхронизировано: 65
   Пропущено QML: 2
   Процент синхронизации: 97.0%
   ⚠️  Обнаружены несинхронизированные события!

   📈 События по типам:
      USER_SLIDER: 34
      STATE_CHANGE: 45
      SIGNAL_EMIT: 67
      SIGNAL_RECEIVED: 65
      USER_CLICK: 12
      USER_COMBO: 8
      USER_COLOR: 5
      MOUSE_DRAG: 23
      MOUSE_WHEEL: 7
      MOUSE_PRESS: 4

============================================================
⚠️  Диагностика завершена - обнаружены проблемы
💡 См. детали выше
============================================================
```

---

## 🔍 Анализ событий

### Ручной анализ:

```bash
python analyze_event_sync.py
```

### С HTML отчетом:

```bash
python analyze_event_sync.py --html
```

Откройте `logs/event_analysis.html` в браузере.

---

## 📝 Структура JSON событий

```json
{
  "timestamp": "2024-12-15T15:30:25.123456",
  "session_id": "20241215_153022",
  "event_type": "USER_SLIDER",
  "source": "python",
  "component": "panel_graphics",
  "action": "slider_key.brightness",
  "old_value": 1.2,
  "new_value": 1.5,
  "metadata": {
    "widget_type": "LabeledSlider",
    "title": "Яркость",
    "unit": ""
  }
}
```

---

## 🎯 Типы событий

### Python

| Тип | Описание | Пример |
|-----|----------|--------|
| **USER_CLICK** | Клик на QCheckBox | `fog_enabled` |
| **USER_SLIDER** | Изменение LabeledSlider | `key.brightness` |
| **USER_COMBO** | Выбор в QComboBox | `background_mode` |
| **USER_COLOR** | Выбор цвета | `key.color` |
| **STATE_CHANGE** | Изменение state | `state.camera.fov` |
| **SIGNAL_EMIT** | Вызов .emit() | `camera_changed.emit()` |

### QML

| Тип | Описание | Пример |
|-----|----------|--------|
| **SIGNAL_RECEIVED** | Получение сигнала | `onCameraChanged` |
| **FUNCTION_CALLED** | Вызов функции | `applyCameraUpdates()` |
| **PROPERTY_CHANGED** | Изменение property | `mainCamera.fieldOfView = 60` |
| **MOUSE_PRESS** | Нажатие мыши | Left/Right/Middle button |
| **MOUSE_DRAG** | Перетаскивание | Camera rotation |
| **MOUSE_WHEEL** | Прокрутка колесика | Zoom in/out |
| **MOUSE_RELEASE** | Отпускание мыши | End of drag |

---

## ✅ Чеклист внедрения

### Python (panel_graphics.py)

- [ ] Импортировать `get_event_logger()` и `create_logging_slider()`
- [ ] Инициализировать `self.event_logger` в `__init__`
- [ ] Заменить все `LabeledSlider` на `create_logging_slider()`
- [ ] Добавить wrapper для всех `QCheckBox`
- [ ] Добавить wrapper для всех `QComboBox`
- [ ] Добавить wrapper для всех `ColorButton`
- [ ] Протестировать слайдеры
- [ ] Протестировать чекбоксы
- [ ] Протестировать комбобоксы

### QML (main.qml)

- [ ] Импортировать `MouseEventLogger`
- [ ] Добавить `MouseEventLogger` в `View3D`
- [ ] Протестировать логирование drag
- [ ] Протестировать логирование zoom
- [ ] Протестировать логирование rotate

### Анализ

- [ ] Запустить приложение
- [ ] Выполнить действия (слайдеры, чекбоксы, мышь)
- [ ] Закрыть приложение
- [ ] Проверить вывод диагностики
- [ ] Проверить `logs/events_*.json`
- [ ] Запустить `analyze_event_sync.py`
- [ ] Проверить HTML отчет

---

## 🐛 Troubleshooting

### Проблема: "Логи пустые"

**Решение**: Убедитесь, что `event_logger` инициализирован в `__init__`:

```python
self.event_logger = get_event_logger()
```

### Проблема: "Дублирующиеся события"

**Решение**: Проверьте, что wrapper подключен ТОЛЬКО ОДИН РАЗ:

```python
# ❌ НЕПРАВИЛЬНО
slider.valueChanged.connect(handler1)
slider.valueChanged.connect(handler2)  # Дубль!

# ✅ ПРАВИЛЬНО
slider.valueChanged.connect(handler1)
```

### Проблема: "Мышь не логируется"

**Решение**: Проверьте z-index `MouseEventLogger`:

```qml
MouseEventLogger {
    z: -1  // Должен быть под остальными элементами
}
```

---

## 🚀 Готово!

После применения всех изменений:

1. ✅ Все клики логируются
2. ✅ Все слайдеры логируются
3. ✅ Все комбобоксы логируются
4. ✅ Все действия мыши логируются
5. ✅ Анализ доступен через `analyze_event_sync.py`

**Следующий шаг**: Применить к реальному `panel_graphics.py`

---

**Версия**: 2.0
**Дата**: 2024-12-15
