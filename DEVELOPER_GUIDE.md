# PneumoStabSim Professional - Developer Setup Guide

## 🚀 Быстрый старт для разработчиков

### Предварительные требования

- **Python 3.8+** (рекомендуется 3.9-3.11)
- **Git** для клонирования репозитория
- **Visual Studio 2022** или **VS Code** для разработки

### Автоматическая настройка

```bash
# 1. Клонирование репозитория
git clone https://github.com/barmaleii77-hub/PneumoStabSim-Professional.git
cd PneumoStabSim-Professional

# 2. Автоматическая настройка окружения
python setup_dev.py

# 3. Активация виртуального окружения
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. Запуск приложения
python app.py
```

## 🛠️ Настройка IDE

### Visual Studio 2022

1. Откройте `PneumoStabSim.sln`
2. Установите Python Tools for Visual Studio (PTVS)
3. Настройте интерпретатор Python: `Tools > Python > Python Environments`
4. Нажмите **F5** для запуска с отладкой

### Visual Studio Code

1. Откройте папку проекта в VS Code
2. Установите расширения:
   - Python
   - Python Debugger
   - Qt for Python
   - EditorConfig for VS Code
3. Выберите интерпретатор: `Ctrl+Shift+P` > "Python: Select Interpreter"
4. Нажмите **F5** для запуска отладки

## 📁 Структура проекта

```
PneumoStabSim-Professional/
├── 📄 app.py                          # Главный файл приложения
├── 📄 apply_patches.py                 # Система применения патчей
├── 📄 performance_monitor.py           # Монитор производительности
├── 📄 setup_dev.py                     # Настройка окружения разработчика
│
├── 📁 src/                             # Исходный код
│   ├── 📁 common/                      # Общие модули
│   │   ├── 📄 __init__.py
│   │   └── 📄 logging_setup.py
│   ├── 📁 ui/                          # Пользовательский интерфейс
│   │   ├── 📄 main_window.py           # Главное окно
│   │   └── 📁 panels/                  # Панели управления
│   │       ├── 📄 panel_geometry.py    # Панель геометрии
│   │       ├── 📄 panel_graphics.py    # Панель графики
│   │       ├── 📄 panel_modes.py       # Панель режимов
│   │       └── 📄 panel_pneumo.py      # Пневматическая панель
│   └── 📁 simulation/                  # Физическая симуляция
│       ├── 📄 manager.py               # Менеджер симуляции
│       └── 📄 physics.py               # Физические расчеты
│
├── 📁 assets/                          # Ресурсы
│   ├── 📁 qml/                         # QML файлы
│   │   ├── 📄 main.qml                 # Главный QML файл
│   │   └── 📁 components/              # QML компоненты
│   ├── 📁 hdr/                         # HDR текстуры для IBL
│   └── 📁 images/                      # Изображения и иконки
│
├── 📁 config/                          # Конфигурация
│   └── 📄 graphics_defaults.py         # Настройки графики по умолчанию
│
├── 📁 logs/                            # Лог файлы
├── 📁 tests/                           # Тесты
├── 📁 docs/                            # Документация
│
├── 📁 .vscode/                         # Настройки VS Code
│   ├── 📄 launch.json                  # Конфигурации запуска
│   ├── 📄 settings.json                # Настройки проекта
│   └── 📄 tasks.json                   # Задачи
│
├── 📄 PneumoStabSim.sln                # Visual Studio Solution
├── 📄 PneumoStabSim.pyproj             # Python Project для VS
├── 📄 pyproject.toml                   # Настройки проекта Python
├── 📄 requirements.txt                 # Зависимости production
├── 📄 requirements-dev.txt             # Зависимости разработки
└── 📄 .editorconfig                    # Настройки форматирования
```

## 🎯 Основные команды разработки

### Запуск приложения

```bash
# Обычный запуск
python app.py

# Режим отладки
python app.py --debug

# Безопасный режим (без 3D)
python app.py --safe-mode

# С мониторингом производительности
python app.py --monitor-perf

# Тестовый режим (автозакрытие через 5с)
python app.py --test-mode
```

### Применение патчей

```bash
# Автоматическое применение всех патчей
python apply_patches.py

# Применение конкретного патча
git apply panel_graphics.patch
```

### Управление зависимостями

```bash
# Установка production зависимостей
pip install -r requirements.txt

# Установка dev зависимостей
pip install -r requirements-dev.txt

# Обновление зависимостей
pip install --upgrade -r requirements.txt
```

