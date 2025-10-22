# 🎯 Unified Python↔QML Event Logging System

## Цель проекта

**Полное отслеживание и анализ всех событий между Python и QML**, чтобы выявить:
- ❌ Пропущенные сигналы (Python emit → QML не получил)
- ⏱️ Медленные обновления (задержки >50ms)
- 🐛 Несинхронизированные состояния

---

## 📂 Структура системы

```
PneumoStabSim-Professional/
├── src/common/
│   └── event_logger.py           # ✅ Singleton EventLogger
├── src/ui/panels/
│   └── panel_graphics.py         # Интеграция логирования кликов
├── assets/qml/
│   └── main.qml                  # Логирование QML событий
├── analyze_event_sync.py         # Анализатор событий
├── docs/
│   └── EVENT_LOGGING_INTEGRATION_GUIDE.md  # Руководство по интеграции
└── logs/
    ├── events_<timestamp>.json   # События (автоматически)
    └── event_analysis.html       # HTML отчет
```

---

## 🚀 Быстрый старт

### 1️⃣ Запустите приложение

```bash
python app.py
```

### 2️⃣ Взаимодействуйте с UI

- Кликайте на чекбоксы
- Двигайте слайдеры
- Меняйте настройки графики

### 3️⃣ Закройте приложение

При выходе автоматически запускается анализ:

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
============================================================
```

---

## 📊 Ручной анализ

### Анализ последней сессии

```bash
python analyze_event_sync.py
```

### Генерация HTML отчета

```bash
python analyze_event_sync.py --html
```

Откройте `logs/event_analysis.html` в браузере.

---

## 🔧 Типы событий

### Python сторона

| Тип | Описание | Пример |
|-----|----------|--------|
| **USER_CLICK** | Клик пользователя | QCheckBox.stateChanged |
| **STATE_CHANGE** | Изменение `self.state` | `state["camera"]["fov"] = 60` |
| **SIGNAL_EMIT** | Вызов `.emit()` | `camera_changed.emit(payload)` |
| **QML_INVOKE** | QMetaObject.invokeMethod | `invokeMethod("applyUpdates")` |
| **PYTHON_ERROR** | Ошибка в Python | Exception в обработчике |

### QML сторона

| Тип | Описание | Пример |
|-----|----------|--------|
| **SIGNAL_RECEIVED** | Получение сигнала | `onCameraChanged` |
| **FUNCTION_CALLED** | Вызов QML функции | `applyCameraUpdates()` |
| **PROPERTY_CHANGED** | Изменение property | `mainCamera.fieldOfView = 60` |
| **QML_ERROR** | Ошибка в QML | Неожиданное значение |

---

## 📝 Формат события (JSON)

```json
{
  "timestamp": "2024-12-15T14:30:25.123456",
  "session_id": "20241215_143022",
  "event_type": "USER_CLICK",
  "source": "python",
  "component": "panel_graphics",
  "action": "click_auto_rotate",
  "old_value": false,
  "new_value": true,
  "metadata": {
    "widget_type": "QCheckBox"
  }
}
```

---

## 🔍 Примеры анализа

### Найти пропущенные сигналы

```python
from src.common.event_logger import get_event_logger

event_logger = get_event_logger()
analysis = event_logger.analyze_sync()

for pair in analysis['pairs']:
    if pair['status'] == 'missing_qml':
        print(f"⚠️  Пропущен: {pair['python_event']['action']}")
```

### Найти медленные обновления

```python
slow = [p for p in analysis['pairs']
        if p['status'] == 'synced' and p['latency_ms'] > 50]

for item in slow:
    print(f"🐌 {item['python_event']['action']}: {item['latency_ms']}ms")
```

---

## 🛠️ Интеграция в новый компонент

### Python

```python
from src.common.event_logger import get_event_logger

class MyPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.event_logger = get_event_logger()

    def on_button_clicked(self):
        # 1️⃣ Логируем клик
        self.event_logger.log_user_click(
            widget_name="my_button",
            widget_type="QPushButton",
            value="clicked"
        )

        # 2️⃣ Обрабатываем
        self._handle_click()

    def _emit_signal(self):
        payload = {"value": 42}

        # 1️⃣ Логируем emit
        self.event_logger.log_signal_emit(
            signal_name="my_signal",
            payload=payload
        )

        # 2️⃣ Эмитим
        self.my_signal.emit(payload)
```

### QML

```qml
Connections {
    target: myPanel

    function onMySignal(params) {
        // ✅ Логируем получение
        console.log("[EVENT] SIGNAL_RECEIVED: mySignal")

        // ✅ Логируем вызов функции
        console.log("[EVENT] FUNCTION_CALLED: handleSignal")

        // Обрабатываем
        handleSignal(params)
    }
}

function handleSignal(params) {
    // ✅ Логируем изменение свойства
    let oldValue = myProperty
    myProperty = params.value
    console.log("[EVENT] PROPERTY_CHANGED: myProperty", oldValue, "→", params.value)
}
```

---

## 📈 Метрики

### Целевые показатели

| Метрика | Цель | Критично |
|---------|------|----------|
| **Sync Rate** | >95% | <90% |
| **Avg Latency** | <20ms | >100ms |
| **Max Latency** | <50ms | >200ms |
| **Missing QML** | 0 | >5 |

---

## 🐛 Типичные проблемы

### 1. Сигнал не доходит до QML

**Симптомы:**
```
⚠️  Пропущен: emit_camera_changed
```

**Причины:**
- ❌ Нет `Connections` в QML
- ❌ Неправильное имя слота (`onCameraChanged` vs `oncamerachanged`)
- ❌ Сигнал эмитится до создания QML объекта

**Решение:**
```qml
// ✅ ПРАВИЛЬНО
Connections {
    target: graphicsPanel
    function onCameraChanged(params) { ... }
}
```

### 2. Медленные обновления

**Симптомы:**
```
🐌 emit_lighting_changed: 187.45ms
```

**Причины:**
- ❌ Тяжелые вычисления в QML функции
- ❌ Множественные property bindings
- ❌ Синхронный invokeMethod

**Решение:**
- ✅ Используйте `Qt.callLater()` для асинхронности
- ✅ Кэшируйте вычисления
- ✅ Батчите обновления

---

## 🔐 Безопасность

- ✅ **Не логируем пароли** или sensitive data
- ✅ **JSON serializable only** - автоматическая сериализация
- ✅ **Ограничение размера лога** - хранится только последняя сессия

---

## 📚 Дополнительные ресурсы

- [EVENT_LOGGING_INTEGRATION_GUIDE.md](docs/EVENT_LOGGING_INTEGRATION_GUIDE.md) - Полное руководство
- [event_logger.py](src/common/event_logger.py) - Исходный код
- [analyze_event_sync.py](analyze_event_sync.py) - Анализатор

---

## ✅ Чеклист внедрения

- [x] Создан `event_logger.py`
- [x] Создан `analyze_event_sync.py`
- [x] Создано руководство по интеграции
- [ ] Интегрировано логирование кликов в `panel_graphics.py`
- [ ] Добавлено логирование emit в Python
- [ ] Добавлено логирование в QML (console.log)
- [ ] Добавлен анализ в `app.py`
- [ ] Протестирована синхронизация

---

**Версия**: 1.0
**Дата**: 2024-12-15
**Автор**: GitHub Copilot
