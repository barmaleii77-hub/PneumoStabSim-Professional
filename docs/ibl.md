# IBL (Image-Based Lighting) — HDR окружение

IBL используется для освещения и фона сцены через HDR карты.

Компоненты
- `IblProbeLoader.qml` — асинхронная загрузка HDR (primary и fallback)
- `ExtendedSceneEnvironment` — `lightProbe`, `probeOrientation`, `probeExposure`

Свойства в QML
- `root.iblEnabled` — master-флаг для освещения и фона
- `root.iblLightingEnabled`, `root.iblBackgroundEnabled` — разделение света и фона
- `root.iblRotationDeg` — поворот skybox (только из пользовательского ввода)
- `root.iblIntensity` — яркость IBL (экспозиция)
- `root.iblPrimarySource`, `root.iblFallbackSource` — пути к HDR

Ключевые правила
- Skybox не зависит от поворота камеры. Только `iblRotationDeg`.
- Не нормализуем углы (SLERP), просто присваиваем `probeOrientation: Qt.vector3d(0, root.iblRotationDeg, 0)`.
- В Python environment payload формируется вложенно (`background`, `ibl`, `fog`, `ambient_occlusion`).

Диагностика
- В QML логируются загрузки HDR и готовность `iblReady`.
- В Python события IBL можно трассировать отдельным логгером (`ibl_logger`).

Типичные проблемы
- Неверные относительные пути HDR — используйте `../hdr/...` относительно `assets/qml/main.qml`.
- Включен `backgroundMode=color` при включённом IBL — включите `Skybox / HDR` в UI.
