# 📊 Улучшенная система логирования v4.9.5

## ✨ Что нового

### 1. **Ротация логов**
- Автоматическое удаление старых логов (хранятся только последние 10)
- Ротация по размеру (10 MB на файл)
- 5 backup файлов на каждый основной лог

### 2. **Унифицированный анализатор**
- Один модуль `log_analyzer.py` вместо трех отдельных
- Комплексный анализ всех типов логов
- Автоматическая генерация рекомендаций

### 3. **Контекстные логгеры**
- Каждый модуль может добавлять свой контекст
- Автоматическое кэширование логгеров
- Улучшенное форматирование с микросекундами

### 4. **Улучшенная диагностика**
- Автоматический запуск после закрытия приложения
- Детальный анализ синхронизации Python↔QML
- Метрики производительности

---

## 📂 Структура логов

```
logs/
├── PneumoStabSim_YYYYMMDD_HHMMSS.log       # Основной лог с timestamp
├── PneumoStabSim_YYYYMMDD_HHMMSS.log.1     # Backup 1
├── PneumoStabSim_YYYYMMDD_HHMMSS.log.2     # Backup 2
├── run.log                                  # Всегда текущий лог (перезаписывается)
├── graphics/
│   ├── session_YYYYMMDD_HHMMSS.jsonl
│   └── analysis_YYYYMMDD_HHMMSS.json
├── ibl/
│   └── ibl_signals_YYYYMMDD_HHMMSS.log
└── events/
    └── python_qml_events.json
```

---

## 🚀 Использование

### Базовое логирование

```python
from src.common.logging_setup import get_category_logger

# Получить логгер для модуля
logger = get_category_logger("MyModule")

# Логирование различных уровней
logger.debug("Детальная информация")
logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.critical("Критическая ошибка")
```

### Логирование с контекстом

```python
from src.common.logging_setup import get_category_logger

# Создаем логгер с контекстом
context = {
    "component": "GraphicsPanel",
    "version": "4.9.5"
}

logger = get_category_logger("UI", context=context)

# Каждое сообщение будет содержать контекст
logger.info("Panel initialized")
# Output: ... | UI | component=GraphicsPanel version=4.9.5 | Panel initialized
```

### Специализированные логгеры

```python
from src.common.logging_setup import (
    log_ui_event,
    log_geometry_change,
    log_exception
)

# UI событие
log_ui_event("button_click", "Geometry panel opened", user="admin")

# Изменение геометрии
log_geometry_change("wheelbase", 2400.0, 2500.0, unit="mm")

# Exception с контекстом
try:
    risky_operation()
except Exception as exc:
    log_exception(exc, context="Loading HDR texture", file_path="studio.hdr")
```

---

## 📊 Автоматическая диагностика

### При закрытии приложения

Автоматически запускается комплексный анализ:

```
============================================================
🔍 ДИАГНОСТИКА ЛОГОВ И СОБЫТИЙ
============================================================

======================================================================
📊 КОМПЛЕКСНЫЙ АНАЛИЗ ЛОГОВ
======================================================================

📁 MAIN
----------------------------------------------------------------------

Метрики:
  • total_lines: 342
  • errors: 0
  • warnings: 2
  • runtime_seconds: 45.3

ℹ️  Информация:
  Основной лог чистый - ошибок нет
  Время работы: 45.3s

⚠️  Предупреждения:
  Обнаружено 2 предупреждений

📁 GRAPHICS
----------------------------------------------------------------------

Метрики:
  • graphics_total_events: 87
  • graphics_synced: 85
  • graphics_failed: 0
  • graphics_sync_rate: 97.7

ℹ️  Информация:
  Синхронизация графики: 97.7% (отлично)
  Категории изменений: {'lighting': 25, 'camera': 15, ...}

📁 IBL
----------------------------------------------------------------------

Метрики:
  • ibl_total_events: 12
  • ibl_errors: 0
  • ibl_success: 2

ℹ️  Информация:
  IBL успешно загружен (2 событий)

📁 EVENTS
----------------------------------------------------------------------

Метрики:
  • event_total: 87
  • event_synced: 85
  • event_missing: 2
  • event_sync_rate: 97.7

ℹ️  Информация:
  Python↔QML синхронизация: 97.7% (отлично)

⚠️  Предупреждения:
  Пропущено QML событий: 2

======================================================================
📋 ИТОГИ
======================================================================

Статус: ⚠️ WARNING
Ошибок: 0
Предупреждений: 3

💡 Рекомендации:
  1. Проверьте QML connections и signals

======================================================================

============================================================
⚠️  Диагностика завершена - обнаружены проблемы
💡 См. детали выше
============================================================
```

---

## 🔧 Конфигурация

### В app.py

```python
from src.common.logging_setup import init_logging, rotate_old_logs

# Ротация старых логов (оставляем только 10 последних)
rotate_old_logs(logs_dir, keep_count=10)

# Инициализация с настройками
logger = init_logging(
    "PneumoStabSim",
    logs_dir,
    max_bytes=10 * 1024 * 1024,  # 10 MB на файл
    backup_count=5,               # 5 backup файлов
    console_output=False          # НЕ выводим в консоль (по умолчанию)
)
```

