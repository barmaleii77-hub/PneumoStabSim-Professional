# Настройка окружения PneumoStabSim-Professional

Документ описывает полный процесс подготовки окружения разработки для Windows и Linux. Используйте его совместно с шаблоном `env.sample` и скриптами автоматизации из репозитория.

## Обзор инструментов

| Инструмент | Назначение | Основные опции |
|------------|-----------|----------------|
| `scripts/bootstrap_uv.py` | Проверка и установка [uv](https://github.com/astral-sh/uv), быстрая синхронизация зависимостей | `--sync`, `--project-dir`, `--force`, `--executable` |
| `make uv-sync` / `make uv-run` | Запуск `uv sync` и выполнение команд внутри окружения | `UV_PROJECT_DIR`, `CMD` |
| `tools/setup_qt.py` | Установка Qt SDK с проверкой контрольных сумм | `--qt-version`, `--modules`, `--output-dir`, `--archives-dir` |
| `activate_environment.(sh|ps1)` | Генерация `.env`, запуск установки Qt и вспомогательных проверок | `--setup`, `--install-qt`, `--qt-version`, `--qt-modules`, `--hash-file` |
| `setup_environment.py` | Совместимость со старыми сценариями: заполнение `.env`, проверка зависимостей | `--python-version`, `--install-qt`, `--hash-file`, `--qt-output-dir` |

## Рекомендуемый процесс с uv

`uv` является основным инструментом управления зависимостями в проекте. Он создаёт изолированное окружение на основе `pyproject.toml`, учитывает `requirements.lock` и гарантирует повторяемость установки.

1. Выполните `python scripts/bootstrap_uv.py --sync`, чтобы установить `uv` (если он ещё не доступен в `PATH`) и сразу синхронизировать зависимости в каталоге проекта.
2. Для регулярного обновления окружения используйте `make uv-sync`. Команда выполняет `uv sync` и обновляет кэш виртуального окружения.
3. Запускайте любые команды внутри окружения через `make uv-run CMD="pytest -k smoke"` или другой аргумент `CMD`. Переменная `UV_PROJECT_DIR` позволяет работать с вложенными проектами или форками.
4. Перед коммитами выполняйте `make check` (эквивалентно последовательному запуску `ruff`, `mypy`, `qmllint` и `pytest` через `uv run`).

### Поддержание зависимостей

- Основной lock-файл: `requirements.lock`. При изменении `pyproject.toml` обновляйте его командой `uv lock` (или `make uv-run CMD="uv lock"`), затем фиксируйте изменения в Git.
- Файлы `requirements.txt` и `requirements-dev.txt` генерируются из lock-файла и используются только для совместимости со старыми скриптами. Не редактируйте их вручную.
- Если требуются альтернативные источники (например, корпоративные зеркала), укажите их через переменные окружения в `.env` и перезапустите `make uv-sync`.

## Подготовка `.env` и Qt SDK

1. Скопируйте шаблон: `cp env.sample .env` (PowerShell: `Copy-Item env.sample .env`).
2. Укажите путь к каталогу Qt в переменной `QT_SDK_ROOT` (по умолчанию Qt устанавливается в `<repo>/Qt`).
3. Для первичной установки Qt выполните одну из команд:
   - `python tools/setup_qt.py --qt-version 6.10.0 --modules qtbase,qtdeclarative,qtshadertools`
   - `./activate_environment.ps1 -Setup -InstallQt -QtVersion 6.10.0` (Windows)
   - `source activate_environment.sh --setup --install-qt --qt-version 6.10.0`
4. После установки перезапустите `make uv-sync`, чтобы убедиться, что переменные из `.env` доступны в среде `uv`.

### Зачем нужны `activate_environment.*`

Скрипты активации отвечают за генерацию `.env`, настройку путей Qt и запуск `setup_environment.py` в режиме совместимости. Используйте их, если необходимо:

- переустановить Qt или переключиться на другую версию SDK;
- обновить `.env` на Windows с учётом PowerShell специфики;
- восстановить окружение на машинах без `uv` (например, в CI до перехода).

## Windows

### Быстрый старт (PowerShell 7+)
```powershell
python scripts/bootstrap_uv.py --sync
make uv-sync
make uv-run CMD="python -m pytest -k smoke"
```

### Дополнительные шаги
1. При необходимости установите **Visual Studio 2022** с рабочей нагрузкой **Desktop development with C++** (для Qt инструментов и отладчиков).
2. Для переустановки Qt выполните `./activate_environment.ps1 -Setup -InstallQt -QtVersion 6.10.0`.
3. Для запуска приложения используйте `make uv-run CMD="python app.py"` — команда автоматически активирует окружение.

### Интеграция с Visual Studio
1. Откройте `PneumoStabSim-Professional.sln`.
2. В свойствах конфигурации импортируйте переменные из `.env` и укажите путь к интерпретатору, созданному `uv` (см. `uv env`).
3. Проверьте, что `QT_PLUGIN_PATH` и `QML2_IMPORT_PATH` включены в переменные среды конфигурации отладки.

### Visual Studio Code
1. Откройте `PneumoStabSim.code-workspace`.
2. Выполните команды быстрого старта в интегрированном терминале.
3. Используйте **Python: Select Interpreter** и выберите `uv` окружение.
4. Задачи `Run App` и `Run Tests` вызывают `make uv-run`, поэтому дополнительных настроек не требуется.

## Linux (Ubuntu/Fedora)

### Обязательные пакеты
```bash
sudo apt update && sudo apt install build-essential ninja-build libgl1-mesa-dev
# Fedora: sudo dnf groupinstall "Development Tools" && sudo dnf install mesa-libGL-devel ninja-build
```

### Быстрый старт
```bash
python3 scripts/bootstrap_uv.py --sync
make uv-sync
make uv-run CMD="pytest -m 'not gui'"
```

### Qt и `.env`
```bash
cp env.sample .env
source activate_environment.sh --setup --install-qt --qt-version 6.10.0 \
    --qt-modules qtbase,qtdeclarative,qtshadertools
make uv-sync
```

### VS Code (Linux)
1. Выполните шаги быстрого старта.
2. В `settings.json` рабочего пространства добавьте
   ```json
   {
     "python.envFile": "${workspaceFolder}/.env"
   }
   ```
3. Выберите интерпретатор `uv` через **Python: Select Interpreter**.

## Проверка окружения

После первичной настройки выполните минимальный набор проверок:

1. `make check` — полный набор линтеров, типизации и тестов.
2. `make uv-run CMD="python -c 'import PySide6, numpy; print(PySide6.__version__, numpy.__version__)'"` — убедиться, что Qt и научные библиотеки доступны.
3. `make uv-run CMD="python app.py --test-mode"` — убедиться, что приложение запускается с корректными путями к Qt.

## Дополнительные сценарии (совместимость)

- `setup_environment.py` и связанные с ним скрипты остаются для поддержания старых установок. Они читают lock-файлы и заполняют `.env`, но не должны использоваться в новых автоматизированных процессах.
- Для ручной проверки хешей зависимостей можно вызвать `make uv-run CMD="pip check --require-hashes -r requirements.txt"`, однако предпочтительным способом остаётся `uv sync`.
- Если необходимо полностью переинициализировать окружение, удалите каталог `.uv/` и выполните шаги быстрого старта заново.
