# Visual Studio Project Setup

## 🎯 Проект Visual Studio для PneumoStabSim-Professional

Это полноценное решение Visual Studio для Python-проекта PneumoStabSim-Professional.

### 📁 Файлы проекта

- **`PneumoStabSim-Professional.sln`** - файл решения Visual Studio
- **`PneumoStabSim-Professional.pyproj`** - файл проекта Python

### 🚀 Открытие проекта

#### Вариант 1: Через файл решения
```
PneumoStabSim-Professional.sln
```
Дважды щелкните на файле решения (.sln) для открытия в Visual Studio.

#### Вариант 2: Через Visual Studio
1. Откройте Visual Studio
2. File → Open → Project/Solution
3. Выберите `PneumoStabSim-Professional.sln`

### ⚙️ Конфигурации сборки

Проект включает три конфигурации:

1. **Debug** - режим отладки с флагом `--verbose`
   - Подробное логирование
   - Символы отладки включены
   - Для разработки и диагностики

2. **Release** - релизный режим
   - Стандартный запуск приложения
   - Оптимизированная производительность
   - Для продакшн использования

3. **Test** - тестовый режим с флагом `--test-mode`
   - Автозакрытие через 5 секунд
   - Быстрая проверка работоспособности
   - Для CI/CD и автоматизированного тестирования

### 🐍 Интерпретатор Python

Проект настроен на использование виртуального окружения `.venv`:

**Windows**: `venv\Scripts\python.exe`
**Linux/macOS**: `.venv/bin/python`

#### Создание виртуального окружения:
```bash
python3.13 -m venv .venv
```

#### Активация:
```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

#### Установка зависимостей:
```bash
pip install -r requirements.txt
```

### 📦 Структура проекта

```
PneumoStabSim-Professional/
├── app.py       # Точка входа приложения
├── src/       # Исходный код
│   ├── ui/     # Пользовательский интерфейс
│   │   ├── main_window.py
│ │   └── panels/            # Панели управления
│   ├── physics/    # Физическая модель
│   ├── mechanics/          # Кинематика подвески
│   ├── pneumo/    # Пневматическая система
│   ├── road/       # Дорожные профили
│   ├── runtime/     # Цикл симуляции
│   ├── core/     # Геометрия
│   └── common/  # Утилиты
├── tests/          # Тесты
│   ├── ui/
│   ├── graphics/
│   └── system/
├── assets/          # Ресурсы
│   ├── qml/    # QML файлы
│   └── hdr/          # HDR текстуры
├── scripts/  # Вспомогательные скрипты
└── docs/        # Документация
```

### 🧪 Запуск тестов

#### Из Visual Studio:
1. Откройте Test Explorer (Test → Test Explorer)
2. Нажмите "Run All Tests"

#### Из командной строки:
```bash
pytest tests/ -v
```

### 🔧 Отладка

1. Установите точки останова (F9) в нужных местах кода
2. Выберите конфигурацию Debug
3. Нажмите F5 или Debug → Start Debugging
4. Используйте Debug Console для выполнения команд

### 📊 Доступные команды запуска

Через Terminal в Visual Studio:

```bash
# Обычный запуск
python app.py

# С подробными логами
python app.py --verbose

# Тестовый режим (автозакрытие 5с)
python app.py --test-mode

# Безопасный режим
python app.py --safe-mode

# Устаревший OpenGL режим
python app.py --legacy
```

### 🛠️ Требования

- **Visual Studio 2019/2022** с компонентом Python Development
- **Python 3.13+** (рекомендуется 3.13.x)
- **PySide6 6.10+** (Qt 6.10 для ExtendedSceneEnvironment)
- **NumPy, SciPy** для физических расчетов

### 📚 Дополнительная документация

- [README.md](README.md) - Основная документация
- [F5_QUICK_START.md](F5_QUICK_START.md) - Быстрый старт для разработчиков
- [VSCODE_PY_SETUP.md](VSCODE_PY_SETUP.md) - Настройка VS Code
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Статус проекта

### ⚠️ Известные проблемы

1. **Путь к интерпретатору**: Убедитесь, что виртуальное окружение `.venv` создано
2. **Qt переменные**: Настройки Qt загружаются из файла `.env`
3. **PYTHONPATH**: Автоматически включает `src\` и корень проекта

### 🔍 Отладочные инструменты

В проекте доступны вспомогательные скрипты:

- **`quick_fix.py`** - автоматическое исправление известных проблем
- **`qml_diagnostic.py`** - диагностика QML файлов
- **`scripts/health_check.py`** - проверка состояния системы
- **`scripts/comprehensive_test.py`** - комплексное тестирование

### 🎨 Расширения Visual Studio

Рекомендуемые расширения:

- **Python** - базовая поддержка Python
- **Python IntelliSense** - автодополнение
- **Python Test Explorer** - интеграция pytest
- **Qt Visual Studio Tools** - поддержка Qt/QML

### 💡 Советы по работе

1. **Используйте конфигурацию Debug** для разработки
2. **Проверяйте Output окно** для логов Qt
3. **Test Explorer** для быстрого запуска тестов
4. **Solution Explorer** для навигации по файлам
5. **Breakpoints** для остановки в нужных точках

### 🆘 Решение проблем

#### Проблема: "Python interpreter not found"
**Решение**: 
1. Tools → Options → Python → Environments
2. Добавьте путь к `.venv\Scripts\python.exe`

#### Проблема: "Module not found"
**Решение**:
```bash
pip install -r requirements.txt
```

#### Проблема: "QML не загружается"
**Решение**:
```bash
python qml_diagnostic.py
```

---

**Версия**: 1.0  
**Последнее обновление**: 2025  
**Совместимость**: Visual Studio 2019/2022, Python 3.13+
