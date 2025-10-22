# 🚀 Быстрая настройка окружения - PneumoStabSim Professional

## Автоматическая настройка (рекомендуется)

### 1. Полная настройка окружения

```powershell
# Запустите скрипт автоматической настройки
.\setup_environment.ps1

# С обновлением pip
.\setup_environment.ps1 -UpdatePip

# Пересоздание venv (если нужно)
.\setup_environment.ps1 -Force -UpdatePip
```

Этот скрипт автоматически:
- ✅ Проверит версию Python (требуется 3.11+, рекомендуется 3.13)
- ✅ Создаст виртуальное окружение `venv`
- ✅ Установит все зависимости из `requirements.txt`
- ✅ Установит dev-зависимости (pytest, black, mypy)
- ✅ Проверит корректность установки PySide6 6.10+
- ✅ Настроит переменные окружения Qt
- ✅ Проверит структуру проекта

### 2. Быстрый запуск приложения

```powershell
# Обычный запуск
.\run.ps1

# С подробными логами
.\run.ps1 -Verbose

# Тестовый режим (авто-закрытие через 5 сек)
.\run.ps1 -Test

# Debug режим (Qt логи)
.\run.ps1 -Debug
```

---

## Ручная настройка

### Шаг 1: Проверка Python

```powershell
# Проверка версии (требуется 3.11+)
python --version
# Должно быть: Python 3.13.x (рекомендуется) или 3.11+
```

### Шаг 2: Создание виртуального окружения

```powershell
# Создание venv
python -m venv venv

# Активация (PowerShell)
.\venv\Scripts\Activate.ps1

# Активация (CMD)
.\venv\Scripts\activate.bat
```

### Шаг 3: Обновление pip

```powershell
python -m pip install --upgrade pip setuptools wheel
```

### Шаг 4: Установка зависимостей

```powershell
# Основные зависимости
pip install -r requirements.txt

# Dev зависимости (для разработки)
pip install pytest pytest-qt black mypy flake8
```

### Шаг 5: Проверка установки

```powershell
# Проверка PySide6
python -c "import PySide6.QtCore as QtCore; print(f'PySide6 {QtCore.__version__} (Qt {QtCore.qVersion()})')"
# Должно быть: PySide6 6.10.x (Qt 6.10.x)

# Проверка NumPy
python -c "import numpy; print(f'NumPy {numpy.__version__}')"

# Проверка SciPy
python -c "import scipy; print(f'SciPy {scipy.__version__}')"
```

---

## Настройка VS Code

### F5 - Запуск и отладка

После настройки окружения нажмите **F5** в VS Code для запуска приложения с отладчиком.

Доступные конфигурации:
- **F5: PneumoStabSim (Главный)** - Основной запуск
- **F5: Verbose** - С подробными логами
- **F5: Test Mode** - Авто-закрытие через 5 сек
- **F5: Current File** - Запуск текущего .py файла
- **F5: Run Tests** - Запуск всех тестов

### Терминал VS Code

При открытии нового терминала автоматически:
- ✅ Активируется `venv`
- ✅ Настраиваются переменные окружения (PYTHONPATH, Qt)
- ✅ Устанавливается кодировка UTF-8
- ✅ Показывается справка с полезными командами

---

## Обязательные поля конфигурации

Перед запуском приложение валидирует `config/app_settings.json`. Убедитесь, что в файле присутствуют следующие ключи и что значения заданы в корректных единицах (СИ):

- `current.simulation.physics_dt` — шаг физики в секундах.
- `current.simulation.render_vsync_hz` — целевая частота отрисовки.
- `current.simulation.max_steps_per_frame` — максимальное число шагов симуляции за кадр.
- `current.simulation.max_frame_time` — ограничение длительности кадра симуляции.
- `current.pneumatic.receiver_volume_limits.min_m3` / `max_m3` — допустимый диапазон объёма ресивера (0 < min < max).
- `current.pneumatic.receiver_volume` — рабочий объём ресивера, лежит внутри диапазона.
- `current.pneumatic.volume_mode` — режим расчёта объёма (`MANUAL` или `GEOMETRIC`).
- `current.pneumatic.master_isolation_open` — состояние главного отсечного клапана.
- `current.pneumatic.thermo_mode` — режим термодинамики (`ISOTHERMAL`, `ADIABATIC`, ...).
- `current.geometry` — непустая секция с геометрическими параметрами (например, `wheelbase`, `track`, `lever_length_m`).
- `current.graphics.materials` — содержит материалы `frame`, `lever`, `tail`, `cylinder`, `piston_body`, `piston_rod`, `joint_tail`, `joint_arm`, `joint_rod`.

