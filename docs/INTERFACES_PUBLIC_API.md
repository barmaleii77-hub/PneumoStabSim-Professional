# Публичные API модулей симулятора

Документ фиксирует актуальные точки интеграции между Python-частью симулятора,
Qt/QML и внешними подсистемами. Контракты перечислены для сервисов, которые
используются UI, симуляцией и тестами. Каждый раздел содержит протокол
взаимодействия и ожидаемые форматы сообщений.

## 1. Настройки и пресеты

### `src/core/interfaces.SettingsOrchestrator`

* `snapshot(paths: Sequence[str]) -> Mapping[str, Any]` — возвращает снимок
  настроек в виде словаря `dotted_path -> payload`. В ответе допускаются только
  JSON-совместимые типы.
* `apply_updates(updates: Mapping[str, Any], auto_save: bool = True) -> Mapping[str, Any]`
  — атомарно применяет пачку обновлений. Все ключи в `updates` записываются в
  виде «дотированной» строки (`"current.simulation.physics_dt"`). Возвращаемое
  значение должно отражать итоговые значения.
* `register_listener(callback)` — регистрирует колбэк, который получает словарь
  обновлённых путей при любой модификации настроек. Колбэк вызывается
  синхронно, поэтому реализация должна заботиться о потокобезопасности.

### `src/simulation/service.TrainingPresetService`

* `list_presets() -> Sequence[Mapping[str, Any]]` — сериализованные пресеты
  (используются UI и тестами). Каждый элемент содержит поля `id`,
  `simulation`, `pneumatic`, `metadata`.
* `describe_preset(preset_id: str) -> Mapping[str, Any]` — QML-представление
  пресета. Возвращает пустой словарь для неизвестного `preset_id`.
* `apply_preset(preset_id: str, auto_save: bool = True) -> Mapping[str, Any]` —
  применяет пресет через оркестратор и возвращает фактические обновления.
  Реализация обязана синхронно уведомить всех слушателей об изменении активного
  пресета.
* `active_preset_id() -> str` — идентификатор пресета, соответствующего
  текущему состоянию настроек. Пустая строка означает «дрейф».
* `register_active_observer(callback)` — регистрирует слушателя смены активного
  пресета. Колбэк вызывается немедленно при подписке.

## 2. Визуализация и UI

### `src/core/interfaces.VisualizationService`

* `dispatch_updates(updates: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Mapping[str, Any]]`
  — нормализует и сохраняет пакеты обновлений (категории: `camera`,
  `geometry`, `quality`, ...). Возвращаемый словарь передаётся в мост UI.
* `state_for(category: str) -> Mapping[str, Any]` — последний известный payload
  по категории.
* `latest_updates() -> Mapping[str, Mapping[str, Any]]` — последняя пачка
  обновлений.
* `access_profile() -> Mapping[str, Any]` — описание активной роли и прав
  доступа. Поле `_access` должно включаться в каждое обновление.
* `prepare_camera_payload(payload)` и `refresh_orbit_presets()` — отвечают за
  агрегацию настроек камеры и орбитальных пресетов.

### `src/ui/scene_bridge.SceneBridge`

* Qt-сигналы: `geometryChanged`, `cameraChanged`, `lightingChanged`, ...,
  `updatesDispatched`. Каждый принимает `QVariantMap`.
* `dispatch_updates(updates: Dict[str, Any]) -> bool` — передаёт данные в
  `VisualizationService` и эмитирует соответствующие сигналы.
* `reset(categories: Iterable[str] | None = None)` — очищает внутренний state и
  эмитирует пустые словари для затронутых категорий.
* `refresh_orbit_presets()` — синхронизирует орбитальные пресеты и возвращает
  актуальный манифест.

## 3. Симуляция и обмен сообщениями

### `src/runtime.state.StateBus`

* Основные сигналы:
  * `state_ready(StateSnapshot)` — публикуется из физического потока.
  * `start_simulation()`, `stop_simulation()`, `reset_simulation()`,
    `pause_simulation()` — команды от UI.
  * `set_physics_dt(float)`, `set_thermo_mode(str)`, `set_master_isolation(bool)`,
    `set_receiver_volume(float, str)` — конфигурационные команды.
  * `performance_update(PerformanceMetrics)` — телеметрия производительности.
* Сигналы должны использовать `Qt.QueuedConnection` при связывании между
  потоками.

### `src/runtime.sync`

* `LatestOnlyQueue` — потокобезопасная очередь с размером 1, выбрасывающая
  устаревшие сообщения. Методы `put_nowait`, `get_nowait` и `get_stats`
  используются для контроля частоты и потерь.
* `PerformanceMetrics` — аккумулирует статистику шага симуляции. Ключевые поля:
  `total_steps`, `avg_step_time`, `realtime_factor`, `frames_dropped`.

## 4. Телеметрия и журналы

### `src.telemetry.tracker.TelemetryTracker`

* `track_user_action(action, metadata=None, context=None)` — записывает событие
  пользователя в `reports/telemetry/user_actions.jsonl`.
* `track_simulation_event(event, metadata=None, context=None)` — события
  симуляции → `reports/telemetry/simulation_events.jsonl`.
* Записи сериализуются в формате JSON Lines и логируются сообщением
  `telemetry_event_recorded`.

### `src.diagnostics.signal_tracing.SignalTracer`

* `attach(obj, signal_name, alias=None)` — подключает обработчик к Qt-сигналу и
  логирует каждое срабатывание (`diagnostics.signals`, событие
  `signal_trace_event`).
* `records` — возвращает кортеж зафиксированных событий.
* `register_sink(callback)` — подписка на каждое событие трассировки.
* `dispose()` — отписка от всех сигналов (важно для тестов и UI).

## 5. Предписания по протоколам

* Все данные между симуляцией и UI передаются словарями с примитивными
  значениями или вложенными структурами (`dict`, `list`).
* Команды управления симуляцией публикуются только через `StateBus` — прямой
  вызов методов `PhysicsWorker` запрещён.
* Любые изменения настроек проходят через `SettingsOrchestrator` или его
  заглушки (см. `tests/helpers/fake_components.py`).
* При добавлении новых категорий визуализации обновляйте `_CATEGORIES` в
  `VisualizationService` и карту `_CATEGORY_PERMISSION_MAP`.

Документ предназначен для синхронизации UI-, симуляционных и тестовых команд,
а также служит базовой спецификацией при интеграции внешних компонентов
(аппаратный ECU, визуализация, системы телеметрии).
