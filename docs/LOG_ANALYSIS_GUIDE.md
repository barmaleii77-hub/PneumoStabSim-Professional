# 🔍 Руководство по анализу логов PneumoStabSim

## 📋 Содержание
- [Быстрый старт](#быстрый-старт)
- [Что анализируется](#что-анализируется)
- [Интерпретация результатов](#интерпретация-результатов)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Быстрый старт

### 1. Запуск приложения и работа
```bash
python app.py
```
- Работайте с приложением
- Меняйте параметры графики
- Закройте приложение

### 2. Анализ логов
```bash
python analyze_logs.py
```

Скрипт автоматически найдёт и проанализирует все свежие логи.

---

## 📊 Что анализируется

### 🎨 **Graphics Logs** (`logs/graphics/session_*.jsonl`)

**Отслеживает:**
- Все изменения параметров графики
- Синхронизацию Python → QML
- Категории изменений (environment, quality, effects, lighting, camera)
- Временную шкалу событий

**Показывает:**
- ✅ Процент успешной синхронизации
- 📊 Распределение по категориям
- 🔝 Топ-10 изменённых параметров
- 🕐 Последние события с временными метками

### 💡 **IBL Logs** (`logs/ibl/ibl_signals_*.log`)

**Отслеживает:**
- События загрузки IBL
- Сигналы компонентов (IblProbeLoader, MainWindow)
- Ошибки и предупреждения HDR текстур

**Показывает:**
- 📋 Статистику по компонентам
- ❌ Ошибки загрузки
- ⚠️ Предупреждения

### 🔧 **System Logs** (`logs/run.log`)

**Отслеживает:**
- Системные ошибки
- Предупреждения
- QML события
- Время запуска/завершения

**Показывает:**
- ⏱️ Продолжительность сессии
- ❌ Критические ошибки
- ⚠️ Предупреждения системы

---

## 📈 Интерпретация результатов

### Синхронизация Python → QML

| Процент | Оценка | Описание |
|---------|--------|----------|
| **95-100%** | 🎉 **ОТЛИЧНО** | Система работает идеально |
| **85-94%** | ✅ **ХОРОШО** | Стабильная работа, незначительные задержки |
| **70-84%** | ⚠️ **УДОВЛЕТВОРИТЕЛЬНО** | Есть проблемы с синхронизацией |
| **<70%** | ❌ **ТРЕБУЕТ ВНИМАНИЯ** | Серьёзные проблемы |

### Пример вывода

```
📊 АНАЛИЗ ГРАФИЧЕСКИХ ЛОГОВ
--------------------------------------------------------------------------------
📄 Файл: session_20251013_171733.jsonl
📦 Размер: 4.6 MB

📈 СТАТИСТИКА:
   Всего событий: 3251
   Синхронизировано: 2902/3251 (89.3%)
   Ожидание: 349
   Ошибки: 0

   Синхронизация: ████████████████████████████████████████████░░░░░░ 89.3%

📋 ПО КАТЕГОРИЯМ:
   environment     1279 ( 39.3%)  ← Больше всего изменений окружения
   quality         956 ( 29.4%)   ← Изменения качества рендеринга
   effects         644 ( 19.8%)   ← Визуальные эффекты
   lighting        351 ( 10.8%)   ← Освещение
   camera          20 (  0.6%)    ← Камера

🔝 ТОП-10 ИЗМЕНЁННЫХ ПАРАМЕТРОВ:
   fog_density                    126x  ← Наиболее активный параметр
   rim.brightness                 116x
   point.brightness               102x
   ...
```

### Цветовая индикация

- 🟢 **Зелёный** — всё отлично, нет проблем
- 🟡 **Жёлтый** — предупреждения, требует внимания
- 🔴 **Красный** — ошибки, требует исправления
- 🔵 **Синий** — информация, нейтральные данные

---

## 💡 Рекомендации

### Если синхронизация < 95%

**Проблема:** Не все параметры синхронизируются с QML

**Решение:**
1. Проверьте QML функции `applyXxxUpdates()` в `main.qml`
2. Убедитесь, что все свойства объявлены
3. Проверьте маппинг параметров в `MainWindow.py`

**Пример исправления:**
```qml
// main.qml
function applyEnvironmentUpdates(params) {
    if (params.fog_enabled !== undefined) {
        fogEnabled = params.fog_enabled  // ✅ Правильный маппинг
    }
    // ... остальные параметры
}
```

### Если много ожидающих событий (pending)

**Проблема:** Слишком быстрые изменения параметров (слайдеры)

**Решение:** Добавьте debounce

**Пример:**
```python
# panel_graphics.py
from PySide6.QtCore import QTimer

class GraphicsPanel:
    def __init__(self):
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._emit_delayed_update)
    
    def on_slider_change(self, value):
        self._pending_value = value
        self._update_timer.start(100)  # Debounce 100ms
    
    def _emit_delayed_update(self):
        self._emit_environment()
```

### Если есть IBL ошибки

**Проблема:** HDR текстуры не загружаются

**Решение:**
1. Проверьте пути к файлам в `assets/hdr/`
2. Убедитесь, что файлы существуют
3. Проверьте права доступа

```bash
# Проверка наличия файлов
ls -la assets/hdr/
```

---

## 🔍 Troubleshooting

### Логи не создаются

**Симптомы:** 
- `analyze_logs.py` показывает "файлы не найдены"
- Директория `logs/` пустая

**Решение:**
1. Убедитесь, что приложение запустилось корректно
2. Проверьте права на запись в директорию `logs/`
3. Проверьте, что `GraphicsLogger` инициализирован в `MainWindow`

```python
# main_window.py
self.graphics_logger = GraphicsLogger()  # ✅ Должен быть вызван
```

### Цвета не отображаются в консоли

**Симптомы:** Вместо цветов видны коды `\033[91m`

**Решение (Windows):**
```bash
# PowerShell
$env:FORCE_COLOR = "true"
python analyze_logs.py

# CMD
set FORCE_COLOR=true
python analyze_logs.py
```

**Решение (постоянное):**
```python
# Редактируйте analyze_logs.py
# Удалите класс Colors или используйте colorama
```

### Ошибка при чтении JSONL

**Симптомы:**
```
❌ Ошибка загрузки: json.decoder.JSONDecodeError
```

**Решение:**
1. Проверьте кодировку файла (должна быть UTF-8)
2. Проверьте, что файл не повреждён
3. Удалите повреждённый файл и создайте новую сессию

```bash
# Проверка кодировки
file logs/graphics/session_*.jsonl

# Удаление повреждённого файла
rm logs/graphics/session_CORRUPT.jsonl
```

---

## 📁 Структура логов

```
logs/
├── graphics/
│   └── session_YYYYMMDD_HHMMSS.jsonl  # Графические события
├── ibl/
│   └── ibl_signals_YYYYMMDD_HHMMSS.log  # IBL события
└── run.log  # Системный лог
```

### Формат Graphics Log

```json
{
  "timestamp": "2025-10-13T17:18:58.123456",
  "category": "effects",
  "parameter_name": "bloom_enabled",
  "old_value": false,
  "new_value": true,
  "applied_to_qml": true,
  "qml_state": {
    "applied": true,
    "timestamp": "2025-10-13T17:18:58.125000"
  }
}
```

### Формат IBL Log

```
2025-10-13T17:17:32.769684 | INFO | MainWindow | IBL Logger initialized
2025-10-13T12:17:32.917Z | INFO | IblProbeLoader | Primary source changed: file:///...
```

---

## 🎯 Использование в CI/CD

### GitHub Actions

```yaml
- name: Analyze Logs
  run: |
    python app.py --test-mode
    python analyze_logs.py > analysis_report.txt
    
- name: Upload Report
  uses: actions/upload-artifact@v3
  with:
    name: log-analysis
    path: analysis_report.txt
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
python analyze_logs.py --quiet
if [ $? -ne 0 ]; then
    echo "❌ Логи содержат критические ошибки!"
    exit 1
fi
```

---

## 📚 Дополнительные ресурсы

- [GRAPHICS_LOGGING_QUICKSTART.md](docs/GRAPHICS_LOGGING_QUICKSTART.md)
- [IBL_LOGGING_GUIDE.md](docs/IBL_LOGGING_GUIDE.md)
- [GRAPHICS_SYNC_FIX_REPORT.md](GRAPHICS_SYNC_FIX_REPORT.md)

---

## 🆘 Получение помощи

Если возникли проблемы:

1. Проверьте эту документацию
2. Посмотрите секцию [Troubleshooting](#troubleshooting)
3. Создайте issue с выводом `analyze_logs.py`

**Шаблон issue:**
```markdown
## Проблема
[Краткое описание]

## Вывод analyze_logs.py
```
[Вставьте вывод]
```

## Окружение
- Python: [версия]
- Qt: [версия]
- OS: [Windows/Linux/macOS]
```

---

**Последнее обновление:** 2024-10-13  
**Версия:** 1.0.0
