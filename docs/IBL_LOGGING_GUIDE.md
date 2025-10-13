# IBL Signal Flow Analysis - Quick Start Guide

## 📝 Что это?

Система анализа сигналов IBL (Image-Based Lighting) записывает все события загрузки HDR текстур в timestamped лог-файлы для последующего анализа.

## 🚀 Быстрый старт

### 1. Запуск приложения с IBL логированием

```bash
python app.py
```

Логи автоматически создаются в:
```
logs/ibl/ibl_signals_YYYYMMDD_HHMMSS.log
```

### 2. Структура лог-файла

```
================================================================================
IBL SIGNAL LOGGER - Signal Flow Analysis
Log started: 2024-01-15T10:30:45.123456
================================================================================

FORMAT: timestamp | level | source | message
--------------------------------------------------------------------------------

2024-01-15T10:30:45.200 | INFO | MainWindow | IBL Logger initialized
2024-01-15T10:30:45.250 | INFO | MainWindow | IBL Logger registered in QML context (BEFORE QML load)
2024-01-15T10:30:45.500 | INFO | IblProbeLoader | IblProbeLoader initialized | Primary: file:///.../hdr/studio.hdr | Fallback: file:///.../assets/studio_small_09_2k.hdr
2024-01-15T10:30:45.550 | INFO | IblProbeLoader | Texture status: Loading | source: file:///.../hdr/studio.hdr
2024-01-15T10:30:45.800 | SUCCESS | IblProbeLoader | HDR probe LOADED successfully: file:///.../hdr/studio.hdr
```

## 📊 Уровни событий

| Уровень | Описание | Пример |
|---------|----------|--------|
| `INFO` | Информационное событие | "IblProbeLoader initialized" |
| `WARN` | Предупреждение | "HDR probe FAILED - switching to fallback" |
| `ERROR` | Ошибка | "CRITICAL: Both HDR probes failed" |
| `SUCCESS` | Успешная операция | "HDR probe LOADED successfully" |

## 🔍 Типичные сценарии

### ✅ Успешная загрузка

```
INFO | IblProbeLoader | IblProbeLoader initialized
INFO | IblProbeLoader | Texture status: Loading
SUCCESS | IblProbeLoader | HDR probe LOADED successfully
```

### ⚠️ Fallback сценарий

```
INFO | IblProbeLoader | Texture status: Loading
WARN | IblProbeLoader | HDR probe FAILED - switching to fallback: ...
INFO | IblProbeLoader | Texture status: Loading
SUCCESS | IblProbeLoader | HDR probe LOADED successfully: [fallback]
```

### ❌ Полный провал

```
ERROR | IblProbeLoader | HDR probe FAILED
WARN | IblProbeLoader | Switching to fallback
ERROR | IblProbeLoader | CRITICAL: Both HDR probes failed to load
```

## 🔧 Отслеживаемые события

### QML события (IblProbeLoader.qml)

1. **Инициализация**
   - `IblProbeLoader initialized` - компонент создан
   - Логирует primary и fallback источники

2. **Изменение статуса текстуры**
   - `Texture status: Null/Loading/Ready/Error` - изменение статуса
   - Проверяется каждые 100ms через Timer

3. **Смена источника**
   - `Primary source changed` - изменился основной источник
   - `Fallback source changed` - изменился резервный источник

4. **Fallback логика**
   - `HDR probe FAILED - switching to fallback` - переключение на резерв
   - `Both HDR probes failed` - оба источника недоступны

5. **Успешная загрузка**
   - `HDR probe LOADED successfully` - текстура загружена

6. **Уничтожение**
   - `IblProbeLoader destroyed` - компонент удален

### Python события (MainWindow)

1. **Инициализация логгера**
   - `IBL Logger initialized` - логгер создан
   - `IBL Logger registered in QML context` - регистрация в QML

2. **Закрытие приложения**
   - `IBL Logger closed on application exit` - корректное закрытие

## 📈 Анализ логов

### Grep команды

