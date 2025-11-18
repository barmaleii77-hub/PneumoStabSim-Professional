# Текущее состояние тестов и логов (2025-11-18)

## Проверенные журналы
- `full_qml_log.txt` (последний запуск UI)
- `qml_errors_full.txt` (агрегированные ошибки QML)
- `reports/qml_error_tasks.md` (сводка повторяющихся ошибок)
- `reports/tests/make-check_20251118121738.log` (результат `make check`)

## Зафиксированные ошибки
1. **QML: отсутствующее свойство `fogDensity`** — загрузка `assets/qml/main.qml` падает на строке 652 из-за привязки `fogDensity` в `SceneEnvironmentController`. Ошибка воспроизводится при старте UI и приводит к аварийному завершению и включению заглушки интерфейса.
2. **QML: отсутствующее свойство `ssaoEnabled`** — аналогичная ошибка на строке 667 в `assets/qml/main.qml` при инициализации SSAO в `SceneEnvironmentController`.
3. **Python↔QML bridge: проверка подписчиков** — попытка вызвать `SignalInstance.receivers` в процессе отправки стартовых параметров геометрии вызывает исключение (`SignalInstance` не имеет атрибута `receivers`), но сигналы продолжают отправляться без проверки подписчиков.
4. **Линтер Ruff (format)** — `make check` останавливается на этапе форматирования: `ruff format --check` требует переформатировать `tests/test_ibl_logger.py`.

## Карта падений по файлам
- `assets/qml/main.qml` — свойства `fogDensity` и `ssaoEnabled` отсутствуют в описании `SceneEnvironmentController` (ошибки загрузки QML). Источники: `full_qml_log.txt`, `qml_errors_full.txt`, `reports/qml_error_tasks.md`.
- `src/ui/main_window.py` / сигналы из `GeometryPanel` — вызов `SignalInstance.receivers` приводит к исключению, что указывает на проблему в Python-bridge при проверке подписчиков.
- `tests/test_ibl_logger.py` — требуется автоформатирование согласно `ruff format --check`.

## Рекомендации для следующего шага
- Добавить/удалить свойства `fogDensity` и `ssaoEnabled` в `SceneEnvironmentController` (или скорректировать связывание) перед повторным запуском `qmllint`/`make check`.
- Обновить логику проверки подписчиков сигналов в Python-bridge, чтобы использовать поддерживаемый API PySide6.
- Применить `ruff format tests/test_ibl_logger.py` для прохождения формат-чека и продолжения пайплайна `make check`.
