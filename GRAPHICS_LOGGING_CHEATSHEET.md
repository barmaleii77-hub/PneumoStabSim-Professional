# 🚀 Graphics Logging - Краткая памятка

## Быстрые команды

```bash
# 1. Запустить тест
python test_graphics_logger.py

# 2. Анализировать последний лог
python analyze_graphics_logs.py logs/graphics/session_*.jsonl

# 3. Экспорт в CSV
python analyze_graphics_logs.py logs/graphics/session_*.jsonl --csv

# 4. Очистить старые логи
# Windows
del logs\graphics\*.jsonl
del logs\graphics\*.json

# Linux/macOS
rm logs/graphics/*.jsonl logs/graphics/*.json
```

## Ключевой код

### В коде приложения

```python
from ui.panels.graphics_logger import get_graphics_logger

# Получить логгер
logger = get_graphics_logger()

# Последние изменения
for event in logger.get_recent_changes(5):
    print(f"{event.parameter_name}: {event.old_value} → {event.new_value}")

# Анализ
analysis = logger.analyze_qml_sync()
print(f"Sync rate: {analysis['sync_rate']:.1f}%")

# Экспорт
logger.export_analysis_report()
```

### Логирование QML обновления

```python
def _log_qml_update(self, category: str, data: dict):
    logger = get_graphics_logger()
    recent = logger.get_recent_changes(1)
    
    if recent and recent[0].category == category:
        event = recent[0]
        
        try:
            # Применить в QML
            self._apply_to_qml(data)
            
            # Логировать успех
            logger.log_qml_update(event, qml_state=data, success=True)
        except Exception as e:
            # Логировать ошибку
            logger.log_qml_update(event, success=False, error=str(e))
```

## Структура файлов

```
PneumoStabSim-Professional/
├── src/ui/panels/
│   ├── graphics_logger.py         # ✅ Основной логгер
│   └── panel_graphics.py          # ✅ Интеграция
├── test_graphics_logger.py        # ✅ Тестовая утилита
├── analyze_graphics_logs.py       # ✅ Анализатор
├── logs/graphics/
│   ├── .gitignore                 # ✅ Исключает логи
│   ├── README.md                  # ✅ Описание
│   ├── session_*.jsonl            # Создается автоматически
│   └── analysis_*.json            # Создается автоматически
└── docs/
    ├── GRAPHICS_LOGGING.md        # ✅ Полная документация
    ├── GRAPHICS_LOGGING_QUICKSTART.md  # ✅ Быстрый старт
    └── README_GRAPHICS_LOGGING.md # ✅ Обзор
```

## Категории изменений

- **lighting** - ключевой, заполняющий, контровой, точечный свет
- **environment** - фон, туман, IBL, AO
- **quality** - тени, AA, производительность
- **camera** - FOV, clipping, auto_rotate
- **effects** - bloom, DOF, motion blur, vignette
- **material** - все PBR параметры материалов

## Диагностика

```python
# Проверить sync rate
analysis = logger.analyze_qml_sync()
if analysis['sync_rate'] < 90:
    print("⚠️ Низкая синхронизация!")

# Найти ошибки
for param, errors in analysis['errors_by_parameter'].items():
    print(f"❌ {param}: {errors}")

# Сравнить состояния
diff = logger.compare_states(panel_state, qml_state)
print(f"Рассинхронизаций: {len(diff['mismatched'])}")
```

## Полезные ссылки

- `docs/GRAPHICS_LOGGING.md` - полная документация
- `docs/GRAPHICS_LOGGING_QUICKSTART.md` - быстрый старт
- `GRAPHICS_LOGGING_COMPLETE.md` - что сделано

---

**Совет**: Всегда проверяйте `sync_rate` - он должен быть >95% для стабильной работы.