```bash
# Все ошибки
grep "ERROR" logs/ibl/ibl_signals_*.log

# Все события загрузки
grep "LOADED successfully" logs/ibl/ibl_signals_*.log

# Все fallback переключения
grep "switching to fallback" logs/ibl/ibl_signals_*.log

# Хронология конкретного источника
grep "studio.hdr" logs/ibl/ibl_signals_*.log
```

### PowerShell анализ

```powershell
# Последний лог-файл
Get-ChildItem logs/ibl/*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Количество ошибок
(Get-Content logs/ibl/ibl_signals_*.log | Select-String "ERROR").Count

# События по уровням
Get-Content logs/ibl/ibl_signals_*.log | Select-String "INFO|WARN|ERROR|SUCCESS" | Group-Object { ($_ -split '\|')[1].Trim() }
```

## 🐛 Диагностика проблем

### Проблема: Лог-файл пустой

**Причина**: Контекст `window` не зарегистрирован в QML

**Проверка**:
```
grep "IBL Logger registered in QML context" logs/ibl/*.log
```

**Решение**: Убедитесь что `setContextProperty("window", self)` вызывается ДО `setSource(qml_url)`

### Проблема: Нет событий от QML

**Причина**: `window.logIblEvent()` недоступен в QML

**Проверка**:
```
grep "TypeError.*logIblEvent.*null" app_output.log
```

**Решение**: Контекст должен устанавливаться ПЕРЕД загрузкой QML файла

### Проблема: "Cannot read property 'logIblEvent' of null"

**Причина**: `window` равен `null` в QML

**Решение**:
1. Проверьте порядок вызовов в `_setup_qml_3d_view()`
2. `context.setContextProperty("window", self)` должен быть ДО `self._qquick_widget.setSource(qml_url)`

### Проблема: "QML Connections: no signal matches onStatusChanged"

**Причина**: `Texture` не имеет сигнала `statusChanged`

**Решение**: Используем `Timer` для polling статуса вместо `Connections`

## 📁 Структура файлов

```
logs/ibl/
├── ibl_signals_20240115_103045.log  # Первый запуск
├── ibl_signals_20240115_110230.log  # Второй запуск
└── ibl_signals_20240115_143520.log  # Третий запуск

src/ui/
├── ibl_logger.py                    # Python IBL логгер
└── main_window.py                   # Интеграция логгера

assets/qml/components/
└── IblProbeLoader.qml              # QML IBL компонент с логированием
```

## 🎯 Полезные паттерны анализа

### 1. Timeline события для конкретной сессии

```bash
cat logs/ibl/ibl_signals_20240115_103045.log | grep "IblProbeLoader"
```

### 2. Проверка успешности fallback

```bash
cat logs/ibl/*.log | grep -A 3 "switching to fallback"
# Должно быть "LOADED successfully" через ~3 строки
```

### 3. Поиск критических ошибок

```bash
cat logs/ibl/*.log | grep "CRITICAL"
```

### 4. Статистика по уровням событий

```bash
cat logs/ibl/*.log | cut -d'|' -f2 | sort | uniq -c
```

## 💡 Tips & Tricks

1. **Логи сохраняются автоматически** - ничего дополнительно делать не нужно
2. **Каждый запуск = новый файл** - логи не перезаписываются
3. **Timestamp в ISO формате** - легко сортировать и фильтровать
4. **Flush после каждой записи** - логи сохраняются даже если приложение крашится

## 🔗 Связанные файлы

- `src/ui/ibl_logger.py` - реализация логгера
- `src/ui/main_window.py` - интеграция в MainWindow
- `assets/qml/components/IblProbeLoader.qml` - QML компонент с логированием
- `logs/ibl/` - директория с лог-файлами

## 📞 Поддержка

При возникновении проблем:
1. Проверьте наличие `logs/ibl/` директории
2. Убедитесь что логи создаются (проверьте timestamp в имени файла)
3. Проверьте права на запись в `logs/` директорию
4. Посмотрите консольный вывод на наличие ошибок Python

---

**Последнее обновление**: 2024-01-15
**Версия**: 1.0
