# Graphics Logging System

Система мониторинга и анализа изменений графических параметров в PneumoStabSim Professional.

## 📋 Содержание

- [Обзор](#обзор)
- [Быстрый старт](#быстрый-старт)
- [Компоненты](#компоненты)
- [Использование](#использование)
- [Анализ логов](#анализ-логов)
- [Примеры](#примеры)

## 🎯 Обзор

Система логирования отслеживает:
- ✅ Все изменения параметров на GraphicsPanel
- ✅ Применение изменений в QML сцене
- ✅ Ошибки синхронизации Python ↔ QML
- ✅ Производительность обновлений

### Зачем это нужно?

1. **Диагностика проблем синхронизации** - находите параметры, которые не применяются в QML
2. **Анализ производительности** - отслеживайте частоту изменений
3. **История изменений** - полная запись всех модификаций графики
4. **Сравнение состояний** - сравнивайте Panel и QML состояния

## 🚀 Быстрый старт

### 1. Тестирование системы

```bash
# Запустить тест логирования
python test_graphics_logger.py

# Анализировать существующий лог
python analyze_graphics_logs.py logs/graphics/session_20240101_120000.jsonl

# Экспортировать в CSV для Excel
python analyze_graphics_logs.py logs/graphics/session_20240101_120000.jsonl --csv
```

### 2. Использование в коде

```python
from ui.panels.panel_graphics import GraphicsPanel
from ui.panels.graphics_logger import get_graphics_logger

# Создать панель
panel = GraphicsPanel()

# Получить логгер
logger = get_graphics_logger()

# Просмотреть последние изменения
for event in logger.get_recent_changes(5):
    print(f"{event.parameter_name}: {event.old_value} → {event.new_value}")

# Экспортировать пресет и отчет
panel.export_sync_analysis()
```

## 🔧 Компоненты

### 1. GraphicsLogger (`src/ui/panels/graphics_logger.py`)

Основной класс логирования:

```python
class GraphicsLogger:
    def log_change(...)          # Записать изменение параметра
    def log_qml_update(...)       # Записать результат применения в QML
    def analyze_qml_sync(...)     # Анализ синхронизации
    def export_analysis_report(...) # Экспорт отчета
    def compare_states(...)       # Сравнение Panel ↔ QML
```

### 2. GraphicsPanel Integration

Автоматическое логирование в `panel_graphics.py`:

```python
def _update_lighting(self, group: str, key: str, value: Any):
    old_value = self.state["lighting"].get(group, {}).get(key)
    self.state["lighting"][group][key] = value

    # Автоматическое логирование
    self.graphics_logger.log_change(
        parameter_name=f"{group}.{key}",
        old_value=old_value,
        new_value=value,
        category="lighting",
        panel_state=self.state
    )
```

### 3. Тестовая утилита (`test_graphics_logger.py`)

Интерактивное тестирование:
- Автоматические тестовые изменения
- Отслеживание QML обновлений
- Экспорт пресета и анализа

### 4. Анализатор логов (`analyze_graphics_logs.py`)

Постобработка логов:
- Статистика изменений
- Временная шкала
- Анализ ошибок
- Экспорт в CSV

## 📊 Использование

### Базовый workflow

```python
# 1. Создать панель (логгер инициализируется автоматически)
panel = GraphicsPanel()

# 2. Изменить параметры (логируется автоматически)
panel.state["lighting"]["key"]["brightness"] = 1.5
panel._emit_lighting()

# 3. Получить логгер
logger = get_graphics_logger()

# 4. Просмотреть изменения
recent = logger.get_recent_changes(10)

# 5. Экспортировать пресет и отчет
panel.export_sync_analysis()
```

### Отслеживание QML обновлений

```python
class MainWindow(QMainWindow):
    def __init__(self):
        self.graphics_panel = GraphicsPanel()

        # Подключить сигналы
        self.graphics_panel.lighting_changed.connect(
            self._on_lighting_changed
        )

    def _on_lighting_changed(self, data):
        logger = get_graphics_logger()
        recent = logger.get_recent_changes(1)

        if recent:
            event = recent[0]

            try:
                # Применить в QML
                self._apply_to_qml(data)

                # Логировать успех
                logger.log_qml_update(
                    event,
                    qml_state={"applied": True},
                    success=True
                )
            except Exception as e:
                # Логировать ошибку
                logger.log_qml_update(
                    event,
                    success=False,
                    error=str(e)
                )
```

### Анализ синхронизации

```python
logger = get_graphics_logger()

# Получить полный анализ
analysis = logger.analyze_qml_sync()

print(f"Всего изменений: {analysis['total_events']}")
print(f"Успешных QML обновлений: {analysis['successful_updates']}")
print(f"Процент синхронизации: {analysis['sync_rate']:.1f}%")

# Проверить ошибки
if analysis['errors_by_parameter']:
    print("\n⚠️ Параметры с ошибками:")
    for param, errors in analysis['errors_by_parameter'].items():
        print(f"  {param}: {len(errors)} ошибок")
```

## 🔍 Анализ логов

### Структура лога (JSONL)

```jsonl
{"event_type": "session_start", "session_id": "20240101_120000", ...}
{"event_type": "parameter_change", "parameter_name": "key.brightness", "old_value": 1.2, "new_value": 1.5, ...}
{"event_type": "parameter_update", "applied_to_qml": true, ...}
{"event_type": "session_end", "stats": {...}, "analysis": {...}}
```

### Анализ с помощью утилиты

```bash
# Базовый анализ
python analyze_graphics_logs.py logs/graphics/session_20240101_120000.jsonl

# С экспортом в CSV
python analyze_graphics_logs.py logs/graphics/session_20240101_120000.jsonl --csv
```

Вывод:
```
✅ Загружено 42 событий из session_20240101_120000.jsonl

============================================================
📊 SUMMARY
============================================================
Session ID: 20240101_120000
Started: 2024-01-01T12:00:00
Total events: 42

By category:
  lighting: 12 events
  environment: 8 events
  quality: 7 events
  camera: 5 events
  effects: 6 events
  material: 4 events

QML Synchronization:
  With QML update: 38/42
  Successful: 36
  Failed: 2
  Sync rate: 85.7%
============================================================
```

### Ручной анализ в Python

```python
import json
from pathlib import Path

log_file = Path("logs/graphics/session_20240101_120000.jsonl")

events = []
with open(log_file) as f:
    for line in f:
        event = json.loads(line)
        if event.get('event_type') == 'parameter_change':
            events.append(event)

# Фильтрация по категории
lighting_changes = [e for e in events if e['category'] == 'lighting']

# Поиск ошибок
errors = [e for e in events if e.get('error')]

# Временной анализ
from datetime import datetime

for event in events:
    ts = datetime.fromisoformat(event['timestamp'])
    print(f"{ts}: {event['parameter_name']} changed")
```

## 📝 Примеры

### Пример 1: Диагностика проблемы auto_rotate

```python
logger = get_graphics_logger()

# Ищем изменения auto_rotate
auto_rotate_events = [
    e for e in logger.events_buffer
    if 'auto_rotate' in e.parameter_name
]

for event in auto_rotate_events:
    print(f"Timestamp: {event.timestamp}")
    print(f"Value: {event.old_value} → {event.new_value}")
    print(f"Applied to QML: {event.applied_to_qml}")
    print(f"Error: {event.error}")
    print()
```

### Пример 2: Сравнение Panel и QML состояний

```python
# Получаем состояние панели
panel_state = graphics_panel.state

# Получаем состояние QML (из QML через сигналы)
qml_state = {
    "camera": {"fov": 60.0, "auto_rotate": True},
    "lighting": {"key": {"brightness": 1.2}}
}

# Сравниваем
diff = logger.compare_states(panel_state['camera'], qml_state['camera'])

print(f"Совпадающих: {len(diff['matching'])}")
print(f"Рассинхронизированных: {len(diff['mismatched'])}")

for m in diff['mismatched']:
    print(f"{m['parameter']}:")
    print(f"  Panel: {m['panel_value']}")
    print(f"  QML:   {m['qml_value']}")
```

### Пример 3: Мониторинг в реальном времени

```python
from PySide6.QtCore import QTimer

def monitor_changes():
    logger = get_graphics_logger()
    recent = logger.get_recent_changes(1)

    if recent:
        event = recent[0]
        print(f"[{event.timestamp}] {event.parameter_name}: {event.new_value}")

        if not event.applied_to_qml:
            print(f"  ⚠️ Not applied to QML yet!")

# Проверяем каждые 2 секунды
timer = QTimer()
timer.timeout.connect(monitor_changes)
timer.start(2000)
```

## 🐛 Troubleshooting

### Проблема: Низкий sync rate (<90%)

```python
analysis = logger.analyze_qml_sync()

if analysis['sync_rate'] < 90:
    # Проверяем проблемные категории
    for cat, stats in analysis['by_category'].items():
        if stats['failed'] > 0:
            print(f"⚠️ {cat}: {stats['failed']}/{stats['total']} failed")

    # Смотрим конкретные ошибки
    for param, errors in analysis['errors_by_parameter'].items():
        print(f"❌ {param}:")
        for error in errors:
            print(f"   - {error}")
```

### Проблема: Параметр не логируется

Проверьте, что:
1. Логгер инициализирован: `self.graphics_logger = get_graphics_logger()`
2. Вызывается `log_change()` в методе обновления
3. `_updating_ui` флаг не блокирует логирование

### Проблема: QML обновления не отслеживаются

Подключите все сигналы GraphicsPanel:

```python
panel.lighting_changed.connect(on_lighting_changed)
panel.environment_changed.connect(on_environment_changed)
panel.quality_changed.connect(on_quality_changed)
panel.camera_changed.connect(on_camera_changed)
panel.effects_changed.connect(on_effects_changed)
panel.material_changed.connect(on_material_changed)
```

## 📚 Документация

- [GRAPHICS_LOGGING.md](GRAPHICS_LOGGING.md) - Полная документация
- [GRAPHICS_LOGGING_QUICKSTART.md](GRAPHICS_LOGGING_QUICKSTART.md) - Быстрый старт

## 🔗 Связанные файлы

- `src/ui/panels/graphics_logger.py` - Основной логгер
- `src/ui/panels/panel_graphics.py` - Интеграция в панель
- `test_graphics_logger.py` - Тестовая утилита
- `analyze_graphics_logs.py` - Анализатор логов
- `logs/graphics/` - Директория логов

---

**Версия**: 5.0.0
**Последнее обновление**: 2024
**Автор**: PneumoStabSim Development Team
