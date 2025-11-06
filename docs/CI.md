# CI и локальные проверки

## GitHub Actions `ci.yml`

Workflow **Continuous Integration** запускается на каждый `push` и `pull_request` в ветки `main` и `develop` и выполняется на матрице `ubuntu-latest` и `windows-latest`. Последовательность шагов:

1. Подготавливает Python 3.13, устанавливает `uv`, dev-зависимости и Qt 6.10.0 (вместе с плагинами `qtquick3d`, `qtshadertools`, `qtimageformats`).
2. Экспортирует пути Qt и устанавливает headless-переменные `QT_QPA_PLATFORM=offscreen`, `QT_QUICK_BACKEND=software`.
3. Запускает `make check`, который в свою очередь выполняет:
   - `python -m tools.ci_tasks verify` → линтеры (`ruff format --check`, `ruff check`), `mypy`, `qmllint`, затем последовательно `pytest` для `tests/unit`, `tests/integration`, `tests/ui` и анализ логов `python tools/analyze_logs.py`.
   - аппаратно-зависимые проверки: `make check-shaders`, `make validate-hdr-orientation`, `make localization-check`, `make qt-env-check`.
4. При сбоях workflow запускает `analyze_logs.py`, сохраняет AI-отчёт в `reports/quality/ai_failure_report.log` и выводит его в лог сборки.
5. Всегда загружает артефакты `reports/quality/**`, `reports/tests/**`, `reports/environment/**`, а также папку `logs/**`.

Все отчёты `tools/ci_tasks.py` складываются в `reports/quality/` и `reports/tests/`, поэтому матрица GitHub Actions получает одинаковую структуру артефактов для Ubuntu и Windows.

## Локальный запуск

### Установка зависимостей и хуков

```sh
pip install -e .[dev]
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
| Комплексная проверка | `make check` | `python -m tools.ci_tasks verify` | Полный CI-пайплайн: lint → mypy → qmllint → тесты → анализ логов + дополнительные проверки Makefile. |

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
- Если необходимо ограничить тесты, создайте файлы `pytest_unit_targets.txt`, `pytest_integration_targets.txt`, `pytest_ui_targets.txt` или задайте переменные окружения `PYTEST_*_TARGETS`.
- Для headless-запуска UI тестов локально экспортируйте `QT_QPA_PLATFORM=offscreen` и `QT_QUICK_BACKEND=software` (значения автоматически устанавливает `tools/ci_tasks test`).
