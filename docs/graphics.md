# Графический конвейер и параметры визуализации

Описание всех групп параметров, которые управляются из `GraphicsPanel` и применяются в QML.

Группы
- Освещение (`lighting`): key/fill/rim/point
- Окружение (`environment`): background, ibl, fog, ambient occlusion
- Качество (`quality`): shadows, antialiasing, render policy, frame rate, OIT
- Камера (`camera`): fov/near/far/speed/autorotate
- Эффекты (`effects`): bloom, DoF, motion blur, lens flare, vignette, tonemap
- Материалы (`materials`): параметры PBR материалов для частей модели

Сигналы из Python
- `lighting_changed(dict)` — payload формируется `_prepare_lighting_payload()`
- `environment_changed(dict)` — payload формируется `_prepare_environment_payload()`
- `quality_changed(dict)` — `_prepare_quality_payload()`
- `camera_changed(dict)` — `_prepare_camera_payload()`
- `effects_changed(dict)` — `_prepare_effects_payload()`

Маппинг lighting
- Python: `state['lighting']` -> QML: `key_light`, `fill_light`, `rim_light`, `point_light`
- Переименование: `point.height` -> `point_light.position_y`

Environment payload (вложенный)
```json
{
  "background": { "mode": "skybox" | "color", "color": "#rrggbb", "skybox_enabled": true },
  "ibl": { "enabled": true, "intensity": 1.3, "source": "../hdr/studio.hdr", "fallback": "../hdr/studio_small_09_2k.hdr" },
  "fog": { "enabled": true, "color": "#b0c4d8", "density": 0.12, "near": 1200, "far": 12000 },
  "ambient_occlusion": { "enabled": true, "strength": 1.0, "radius": 8.0 }
}
```

Прямые вызовы QML
- `applyLightingUpdates`, `applyEnvironmentUpdates`, `applyQualityUpdates`, `applyCameraUpdates`, `applyEffectsUpdates`
- Вызываются из `MainWindow` напрямую через `QMetaObject.invokeMethod` (без очереди) для надёжного применения.

Дефолтные значения эффектов
- `lensFlareEnabled=false`, `vignetteEnabled=false` — чтобы не включались до прихода сигналов из Python

Диагностика
- В QML логируются вызовы функций (`console.log`) и важные состояния (IBL ready, skyboxActive)
- В Python логируем `log_qml_invoke`, `log_signal_emit`, и помечаем события как `applied_to_qml`
