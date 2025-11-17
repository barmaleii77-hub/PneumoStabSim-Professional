# Итоги проверки качества (2025-03-05)

## Подготовка окружения
- Выполнено `make uv-sync` для установки зависимостей через uv (Python 3.13). 
- Установлены системные библиотеки для Qt/GL (`libgl1`, `libegl1`, `libxkbcommon0` и зависимости) для прохождения GUI-тестов.

## Запущенные команды
1. `ruff check` — завершено успешно, предупреждение о невалидном коде правила в `# noqa` (src/ui/main_window_pkg/main_window_refactored.py:40).
2. `mypy --config-file mypy.ini @mypy_targets.txt` — без замечаний.
3. `qmllint` для целей из `qmllint_targets.txt` — множество предупреждений об отсутствующих модулях/импортах, var-свойствах и не квалифицированных обращениях к id.
4. `coverage run -m pytest` — выполнено с ошибками и падениями тестов.
5. `coverage html -d reports/coverage_html` и `coverage xml -o reports/coverage.xml` — артефакты покрытий сохранены в `reports/`.

## Сводка по pytest
- Всего: 812 тестов; 792 пройдены, 1 пропущен, 6 ошибок, 13 падений.
- Ключевые проблемы:
  - Отсутствующие фикстуры `baseline_images_dir`, `physics_case_loader`, `settings_service` в нескольких тестах (graphics, physics, simulation, tools CLI).
  - QML загрузка `SimulationRoot.qml`/`main.qml` завершается ошибками (alias flowModelProxy, таймауты загрузки сцен).
  - Несоответствия ожидаемых данных панелей и fallback-графики, проблемы с событиями сигналов и холстом анимации.

## Покрытие ключевых модулей
Отчёт выборочно по модулям HDR, отражений и физики:

| Модуль | Покрытие |
| --- | --- |
| `src/common/settings_manager.py` (HDR-пути и нормализация) | 79% |
| `src/graphics/materials/baseline.py` (HDR skybox metadata) | 66% |
| `src/ui/environment_schema.py` (настройки отражений/среды) | 85% |
| `src/physics/forces.py` | 92% |
| `src/physics/integrator.py` | 83% |
| `src/physics/pneumo_system.py` | 87% |

Полные отчёты: `reports/coverage_html/index.html` (HTML) и `reports/coverage.xml` (XML).

## Наблюдения по qmllint
Основные категории предупреждений: неразрешённые импорты модулей (`CustomGeometry`, `environment`, `components`, `lighting` и др.), var-свойства, которые лучше заменить функциями, и многочисленные необоснованные обращения без квалификаторов к id в элементах сцены и панелях.