### Verbose mode

```bash
# Включить вывод логов в консоль
py app.py --verbose
```

В этом режиме логи INFO+ дублируются в консоль с цветным форматированием.

---

## 📈 Метрики

### Автоматические метрики

Система автоматически собирает:

- **Основной лог:**
  - Общее количество строк
  - Количество ошибок
  - Количество предупреждений
  - Время работы приложения

- **Graphics:**
  - Общее количество событий
  - Синхронизированные события
  - Неудачные обновления
  - Процент синхронизации
  - Распределение по категориям

- **IBL:**
  - Всего событий
  - Ошибки загрузки
  - Предупреждения
  - Успешные загрузки

- **Events (Python↔QML):**
  - Всего сигналов
  - Синхронизированных
  - Пропущенных QML
  - Процент синхронизации

### Пользовательские метрики

```python
from src.common.logging_setup import log_performance_metric

# Логирование своих метрик
log_performance_metric("frame_time", 16.7, unit="ms")
log_performance_metric("memory_usage", 125.5, unit="MB")
log_performance_metric("sync_rate", 97.5, unit="%")
```

---

## 🎯 Рекомендации

### 1. Когда использовать разные уровни

- **DEBUG**: Детальная диагностика (параметры, состояния)
- **INFO**: Информационные сообщения (инициализация, события)
- **WARNING**: Проблемы, которые можно игнорировать
- **ERROR**: Ошибки, требующие внимания
- **CRITICAL**: Фатальные ошибки

### 2. Категории логгеров

Используйте стандартные категории:

```python
# UI события
logger = get_category_logger("UI")

# Геометрия
logger = get_category_logger("GEOMETRY")

# Графика
logger = get_category_logger("GRAPHICS")

# IBL
logger = get_category_logger("IBL")

# QML
logger = get_category_logger("QML")

# Симуляция
logger = get_category_logger("SIMULATION")
```

### 3. Обработка исключений

```python
from src.common.logging_setup import log_exception

try:
    risky_operation()
except Exception as exc:
    log_exception(
        exc,
        context="Critical operation",
        param1="value1",
        param2="value2"
    )
    # Дальнейшая обработка...
```

---

## 🐛 Troubleshooting

### Проблема: Логи не создаются

**Решение:**
```python
# Проверьте инициализацию
logger = setup_logging()
if logger:
    print("✅ Logging OK")
else:
    print("❌ Logging failed")
```

### Проблема: Слишком большие логи

**Решение:**
```python
# Увеличьте ротацию
rotate_old_logs(logs_dir, keep_count=20)

# Или уменьшите max_bytes
logger = init_logging(
    "PneumoStabSim",
    logs_dir,
    max_bytes=5 * 1024 * 1024,  # 5 MB вместо 10 MB
    backup_count=3
)
```

### Проблема: Диагностика не запускается

**Проверьте:**
```bash
# Есть ли модуль log_analyzer?
py -c "from src.common.log_analyzer import run_full_diagnostics; print('OK')"

# Fallback на старую версию
py analyze_logs.py
```

---

## 📚 API Reference

### logging_setup.py

#### `init_logging(app_name, log_dir, max_bytes=10MB, backup_count=5, console_output=False)`
Инициализирует логирование с ротацией

#### `get_category_logger(category, context=None)`
Получает логгер для категории с опциональным контекстом

#### `rotate_old_logs(log_dir, keep_count=10)`
Удаляет старые логи, оставляя только последние N

#### Специализированные функции:
- `log_valve_event(time, line, kind, state, dp, mdot)`
- `log_pressure_update(time, location, pressure, temperature, mass)`
- `log_ode_step(time, step_num, dt, error=None)`
- `log_export(operation, path, rows)`
- `log_ui_event(event, details="", **kwargs)`
- `log_geometry_change(param_name, old_value, new_value, **kwargs)`
- `log_simulation_step(step_num, sim_time, dt)`
- `log_performance_metric(metric_name, value, unit="")`
- `log_exception(exc, context="", **kwargs)`

### log_analyzer.py

#### `run_full_diagnostics(logs_dir=Path("logs"))`
Запускает полную диагностику всех логов
- Returns: `bool` - True если нет критических проблем

#### `quick_diagnostics(logs_dir=Path("logs"))`
Быстрая диагностика - только ключевые метрики
- Returns: `Dict[str, any]` с метриками

---

## ✅ Итоги улучшений

| Компонент | Было | Стало |
|-----------|------|-------|
| **Ротация** | Ручная очистка | Автоматическая |
| **Размер логов** | Неограниченный | 10 MB + 5 backups |
| **Анализаторы** | 3 отдельных скрипта | 1 унифицированный |
| **Контекст** | Нет | Опциональный |
| **Микросекунды** | Нет | Есть |
| **Цветной вывод** | Нет | Опциональный |
| **Кэширование логгеров** | Нет | Автоматическое |

---

**Версия**: v4.9.5  
**Дата**: 2025-01-13  
**Статус**: ✅ Полностью реализовано
