# 🤖 GitHub Copilot Configuration Guide

## ✅ Настройки применены успешно!

### 📁 Созданные файлы

1. **`.github/copilot-instructions.md`** ✅ (опубликовано на GitHub)
   - Инструкции для GitHub Copilot
   - Правила кодирования на русском языке
   - Python 3.13 и Qt 6.10 best practices

2. **`.vscode/settings.json`** ✅ (локально обновлено)
   - VS Code настройки для проекта
   - GitHub Copilot включён
   - Python 3.13 конфигурация
   - Qt 6.10 переменные окружения

3. **`.vscode/extensions.json`** ✅ (локально обновлено)
   - Рекомендуемые расширения
   - GitHub Copilot и Copilot Chat

---

## 🚀 Как использовать

### 0. Подготовка окружения
1. Запусти `make cipilot-env` — команда создаст `.env.cipilot` и отчёт `reports/quality/cipilot_environment.json`.
2. Подключи переменные окружения: `source ./.env.cipilot` (PowerShell: `Get-Content .env.cipilot | ForEach-Object { $_ -replace '^export ', 'set ' }`).
3. Убедись, что в отчёте зафиксированы версии PySide6/Qt 6.10 и корректные пути `QT_PLUGIN_PATH`, `QML2_IMPORT_PATH`.

### 1. GitHub Copilot теперь:

✅ **Отвечает на русском языке** для:
- Комментариев к коду
- Docstrings
- Сообщений об ошибках
- User-facing strings

✅ **Использует английский** для:
- Названий переменных
- Названий функций
- Git commit messages (titles)

✅ **Следует стандартам проекта**:
- Python 3.13 type hints (`str | None`)
- Qt 6.10 SLERP (без ручной нормализации углов!)
- PEP 8 style guide
- Batch updates для производительности

### 2. Примеры генерируемого кода:

#### Python функция:
```python
def calculate_position(angle: float, length: float) -> tuple[float, float]:
    """
    Вычисляет позицию точки по углу и длине.

    Args:
        angle: Угол в градусах
        length: Длина в миллиметрах

    Returns:
        Кортеж (x, y) координат в мм
    """
    rad = math.radians(angle)
    return length * math.cos(rad), length * math.sin(rad)
```

#### QML код:
```qml
// ✅ ПРАВИЛЬНО: прямое присваивание углов
property real iblRotationDeg: 0  // Qt сам интерполирует через SLERP

// ❌ НЕПРАВИЛЬНО: ручная нормализация (Copilot НЕ предложит)
// angle = angle % 360  // НИКОГДА не делать!
```

---

## 🔧 Ключевые правила проекта

### 1. **НИКОГДА не нормализуй углы в QML**
Copilot знает: Qt использует SLERP, ручная нормализация вызывает flip на 180°

### 2. **Batch Updates**
Copilot будет предлагать группировать обновления:
```python
updates = {
    "geometry": {...},
    "lighting": {...},
    "materials": {...}
}
self._qml_root_object.applyBatchedUpdates(updates)
```

### 3. **Type Hints везде**
Python 3.13 синтаксис:
```python
def process(value: str | None) -> list[dict[str, Any]]:
    ...
```

---

## 📊 Статус настройки

| Компонент | Статус | Описание |
|-----------|--------|----------|
| GitHub Copilot Instructions | ✅ Опубликовано | `.github/copilot-instructions.md` |
| VS Code Settings | ✅ Локально | `.vscode/settings.json` (в .gitignore) |
| VS Code Extensions | ✅ Локально | `.vscode/extensions.json` (в .gitignore) |
| Python Version | ✅ 3.13.x | Настроено в settings.json |
| Qt Version | ✅ 6.10.x | Переменные окружения Qt 6.10 |
| Language | ✅ Русский | Комментарии и docstrings |

---

## 🎯 Как проверить работу

### Тест 1: Попросите Copilot создать функцию
```
Prompt: "Создай функцию для расчета кинематики подвески"
```

**Ожидаемый результат:**
- ✅ Комментарии на русском
- ✅ Type hints Python 3.13
- ✅ Docstring на русском с примерами

### Тест 2: Попросите Copilot создать QML компонент
```
Prompt: "Создай QML компонент для вращения IBL"
```

**Ожидаемый результат:**
- ✅ Комментарии на русском
- ✅ БЕЗ нормализации углов
- ✅ Прямое присваивание property real angle: 0

### Тест 3: Попросите объяснить код
```
Prompt: "Объясни эту функцию"
```

**Ожидаемый результат:**
- ✅ Объяснение на русском языке
- ✅ Технические термины на английском

---

## 🔄 Обновление настроек

Если нужно изменить правила:

1. Отредактируйте `.github/copilot-instructions.md`
2. Сделайте commit и push:
   ```bash
   git add .github/copilot-instructions.md
   git commit -m "UPDATE: Copilot instructions"
   git push
   ```
3. GitHub Copilot автоматически подхватит изменения

---

## 📚 Дополнительные ресурсы

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Python 3.13 What's New](https://docs.python.org/3.13/whatsnew/3.13.html)
- [Qt 6.10 Release Notes](https://www.qt.io/blog/qt-6.10-released)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)

---

## ✅ Готово к использованию!

GitHub Copilot теперь настроен для работы с:
- 🐍 Python 3.13
- 🖼️ Qt 6.10
- 🇷🇺 Русский язык для комментариев
- 🚀 Best practices проекта PneumoStabSim

**Начинайте кодить - Copilot поможет!** 🎉