### Тестирование и качество кода

```bash
# Запуск тестов
pytest tests/ -v

# Проверка типов
mypy src/ app.py

# Линтинг
flake8 src/ app.py

# Форматирование кода
black . --line-length=88

# Сортировка импортов
isort . --profile black
```

### Сборка проекта

```bash
# Создание wheel пакета
python -m build

# Очистка временных файлов
python scripts/clean.py
```

## 🐛 Отладка

### Настройки отладки для VS Code

Конфигурации отладки в `.vscode/launch.json`:

- **PneumoStabSim: Launch Main** - обычный запуск
- **PneumoStabSim: Launch (Debug Mode)** - с полной отладкой Qt
- **PneumoStabSim: Launch (Safe Mode)** - без 3D функций
- **Apply Patches** - отладка системы патчей

### Полезные переменные окружения для отладки

```bash
# Qt отладка
export QT_DEBUG_PLUGINS=1
export QT_LOGGING_RULES="*.debug=true"

# Python отладка
export PYTHONDEBUG=1
export PYTHONVERBOSE=1
```

### Логирование

Логи сохраняются в папку `logs/`:
- `app.log` - основные логи приложения
- `performance.log` - логи производительности
- `qt.log` - логи Qt framework

## 🔧 Системные требования разработчика

### Windows

- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.8-3.11 (из python.org)
- **Visual Studio**: 2022 Community/Professional
- **Git**: Git for Windows
- **RAM**: 8GB+ (рекомендуется 16GB)

### Linux

- **OS**: Ubuntu 20.04/22.04, Debian 11+, Fedora 35+
- **Python**: 3.8-3.11
- **Deps**: `sudo apt install python3-dev qt6-base-dev`
- **RAM**: 8GB+ (рекомендуется 16GB)

### macOS

- **OS**: macOS 11+ (Big Sur)
- **Python**: 3.9-3.11 (через Homebrew)
- **Xcode**: Command Line Tools
- **RAM**: 8GB+ (рекомендуется 16GB)

## 📚 Архитектура

### Основные компоненты

1. **app.py** - точка входа, настройка Qt окружения
2. **MainWindow** - главное окно с QML представлением
3. **Panels** - панели управления параметрами
4. **QML Layer** - 3D визуализация и UI
5. **SimulationManager** - физические расчеты
6. **PerformanceMonitor** - мониторинг производительности

### Поток данных

```
Python Panels → Signals → QML Properties → Qt Quick 3D → GPU Rendering
      ↑                                                         ↓
  User Input ←                                            Visual Output
```

### Система патчей

- **apply_patches.py** - автоматическое применение
- **Backup система** - автоматические резервные копии
- **Git integration** - использует `git apply` когда возможно
- **Rollback** - возможность отката изменений

## 🤝 Вкладывание в проект

### Стиль кода

- **Python**: PEP 8 + Black formatting (88 символов)
- **QML**: 4 пробела, camelCase для properties
- **Commit**: [Conventional Commits](https://www.conventionalcommits.org/)

### Процесс разработки

1. Создайте feature branch: `git checkout -b feature/my-feature`
2. Внесите изменения следуя стилю кода
3. Добавьте тесты если нужно
4. Запустите полную проверку: `pytest && mypy . && flake8 .`
5. Создайте Pull Request

### Pre-commit hooks

```bash
# Установка pre-commit hooks
pre-commit install

# Ручной запуск проверок
pre-commit run --all-files
```

## 🆘 Решение проблем

### Проблемы с PySide6

```bash
# Переустановка PySide6
pip uninstall PySide6 shiboken6
pip install PySide6>=6.5.0
```

### Проблемы с Qt Quick 3D

```bash
# Проверка доступности 3D
python -c "from PySide6.QtQuick3D import *; print('Qt Quick 3D OK')"

# Fallback на Legacy OpenGL
python app.py --legacy
```

### Проблемы с производительностью

```bash
# Профилирование
python app.py --monitor-perf

# Проверка GPU
python -c "from OpenGL.GL import *; print(glGetString(GL_RENDERER))"
```

## 📞 Поддержка

- **GitHub Issues**: [Report Bug](https://github.com/barmaleii77-hub/PneumoStabSim-Professional/issues)
- **Discussions**: [Q&A](https://github.com/barmaleii77-hub/PneumoStabSim-Professional/discussions)
- **Wiki**: [Documentation](https://github.com/barmaleii77-hub/PneumoStabSim-Professional/wiki)

---

**Счастливого кодинга! 🚀**
