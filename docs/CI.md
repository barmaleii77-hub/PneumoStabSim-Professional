# CI и локальные проверки

## GitHub Actions `ci.yml`

Новая сборка состоит из двух заданий:

| Джоб | ОС | Действия |
| --- | --- | --- |
| `lint` | Ubuntu | Устанавливает проект с dev-зависимостями, запускает `python -m tools.ci_tasks lint` и `python -m tools.ci_tasks typecheck`. |
| `tests` | Ubuntu, Windows | Скачивает Qt6.10.0, устанавливает проект и запускает `python -m tools.ci_tasks test` (на Linux внутри `xvfb-run`). |

Ключевые параметры окружения:

- Python:3.13.
- Qt:6.10.0 (qtquick3d, qtshadertools, qtimageformats).
- Переменные среды: `QT_QPA_PLATFORM=offscreen`, `QT_QUICK_BACKEND=software` для headless-запуска.

Успешное прохождение джоба `lint` является обязательным для запуска матрицы тестов.

## Локальный запуск

### Установка зависимостей и хуков

```sh
pip install -e .[dev]
pre-commit install
```

### Основные команды

| Цель | Make | Python модуль | Описание |
| --- | --- | --- | --- |
| Линтеры | `make lint` | `python -m tools.ci_tasks lint` | `ruff format --check` + `ruff check` над `app.py`, `src/`, `tests/`, `tools/`. |
| Типы | `make typecheck` | `python -m tools.ci_tasks typecheck` | `mypy` с конфигурацией из `pyproject.toml` и списком целей из `mypy_targets.txt`. |
| QML | `make qml-lint` | `python -m tools.ci_tasks qml-lint` | `qmllint`/`pyside6-qmllint` по целям из `qmllint_targets.txt` или `QML_LINT_PATHS`. |
| Тесты | `make test` | `python -m tools.ci_tasks test` | `pytest` над целями из `pytest_targets.txt` или каталога `tests`. |
| Комплексная проверка | `make check` | `python -m tools.ci_tasks verify` | Последовательно выполняет lint, mypy, qmllint и pytest. |

Для полного цикла перед пушем используйте:

```sh
pre-commit run --all-files
make check
```

## Подсказки

- Файл `tools/ci_tasks.py` обеспечивает единое поведение для Makefile, GitHub Actions и консольных сценариев.
- Хук `mypy` в `pre-commit` читает настройки из `pyproject.toml`; файл `mypy.ini` сохранён как зеркало для старых инструментов.
- Если необходимо добавить новые каталоги в проверки, обновите `PYTHON_LINT_PATHS` в Makefile или переменную среды перед запуском скриптов.