При отсутствии любого из перечисленных значений запуск будет прерван с диагностикой до создания окна.

### Миграция единиц (legacy → SI)

Если вы обновляетесь со старой версии настроек, выполните следующие шаги:

1. Сделайте резервную копию `config/app_settings.json`.
2. Приведите все значения геометрии к метрам, а давления — к Паскалям (см. комментарии в файле).
3. Убедитесь, что секция `metadata.units_version` установлена в `"si_v2"`.
4. Запустите приложение (`python app.py --test-mode` или `python app.py`) — при старте выполнится дополнительная проверка и будет выведено предупреждение, если какие-либо поля ещё требуют обновления.

Доступные команды в терминале:
```powershell
run              # Запустить приложение
run -Verbose     # С подробными логами
run -Test        # Тестовый режим
test             # Запустить все тесты
test -Coverage   # Тесты с покрытием
fmt              # Форматировать код (black)
typecheck        # Проверить типы (mypy)
clean            # Очистить кэш Python
install          # Установить зависимости
update-pip       # Обновить pip
info             # Показать справку
```

### Tasks (Ctrl+Shift+P → Tasks: Run Task)

- **▶️ Запустить PneumoStabSim**
- **🧪 Запустить все тесты (pytest)**
- **🔍 Проверка типов (mypy)**
- **✨ Форматирование кода (black)**
- **📦 Установить зависимости (pip)**
- **🔄 Обновить pip и setuptools**
- **🧹 Очистка кэша Python**
- **📊 Покрытие тестами (coverage)**
- **🔎 Проверка Qt окружения**

---

## Переменные окружения

Файл `.env` содержит важные настройки Qt/QtQuick3D:

```bash
# Python
PYTHONPATH=.;src
PYTHONIOENCODING=utf-8
PYTHONUNBUFFERED=1

# Qt/QtQuick3D
QSG_RHI_BACKEND=d3d11                      # Direct3D 11 (Windows)
QSG_INFO=0                                 # Отключить Qt логи
QT_LOGGING_RULES=*.debug=false             # Фильтр логов
QT_ASSUME_STDERR_HAS_CONSOLE=1             # Вывод в консоль
QT_AUTO_SCREEN_SCALE_FACTOR=1              # Auto HiDPI
QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough # Scaling policy
QT_ENABLE_HIGHDPI_SCALING=1                # HiDPI support
PSS_DIAG=1                                 # Диагностика приложения
```

---

## Требования

### Системные требования

- **OS**: Windows 10/11, Ubuntu 22.04+, macOS 13+
- **Python**: 3.11+ (рекомендуется **3.13**)
- **RAM**: 4 GB минимум, 8 GB рекомендуется
- **GPU**: DirectX 11 compatible (Windows) или OpenGL 4.1+ (Linux/Mac)

### Версии зависимостей

| Пакет | Версия | Назначение |
|-------|--------|------------|
| **PySide6** | ≥ 6.10.0 | Qt6 bindings + QtQuick3D |
| **NumPy** | ≥ 1.24.0 | Численные вычисления |
| **SciPy** | ≥ 1.10.0 | Научные расчеты, ODE solver |
| **matplotlib** | ≥ 3.5.0 | Графики |
| **Pillow** | ≥ 9.0.0 | Обработка HDR текстур |
| **pytest** | ≥ 7.0.0 | Тестирование |
| **black** | ≥ 23.0 | Форматирование кода |
| **mypy** | ≥ 1.6.0 | Проверка типов |

---

## Запуск приложения

### Командная строка

```powershell
# Активировать venv
.\venv\Scripts\Activate.ps1

# Обычный запуск
python app.py

# С подробными логами
python app.py --verbose

# Тестовый режим (авто-закрытие)
python app.py --test-mode

# Комбинация
python app.py --verbose --test-mode
```

