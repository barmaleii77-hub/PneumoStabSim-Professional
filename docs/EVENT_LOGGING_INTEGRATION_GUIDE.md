# 🎯 Event Logging Integration Guide

## Цель
Логировать **ВСЕ** события в Python и QML для анализа синхронизации.

---

## 📋 Что логируем

### **Python сторона:**
1. ✅ **USER_CLICK** - клик пользователя (ПЕРЕД обработчиком)
2. ✅ **STATE_CHANGE** - изменение state
3. ✅ **SIGNAL_EMIT** - вызов .emit()
4. ✅ **QML_INVOKE** - QMetaObject.invokeMethod

### **QML сторона:**
5. ✅ **SIGNAL_RECEIVED** - получен сигнал (onXxxChanged)
6. ✅ **FUNCTION_CALLED** - вызвана функция (applyLightingUpdates)
7. ✅ **PROPERTY_CHANGED** - изменено свойство (property binding)

---

## 🔧 Шаг 1: Интеграция EventLogger в GraphicsPanel

### **1.1 Импорт в `panel_graphics.py`**

```python
# В начале файла, после существующих импортов
from src.common.event_logger import get_event_logger, EventType
```

### **1.2 Инициализация в `__init__`**

```python
def __init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)

    self.logger = logging.getLogger(__name__)
    self.settings = QSettings("PneumoStabSim", "GraphicsPanel")
    self._updating_ui = False

    # ✅ НОВОЕ: Инициализируем event logger
    self.event_logger = get_event_logger()

    # Инициализируем логгер графических изменений
    self.graphics_logger = get_graphics_logger()
    self.logger.info("📊 Graphics logger initialized")
    # ... остальной код
```

---

## 🔧 Шаг 2: Логирование кликов ПЕРЕД обработчиками

### **2.1 Для QCheckBox (например, auto_rotate)**

**❌ БЫЛО:**
```python
auto_rotate = QCheckBox("Автоповорот", self)
auto_rotate.stateChanged.connect(lambda state: self._update_camera("auto_rotate", state == Qt.Checked))
```

**✅ СТАЛО:**
```python
auto_rotate = QCheckBox("Автоповорот", self)

def on_auto_rotate_clicked(state: int):
    checked = (state == Qt.Checked)

    # 1️⃣ Логируем КЛИК (перед обработчиком)
    self.event_logger.log_user_click(
        widget_name="auto_rotate",
        widget_type="QCheckBox",
        value=checked
    )

    # 2️⃣ Вызываем обработчик
    self._update_camera("auto_rotate", checked)

auto_rotate.stateChanged.connect(on_auto_rotate_clicked)
```

### **2.2 Для LabeledSlider**

**❌ БЫЛО:**
```python
fov = LabeledSlider("Поле зрения", 10.0, 120.0, 0.5, decimals=1, unit="°")
fov.valueChanged.connect(lambda v: self._update_camera("fov", v))
```

**✅ СТАЛО:**
```python
fov = LabeledSlider("Поле зрения", 10.0, 120.0, 0.5, decimals=1, unit="°")

def on_fov_changed(v: float):
    # 1️⃣ Логируем КЛИК
    self.event_logger.log_user_click(
        widget_name="fov",
        widget_type="LabeledSlider",
        value=v
    )

    # 2️⃣ Вызываем обработчик
    self._update_camera("fov", v)

fov.valueChanged.connect(on_fov_changed)
```

---

## 🔧 Шаг 3: Логирование изменений state

### **В методах `_update_camera`, `_update_environment` и т.д.**

**✅ УЖЕ ЕСТЬ:**
```python
def _update_camera(self, key: str, value: Any) -> None:
    if self._updating_ui:
        return

    # Сохраняем старое значение
    old_value = self.state["camera"].get(key)

    # Обновляем state
    self.state["camera"][key] = value

    # ✅ Логируем STATE_CHANGE
    self.event_logger.log_state_change(
        category="camera",
        parameter=key,
        old_value=old_value,
        new_value=value
    )

    self._emit_camera()
```

---

## 🔧 Шаг 4: Логирование вызовов .emit()

### **В методах `_emit_camera`, `_emit_lighting` и т.д.**

**❌ БЫЛО:**
```python
def _emit_camera(self) -> None:
    payload = self._prepare_camera_payload()
    self.camera_changed.emit(payload)
```

