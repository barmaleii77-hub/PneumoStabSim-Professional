# Release Quality Matrix

Матрица статусов ключевых проверок качества для текущей ветки / версии.

Обновляйте файл при подготовке релиза: каждая строка соответствует проверке,
статус фиксируется как pass/fail/na, комментарий кратко объясняет причину
отклонения или ссылку на артефакт отчёта.

## Legend
- pass: критерий выполнен
- fail: обнаружены проблемы (требует исправлений до релиза)
- na: не применимо к данному релизу

## Current Version
- Version: v2.1.0 (draft)
- Date: TBD
- Branch: feature/hdr-assets-migration
- Coverage threshold (COVERAGE_MIN_PERCENT): 75.0%

## Checks

| Check | Status | Artifact | Comment |
|-------|--------|----------|---------|
| Lint (ruff/flake8) | pass | reports/quality/ruff_check.log | Нет блокирующих ошибок |
| Typecheck (mypy) | pass | reports/quality/mypy.log | Ошибок типов не обнаружено |
| QML Lint | pass | reports/quality/qmllint.log | Автогенерация целей активна |
| Tests: unit | pass | reports/tests/unit.xml | Все пройдены |
| Tests: integration | pass | reports/tests/integration.xml | Все пройдены |
| Tests: ui | pass | reports/tests/ui.xml | Прогон завершён без skip |
| Shader validation | na | — | Шаг пропущен (CI_TASKS_SKIP_SHADERS=1) |
| Security (bandit) | pass | reports/quality/bandit.log | Уровень medium/medium принят |
| HDR assets verify | pass | reports/quality/hdr_verify.log | Все манифесты совпадают |
| Coverage >= 75% | pass | reports/quality/coverage.json | Порог удовлетворён |
| Performance scenario (phase3) | pass | reports/performance/ui_phase3_profile.json | FPS/память в допуске |
| Settings migration | pass | reports/quality/settings_migrate.log | Ошибок не выявлено |
| Environment trace | pass | reports/quality/launch_traces/launch_trace_latest.log | Qt переменные валидны |
| Skipped tests policy | pass | reports/tests/skipped_tests_summary.md | Отсутствуют skip |

## Actions Before Release
- Уточнить дату версии и обновить Version/Date поля.
- Проверить отсутствие новых legacy ключей в settings.
- При включении шейдерной сборки обновить строку Shader validation.

## Update Procedure
1. Запустить `make verify` + `make perf-check`.
2. Обновить статусы в таблице.
3. Закоммитить файл вместе с релизной документацией.
4. Сформировать тег и релиз заметки.

## History
- v2.1.0 (draft): initial matrix.