### VS Code

1. Откройте проект в VS Code
2. Нажмите **F5**
3. Выберите конфигурацию запуска

### Через скрипт

```powershell
.\run.ps1              # Обычный запуск
.\run.ps1 -Verbose     # С логами
.\run.ps1 -Test        # Тестовый режим
.\run.ps1 -Debug       # С Qt debug логами
```

---

## Тестирование

### Запуск тестов

```powershell
# Все тесты
pytest tests/

# С подробным выводом
pytest tests/ -v

# С покрытием
pytest --cov=src --cov-report=html tests/

# Конкретный файл
pytest tests/test_geometry.py

# Конкретный тест
pytest tests/test_geometry.py::test_point_distance
```

### Проверка типов

```powershell
# Проверка всего проекта
mypy src/ --config-file=pyproject.toml

# Конкретный модуль
mypy src/core/geometry.py
```

### Форматирование кода

```powershell
# Форматирование всего проекта
black src/ tests/ app.py

# Проверка без изменений
black --check src/ tests/ app.py
```

---

## Устранение неполадок

### Проблема: PySide6 не установлен или неправильная версия

```powershell
# Переустановка PySide6
pip uninstall PySide6 shiboken6
pip install "PySide6>=6.10.0,<7.0.0"

# Проверка версии
python -c "import PySide6.QtCore as QtCore; print(QtCore.qVersion())"
```

### Проблема: Ошибки импорта модулей

```powershell
# Проверка PYTHONPATH
echo $env:PYTHONPATH
# Должно быть: C:\...\PneumoStabSim-Professional;C:\...\PneumoStabSim-Professional\src

# Установка вручную (PowerShell)
$env:PYTHONPATH = "$PWD;$PWD\src"
```

### Проблема: Кодировка в консоли

```powershell
# PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# CMD
chcp 65001
set PYTHONIOENCODING=utf-8
```

### Проблема: Qt не находит графический backend

```powershell
# Установка Direct3D 11 (Windows)
$env:QSG_RHI_BACKEND = "d3d11"

# Или OpenGL (универсально)
$env:QSG_RHI_BACKEND = "opengl"

# Проверка доступных backend'ов
python -c "from PySide6.QtQuick import QQuickWindow; print(QQuickWindow.graphicsApi())"
```

### Проблема: Высокая нагрузка на GPU

```powershell
# Отключение некоторых эффектов в .env
QSG_INFO=1                    # Показать Qt debug info
QT_QUICK_BACKEND=software     # Программный рендеринг (медленнее, но стабильнее)
```

---

## Дополнительная информация

### Структура проекта

```
PneumoStabSim-Professional/
├── app.py                    # ⚡ Главная точка входа
├── run.ps1                   # 🚀 Быстрый запуск
├── setup_environment.ps1     # 🔧 Автоматическая настройка
├── requirements.txt          # 📦 Зависимости
├── pyproject.toml           # ⚙️  Конфигурация проекта
├── .env                     # 🌍 Переменные окружения
├── src/                     # 🐍 Исходный код Python
│   ├── bootstrap/          # Инициализация
│   ├── core/               # Геометрия и кинематика
│   ├── simulation/         # Физическая модель
│   ├── ui/                 # Qt/QML интеграция
│   └── diagnostics/        # Логирование
├── assets/                  # 🎨 Ресурсы
│   ├── qml/                # QML компоненты
│   └── hdr/                # HDR окружение
├── tests/                   # 🧪 Тесты
└── .vscode/                # 🔧 Конфигурация VS Code
    ├── settings.json       # Настройки редактора
    ├── launch.json         # Конфигурации запуска (F5)
    ├── tasks.json          # Задачи
    └── profile.ps1         # PowerShell профиль
```

### Полезные ссылки

- **Qt 6.10 Documentation**: https://doc.qt.io/qt-6/
- **PySide6 Documentation**: https://doc.qt.io/qtforpython-6/
- **Python 3.13**: https://docs.python.org/3.13/
- **GitHub Repository**: https://github.com/barmaleii77-hub/PneumoStabSim-Professional

---

**Версия**: 4.9.5
**Последнее обновление**: 2024
**Лицензия**: MIT
