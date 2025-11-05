# Трассировка исполнения и тестирование (2025-10-21)

## Подготовка окружения
- Установлены системные зависимости `libgl1`, `libegl1` и дополнительные библиотеки XCB для запуска PySide6.
- Выполнена установка Python-зависимостей из `requirements.txt` и `requirements-dev.txt`.

## Реализованные обновления
1. **Схема окружения QML**
   - Добавлена строгая схема `src/ui/environment_schema.py` для всех параметров окружения Qt 6.10.
   - Реализована валидация, приведение типов и проверка взаимных ограничений (`fog_near` < `fog_far`).
2. **Термодинамика пневмосистемы**
   - Переписан модуль `src/pneumo/gas_state.py`: добавлены классы `LineGasState`, `TankGasState`, функции `iso_update`, `adiabatic_update`, `create_*` и `apply_instant_volume_change`.
   - Обеспечена совместимость с тестами на идеальный газ и режимы ресивера.
3. **Конфигурация по умолчанию**
   - Создан `src/app/config_defaults.py` с фабриками для системной конфигурации, газовой сети и параметров симуляции.
4. **Централизованное структурированное логирование**
   - Добавлена фабрика логеров `src/diagnostics/logger_factory.py`, настраивающая `structlog` и перенаправляющая все `logging`-совместимые вызовы в JSON-пайплайн.
   - Обновлены `src/diagnostics/signal_tracing.py`, `src/diagnostics/profiler.py` и DI-контейнер `src/core/container.py`, чтобы использовать привязанные логеры и сохранять контекст модуля.
   - QML fallback сцена (`assets/qml/SimulationFallbackRoot.qml`) публикует события через `assets/qml/diagnostics/LogBridge.js`, благодаря чему console-логи имеют такой же JSON-формат, как Python-диагностика.
5. **Маршрутизация телеметрии**
   - Пакет `src/telemetry/` реализует трекер пользовательских действий и симуляционных событий и сохраняет их в `reports/telemetry/*.jsonl`.
   - Каждый event сопровождается контекстом (метаданные, источник), что упрощает анализ отчётами и скриптами Python.

## Тестирование
- `QT_QPA_PLATFORM=offscreen pytest -q` *(фейл: отсутствует метод `RangeSlider.step`, не реализованы `GeometryPanel.get_parameters`, отсутствует `QSignalSpy` в PySide6)*.
- `ruff check src` *(фейл: 441 существующих стилевых/импортных проблем в UI-панелях и виджетах).*
