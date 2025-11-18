# Стратегия CI/CD PneumoStabSim Professional

[![CI (develop)](https://github.com/barmaleii77-hub/PneumoStabSim-Professional/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/barmaleii77-hub/PneumoStabSim-Professional/actions/workflows/ci.yml)
[![Nightly](https://github.com/barmaleii77-hub/PneumoStabSim-Professional/actions/workflows/nightly.yml/badge.svg)](https://github.com/barmaleii77-hub/PneumoStabSim-Professional/actions/workflows/nightly.yml)
[![Release](https://github.com/barmaleii77-hub/PneumoStabSim-Professional/actions/workflows/release.yml/badge.svg)](https://github.com/barmaleii77-hub/PneumoStabSim-Professional/actions/workflows/release.yml)

Актуальная экосистема GitHub Actions состоит из четырёх взаимодополняющих конвейеров:

- `ci.yml` — проверяет каждый push и pull request в ветки `main`, `develop` и `feature/*`, гарантируя прохождение агрегированного `make check` на Linux и Windows.
- `nightly.yml` — ночной прогон (cron `0 3 * * *`) и реагирование на push в `main`, `develop`, `feature/*` с расширенной матрицей и сбором метрик качества.
- `branch-audit.yml` — аудит устаревших веток по расписанию (`0 4 * * 1`) и при push в `main`, `develop`, `feature/*`; открывает/обновляет issue для веток без активности.
- `release.yml` — пуши в `main`, `develop`, `feature/*` и `feature/hdr-assets-migration`, pull request в те же ветки, а также теги `v*` и ручные запуски собирают релизные артефакты (пакеты PyInstaller/CX-Freeze + wheel/SDist) с опциональным GPG-подписанием.

## Детализация workflow

### CI (`.github/workflows/ci.yml`)

| Шаг | Содержание |
| --- | --- |
| Подготовка | Checkout, установка Python 3.13, `uv` и Qt 6.10 (через `tools/setup_qt.py`). |
| `make check` | Запускает `python -m tools.ci_tasks verify`, включающий Ruff, mypy, `qmllint`, `bandit`, pytest (под управлением `coverage`). Дополнительно выполняются проверки шейдеров и среды Qt. |
| Постобработка | Генерация отчётов (`reports/quality/**`, `reports/tests/**`) и публикация артефактов. При падении сборки срабатывает анализ логов. |

Особенности:

- Покрытие исполняется в режиме `coverage run --parallel-mode`, результаты объединяются в `reports/quality/coverage.json` и транслируются в `reports/quality/dashboard.csv` через `tools.quality.report_metrics`.
- В `reports/quality/latest_metrics.json` фиксируются агрегированные метрики (процент покрытия, суммарная длительность тестов и разбивка по суитам).
- В отчёт `bandit.log` сохраняются результаты статического анализа безопасности.

### Nightly (`.github/workflows/nightly.yml`)

| Шаг | Содержание |
| --- | --- |
| Матрица | Ubuntu + Windows, запуск под offscreen Qt. |
| Базовая подготовка | Аналогична CI: установка зависимостей, Qt, `make check`. |
| Дополнительные прогоны | `make autonomous-check`, `make smoke`, `make integration`. |
| Метрики | После `make check` автоматически формируются coverage/test-duration метрики и обновляется `reports/quality/dashboard.csv`, которые выгружаются артефактами nightly. |

Nightly служит источником исторических данных качества и позволяет отслеживать динамику покрытия и времени выполнения тестов. Дополнительно workflow запускается при push в ветки `main`, `develop`, `feature/*`, чтобы команды видели результаты расширенной проверки до ночного окна.

### Branch Audit (`.github/workflows/branch-audit.yml`)

| Шаг | Содержание |
| --- | --- |
| Контейнер | `ghcr.io/github/gh-cli:2.48.0` с установленным `python3`.
| Аудит | Скрипт проходит по списку веток репозитория, исключая защищённые (`main`, `develop`, `gh-pages`, `feature/*` и ветку по умолчанию), и собирает ветки без коммитов старше порога `THRESHOLD_DAYS` (по умолчанию 30).
| Отчёт | Результаты выводятся в `GITHUB_STEP_SUMMARY`, а также публикуется предупреждение для каждой устаревшей ветки. При необходимости создаётся/обновляется issue с ярлыком `branch-audit`.

Workflow запускается по cron `0 4 * * 1` и на каждый push в `main`, `develop`, `feature/*`, что ускоряет обнаружение устаревших веток после активной разработки.

### Release (`.github/workflows/release.yml`)

| Шаг | Содержание |
| --- | --- |
| Триггеры | Push в `main`, `develop`, `feature/*`, `feature/hdr-assets-migration`; pull request в эти ветки; теги `v*`; ручной запуск `workflow_dispatch`. |
| Подготовка | `uv sync --frozen --extra release` подтягивает PyInstaller, CX-Freeze и `build`. |
| Сборка | `make package-all` формирует дистрибутивы PyInstaller/CX-Freeze и Python wheel/SDist (в `dist/packages`). |
| Проверки | Вычисление SHA256 для всех артефактов, опциональное GPG-подписание при наличии секретов. |
| Публикация | `softprops/action-gh-release` загружает архивы, wheel, SDist, манифесты и сигнатуры. |

## Метрики и артефакты качества

- **Coverage:** `reports/quality/coverage.json` (сырой отчёт `coverage json`).
- **Метрики качества:** `reports/quality/latest_metrics.json` + агрегирующий CSV `reports/quality/dashboard.csv` (обновляется `tools.quality.report_metrics`).
- **JUnit / анализ:** `reports/tests/*.xml` и `reports/tests/test_analysis_summary.*` остаются в артефактах CI и nightly.

Файл `dashboard.csv` предназначен для построения временных рядов; каждая строка добавляется при успешном прогоне `make check`.

## Паритет локальных инструментов

- `make check` использует тот же пайплайн, что и CI, включая `bandit` и генерацию coverage/метрик.
- Для локального запуска только security-аудита доступна команда `make security`.
- При необходимости отключить сбор покрытия установите `CI_TASKS_ENABLE_COVERAGE=0` перед вызовом `make check`.
- Локальные отчёты располагаются в `reports/quality/` и `reports/tests/`, что упрощает сравнение с CI.

## Обязательные статус-чеки

- **CI / Quality gate (ubuntu-latest)** и **CI / Quality gate (windows-latest)** — результаты матричного job из `ci.yml`.
- Дополнительные workflow (`nightly`, `release`) не блокируют merge, но их статусы отслеживаются инфраструктурой.

## История изменений

- **2025-02-26** — добавлен security-анализ (`bandit`), автоматическая публикация coverage/test-duration метрик и расширенная сборка релизов (wheel/SDist). Обновлены статус-бейджи и описание пайплайнов.
- **2025-10-22** — переход на обновлённый `ci.yml`, единое кэширование и SLA для красных сборок.
- **2025-11-11** — `nightly.yml` и `branch-audit.yml` теперь реагируют на push в `feature/*` (и основные ветки), чтобы вся команда получала ранние сигналы о регрессиях.
