# Система логирования графических изменений

## Описание

Система логирования отслеживает все изменения графических параметров в `GraphicsPanel` и анализирует их синхронизацию с QML сценой. Это критически важно для диагностики проблем синхронизации Python ↔ QML.

## Архитектура

### Компоненты

1. **GraphicsLogger** (`src/ui/panels/graphics_logger.py`)
   - Записывает все изменения параметров
   - Отслеживает применение изменений в QML
   - Анализирует синхронизацию
   - Экспортирует отчеты

2. **GraphicsPanel Integration** (`src/ui/panels/panel_graphics.py`)
   - Вызывает логгер при каждом изменении
   - Передает старые и новые значения
   - Категоризирует изменения

3. **Логи сессий** (`logs/graphics/session_*.jsonl`)
   - JSONL формат для легкого парсинга
   - Каждая строка - одно событие
   - Поддержка потоковой обработки

## Использование

### Базовый пример

```python
from ui.panels.panel_graphics import GraphicsPanel
from ui.panels.graphics_logger import get_graphics_logger

# Создаем панель (логгер инициализируется автоматически)
panel = GraphicsPanel()

# Изменяем параметр
panel.state["lighting"]["key"]["brightness"] = 1.5
panel._emit_lighting()

# Получаем логгер для анализа
logger = get_graphics_logger()

# Получаем последние изменения
recent = logger.get_recent_changes(10)
for event in recent:
    print(f"{event.parameter_name}: {event.old_value} → {event.new_value}")

# Экспортируем анализ
logger.export_analysis_report()
```

### Отслеживание QML обновлений

```python
# В обработчике сигнала изменения
def on_lighting_changed(self, data):
    logger = get_graphics_logger()
    recent = logger.get_recent_changes(1)

    if recent:
        event = recent[0]

        # Логируем успешное применение в QML
        logger.log_qml_update(
            event,
            qml_state={"applied_to_qml": True},
            success=True
        )

        # Или логируем ошибку
        # logger.log_qml_update(
        #     event,
        #     success=False,
        #     error="QML property not found"
        # )
```

### Анализ синхронизации

```python
logger = get_graphics_logger()

# Получить полный анализ
analysis = logger.analyze_qml_sync()

print(f"Всего изменений: {analysis['total_events']}")
print(f"Успешных QML обновлений: {analysis['successful_updates']}")
print(f"Процент синхронизации: {analysis['sync_rate']:.1f}%")

# Проблемные параметры
for param, errors in analysis['errors_by_parameter'].items():
    print(f"⚠️ {param}: {len(errors)} ошибок")
```

### Сравнение состояний

```python
logger = get_graphics_logger()

# Состояние панели
panel_state = panel.state

# Состояние QML (получаем из QML через signals)
qml_state = {...}

# Сравниваем
diff = logger.compare_states(panel_state, qml_state)

print(f"Совпадающих параметров: {len(diff['matching'])}")
print(f"Рассинхронизированных: {len(diff['mismatched'])}")

for mismatch in diff['mismatched']:
    print(f"  {mismatch['parameter']}:")
    print(f"    Panel: {mismatch['panel_value']}")
    print(f"    QML:   {mismatch['qml_value']}")
```

### Мониторинг HDR bloom и fallback'ов

- Каждый сдвиг `bloom.hdr_max` и `bloom.hdr_scale` появляется как отдельное событие `parameter_change` в `logs/graphics/session_*.jsonl` и содержит новое значение, диапазон и отметку успешного применения в QML. Используйте фильтр `grep "bloom.hdr_"` для быстрого просмотра.
- При выборе отсутствующего HDR-файла `MainWindow.normalizeHdrPath` логирует предупреждение `normalizeHdrPath: HDR asset not found (input=…, candidates=…)`, а панель окружения сбрасывает статус HDR на `—`. Эти сообщения помогают поддержке понять, почему bloom внезапно отключился.
- IBL-лог (`logs/ibl/ibl_signals_*.log`) дополняет картину: строки `IBL:Fallback` фиксируют переход на резервную HDR-карту, а значит, bloom будет использовать базовый набор значений из `config/app_settings.json`.

## Структура событий

### GraphicsChangeEvent

