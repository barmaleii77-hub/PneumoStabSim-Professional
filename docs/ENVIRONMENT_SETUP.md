# Настройка окружения PneumoStabSim-Professional

Документ описывает полный процесс подготовки окружения разработки для Windows и Linux. Используйте его совместно с шаблоном `env.sample` и скриптом `setup_environment.py`.

## Обзор инструментов

| Инструмент | Назначение | Основные опции |
|------------|-----------|----------------|
| `setup_environment.py` | Создание виртуального окружения, установка зависимостей, Qt SDK, тестовая проверка | `--python-version`, `--install-qt`, `--qt-version`, `--qt-modules`, `--hash-file`, `--qt-output-dir` |
| `activate_environment.sh` | Загрузка `.env` и запуск `setup_environment.py` в Linux/macOS | `--python-version`, `--install-qt`, `--qt-version`, `--qt-modules`, `--hash-file`, `--setup` |
| `activate_environment.ps1` | Аналогичный сценарий для Windows PowerShell | `-PythonVersion`, `-InstallQt`, `-QtVersion`, `-QtModules`, `-HashFile`, `-Setup` |
| `env.sample` | Шаблон переменных окружения, включая пути к Qt и журналы | Настройте `QT_SDK_ROOT`, `QT_INSTALL_LOG`, `DEPENDENCIES_FILE` |

## Подготовка `.env`
1. Скопируйте шаблон: `cp env.sample .env` (PowerShell: `Copy-Item env.sample .env`).
2. Укажите путь к установленному Qt SDK (`QT_SDK_ROOT`) и при необходимости имя файла зависимостей с хешами (`DEPENDENCIES_FILE`).
3. Добавьте требуемые опции журналирования (`PNEUMOSTABSIM_LOG_LEVEL`, `QT_LOGGING_RULES`).

## Windows

### Установка инструментов Visual Studio
1. Скачайте **Visual Studio 2022** (Community или Professional).
2. Установите рабочую нагрузку **Desktop development with C++** с компонентами:
   - Windows 10/11 SDK.
   - MSVC v143 x64/x86 build tools.
3. Перезагрузите систему после установки.

### PowerShell сценарий
```powershell
# Первая настройка
./activate_environment.ps1 -Setup -InstallQt -PythonVersion 3.13 `
    -QtVersion 6.7.2 -QtModules "qtbase;qtdeclarative;qtshadertools" `
    -HashFile requirements.txt

# Повторная активация в текущей сессии
./activate_environment.ps1 -PythonVersion 3.13
```

### Интеграция с Visual Studio
1. Откройте решение `PneumoStabSim-Professional.sln`.
2. В меню **Project → Properties** настройте **Environment** для конфигураций Debug/Release, импортировав `.env` (через `VC++ Directories → Include Directories` для Qt).
3. Убедитесь, что `QT_SDK_ROOT\bin` добавлен в `PATH`.
4. Для запуска Python-части используйте **Python Environments** → **Add Environment** → *Existing environment* и укажите виртуальное окружение `venv`.

### VS Code
1. Откройте рабочее пространство `PneumoStabSim.code-workspace`.
2. Выполните `./activate_environment.ps1 -Setup` из интегрированного терминала, чтобы обновить `.env` и установить Qt.
3. Выберите интерпретатор `Python: Select Interpreter` → `<project>\venv\Scripts\python.exe`.
4. Для запусков добавлены конфигурации `Run App` и `Run Tests`; они используют переменные из `.env`.

## Linux (Ubuntu/Fedora)

### Обязательные пакеты
```bash
sudo apt update && sudo apt install build-essential ninja-build libgl1-mesa-dev
# Fedora: sudo dnf groupinstall "Development Tools" && sudo dnf install mesa-libGL-devel ninja-build
```

### Скрипт установки
```bash
cp env.sample .env
source activate_environment.sh --setup --install-qt --python-version 3.13 \
    --qt-version 6.7.2 --qt-modules qtbase,qtdeclarative,qtshadertools
```

### Использование в терминале
- Активировать окружение: `source activate_environment.sh --python-version 3.13`.
- Проверить Qt: `echo $QT_SDK_ROOT && ls "$QT_SDK_ROOT"`.
- Запустить тесты: `python -m pytest` (пакеты устанавливаются в виртуальное окружение `venv`).

### VS Code (Linux)
1. Откройте рабочее пространство.
2. В терминале выполните `source activate_environment.sh --setup`.
3. Выберите интерпретатор `venv/bin/python`.
4. Добавьте в `settings.json` (пользователь или рабочее пространство):
   ```json
   {
     "python.envFile": "${workspaceFolder}/.env"
   }
   ```

## Проверка хешей зависимостей
1. Добавьте в `requirements.txt` строки с хешами (`package==version --hash=sha256:...`).
2. Запустите `setup_environment.py` с параметром `--hash-file requirements.txt` либо укажите файл через активационные скрипты.
3. Скрипт автоматически добавит `--require-hashes` к команде `pip install`. В лог установки (`logs/pip_hash_verification.log` или указанный файл) будут сохранены результаты проверки.

## Установка Qt SDK
- По умолчанию загружается версия `6.7.2` в каталог `Qt` внутри проекта.
- Измените директорию `--qt-output-dir` для установки в общее расположение, например `C:\Qt` или `/opt/qt`.
- Дополнительные модули передаются списком через `--qt-modules`. Для списка доступных модулей используйте `python -m aqt list-qt windows desktop 6.7.2`.

## Полезные команды
```bash
# Быстрая настройка без установки Qt (если уже установлен)
python setup_environment.py --python-version 3.13

# Установка Qt с локальным архивом
python setup_environment.py --install-qt --qt-archives-dir ~/Downloads/qt-cache

# Проверка зависимостей из lock-файла
python setup_environment.py --hash-file requirements.lock
```

## Отладка
- Файл журнала установки Qt задаётся переменной `QT_INSTALL_LOG` (по умолчанию `logs/qt_install.log`).
- Проверка версий Python и Qt выводится в консоль при запуске `setup_environment.py`.
- Если установка Qt завершается с ошибкой, повторите запуск с флагом `--install-qt` и убедитесь, что доступен интернет или локальный архив.

## После настройки
Рекомендуется выполнить ручную проверку окружения:

1. Запустите тесты: `python -m pytest`.
2. Запустите линтер: `flake8 src tests`.
3. Запустите приложение: `python app.py --test-mode`.
