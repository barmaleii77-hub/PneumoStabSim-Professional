# Сквозной план трассировки и отладки PneumoStabSim Professional

## 1. Цели и принципы
- Гарантировать, что **все параметры** загружаются и сохраняются через `SettingsManager` без скрытых дефолтов или переопределений (`src/common/settings_manager.py`).
- Обеспечить построчную трассировку взаимодействия Python↔QML, включая сигналы, биндинги и обработчики (`src/ui/main_window`, `assets/qml`).
- Проверить алгоритмы симуляции, влияющие на анимированную схему (`src/runtime`, `src/physics`, `src/pneumo`, `src/road`).
- Подтвердить соответствие UI требованиям Qt 6.10: один параметр — один контрол, отсутствие скрытой логики, корректные диапазоны и типы.
- Сохранить полную трассируемость: любой параметр из `config/app_settings.json` должен иметь явный путь от JSON до виджета/эффекта и обратно при сохранении.

## 2. Подготовка окружения
1. Активировать Python 3.13 и установить зависимости из `requirements.txt` и `requirements-dev.txt` (выполнено `pip install -r ...`).
2. Экспортировать переменные `QT_QPA_PLATFORM=xcb` (или `offscreen` для CI) и `PSS_VERBOSE_CONFIG=1` для отслеживания путей загрузки настроек.
3. Настроить `QT_PLUGIN_PATH` и `QML2_IMPORT_PATH`, указывая на `assets/qml` и каталоги PySide6.
4. Включить Qt debugging tooling: `QT_LOGGING_RULES=qt.quick3d=true;qt.scenegraph.*=true`.
5. Подготовить профилировщики: `line_profiler`, `memory_profiler`, Qt Quick Profiling (через `QSG_VISUALIZE=overdraw` и `QSG_RHI_DEBUG_LAYER=1`).

## 3. Общая методология трассировки
1. **Инвентаризация параметров:**
   - Сгенерировать таблицу (скрипт `tools/trace_graphics_to_canvas.py`) с путями JSON → Python атрибут → QML свойство.
   - Для каждой записи проверить наличие обратного пути (UI → Python → JSON) через слоты `state_sync.py` и `SettingsManager.set()`.
2. **Статический анализ:**
   - `ruff`, `flake8`, `pylint`, `mypy` по всему `src`.
   - `qmlformat` и `qmlimportscanner` для `assets/qml`.
3. **Динамическая трассировка:**
   - Запуск приложения через `python -m src.app_runner --trace` (опция трассировки уже реализована в `src/app_runner.py`).
   - Использовать `PYTHONBREAKPOINT=ipdb.set_trace` внутри критических обработчиков (`signals_router.py`, `qml_bridge.py`).
   - Включить QML Inspector (`QMLSCENE_DEVICE=softwarecontext`, `QQmlDebuggingEnabler::enable`).
4. **Логирование:**
   - Проверить, что `src/common/logging_config.py` (если присутствует) или `logging.basicConfig` включают DEBUG для ключевых модулей.
   - Убедиться, что `SettingsManager` логирует путь к файлу, количество материалов и ошибки сохранения.

## 4. Python-трассировка по подсистемам
1. **Инициализация приложения (`src/app.py`, `src/app_runner.py`):**
   - Построчно проследить формирование `ApplicationContext`, создание `SettingsManager`, запуск `MainWindow`.
   - Проверить обработку аргументов CLI (`src/cli`).
2. **Менеджер настроек (`src/common/settings_manager.py`):**
   - Проанализировать `_resolve_settings_file`, `load`, `save`, `set`, `snapshot_defaults`.
   - Протестировать негативные сценарии: отсутствующий файл, повреждённый JSON, миграция ключей.
3. **Главное окно (`src/ui/main_window`):**
   - `ui_setup.py`: убедиться, что каждый контрол связывается с уникальным параметром и диапазоном.
   - `qml_bridge.py`: проследить отправку батч-обновлений в `root.pendingPythonUpdates` и обратные сигналы из QML.
   - `signals_router.py`: проверить маршрутизацию сигналов Qt → Python, отсутствие двойной подписки.
   - `state_sync.py`: убедиться, что загрузка/сохранение настроек использует `SettingsManager` без локальных дефолтов.
   - `menu_actions.py`: проверить обработчики «Сохранить», «Сбросить» и экспорт/импорт настроек.
4. **UI-панели (`src/ui/panels`)**
   - Для каждой панели (lighting, environment, camera, effects, quality, geometry) пройти методы `bind_settings`, `on_value_changed`, `apply_to_qml`.
   - Убедиться в отсутствии «магических коэффициентов»: значения извлекаются из JSON и отображаются напрямую.
5. **Runtime-система (`src/runtime`):**
   - `state.py`: структура `StateSnapshot`, проверка сериализации.
   - `sync.py`: очереди и метрики, контроль за потерянными кадрами.
   - `sim_loop.py`: конфигурация `PhysicsWorker`, загрузка таймингов, применение настроек (dt, лимиты, режимы).
   - Проверить потоки: QThread → PhysicsWorker, сигналы `state_ready`, `performance_update`, обработка ошибок.