**✅ СТАЛО:**
```python
def _emit_camera(self) -> None:
    payload = self._prepare_camera_payload()

    # ✅ Логируем SIGNAL_EMIT
    self.event_logger.log_signal_emit(
        signal_name="camera_changed",
        payload=payload
    )

    self.camera_changed.emit(payload)
```

---

## 🔧 Шаг 5: Логирование в QML

### **5.1 Получение сигнала в QML**

```qml
// main.qml
Connections {
    target: graphicsPanel

    function onCameraChanged(params) {
        // ✅ Логируем SIGNAL_RECEIVED
        console.log("[EVENT] SIGNAL_RECEIVED: cameraChanged")

        // Вызываем функцию обработки
        applyCameraUpdates(params)
    }
}
```

### **5.2 Вызов функции в QML**

```qml
function applyCameraUpdates(params) {
    // ✅ Логируем FUNCTION_CALLED
    console.log("[EVENT] FUNCTION_CALLED: applyCameraUpdates", JSON.stringify(params))

    // Применяем изменения
    if (params.fov !== undefined) {
        // ✅ Логируем PROPERTY_CHANGED
        let oldValue = mainCamera.fieldOfView
        mainCamera.fieldOfView = params.fov
        console.log("[EVENT] PROPERTY_CHANGED: mainCamera.fieldOfView", oldValue, "→", params.fov)
    }

    // ... остальные параметры
}
```

---

## 📊 Шаг 6: Анализ синхронизации

### **6.1 В `app.py` после закрытия приложения**

```python
def run_log_diagnostics():
    """Запускает диагностику логов после закрытия приложения"""
    print("\n" + "="*60)
    print("🔍 ДИАГНОСТИКА СОБЫТИЙ Python↔QML")
    print("="*60)

    from src.common.event_logger import get_event_logger

    event_logger = get_event_logger()

    # Экспортируем события в JSON
    events_file = event_logger.export_events()
    print(f"\n📁 События экспортированы: {events_file}")

    # Анализируем синхронизацию
    analysis = event_logger.analyze_sync()

    print(f"\n📊 Результаты анализа:")
    print(f"   Всего сигналов: {analysis['total_signals']}")
    print(f"   Синхронизировано: {analysis['synced']}")
    print(f"   Пропущено QML: {analysis['missing_qml']}")
    print(f"   Процент синхронизации: {analysis['sync_rate']:.1f}%")
    print(f"   Средняя задержка: {analysis['avg_latency_ms']:.2f} мс")
    print(f"   Макс. задержка: {analysis['max_latency_ms']:.2f} мс")

    if analysis['missing_qml'] > 0:
        print(f"\n⚠️  Обнаружены несинхронизированные события:")
        for pair in analysis['pairs']:
            if pair['status'] == 'missing_qml':
                event = pair['python_event']
                print(f"   • {event['action']} ({event['timestamp']})")

    print("="*60)
```

### **6.2 Добавить в `app.py` в функцию `main()`**

```python
def main():
    # ... существующий код ...

    result = app.exec()

    # ✅ НОВОЕ: Анализ событий после выхода
    run_log_diagnostics()

    return result
```

---

## 📝 Пример вывода анализа

```
============================================================
🔍 ДИАГНОСТИКА СОБЫТИЙ Python↔QML
============================================================

📁 События экспортированы: logs/events_20241215_143022.json

📊 Результаты анализа:
   Всего сигналов: 45
   Синхронизировано: 42
   Пропущено QML: 3
   Процент синхронизации: 93.3%
   Средняя задержка: 12.45 мс
   Макс. задержка: 87.32 мс

⚠️  Обнаружены несинхронизированные события:
   • emit_camera_changed (2024-12-15T14:30:25.123456)
   • emit_lighting_changed (2024-12-15T14:30:28.456789)
   • emit_effects_changed (2024-12-15T14:30:31.789012)
============================================================
```

---

## 🎯 Ожидаемый результат

После внедрения у вас будет:

1. ✅ **Полный трейс** всех событий Python→QML
2. ✅ **Точное определение** пропущенных сигналов
3. ✅ **Метрики задержек** между Python и QML
4. ✅ **JSON файл** со всеми событиями для детального анализа

---

## 🚀 Следующие шаги

1. Добавить `event_logger.py` (уже создан)
2. Интегрировать логирование кликов в `panel_graphics.py`
3. Добавить логирование emit в Python
4. Добавить логирование в QML (console.log)
5. Добавить анализ в `app.py`

**Готов к реализации?**
