# CI и локальные проверки

## GitHub Actions `ci.yml`

Workflow **Continuous Integration** запускается на каждый `push` и `pull_request` в ветки `main` и `develop` и выполняется на матрице `ubuntu-latest` и `windows-latest`. Последовательность шагов:

1. Устанавливает headless-пакеты (`xvfb`, `xauth`, `dbus-x11`, Mesa software GL, `libosmesa6(-dev)`, `mesa-utils(-extra)`, `libglu1-mesa(-dev)`, `libegl1`, `libegl1-mesa(-dev)`, `libgles2`, `libgles2-mesa(-dev)`, `libgbm1`, `libdrm2`, `libxcb-*`, `libvulkan1`, `mesa-vulkan-drivers`, `vulkan-tools`) — все эти пакеты явно устанавливаются в workflow-файлах (`.github/workflows/*.yml`), включая оба варианта `libgles2` и `libgles2-mesa(-dev)` для полной совместимости с Dockerfile и install-скриптами. Этого достаточно для Mesa software rendering, проверки fallback-шейдеров и виртуального дисплея Qt Quick 3D.
2. Подготавливает Python 3.13, устанавливает `uv`, dev-зависимости и Qt 6.10.0 (вместе с плагинами `qtquick3d`, `qtshadertools`, `qtimageformats`). Скрипт `tools/setup_qt.py` по умолчанию разворачивает именно версию **6.10.0**, чтобы избежать расхождений между локальной средой, CI и документацией.
3. Экспортирует пути Qt и headless-переменные (`QT_QPA_PLATFORM=offscreen`, `QT_QUICK_BACKEND=software`, `QT_QUICK_CONTROLS_STYLE=Fusion`, `LIBGL_ALWAYS_SOFTWARE=1`, `MESA_GL_VERSION_OVERRIDE=4.1`, `MESA_GLSL_VERSION_OVERRIDE=410`).
4. Запускает `make check` (на Linux через `scripts/xvfb_wrapper.sh`), который в свою очередь выполняет:
   - `python -m tools.ci_tasks verify` → линтеры (`ruff format --check`, `ruff check`), `mypy`, `qmllint`, затем последовательно `pytest` для `tests/unit`, `tests/integration`, `tests/ui` и анализ логов `python tools/analyze_logs.py`.
   - аппаратно-зависимые проверки: `make check-shaders`, `make monitor-shader-logs` (обёртка над `python tools/check_shader_logs.py` с флагами `--fail-on-warnings --expect-fallback`), `make validate-hdr-orientation`, `make localization-check`, `make qt-env-check`.
5. При сбоях workflow запускает `analyze_logs.py`, сохраняет AI-отчёт в `reports/quality/ai_failure_report.log` и выводит его в лог сборки.
6. Всегда загружает артефакты `reports/quality/**`, `reports/tests/**`, `reports/environment/**`, а также папку `logs/**`.

Все отчёты `tools/ci_tasks.py` складываются в `reports/quality/` и `reports/tests/`, поэтому матрица GitHub Actions получает одинаковую структуру артефактов для Ubuntu и Windows.

## Локальный запуск

### Установка зависимостей и хуков

```sh
make uv-sync
pre-commit install --hook-type pre-commit --hook-type pre-push
```

### Основные команды

| Цель | Make | Python модуль | Описание |
| --- | --- | --- | --- |
| Линтеры | `make lint` | `python -m tools.ci_tasks lint` | Проверка `ruff format --check` + `ruff check` для `app.py`, `src/`, `tests/`, `tools/`. |
| Типы | `make typecheck` | `python -m tools.ci_tasks typecheck` | `mypy` с конфигурацией `mypy.ini`/`pyproject.toml` и целями из `mypy_targets.txt`. |
| QML | `make qml-lint` | `python -m tools.ci_tasks qml-lint` | `qmllint`/`pyside6-qmllint` по путям из `qmllint_targets.txt` или `QML_LINT_PATHS`. |
| Юнит-тесты | `make test-unit` | `python -m tools.ci_tasks test-unit` | Быстрый прогон `pytest` по `tests/unit` или списку из `pytest_unit_targets.txt`. |
| Интеграционные тесты | `make test-integration` | `python -m tools.ci_tasks test-integration` | Запускает `tests/integration` (поддерживаются overrides через `PYTEST_INTEGRATION_TARGETS`). |
| UI/QML тесты | `make test-ui` | `python -m tools.ci_tasks test-ui` | Полный прогон `tests/ui` с headless-настройками Qt. |
| Анализ логов | `make analyze-logs` | `python -m tools.ci_tasks analyze-logs` | Готовит отчёт `logs/graphics/analysis_latest.json` и выводит сводку в консоль. |
| Полный тестовый набор | `make test` | `python -m tools.ci_tasks test` | Последовательно запускает юнит, интеграционные и UI тесты, затем анализ логов. |
| Комплексная проверка | `make check` | `python -m tools.ci_tasks verify` | Полный CI-пайплайн: lint → mypy → qmllint → тесты → анализ логов + дополнительные проверки Makefile. На Linux используйте `bash scripts/xvfb_wrapper.sh make check`, чтобы повторить поведение CI. |

### Обязательные кроссплатформенные прогоны

После любого изменения кода выполняйте две последовательности:

1. `make cross-platform-prep` → `make cross-platform-test` на Linux/CI-контейнере.
2. `python -m tools.task_runner cross-platform-prep -- --use-uv` → `python -m tools.task_runner cross-platform-test -- --pytest-args tests` на Windows.

