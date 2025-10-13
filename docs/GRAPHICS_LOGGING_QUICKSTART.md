# Quick Start: Graphics Logging

## 🚀 Быстрый старт

### 1. Запуск теста

```bash
python test_graphics_logger.py
```

### 2. Просмотр результатов

Логи сохраняются в `logs/graphics/`:
- `session_YYYYMMDD_HHMMSS.jsonl` - детальный лог изменений
- `analysis_YYYYMMDD_HHMMSS.json` - отчет анализа

### 3. Анализ в коде

```python
from ui.panels.graphics_logger import get_graphics_logger

logger = get_graphics_logger()

# Последние изменения
for event in logger.get_recent_changes(5):
    print(f"{event.parameter_name}: {event.old_value} → {event.new_value}")

# Статистика синхронизации
analysis = logger.analyze_qml_sync()
print(f"Sync rate: {analysis['sync_rate']:.1f}%")

# Экспорт отчета
logger.export_analysis_report()
```

## 📊 Что отслеживается

- ✅ **Lighting** - все источники света (key, fill, rim, point)
- ✅ **Environment** - фон, туман, IBL, AO
- ✅ **Quality** - тени, AA, производительность
- ✅ **Camera** - FOV, clipping, скорость
- ✅ **Effects** - bloom, DOF, motion blur
- ✅ **Materials** - все параметры PBR материалов

## 🔍 Что анализируется

- Количество изменений по категориям
- Процент успешной синхронизации с QML
- Параметры с ошибками
- Рассинхронизация Panel ↔ QML

## 📁 Структура логов

```
logs/graphics/
├── session_20240101_120000.jsonl     # Детальный лог
└── analysis_20240101_120000.json     # Анализ сессии
```

## 🐛 Диагностика проблем

### Проблема: Низкий sync rate

```python
analysis = logger.analyze_qml_sync()

if analysis['sync_rate'] < 90:
    # Смотрим ошибки
    for param, errors in analysis['errors_by_parameter'].items():
        print(f"⚠️ {param}: {errors}")
```

### Проблема: Параметр не применяется в QML

```python
# Проверяем последние изменения
recent = logger.get_recent_changes(10)

for event in recent:
    if event.parameter_name == "camera.auto_rotate":
        print(f"Applied to QML: {event.applied_to_qml}")
        print(f"Error: {event.error}")
```

## 📚 Полная документация

См. [GRAPHICS_LOGGING.md](GRAPHICS_LOGGING.md) для подробной информации.

---

**Tip**: Используйте `panel.export_sync_analysis()` для быстрого экспорта отчета из GraphicsPanel.
