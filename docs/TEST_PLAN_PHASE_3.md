# TEST_PLAN_PHASE_3.md — UI Phase 3 Playbook

Документ описывает целевые сценарии тестирования UI Phase 3 и связывает их с
фактическими автотестами. Он дополняет отчёт
`reports/tests/ui_phase3_test_gap_analysis_20251105.md` и служит чеклистом для
закрытия выявленных пробелов.

## 1. Обзор

| Подсистема | Цель | Автотесты | Планируемые дополнения |
| --- | --- | --- | --- |
| Training Presets | Проверка переключения преднастроек тренажёра и сохранения в сессии | *(в разработке)* | `tests/ui/test_training_presets.py` (создать): открыть панель, выбрать пресет, проверить обновление настроек сцены. |
| Diagnostics Overlay | Активация/деактивация HUD диагностик, проверка структурированных логов | `tests/ui/test_diagnostics_overlay.py` | Добавить проверку JSON логов и связь с `structlog` (см. docs/CODEX_COPILOT_PROMPT.md). |
| Camera HUD | Отображение накладок камеры, корректное позиционирование при изменении FOV | `tests/ui/test_camera_hud.py` | Расширить сценариями переключения орбитального режима и HUD в режиме free-cam. |
| HDR Toggle & Tonemap | Сохранение выбора HDR карты и режима тонемапинга | `tests/ui/test_hdr_toggle.py` | Добавить smoke-сценарий для Lavapipe (Vulkan) и проверку записи в settings manager. |
| Slider Dynamic Ranges | Диапазоны и шаги слайдеров в панели графики | `tests/ui/test_dynamic_sliders.py` | Покрыть синхронизацию с `config/app_settings.json` и валидацию ошибок. |
| Environment Backend Migration | Смена OpenGL/Vulkan/ANGLE без перезапуска | `tests/system/test_environment_migration.py` | Дополнить headless сценарием с `PSS_HEADLESS=1` и фиксацией логов. |

## 2. Запуск

```bash
# Базовый прогон headless UI Phase 3
make uv-run CMD="pytest -p pytestqt.plugin tests/ui/test_diagnostics_overlay.py"

# Полный пакет (после реализации оставшихся сценариев)
make uv-run CMD="pytest -p pytestqt.plugin tests/ui/test_phase3_suite.py"
```

## 3. Отчётность

- Результаты каждого прогона сохраняйте в `reports/tests/ui_phase3/` с именованием
  `YYYYMMDD_HHMMSS_<scenario>.md`.
- При добавлении нового теста обновляйте таблицу выше и отмечайте статус в
  `docs/RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md`.
- Обновлённые наблюдения по покрытиям заносите в
  `reports/tests/ui_phase3_test_gap_analysis_20251105.md` (дополнение в виде
  датированных блоков).

## 4. Manual QA

| Шаг | Описание | Артефакт |
| --- | --- | --- |
| 1 | Запустить приложение с `python app.py --phase3` | Скриншоты HUD в `reports/ui/` |
| 2 | Переключить HDR окружение через панель графики | `reports/ui/hdr_toggle_<date>.png` |
| 3 | Активировать диагностику (`Ctrl+D`) | Лог `reports/tests/diagnostics_overlay.log` |
| 4 | Проверить сохранение настроек после перезапуска | Обновить `reports/tests/ui_phase3_persistence.md` |

> Держите файл в актуальном состоянии — отсутствие записи по сценарию означает, что
> тест не покрыт и должен быть добавлен в ближайший спринт.