6. **Физика и пневматика (`src/physics`, `src/pneumo`, `src/road`):**
   - Убедиться, что параметры (жёсткости, демпферы, давления) берутся из настроек.
   - Запустить тесты на крайние значения (минимальные/максимальные давления, отключенные контуры).

## 5. План трассировки QML
1. **Главный файл `assets/qml/main.qml`:**
   - Проследить `applyBatchedUpdates` и функции `applyGeometryUpdates`, `applyCameraUpdates`, `applyLightingUpdates`, `applyEffectsUpdates`.
   - Проверить util-функции `require*`, убедиться, что они вызываются для каждого параметра.
   - Проверить, что `batchUpdatesApplied` сигнал возвращается в Python (`qml_bridge.py`).
2. **Компоненты окружения и эффектов:**
   - `assets/qml/effects/PostEffects.qml`, `FogEffect.qml`, `SceneEnvironmentController.qml`: верифицировать сопоставление свойств (`SceneEnvironment`, `Tonemap`, `Bloom`, `Vignette`).
   - `assets/qml/lighting/*.qml`: проверить соответствие между JSON и источниками света (brightness, color, angles, shadow flags).
3. **Геометрия и анимация:**
   - `assets/qml/geometry/Frame.qml`, `SuspensionCorner.qml`, `CylinderGeometry.qml`: убедиться в корректных биндингах на `StateCache`/`GeometryCalculations`.
   - `assets/qml/core/StateCache.qml`, `GeometryCalculations.qml`: проследить алгоритмы интерполяции и нормализации углов.
   - Проверить, что анимация синхронизирована с `runtime/sim_loop.py` через `Qt.callLater`/`NumberAnimation` и сигналы `state_ready`.
4. **Камера:**
   - `assets/qml/camera/*.qml`: проверить диапазоны `MouseControls`, `CameraController` против настроек (`graphics.camera`).
5. **Диагностические QML (`assets/qml/diagnostic.qml`, `main_canvas_2d.qml`)**
   - Убедиться, что они используют те же источники данных и отключены/неактивны, если параметр не поддерживается.

## 6. Проверка UI и сигналов
1. Сгенерировать список всех сигналов Qt в Python (`rg "Signal\(" src/ui`) и убедиться, что каждый имеет тест или ручную проверку.
2. Использовать `pytest-qt` для автотестов взаимодействий: симулировать изменения параметров, убедиться в вызове `SettingsManager.set` и отправке батчей в QML.
3. Проверить, что отключенные элементы UI (`setEnabled(False)`) соответствуют параметрам, запрещённым документацией Qt 6.10.
4. Использовать `QSignalSpy` в тестах для проверки отсутствия двойных эмиссий.

## 7. Тестирование и контроль качества
1. **Юнит-тесты:** `pytest --qt-api=pyside6`.
2. **Интеграционные тесты:** `tests/ui/test_graphics_pipeline.py`, `tests/runtime/test_sim_loop.py` (при наличии); если отсутствуют — разработать сценарии.
3. **Линтеры и статический анализ:** `ruff check src`, `flake8 src`, `pylint src`, `mypy src`, `black --check .`.
4. **QML проверка:** `qmlformat --check assets/qml/main.qml`, `qmlimportscanner assets/qml/main.qml`.
5. **Профилирование:** Запуск `line_profiler` на горячих участках (`sim_loop.step`, `geometry_bridge.update_scene`).
6. **Регрессионные тесты:** сравнение сохранённого `config/app_settings.json` до/после с ожидаемыми значениями (скрипт `tests/utils/check_settings_snapshot.py`).

## 8. План исправления и отчётности
1. Любые обнаруженные расхождения документировать в `docs/TRACING_EXECUTION_LOG.md` (создать журнал).
2. Для каждого дефекта фиксировать:
   - ID параметра, путь JSON → UI.
   - Описание нарушения (скрытый дефолт, неверный диапазон, двойная обработка).
   - Шаги воспроизведения и тесты, подтверждающие исправление.
3. Изменения оформлять в отдельных коммитах с ссылкой на проверенную подсистему (например, `fix(ui): align lighting sliders with settings`).
4. Перед коммитом обязательно повторять полный набор тестов и линтеров.

## 9. Лучшие практики (сводка)
- Основываться на рекомендациях Qt 6.10: использовать `PropertyBinding`, `Connections`, `SceneEnvironment`, избегать устаревших API.
- Для настройки освещения и эффектов применять реальные диапазоны из официальной документации (яркость, coneAngle, blurAmount и т.д.).
- Следовать подходу «single source of truth» для конфигурации — JSON + `SettingsManager`.
- Все взаимодействия Python↔QML выполнять через батчевые обновления и сигналы, избегая прямого доступа к QML объектам без проверок.
- Обеспечивать тестируемость: каждый сигнал/слот должен иметь либо автоматический тест, либо ручной сценарий с явным чек-листом.
