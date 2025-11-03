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

## FogEffect v4.9.5 — компиляция шейдеров и fallback

- **Файлы:** `assets/qml/effects/FogEffect.qml`, `assets/shaders/effects/fog.vert`, `assets/shaders/effects/fog.frag`,
  `assets/shaders/effects/fog_fallback.frag`.
- **Цель:** гарантировать корректную компиляцию шейдеров при включённых флагах `QSG_INFO=1` и `QSG_RHI_DEBUG_LAYER=1`
  для всех рендер-бэкендов (ANGLE/D3D11, OpenGL, Vulkan/Metal) и сохранить визуально ожидаемый результат тумана.
- **Fallback:** при отсутствии depth-текстуры или ошибке компиляции активируется `fog_fallback.frag` и в
  `SceneEnvironmentController.qml` автоматически выключается туман, если причина — ошибка компиляции.

### Проверка компиляции шейдеров

1. Запустить приложение c включённым логированием Qt Shader Graph:

   ```bash
   QSG_INFO=1 QSG_RHI_DEBUG_LAYER=1 python app.py --test-mode
   ```

2. В логах искать строки `FogEffect`/`Shader` с ошибками. При успешной компиляции статус `Shader.Ready` не сопровождается
   сообщениями `❌ FogEffect`.
3. Для ANGLE/D3D11 и Vulkan/Metal дополнительно убедиться, что `FogEffect` фиксирует принятый профиль шейдеров через
   `preferDesktopShaderProfile` и при необходимости запрашивает десктопный GLSL (`requestDesktopShaderProfile(...)`).

> ℹ️ В CI-контейнере Qt Quick 3D работает в headless-режиме. Перед запуском необходимо установить системные
> зависимости `libgl1`, `libegl1`, `libxkbcommon0`, `libxkbcommon-x11-0`, иначе импорт PySide6 завершится ошибкой
> (`libGL.so.1`/`libxkbcommon.so.0` не найдены). После установки запуск команды выше завершается успешно, в логе
> фиксируются статусы `Shader.Ready` без сообщений об ошибках компиляции.

### Проверка визуального результата

1. На настольных системах (Windows ANGLE/D3D11, Linux/OpenGL, macOS Metal) включить туман в панели окружения и убедиться,
   что плотность, цвет и высотный профиль применяются в реальном времени.
2. На мобильных устройствах (Android/iOS, обычно GLES) проверить, что при сообщении `reportedGlesContext` эффект выбирает
   GLES-профиль и сохраняет ожидаемое визуальное поведение.
3. Искусственно отключить depth-текстуру (в панели разработчика или модифицируя `depthTextureAvailable`) и подтвердить,
   что активируется fallback-шейдер и лог выдаёт `⚠️ FogEffect: depth texture unavailable; using fallback shader`.
4. После восстановления глубины убедиться, что `SceneEnvironmentController` записывает `✅ Fog fallback cleared`.

### Документирование результатов

- Снимки логов и скриншотов визуальных проверок прикладываются к Phase 3 в разделе «Fog pipeline stability».
- При обновлении шейдеров фиксировать изменения и выводы в этом разделе, чтобы сохранить трассировку решений.

### Профиль GLSL 450 core и поведение fallback

- Основной фрагментный шейдер `fog.frag` переведён на `#version 450 core`, чтобы соответствовать требованию Qt Quick 3D
  поставлять «Vulkan-style GLSL» даже при запуске на OpenGL/ANGLE-бэкендах и тем самым получать корректный SPIR-V
  байткод через `qt_shader_tools`. [Qt docs подтверждают требование к Vulkan-совместимому GLSL для эффектов.][qt-effect]
- Fallback-шейдер `fog_fallback.frag` оставлен на `#version 330 core` без явных биндингов, что гарантирует загрузку в
  OpenGL ES/ANGLE профилях, когда `FogEffect` фиксирует отсутствие depth-текстуры (`depthTextureAvailable=false`) или
  ловит `Shader.Error` и принудительно переключает `passes` на безопасный режим.
- В QML-логике `FogEffect.qml` fallback активируется при ошибках компиляции или когда рендер-профиль не поддерживает
  GLSL 4.50. Таймер анимации автоматически выключается, пока `fallbackActive == true`, что предотвращает обращения к
  недоступным uniform'ам.
- Обновление профиля зафиксировано тестами: `make check` проходит без ошибок, включая `qmllint`, что подтверждено
  отчётом `reports/tests/make_check_20250213.md`.
- Рекомендации basysKom по compute/эффектным шейдерам (минимум GLSL 4.40 и автоматическая компиляция в SPIR-V)
  подтверждают выбор профиля 4.50 как безопасного запаса для Qt Quick 3D. [см. обзор basysKom.][basyskom-compute]

#### Ссылки

- [Qt docs — Effect QML Type][qt-effect]
- [basysKom — Use compute shader in Qt Quick][basyskom-compute]
- [Лог проверок `make check` (2025‑02‑13)](../reports/tests/make_check_20250213.md)


## ✅ Валидация Qt 6.10 (2025-11-03)

| Команда | Рендер-бэкенд | Итог | Комментарии |
|---------|----------------|------|-------------|
| `QT_QPA_PLATFORM=offscreen QT_RHI_BACKEND=vulkan … python app.py --test-mode --diag` | Qt Quick 3D → OpenGL RHI (software fallback) | ⚠️ | Контейнер без GPU: Qt сообщает `Backend: opengl` и `Loading backend software`, переключаясь на программный рендер. 【F:reports/run_vulkan_20251103.log†L21-L31】 |
| `QT_QPA_PLATFORM=offscreen QT_RHI_BACKEND=opengl … python app.py --test-mode --diag` | Qt Quick 3D → OpenGL RHI (software fallback) | ⚠️ | Идентичное поведение: Qt сразу загружает software-бэкэнд. 【F:reports/run_opengl_20251103.log†L21-L31】 |

### Основные наблюдения

- **Компиляция шейдеров:** Bloom, SSAO, DOF и Fog успешно резолвят как основные, так и fallback-шейдеры; сообщений `ERROR` от компилятора нет. 【F:reports/run_vulkan_20251103.log†L32-L207】
- **Fallback в ограниченном профиле:** Отсутствие depth/velocity текстур в offscreen-среде приводит к деградации SSAO, DOF, Motion Blur и Fog до безопасных режимов. 【F:reports/run_vulkan_20251103.log†L167-L205】
- **Материалы:** `SharedMaterials` и динамические материалы сцены инициализируются без ошибок; предупреждения касаются только отсутствующих сигналов/свойств в Connections. 【F:reports/run_vulkan_20251103.log†L159-L208】
- **QSG_INFO / RHI:** Qt логирует использование профиля Desktop GLSL 4.5 и переключение на software-путь; дополнительных RHI-ошибок не зафиксировано. 【F:reports/run_vulkan_20251103.log†L23-L197】
- **Ограничения тестовой среды:** QQuick offscreen не предоставляет Direct3D (ANGLE), поэтому покрытие D3D11 невозможно подтвердить. Необработанные предупреждения `applyGeometryUpdates` и `CameraStateHud` остаются и требуют ручной ревизии. 【F:reports/run_vulkan_20251103.log†L208-L220】

> ℹ️ В headless-режиме невозможно визуально подтвердить градиентный материал и прочие пост-эффекты. Для полной проверки требуется система с доступным GPU и интерактивным выводом.

[qt-effect]: https://doc.qt.io/qt-6/qml-qtquick3d-effect.html#details
[basyskom-compute]: https://www.basyskom.de/use-compute-shader-in-qt-quick/
