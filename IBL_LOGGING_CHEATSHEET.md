# IBL Signal Flow - Quick Reference Card

## 🚀 Quick Start

```bash
# Запуск с IBL логированием
python app.py

# Логи создаются автоматически:
logs/ibl/ibl_signals_YYYYMMDD_HHMMSS.log
```

## 📊 Формат лога

```
timestamp | level | source | message
```

**Пример**:
```
2024-01-15T10:30:45.500 | INFO | IblProbeLoader | Texture status: Ready
```

## 🔍 Быстрый анализ

### Windows (PowerShell)
```powershell
# Последний лог
ls logs\ibl\*.log | sort LastWriteTime -desc | select -first 1

# Все ошибки
cat logs\ibl\*.log | sls "ERROR"

# События загрузки
cat logs\ibl\*.log | sls "LOADED successfully"

# Fallback события
cat logs\ibl\*.log | sls "switching to fallback"
```

### Linux/macOS (Bash)
```bash
# Последний лог
ls -t logs/ibl/*.log | head -1

# Все ошибки
grep "ERROR" logs/ibl/*.log

# События загрузки
grep "LOADED successfully" logs/ibl/*.log

# Fallback события
grep "switching to fallback" logs/ibl/*.log
```

## 📈 Уровни событий

| Уровень | Значение |
|---------|----------|
| `INFO` | Информация |
| `WARN` | Предупреждение |
| `ERROR` | Ошибка |
| `SUCCESS` | Успех |

## 🔄 Типичные сценарии

### ✅ Успех
```
INFO → Texture status: Loading → SUCCESS: LOADED successfully
```

### ⚠️ Fallback
```
WARN: FAILED → switching to fallback → SUCCESS: LOADED successfully
```

### ❌ Провал
```
ERROR: FAILED → WARN: switching to fallback → ERROR: Both probes failed
```

## 🎯 Ключевые события

| Событие | Что значит |
|---------|------------|
| `IblProbeLoader initialized` | Компонент создан |
| `Texture status: Loading` | Загрузка началась |
| `Texture status: Ready` | Текстура готова |
| `Texture status: Error` | Ошибка загрузки |
| `HDR probe FAILED` | Не удалось загрузить |
| `switching to fallback` | Переход на резерв |
| `LOADED successfully` | Успешно загружено |
| `Both probes failed` | Все источники мертвы |

## 🐛 Быстрая диагностика

### Проблема: Нет логов
```bash
# Проверка регистрации
grep "IBL Logger registered" logs/ibl/*.log
```
**Решение**: `setContextProperty` должен быть ДО `setSource`

### Проблема: TypeError в QML
```bash
# Поиск ошибки
grep "logIblEvent.*null" app_output.log
```
**Решение**: Контекст `window` не установлен

### Проблема: Нет событий от QML
```bash
# Проверка инициализации
grep "IblProbeLoader initialized" logs/ibl/*.log
```
**Решение**: Проверьте `writeLog()` в QML

## 📁 Файлы

```
src/ui/ibl_logger.py              # Логгер
src/ui/main_window.py             # Интеграция
assets/qml/components/
  IblProbeLoader.qml              # QML компонент
logs/ibl/
  ibl_signals_*.log               # Лог-файлы
```

## 💡 Pro Tips

1. **Автоматическое сохранение** - flush после каждой записи
2. **Новый файл при запуске** - timestamp в имени
3. **ISO timestamp** - легко парсить
4. **Консоль дублируется** - логи видны в терминале

## 🔗 Полная документация

См. `docs/IBL_LOGGING_GUIDE.md`

---

**v1.0** | 2024
