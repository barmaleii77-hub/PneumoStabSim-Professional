# Training Workflows

Этот документ описывает систему учебных пресетов, добавленную в симулятор,
и связывает Python-каталог пресетов, UI-слой QML и тестовые сценарии.

## Каталог пресетов

- **Модуль**: `src/simulation/presets/`
- **Ключевые классы**:
  - `TrainingPreset` — описывает конфигурацию симуляции, пневматики и метаданные обучения.
  - `TrainingPresetMetadata` — хранит информацию о целях, длительности и сложности, а также пометки по сценарию (`scenario_id`, `scenario_label`, `scenario_summary`).
  - `TrainingPresetLibrary` — управляет коллекцией пресетов, применяет их к `SettingsManager` и определяет активный пресет по текущим настройкам.
- **Готовая фабрика**: `get_default_training_library()` возвращает библиотеку с семью профилями: `baseline`, `precision_mode`, `rapid_iteration`, `endurance_validation`, `pneumo_diagnostics`, `road_response_matrix`, `visual_diagnostics_suite`.
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

## Новые встроенные пресеты

| ID | Назначение | Ключевые фичи |
| --- | --- | --- |
| `pneumo_diagnostics` | Диагностика пневмосистемы | Акцент на открытии клапанов, FlowNetwork с визуализацией стрелок потока (`assets/qml/PneumoStabSim/scene/FlowNetwork.qml`). |
| `road_response_matrix` | Сравнение road-моделей | Переключение профилей дороги и анализ частотной реакции с помощью телеметрии (`assets/qml/components/TelemetryChartPanel.qml`). |
| `visual_diagnostics_suite` | Настройка графики и HUD | Камера фиксируется на эталонной позе, доступны индикаторы SceneBridge и шкала камеры (`assets/qml/components/BridgeIndicatorsPanel.qml`, `assets/qml/camera/CameraStateHud.qml`). |

Каждый пресет использует новые сценарии (`pneumo-diagnostics`, `road-matrix`, `visual-diagnostics`) из `src/simulation/presets/scenarios.py`, которые содержат расширенные метрики для отчётности.

## Сценарии использования

### Проверка пневмосистемы и визуализация клапанов

1. Примените пресет `pneumo_diagnostics` в TrainingPanel — FlowNetwork отобразит активные клапаны через `ValveIndicator` и направление потоков (`assets/qml/PneumoStabSim/scene/FlowNetwork.qml`).
2. Включите запись телеметрии по давлению и расходам, используя TelemetryChartPanel (`assets/qml/components/TelemetryChartPanel.qml`) для контроля латентности клапанов.
3. Сравните восстановление давления ресивера с метриками `receiver_recovery_time` в TrainingPanel (поля метаданных из `src/simulation/presets/library.py`).

### Матрица дорожных моделей и графики подвески

1. Выберите `road_response_matrix`, затем переключайте профили дороги через элементы UI панели обучения.
2. Используйте TelemetryChartPanel в режиме «Автомасштаб Y» для сравнения пиков энергий (`assets/qml/components/TelemetryChartPanel.qml`).
3. Отслеживайте обновления геометрии и симуляции через BridgeIndicatorsPanel, чтобы убедиться, что сцена синхронизирована (`assets/qml/components/BridgeIndicatorsPanel.qml`).

### Настройка визуальных панелей и HUD

1. Активируйте `visual_diagnostics_suite`, чтобы зафиксировать подвеску в эталонной позе.
2. Используйте CameraStateHud для проверки шкалы сцены и расстояний (`assets/qml/camera/CameraStateHud.qml`).
3. Включите SignalTracePanel для мониторинга событий SceneBridge и телеметрии (`assets/qml/components/SignalTracePanel.qml`).

Запуск `make check` выполняет линтеры и pytest, гарантируя целостность функциональности и документации.
