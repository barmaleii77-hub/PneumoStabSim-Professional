# 🚀 Система логирования - Quick Start

## 1-минутная инструкция

### Использование в коде

```python
# 1. Получить логгер
from src.common.logging_setup import get_category_logger

logger = get_category_logger("MyModule")

# 2. Логировать
logger.info("Модуль инициализирован")
logger.debug(f"Параметр изменен: {value}")
logger.warning("Внимание: потенциальная проблема")
logger.error("Ошибка обработки")
```

### Запуск приложения

```bash
# Обычный запуск
py app.py

# С выводом в консоль
py app.py --verbose

# Тест-режим (5 сек + диагностика)
py app.py --test-mode
```

### После закрытия

Автоматически запускается диагностика и выводит результаты в консоль:

```
🔍 ДИАГНОСТИКА ЛОГОВ И СОБЫТИЙ
...
✅ Диагностика завершена
```

## Специализированные функции

```python
from src.common.logging_setup import (
    log_ui_event,
    log_geometry_change,
    log_exception,
    log_performance_metric
)

# UI событие
log_ui_event("button_click", "Settings opened")

# Геометрия
log_geometry_change("wheelbase", 2400, 2500, unit="mm")

# Ошибка
try:
    something()
except Exception as exc:
    log_exception(exc, context="Operation failed")

# Метрика
log_performance_metric("frame_time", 16.7, unit="ms")
```

## Категории логгеров

- `UI` - UI события
- `GEOMETRY` - геометрия
- `GRAPHICS` - графика
- `IBL` - IBL события
- `QML` - QML события
- `SIMULATION` - симуляция
- `PERFORMANCE` - производительность

## Логи хранятся в

```
logs/
├── PneumoStabSim_YYYYMMDD_HHMMSS.log  # Основной
├── run.log                             # Текущий (всегда)
├── graphics/                           # Графика
├── ibl/                                # IBL
└── events/                             # Python↔QML
```

## Автоматическая ротация

- ✅ Старые логи удаляются (хранятся только 10 последних)
- ✅ Ротация по размеру (10 MB → создается backup)
- ✅ Держится 5 backup файлов

## Полная документация

См. `docs/LOGGING_SYSTEM_V495.md`

---

**Tip**: Всегда проверяйте результаты диагностики после закрытия приложения!
