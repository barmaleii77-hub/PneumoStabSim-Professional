# Training Workflows

Этот документ описывает новую систему учебных пресетов, добавленную в симулятор.
Она связывает Python-каталог пресетов, UI-слой QML и тестовые сценарии.

## Каталог пресетов

- **Модуль**: `src/simulation/presets/`
- **Ключевые классы**:
  - `TrainingPreset` — описывает конфигурацию симуляции, пневматики и метаданные обучения.
  - `TrainingPresetMetadata` — хранит информацию о целях, длительности и сложности, а также пометки по сценарию (`scenario_id`, `scenario_label`, `scenario_summary`).
  - `TrainingPresetLibrary` — управляет коллекцией пресетов, применяет их к `SettingsManager` и определяет активный пресет по текущим настройкам.
- **Готовая фабрика**: `get_default_training_library()` возвращает библиотеку с четырьмя профилями: `baseline`, `precision_mode`, `rapid_iteration`, `endurance_validation`.
- **Хранение параметров**: все числовые значения автоматически приводятся к типу `float`, булевы и строковые параметры сохраняют оригинальный вид. Метод `apply()` обновляет соответствующие пути в `SettingsManager` и генерирует события изменения настроек.
- **Сценарии**: `src/simulation/presets/scenarios.py` содержит общий каталог `SCENARIO_INDEX`. Он используется как для генерации метаданных, так и в тестах (`tests/scenarios/`).

### Добавление нового пресета

1. Создайте новый объект `TrainingPreset` в `DEFAULT_PRESETS` (см. `src/simulation/presets/library.py`).
2. При помощи вспомогательной функции `_build_metadata` добавьте блок `metadata`, указав `scenario_id`. При инициализации метаданных будут автоматически подтянуты `scenario_label`, `scenario_summary` и метрики из `SCENARIO_INDEX`.
3. Если сценария ещё нет, добавьте его в `src/simulation/presets/scenarios.py`, а затем импортируйте в `tests/scenarios/__init__.py`.
4. Расширьте тесты (`tests/scenarios/test_training_presets.py`), чтобы зафиксировать новую метрику или теги, если необходимо.

## Python ↔ QML мост

- **Файл**: `src/ui/bridge/training_bridge.py`
- **Класс**: `TrainingPresetBridge`
  - Экспортирует список пресетов (`presets`), активный пресет (`activePresetId`) и подробные данные выбранного пресета (`selectedPreset`).
  - Метод `applyPreset(preset_id)` обновляет настройки и возвращает `True`, если пресет применён успешно.
  - Реагирует на события `SettingsEventBus`, поэтому активный пресет пересчитывается при любых внешних изменениях.
- **Регистрация контекста**: в `UISetup._setup_qml_3d_view` мост выставляется в QML под именем `trainingBridge`.

## Пользовательский интерфейс QML

- **Модуль**: `assets/qml/training/`
- **Компонент**: `TrainingPanel.qml`
  - Отображает кнопки пресетов (через `Common.PresetButtons`).
  - Выводит теги, цели обучения, рекомендованные модули и метрики.
  - Показывает выбранные значения симуляции и пневматики в виде таблиц.
  - Отображает расширенные сведения о сценарии (`scenarioLabel`, `scenarioSummary`, заметки).
  - По умолчанию панель прикреплена к правому верхнему углу `main.qml`; параметр `showTrainingPresets` позволяет скрыть панель.

## Тестовые сценарии

- **Каталог**: `tests/scenarios/`
  - `__init__.py` содержит дескрипторы базовых сценариев (`SCENARIO_INDEX`).
  - `test_training_presets.py` проверяет:
    - согласованность метаданных пресетов со сценариями;
    - корректность применения пресета к `SettingsManager`;
    - детекцию расхождений через `matches_settings` и `resolve_active_id`.

Запуск `make check` выполняет линтеры и pytest, гарантируя целостность новой функциональности.