```python
@dataclass
class GraphicsChangeEvent:
    timestamp: str              # ISO формат
    parameter_name: str         # Имя параметра (например, "key.brightness")
    old_value: Any             # Старое значение
    new_value: Any             # Новое значение
    category: str              # lighting, material, environment, quality, camera, effects
    panel_state: Dict[str, Any] # Полное состояние панели
    qml_state: Optional[Dict[str, Any]] = None  # Состояние QML после применения
    applied_to_qml: bool = False               # Применено ли в QML
    error: Optional[str] = None                # Текст ошибки
```

## Формат логов

### Структура файла сессии

```jsonl
{"event_type": "session_start", "session_id": "20240101_120000", "timestamp": "2024-01-01T12:00:00"}
{"event_type": "parameter_change", "parameter_name": "key.brightness", "old_value": 1.2, "new_value": 1.5, ...}
{"event_type": "parameter_update", "parameter_name": "key.brightness", "applied_to_qml": true, ...}
{"event_type": "session_end", "session_id": "20240101_120000", "stats": {...}, "analysis": {...}}
```

### Отчет анализа (JSON)

```json
{
  "status": "ok",
  "total_events": 42,
  "with_qml_update": 38,
  "successful_updates": 36,
  "failed_updates": 2,
  "sync_rate": 85.7,
  "by_category": {
    "lighting": {
      "total": 12,
      "with_qml": 12,
      "successful": 12,
      "failed": 0
    },
    "camera": {
      "total": 5,
      "with_qml": 3,
      "successful": 2,
      "failed": 1
    }
  },
  "errors_by_parameter": {
    "camera.auto_rotate": ["QML property not found"]
  },
  "recent_changes": [...]
}
```

## Тестирование

### Запуск тестов

```bash
python test_graphics_logger.py
```

Тестовый скрипт:
1. Создает окно с GraphicsPanel
2. Автоматически выполняет тестовые изменения
3. Отслеживает применение в QML
4. Экспортирует анализ при закрытии

### Ожидаемый вывод

```
🧪 GRAPHICS LOGGER TEST STARTED
====================================================================
Test window ready. Use buttons to:
  1. Run test changes
  2. Export analysis report
====================================================================

🧪 Running test changes sequence...

1️⃣ Testing lighting changes...
📊 GRAPHICS CHANGE: lighting.key.brightness: 1.2 → 1.5
   ✅ QML updated: key.brightness

2️⃣ Testing environment changes...
📊 GRAPHICS CHANGE: environment.fog_density: 0.12 → 0.25
   ✅ QML updated: fog_density

...

====================================================================
📊 GRAPHICS SYNC ANALYSIS
====================================================================
Total changes: 6
Successful QML updates: 6
Failed QML updates: 0
Sync rate: 100.0%

By category:
  lighting: 1 changes, 1 synced
  environment: 1 changes, 1 synced
  camera: 1 changes, 1 synced
  quality: 1 changes, 1 synced
  effects: 1 changes, 1 synced
  material: 1 changes, 1 synced
====================================================================
Full report: logs/graphics/analysis_20240101_120000.json
====================================================================
```

## Интеграция с MainWindow

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Создаем панель графики
        self.graphics_panel = GraphicsPanel()

        # Подключаем сигналы для отслеживания QML обновлений
        self.graphics_panel.lighting_changed.connect(
            lambda data: self._on_graphics_updated("lighting", data)
        )
        # ... другие сигналы

    def _on_graphics_updated(self, category: str, data: dict):
        """Обработчик обновления графики"""
        logger = get_graphics_logger()
        recent = logger.get_recent_changes(1)

        if recent and recent[0].category == category:
            event = recent[0]

            try:
                # Применяем в QML
                self._apply_to_qml(category, data)

                # Логируем успех
                logger.log_qml_update(
                    event,
                    qml_state={"category": category, "data": data},
                    success=True
                )
            except Exception as e:
                # Логируем ошибку
                logger.log_qml_update(
                    event,
                    success=False,
                    error=str(e)
                )
```

## Диагностика проблем

### Низкий процент синхронизации

```python
analysis = logger.analyze_qml_sync()

