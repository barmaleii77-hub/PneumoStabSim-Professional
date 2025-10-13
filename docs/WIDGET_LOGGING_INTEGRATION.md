# Пример интеграции логирования в panel_graphics.py

## ✅ Вариант 1: С помощью фабрики (рекомендуется)

```python
from src.common.logging_slider_wrapper import create_logging_slider
from src.common.event_logger import get_event_logger

class GraphicsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        
        # Инициализируем event logger
        self.event_logger = get_event_logger()
        
        # ... остальной код ...
    
    def _build_key_light_group(self) -> QGroupBox:
        group = QGroupBox("Ключевой свет", self)
        grid = QGridLayout(group)
        
        # ✅ НОВОЕ: Создаем слайдер с логированием
        brightness_slider, brightness_logging = create_logging_slider(
            title="Яркость",
            minimum=0.0,
            maximum=10.0,
            step=0.05,
            widget_name="key.brightness",  # ✅ Уникальное имя
            decimals=2,
            parent=self
        )
        
        # Подключаем обработчик к wrapper'у
        brightness_logging.valueChanged.connect(
            lambda v: self._update_lighting("key", "brightness", v)
        )
        
        # Сохраняем в controls
        self._lighting_controls["key.brightness"] = brightness_slider
        
        grid.addWidget(brightness_slider, 0, 0, 1, 2)
        
        return group
```

---

## ✅ Вариант 2: Ручная обертка (для существующего кода)

```python
from src.common.event_logger import get_event_logger

class GraphicsPanel(QWidget):
    def _build_key_light_group(self) -> QGroupBox:
        group = QGroupBox("Ключевой свет", self)
        grid = QGridLayout(group)
        
        # Создаем обычный слайдер
        brightness = LabeledSlider("Яркость", 0.0, 10.0, 0.05, decimals=2)
        
        # ✅ ДОБАВЛЯЕМ: Wrapper для логирования
        def on_brightness_changed(value: float):
            # 1️⃣ Логируем изменение слайдера
            old_value = self.state["lighting"]["key"].get("brightness")
            self.event_logger.log_user_slider(
                slider_name="key.brightness",
                old_value=old_value,
                new_value=value,
                title="Яркость"
            )
            
            # 2️⃣ Вызываем обработчик
            self._update_lighting("key", "brightness", value)
        
        brightness.valueChanged.connect(on_brightness_changed)
        self._lighting_controls["key.brightness"] = brightness
        grid.addWidget(brightness, 0, 0, 1, 2)
        
        return group
```

---

## ✅ Вариант 3: Для QCheckBox

```python
from src.common.event_logger import get_event_logger

def _build_fog_group(self) -> QGroupBox:
    group = QGroupBox("Туман", self)
    grid = QGridLayout(group)
    
    enabled = QCheckBox("Включить туман", self)
    
    # ✅ Wrapper для логирования
    def on_fog_enabled_changed(state: int):
        checked = (state == Qt.Checked)
        
        # 1️⃣ Логируем клик
        self.event_logger.log_user_click(
            widget_name="fog_enabled",
            widget_type="QCheckBox",
            value=checked,
            text="Включить туман"
        )
        
        # 2️⃣ Вызываем обработчик
        self._update_environment("fog_enabled", checked)
    
    enabled.stateChanged.connect(on_fog_enabled_changed)
    self._environment_controls["fog.enabled"] = enabled
    grid.addWidget(enabled, 0, 0, 1, 2)
    
    return group
```

---

## ✅ Вариант 4: Для QComboBox

```python
def _build_background_group(self) -> QGroupBox:
    group = QGroupBox("Фон и HDR", self)
    grid = QGridLayout(group)
    
    mode_combo = QComboBox(self)
    mode_combo.addItem("Сплошной цвет", "color")
    mode_combo.addItem("Skybox / HDR", "skybox")
    
    # Сохраняем предыдущее значение
    previous_mode = [None]  # Используем список для изменяемости в closure
    
    # ✅ Wrapper для логирования
    def on_mode_changed(index: int):
        new_mode = mode_combo.currentData()
        
        # 1️⃣ Логируем выбор
        self.event_logger.log_user_combo(
            combo_name="background_mode",
            old_value=previous_mode[0],
            new_value=new_mode,
            index=index,
            text=mode_combo.currentText()
        )
        
        previous_mode[0] = new_mode
        
        # 2️⃣ Вызываем обработчик
        self._update_environment("background_mode", new_mode)
    
    mode_combo.currentIndexChanged.connect(on_mode_changed)
    self._environment_controls["background.mode"] = mode_combo
    grid.addWidget(mode_combo, 0, 1)
    
    return group
```

---

## ✅ Вариант 5: Для ColorButton

```python
from src.common.logging_slider_wrapper import LoggingColorButton

def _build_key_light_group(self) -> QGroupBox:
    group = QGroupBox("Ключевой свет", self)
    grid = QGridLayout(group)
    
    # Создаем обычную ColorButton
    color_button = ColorButton()
    
    # Оборачиваем в logging wrapper
    logging_button = LoggingColorButton(color_button, "key.color")
    
    # ✅ Подключаем к wrapper'у
    # (логирование происходит автоматически внутри wrapper'а)
    color_button.color_changed.connect(
        lambda c: self._update_lighting("key", "color", c)
    )
    
    self._lighting_controls["key.color"] = color_button
    # ... добавляем в layout ...
```

---

## 📊 Результат логирования

После применения wrapper'ов в логе будут события:

```json
[
  {
    "timestamp": "2024-12-15T15:30:25.123456",
    "event_type": "USER_SLIDER",
    "component": "panel_graphics",
    "action": "slider_key.brightness",
    "old_value": 1.2,
    "new_value": 1.5,
    "metadata": {
      "widget_type": "LabeledSlider",
      "title": "Яркость",
      "unit": ""
    }
  },
  {
    "timestamp": "2024-12-15T15:30:25.145678",
    "event_type": "STATE_CHANGE",
    "component": "state.lighting",
    "action": "brightness",
    "old_value": 1.2,
    "new_value": 1.5
  },
  {
    "timestamp": "2024-12-15T15:30:25.156789",
    "event_type": "SIGNAL_EMIT",
    "component": "panel_graphics",
    "action": "emit_lighting_changed",
    "new_value": {
      "key_light": {"brightness": 1.5, "color": "#ffffff"}
    }
  }
]
```

---

## 🎯 Рекомендации

1. **Используйте Вариант 1** для новых слайдеров
2. **Используйте Вариант 2** для быстрой интеграции в существующий код
3. **Логируйте ВСЕ**: слайдеры, чекбоксы, комбобоксы, кнопки цвета
4. **Сохраняйте старое значение** для всех виджетов (для анализа изменений)

---

## ✅ Чеклист интеграции

- [ ] Заменить создание LabeledSlider на `create_logging_slider()`
- [ ] Добавить wrapper для QCheckBox
- [ ] Добавить wrapper для QComboBox
- [ ] Добавить wrapper для ColorButton
- [ ] Протестировать логирование
- [ ] Проверить анализ `analyze_event_sync.py`