Скрипт `tools.cross_platform_test_prep` синхронизирует `uv`-окружение, ставит системные пакеты (`apt`/`choco`) и удостоверяется, что `PySide6` и `pytest-qt` доступны. На Linux он повторяет набор пакетов из Dockerfile (Mesa/Qt стек, `git`, `curl`, `pkg-config`, `build-essential`, `libx11-*`, `libxcb-*`, `libegl-dev`, `libgles-dev`, `mesa-utils-extra`, `libvulkan1`, `mesa-vulkan-drivers`, `vulkan-tools` и др.) и фиксирует стиль `QT_QUICK_CONTROLS_STYLE=Fusion`, чтобы headless-прогон совпадал с рабочей средой. Если зависимости отсутствуют, `pytest` аварийно завершает прогон с подсказкой повторно запустить подготовку, поэтому пропуски GUI/QML тестов невозможны. Допускается временно признать пропуски через `--allow-skips` или `PSS_ALLOW_SKIPPED_TESTS=1`, однако CI-конвейеры должны выполняться без этих флагов.

### Headless-рецепт (CI и контейнеры)

1. **Переменные окружения**
   ```sh
   export QT_QPA_PLATFORM=offscreen
   export QT_QUICK_BACKEND=software
   export QT_QUICK_CONTROLS_STYLE=Fusion
   export QSG_RHI_BACKEND=opengl
   export LIBGL_ALWAYS_SOFTWARE=1
   ```
   На macOS допускается `QT_QPA_PLATFORM=minimal` в паре с `QT_MAC_WANTS_LAYER=1`,
   если требуется инициализировать Metal без окон. Для Windows RDP-сессий
   достаточно `QT_QPA_PLATFORM=offscreen` + `QSG_RHI_BACKEND=d3d11`.
   Для диагностики сохраните снимок окружения: `python app.py --safe --env-report ci-env.md`.
2. **Smoke-проверка** — `python app.py --safe` (alias: `--test-mode`). Скрипт
   выполняет импорт Qt, прогоняет диагностические проверки и завершает процесс
   без инициализации QML сцены.
3. **Проверка совместимости** — при необходимости добавьте `--legacy`, чтобы
   принудительно использовать OpenGL и убедиться, что fallback-шейдеры
   компилируются корректно.
4. **CI wrapper** — GitHub Actions выполняет `make check` через
   `scripts/xvfb_wrapper.sh`, что обеспечивает виртуальный дисплей и повторяет
   локальные условия Mesa.

### Pre-commit хуки

- При установке `pre-commit` активируются:
  - `ci-fast-lint` (стадия `pre-commit`) — обёртка над `python -m tools.ci_tasks lint`.
  - `ci-typecheck` и `ci-test-unit` (стадия `pre-push`) — гарантируют, что перед публикацией проходят типы и базовые тесты.
  - `pytest-gui` остаётся ручным (`pre-commit run pytest-gui`) и выполняет `python -m tools.ci_tasks test-ui` для полной проверки QML/GUI.
- Дополнительные проверки (`check-ui-utf8`, `check-forbidden-artifacts`) запускаются на каждом коммите и не требуют передачи файлов.

Для полного цикла перед пушем рекомендуется выполнить:

```sh
pre-commit run --all-files
make check
```

## Подсказки

- `tools/ci_tasks.py` — единая точка входа для Makefile, локальных сценариев и GitHub Actions. Выходные логи лежат в `reports/quality/*.log` и `reports/tests/*.xml`.
- После `make check` формируется `reports/tests/shader_logs_summary.json` (через `tools/check_shader_logs.py`). Файл фиксирует предупреждения/ошибки Qt Shader Baker и наличие fallback-шейдеров.
- `pytest_targets.txt` перечисляет дополнительные критические сценарии, которые запускаются *вместе* с базовыми юнит/интеграционными/UI-сьютами. Файл не ограничивает тестовый набор и должен оставаться пустым по умолчанию: чтобы временно сократить прогон, используйте `pytest_unit_targets.txt`, `pytest_integration_targets.txt`, `pytest_ui_targets.txt` или переменные окружения `PYTEST_*_TARGETS`.
- GitHub Actions обрабатывает пропуски через `python -m tools.ci_tasks check-skips --require-report`. Любые `skip`/`xfail` должны быть явно помечены `# pytest-skip-ok` и сопровождаться комментарием; без явного `CI_SKIP_REASON` и флага `PSS_ALLOW_SKIPPED_TESTS=1` сборка завершается ошибкой.
- Для headless-запуска UI тестов локально экспортируйте `QT_QPA_PLATFORM=offscreen` и `QT_QUICK_BACKEND=software` (значения автоматически устанавливает `tools/ci_tasks test`). На Linux задействуйте `scripts/xvfb_wrapper.sh <команда>` для Qt Quick 3D/QtCharts.
- `make check` автоматически вызывает `make uv-sync --extra dev`, поэтому lock-файл и dev-зависимости синхронизируются перед запуском линтеров и тестов.
- Новые тесты должны выполняться на всех поддерживаемых платформах. Не помечайте их `skip`/`xfail` без документированного исключения; вместо этого фиксируйте недостающие зависимости через `tools.cross_platform_test_prep` и указывайте причину в `CI_SKIP_REASON`, если пропуски временно признаны в CI.