if analysis['sync_rate'] < 90:
    print("⚠️ Низкий процент синхронизации!")

    # Проверяем проблемные категории
    for cat, stats in analysis['by_category'].items():
        if stats['failed'] > 0:
            print(f"  Проблемы в категории: {cat}")
            print(f"    Неудачных: {stats['failed']}/{stats['total']}")
```

### Поиск рассинхронизаций

```python
# Периодически сравниваем состояния
def check_sync():
    panel_state = graphics_panel.state
    qml_state = get_qml_state()  # Получаем из QML

    diff = logger.compare_states(panel_state, qml_state)

    if diff['mismatched']:
        print(f"⚠️ Найдено {len(diff['mismatched'])} рассинхронизаций")
        for m in diff['mismatched']:
            print(f"  {m['parameter']}: {m['panel_value']} != {m['qml_value']}")

# Запускаем проверку каждые 5 секунд
QTimer.interval(5000, check_sync)
```

## Лучшие практики

1. **Всегда логируйте результат применения в QML**
   - Используйте `log_qml_update()` после каждого изменения
   - Передавайте состояние QML для сравнения

2. **Регулярно экспортируйте анализ**
   - При закрытии приложения
   - После больших изменений
   - При возникновении ошибок

3. **Анализируйте логи при багах**
   - Проверяйте `errors_by_parameter`
   - Ищите паттерны в неудачных обновлениях
   - Сравнивайте состояния панели и QML

4. **Категоризируйте изменения правильно**
   - `lighting` - все источники света
   - `environment` - фон, туман, IBL, AO
   - `material` - параметры материалов
   - `quality` - настройки рендеринга
   - `camera` - параметры камеры
   - `effects` - постэффекты

## Расширение

### Добавление новой категории

```python
# В GraphicsPanel
def _update_custom(self, key: str, value: Any) -> None:
    if self._updating_ui:
        return

    old_value = self.state["custom"].get(key)
    self.state["custom"][key] = value

    # Логируем изменение
    self.graphics_logger.log_change(
        parameter_name=key,
        old_value=old_value,
        new_value=value,
        category="custom",  # Новая категория
        panel_state=self.state
    )

    self._emit_custom()
```

### Кастомные метрики

```python
# Расширяем GraphicsLogger
class CustomGraphicsLogger(GraphicsLogger):
    def analyze_performance(self) -> Dict[str, Any]:
        """Анализ производительности изменений"""
        timings = []

        for i in range(1, len(self.events_buffer)):
            prev = self.events_buffer[i-1]
            curr = self.events_buffer[i]

            prev_time = datetime.fromisoformat(prev.timestamp)
            curr_time = datetime.fromisoformat(curr.timestamp)

            delta = (curr_time - prev_time).total_seconds()
            timings.append(delta)

        return {
            'avg_time_between_changes': sum(timings) / len(timings),
            'max_time': max(timings),
            'min_time': min(timings)
        }
```

## Troubleshooting

### Проблема: События не логируются

**Решение**: Проверьте инициализацию логгера

```python
# Убедитесь, что логгер инициализирован
from ui.panels.graphics_logger import get_graphics_logger

logger = get_graphics_logger()
print(f"Logger initialized: {logger is not None}")
```

### Проблема: QML обновления не отслеживаются

**Решение**: Подключите обработчики сигналов

```python
# Подключите ВСЕ сигналы GraphicsPanel
panel.lighting_changed.connect(on_lighting_changed)
panel.environment_changed.connect(on_environment_changed)
panel.quality_changed.connect(on_quality_changed)
panel.camera_changed.connect(on_camera_changed)
panel.effects_changed.connect(on_effects_changed)
panel.material_changed.connect(on_material_changed)
```

### Проблема: Логи не сохраняются

**Решение**: Проверьте права доступа к директории

```python
from pathlib import Path

log_dir = Path("logs/graphics")
log_dir.mkdir(parents=True, exist_ok=True)

# Проверка прав записи
test_file = log_dir / "test.txt"
try:
    test_file.write_text("test")
    test_file.unlink()
    print("✅ Write access OK")
except Exception as e:
    print(f"❌ Write access denied: {e}")
```

---

**Версия**: 1.0.0
**Дата**: 2024
**Автор**: PneumoStabSim Development Team
