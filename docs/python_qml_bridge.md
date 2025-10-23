# Мост Python ↔ QML

Прямые вызовы QML и батч-обновления.

Прямые вызовы
- Используем `QMetaObject.invokeMethod(root, method, DirectConnection, Q_ARG("QVariant", params))`
- Применено для: `applyEnvironmentUpdates`, `applyLightingUpdates`, `applyQualityUpdates`, `applyCameraUpdates`, `applyEffectsUpdates`
- Причина: моментальное применение и надёжность, без потерь в очередях

Батч-обновления
- Свойство `pendingPythonUpdates` на `root` (Item)
- `applyBatchedUpdates(updates)` внутри QML применяет все категории
- В Python `_push_batched_updates()` пробует путь через свойство, иначе — прямые вызовы

Подготовка payload’ов в Python (GraphicsPanel)
- `_prepare_lighting_payload()` — маппит `key/fill/rim/point` → `key_light/...`, `height` → `position_y`
- `_prepare_environment_payload()` — вложенная структура `background`, `ibl`, `fog`, `ambient_occlusion`
- `_prepare_quality_payload()` — плоские поля `taa_enabled`, `fxaa_enabled`, + вложенные `shadows`/`antialiasing`
- `_prepare_camera_payload()` — копия `state['camera']`
- `_prepare_effects_payload()` — копия `state['effects']`

Логирование
- `event_logger.log_qml_invoke(name, params)` — Python→QML вызов
- `event_logger.log_signal_emit(name, payload)` — отправка сигнала из Python
- В `main_window.py` помечаем успешные обновления как `applied_to_qml`

## События настроек

- В QML-контекст прокидывается `settingsEvents` — `SettingsEventBus` из Python.
- Доступные сигналы:
 - `settingChanged(change)` — одиночное изменение. Payload содержит `path`, `category`, `changeType`, `oldValue`, `newValue`, `timestamp`.
 - `settingsBatchUpdated(batch)` — батч-дифф (например, при `set_category()` или сбросе). Внутри `changes` и `summary` с количеством и категориями.
- `SettingsManager` автоматически эмитит эти события для `set`, `set_category`, `reset_to_defaults`, `save_current_as_defaults`.
- QML подписывается через `Connections { target: settingsEvents }` — теперь обновления параметров гарантированно достигают сцены.

## Сервис трассировки сигналов

- Новый контекст `signalTrace` (Singleton `SignalTraceService`).
- Задачи:
 - Регистрирует подписчиков (`registerSubscription(signal, name, source)`).
 - Собирает последние значения (`latestValues`) и список подписок (`subscriptions`).
 - Пишет журнал в `logs/signal_trace.jsonl` (можно отключать/фильтровать через `diagnostics.signalTrace` в `app_settings.json`).
- В `main.qml` добавлена overlay-панель `Signal trace` (включается флагом `overlayEnabled`).
- Для CLI-диагностики есть утилита `tools/trace_signals.py`:
   ```bash
   python tools/trace_signals.py --summary
   python tools/trace_signals.py --signal settings.settingChanged --since 2025-01-01
   ```
