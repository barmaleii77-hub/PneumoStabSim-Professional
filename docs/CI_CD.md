# CI/CD PneumoStabSim Professional

Документ описывает актуальную конфигурацию GitHub Actions и локальные проверки качества.

##1. Общая схема

- Файл воркфлоу: `.github/workflows/ci-cd.yml`
- Триггеры: `push` и `pull_request` в ветки `master`, `develop`
- Матрица тестов: `ubuntu-latest`, `windows-latest`, `macos-latest` × Python3.13

##2. Этапы конвейера

###2.1 Test Suite
- Устанавливает зависимости `pip install .[dev]`
- Настраивает Qt переменные окружения (offscreen-рендеринг)
- Запускает `pytest` для `tests/unit`, `tests/integration`, `tests/system`
- Собирает и загружает покрытие в Codecov (coverage.xml)

###2.2 Lint
- Проверка `flake8` (ошибки и статистика)
- Контроль форматирования `black --check`
- Статический анализ `mypy`
- **Новый шаг**: `python tools/audit_config.py --update-report` с последующей проверкой `git diff` для `reports/config_audit_report.md`

###2.3 Build Documentation
- Установка `pip install .[docs]`
- Сборка Sphinx: `sphinx-build -b html docs docs/_build/html`
- Публикация артефакта с HTML-документацией

###2.4 Release (только push в master)
- Подготовка черновика релиза и тэга `v2.0.0`

###2.5 Check Forbidden Artifacts
- Запуск `python tools/check_forbidden_artifacts.py`
- Гарантирует отсутствие случайных бинарников и временных файлов

##3. Локальные проверки перед коммитом

1. Установить зависимости:
 ```bash
 pip install -r requirements.txt
 pip install -r requirements-dev.txt
 ```
2. Выполнить pre-commit (обновляет отчёт аудита автоматически):
 ```bash
 pre-commit run --all-files
 ```
3. Запустить тесты:
 ```bash
 pytest
 ```
4. Убедиться, что `reports/config_audit_report.md` не меняется при повторном запуске `python tools/audit_config.py --update-report`.

##4. Отчёт аудита конфигурации в CI

- Если `audit_config` фиксирует расхождения, lint-джоба завершается ошибкой.
- При обновлении конфигурации необходимо коммитить изменения в baseline, schema и hash файлах, иначе CI не пройдёт.

##5. Частые проблемы

| Симптом | Решение |
| ------- | ------- |
| CI падает на шаге `Audit configuration consistency` | Перезапустите `python tools/audit_config.py --update-report`, обновите baseline и SHA256, закоммитьте отчёт |
| PySide6 не устанавливается локально | Используйте Python3.1364-bit и обновите pip (`pip install --upgrade pip`) |
| Разный результат тестов локально и в CI | Проверьте, что активировано виртуальное окружение и установлены dev-зависимости |

Документ актуален для конвейера января2025 года.
