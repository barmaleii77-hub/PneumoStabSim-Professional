# 🚀 PneumoStabSim Professional - Виртуальная среда

## Быстрый старт

### 1. Автоматическая настройка и запуск
```bash
# Запуск приложения (автоматически создаст venv если нужно)
run.bat

# Или с параметрами
run.bat --test-mode
run.bat --debug
```

### 2. Полная настройка виртуальной среды
```bash
# Создание и настройка виртуальной среды
activate_venv.bat

# После настройки среда останется активной в текущем терминале
```

### 3. Проверка статуса
```bash
# Проверка состояния виртуальной среды
status.bat
```

## 📁 Структура виртуальной среды

```
PneumoStabSim-Professional/
├── venv/                       # Виртуальная среда Python
│   ├── Scripts/
│   │   ├── python.exe         # Python интерпретатор
│   │   ├── pip.exe            # Менеджер пакетов
│   │   └── activate.bat       # Активация среды
│   └── Lib/site-packages/     # Установленные пакеты
├── activate_venv.bat          # Создание и настройка среды
├── activate_venv.ps1          # PowerShell версия
├── activate_venv.sh           # Linux/macOS версия
├── run.bat                    # Быстрый запуск приложения
├── status.bat                 # Проверка статуса
├── install_dev.bat            # Установка dev зависимостей
├── .env                       # Переменные окружения
├── requirements.txt           # Основные зависимости
└── requirements-dev.txt       # Зависимости для разработки
```

## 🔧 Команды управления средой

### Базовые команды
```bash
# Активация среды (если уже создана)
venv\Scripts\activate.bat

# Деактивация среды
deactivate

# Проверка версии Python
python --version

# Список установленных пакетов
pip list
```

### Команды разработки
```bash
# Установка dev зависимостей
install_dev.bat

# Запуск тестов
pytest

# Форматирование кода
black .

# Проверка стиля
flake8

# Анализ типов
mypy src
```

### Команды приложения
```bash
# Основные режимы запуска
python app.py                    # Обычный режим
python app.py --test-mode        # Тестовый режим (5 сек)
python app.py --debug            # Режим отладки
python app.py --no-block         # Неблокирующий режим

# Диагностика
python scripts\check_environment.py     # Проверка окружения
python scripts\comprehensive_test.py    # Полное тестирование
```

## 🌍 Переменные окружения

Автоматически устанавливаются из файла `.env`:

```bash
PYTHONPATH=.;src                        # Пути Python модулей
QSG_RHI_BACKEND=d3d11                   # Qt графический backend
QT_LOGGING_RULES=js.debug=true          # Qt отладка
PYTHONOPTIMIZE=1                        # Оптимизация Python
PYTHONUNBUFFERED=1                      # Небуферизованный вывод
```

## 💻 Поддерживаемые платформы

| Платформа | Скрипт активации | Backend |
|-----------|------------------|---------|
| Windows   | `activate_venv.bat` | Direct3D 11 |
| PowerShell | `activate_venv.ps1` | Direct3D 11 |
| Linux     | `activate_venv.sh` | OpenGL |
| macOS     | `activate_venv.sh` | OpenGL |

## 🔍 Устранение проблем

### Виртуальная среда не создается
```bash
# Проверьте установку Python
python --version

# Создайте среду вручную
python -m venv venv

# Активируйте и установите зависимости
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Приложение не запускается
```bash
# Проверьте статус
status.bat

# Переустановите зависимости
pip install -r requirements.txt --force-reinstall

# Проверьте окружение
python scripts\check_environment.py
```

### Проблемы с Qt/OpenGL
```bash
# Смените backend на OpenGL
set QSG_RHI_BACKEND=opengl
python app.py

# Или используйте software rendering
set QT_QUICK_BACKEND=software
python app.py
```

## 📊 Мониторинг производительности

```bash
# Профилирование памяти
python -m memory_profiler app.py

# Профилирование времени
python -m line_profiler app.py

# Benchmark тесты
pytest --benchmark-only
```

## 🎯 Рекомендации по использованию

1. **Для ежедневной разработки**: используйте `run.bat`
2. **Для настройки среды**: используйте `activate_venv.bat`
3. **Для проверки статуса**: используйте `status.bat`
4. **Для разработки**: установите `install_dev.bat`

## ✅ Проверка готовности

После настройки виртуальной среды должны работать следующие команды:

```bash
✓ python app.py --test-mode      # Запуск в тестовом режиме
✓ python --version               # Python 3.8+
✓ pip list                       # Список пакетов
✓ pytest                         # Если установлены dev зависимости
```

---
*Виртуальная среда настроена и готова к работе! 🎉*
