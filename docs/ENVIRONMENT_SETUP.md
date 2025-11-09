# Настройка окружения PneumoStabSim-Professional

Документ описывает полный процесс подготовки окружения разработки для Windows и Linux. Используйте его совместно с шаблоном `env.sample` и скриптами автоматизации из репозитория.

## Обзор инструментов

| Инструмент | Назначение | Основные опции |
|------------|-----------|----------------|
| `scripts/bootstrap_uv.py` | Проверка и установка [uv](https://github.com/astral-sh/uv), быстрая синхронизация зависимостей | `--sync`, `--lock`, `--export-requirements`, `--project-dir`, `--force`, `--executable` |
| `make uv-sync`, `make uv-sync-locked`, `make uv-run`, `make uv-lock`, `make uv-export-requirements`, `make uv-release-refresh` | Синхронизация окружения, генерация lock-файла и экспорт requirements | `UV_PROJECT_DIR`, `CMD`, `UV_SYNC_ARGS`, `UV_RUN_ARGS`, `UV_LOCKFILE` |
| `tools/setup_qt.py` | Установка Qt SDK с проверкой контрольных сумм | `--qt-version`, `--modules`, `--output-dir`, `--archives-dir`, `--refresh-requirements` |
| `activate_environment.(sh|ps1)` | Генерация `.env`, запуск установки Qt и вспомогательных проверок | `--setup`, `--install-qt`, `--qt-version`, `--qt-modules`, `--hash-file` |
| `setup_environment.py` | Совместимость со старыми сценариями: заполнение `.env`, проверка зависимостей | `--python-version`, `--install-qt`, `--hash-file`, `--qt-output-dir` |

## Рекомендуемый процесс с uv

`uv` является основным инструментом управления зависимостями в проекте. Он создаёт изолированное окружение на основе `pyproject.toml`, использует `uv.lock` и гарантирует повторяемость установки.

1. Выполните `python scripts/bootstrap_uv.py --sync`, чтобы установить `uv` (если он ещё не доступен в `PATH`) и сразу синхронизировать зависимости в каталоге проекта.
2. Применяйте зафиксированные в `uv.lock` версии зависимостей командой `make uv-sync-locked`. Она выполняет `uv sync --locked --frozen` и не изменяет lock-файл.
3. Для обновления зависимостей после изменения `pyproject.toml` выполните `make uv-lock` (или `uv lock`), после чего запустите `make uv-release-refresh`, чтобы заодно пересобрать `requirements*.txt`. Если нужно протестировать альтернативные версии, можно вызвать `make uv-sync UV_SYNC_ARGS=""` (без `--frozen`).
4. Запускайте любые команды внутри окружения через `make uv-run CMD="pytest -k smoke"` или другой аргумент `CMD`. Переменные `UV_PROJECT_DIR` и `UV_RUN_ARGS` позволяют работать с вложенными проектами или форками.
5. Перед коммитами выполняйте `make check` (эквивалентно последовательному запуску `ruff`, `mypy`, `qmllint` и `pytest` через `uv run`).

### Поддержание зависимостей

- Основной lock-файл: `uv.lock`. При изменении `pyproject.toml` обновляйте его командой `uv lock` (или `make uv-run CMD="uv lock"`), затем фиксируйте изменения в Git.
- Файлы `requirements.txt`, `requirements-dev.txt` и `requirements-compatible.txt` генерируются из `uv.lock` и используются только для совместимости со старыми скриптами. Не редактируйте их вручную.
- Для регенерации предпочитайте автоматические цели `make uv-export-requirements` или `make uv-release-refresh`. Они выполняют `uv export` в режиме `--locked` и гарантируют консистентность с lock-файлом. Аналогичную операцию можно запустить из одного шага: `python scripts/bootstrap_uv.py --export-requirements`.
- Если требуется явно увидеть команды, используйте `uv export` напрямую (вариант для CI или отладки):
  ```bash
  uv export --format requirements.txt --output-file requirements.txt --no-dev --locked --no-emit-project
  uv export --format requirements.txt --output-file requirements-dev.txt --extra dev --locked --no-emit-project
  uv export --format requirements.txt --output-file requirements-compatible.txt --no-dev --locked --no-emit-project --no-annotate --no-hashes
  ```
- Если требуются альтернативные источники (например, корпоративные зеркала), укажите их через переменные окружения в `.env` и перезапустите `make uv-sync-locked`.

### Экспорт requirements из lock-файла

После обновления зависимостей в `pyproject.toml` выполните:

```bash
uv lock
make uv-export-requirements
```

Команда `make uv-export-requirements` последовательно вызывает `uv export` в трёх режимах и создаёт:

- `requirements.txt` — основной список без `dev`-зависимостей с хешами;
- `requirements-dev.txt` — расширенный список с `dev`-extras и хешами;
- `requirements-compatible.txt` — облегчённый список без аннотаций и хешей для устаревших систем установки.

Для релизных пайплайнов удобна цель `make uv-release-refresh`, которая объединяет оба шага (сначала обновляет `uv.lock`, затем пересобирает все производные файлы). CI использует те же команды, поэтому источником истины остаётся `uv.lock`.

## Подготовка `.env` и Qt SDK

1. Скопируйте шаблон: `cp env.sample .env` (PowerShell: `Copy-Item env.sample .env`).
2. Укажите путь к каталогу Qt в переменной `QT_SDK_ROOT` (по умолчанию Qt устанавливается в `<repo>/Qt`).
3. Для первичной установки Qt выполните одну из команд:
   - `python tools/setup_qt.py --qt-version 6.10.0 --modules qtquick3d,qtshadertools,qtimageformats`
   - `./activate_environment.ps1 -Setup -InstallQt -QtVersion 6.10.0` (Windows)
   - `source activate_environment.sh --setup --install-qt --qt-version 6.10.0`
4. После установки перезапустите `make uv-sync-locked`, чтобы убедиться, что переменные из `.env` доступны в среде `uv`.

### Зачем нужны `activate_environment.*`

Скрипты активации отвечают за генерацию `.env`, настройку путей Qt и запуск `setup_environment.py` в режиме совместимости. Используйте их, если необходимо:

- переустановить Qt или переключиться на другую версию SDK;
- обновить `.env` на Windows с учётом PowerShell специфики;
- восстановить окружение на машинах без `uv` (например, в CI до перехода).

### Каталог PowerShell и вспомогательных скриптов

Ниже перечислены основные сценарии автоматизации, доступные в репозитории. Все
они рассчитаны на запуск из корня проекта.

| Скрипт | Назначение | Когда использовать |
| ------ | ---------- | ----------------- |
| `activate_environment.ps1` | Загружает переменные из `.env`, при необходимости пересоздаёт `.venv` через `uv` и активирует его в текущей сессии PowerShell. | Повседневная работа в Windows-терминале, запуск перед `make`/`python` командами. |
| `scripts/activate_environment.ps1` | Тонкая обёртка над корневым скриптом для обратной совместимости с существующими путями в CI и документации. | Когда автоматизация ожидает сценарий именно в `scripts/`. |
| `setup_environment.ps1` | Полная переинициализация окружения: поиск Python 3.11–3.13, установка `uv`, пересборка `.env`, подготовка каталогов и проверка зависимостей. | Первичная настройка машины, восстановление после сбоя окружения. |
| `setup_all_paths.ps1` | Настройка `PYTHONPATH`, Qt-переменных и путей к активам внутри текущей сессии PowerShell; умеет валидацию путей. | Когда требуется вручную переопределить переменные среды без переустановки зависимостей. |
| `setup_paths_quick.ps1` | Упрощённый вариант предыдущего скрипта без дополнительных проверок и логирования. | Быстрый локальный запуск на доверенной машине/CI, где все каталоги уже на месте. |
| `activate_venv.ps1` | Создаёт стандартное `venv` через `py -3.13 -m venv`, устанавливает зависимости из `requirements*.txt` и активирует окружение. | Легаси режим для систем без `uv` или при необходимости полного офлайн-набора зависимостей. |
| `scripts/bootstrap_uv.py` | Проверяет наличие `uv`, при необходимости устанавливает его и выполняет `uv sync`. | До запуска `make uv-sync-locked`, чтобы гарантировать доступность `uv`. |
| `tools/environment/verify_qt_setup.py` | Убеждается, что Qt SDK найден, проверяет контрольные суммы и корректность путей `QML2_IMPORT_PATH`/`QT_PLUGIN_PATH`. | После установки Qt или при проблемах с обнаружением модулей QML. |

## Windows

### Быстрый старт (PowerShell 7+)
```powershell
python scripts/bootstrap_uv.py --sync
make uv-sync-locked
make uv-run CMD="python -m pytest -k smoke"
```

### Дополнительные шаги
1. При необходимости установите **Visual Studio 2022** с рабочей нагрузкой **Desktop development with C++** (для Qt инструментов и отладчиков).
2. Для переустановки Qt выполните `./activate_environment.ps1 -Setup -InstallQt -QtVersion 6.10.0`.
3. Для запуска приложения используйте `make uv-run CMD="python app.py"` — команда автоматически активирует окружение.

### Интеграция с Visual Studio
> ⚠️ Поддержка Visual Studio и `.pyproj/.sln` проектов прекращена. Используйте VS Code
> или терминал с `uv` для запуска и отладки.

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
make uv-sync-locked
make uv-run CMD="pytest -m 'not gui'"
```

### Qt и `.env`
```bash
cp env.sample .env
source activate_environment.sh --setup --install-qt --qt-version 6.10.0 \
    --qt-modules qtquick3d,qtshadertools,qtimageformats
make uv-sync-locked
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
- Для ручной проверки хешей зависимостей можно вызвать `make uv-run CMD="pip check --require-hashes -r requirements.txt"`, однако предпочтительным способом остаётся `make uv-sync-locked`.
- Если необходимо полностью переинициализировать окружение, удалите каталог `.uv/` и выполните шаги быстрого старта заново.
