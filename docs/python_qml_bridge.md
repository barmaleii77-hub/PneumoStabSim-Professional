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
