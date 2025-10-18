import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick.Controls
import "components"
import "core"
import "camera"
import "lighting"
import "scene"
import "geometry"

/*
 * PneumoStabSim - ENHANCED WORKING VERSION
 * ✅ Геометрия, материалы, окружение (IBL), анимация, автообновление
 */
Item {
    id: root
    anchors.fill: parent

    // ===============================================================
    // МОСТ PYTHON → QML (батч-обновления)
    // ===============================================================
    property var pendingPythonUpdates: null
    signal batchUpdatesApplied(var summary)

    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates)
            return;
        try {
            applyBatchedUpdates(pendingPythonUpdates);
        } finally {
            pendingPythonUpdates = null; // очищаем после применения
        }
    }

    function setIfExists(obj, prop, value) {
        try {
            if (obj && (prop in obj || typeof obj[prop] !== 'undefined')) {
                obj[prop] = value;
            }
        } catch (e) { /* ignore */ }
    }

    function applyBatchedUpdates(updates) {
        if (!updates) return;
        var applied = {};
        if (updates.geometry) { applyGeometryUpdates(updates.geometry); applied.geometry = true; }
        if (updates.camera) { applyCameraUpdates(updates.camera); applied.camera = true; }
        if (updates.lighting) { applyLightingUpdates(updates.lighting); applied.lighting = true; }
        if (updates.environment) { applyEnvironmentUpdates(updates.environment); applied.environment = true; }
        if (updates.quality) { applyQualityUpdates(updates.quality); applied.quality = true; }
        if (updates.materials) { applyMaterialUpdates(updates.materials); applied.materials = true; }
        if (updates.effects) { applyEffectsUpdates(updates.effects); applied.effects = true; }
        if (updates.animation) { applyAnimationUpdates(updates.animation); applied.animation = true; }
        batchUpdatesApplied(applied);
        // Автоподгон камеры после батч-обновлений геометрии
        if (updates.geometry && root.autoFitCameraOnGeometryChange)
            fitCameraToModel(true);
    }

    function applyGeometryUpdates(p) {
        if (!p) return;
        // Обновляем корневые свойства (миллиметры → миллиметры)
        setIfExists(root, 'userFrameLength', p.frameLength);
        setIfExists(root, 'userFrameHeight', p.frameHeight);
        setIfExists(root, 'userBeamSize', p.frameBeamSize);
        setIfExists(root, 'userLeverLength', p.leverLength);
        setIfExists(root, 'userCylinderLength', p.cylinderBodyLength);
        setIfExists(root, 'userTrackWidth', p.trackWidth);
        // userFrameToPivot — расстояние РАМА→ОСЬ РЫЧАГА, НЕ зависит от колеи
        setIfExists(root, 'userFrameToPivot', p.frameToPivot);
        setIfExists(root, 'userRodPosition', p.rodPosition);
        setIfExists(root, 'userBoreHead', p.boreHead);
        setIfExists(root, 'userRodDiameter', p.rodDiameter);
        setIfExists(root, 'userPistonThickness', p.pistonThickness);
        setIfExists(root, 'userPistonRodLength', p.pistonRodLength);
        // Сегменты цилиндра (если придут)
        if (p.cylinderSegments) setIfExists(root, 'cylinderSegments', p.cylinderSegments);
        if (p.cylinderRings) setIfExists(root, 'cylinderRings', p.cylinderRings);
    }

    function applyCameraUpdates(p) {
        if (!p) return;
        if (typeof p.fov === 'number') root.cameraFov = p.fov;
        if (typeof p.near === 'number') root.cameraNear = p.near;
        if (typeof p.far === 'number') root.cameraFar = p.far;
        // Автовращение камеры (необязательно)
        if (typeof p.auto_rotate_enabled === 'boolean') root.autoRotateEnabled = p.auto_rotate_enabled;
        if (typeof p.auto_rotate_speed === 'number') root.autoRotateSpeed = p.auto_rotate_speed;
        // Вспомогательно: автоподгон
        if (typeof p.auto_fit === 'boolean') root.autoFitCameraOnGeometryChange = p.auto_fit;
        if (typeof p.center_camera === 'boolean' && p.center_camera) fitCameraToModel(true);
    }

    function applyLightingUpdates(p) {
        if (!p) return;
        function applyDir(lightObj, data) {
            if (!data) return;
            if (typeof data.brightness === 'number') setIfExists(lightObj, 'brightness', data.brightness);
            if (typeof data.color === 'string') setIfExists(lightObj, 'color', data.color);
            if (typeof data.angle_x === 'number') lightObj.eulerRotation.x = data.angle_x;
            if (typeof data.angle_y === 'number') lightObj.eulerRotation.y = data.angle_y;
            if (typeof data.cast_shadow === 'boolean') setIfExists(lightObj, 'castsShadow', data.cast_shadow);
        }
        if (p.key || p.fill || p.rim) {
            applyDir(keyLight, p.key);
            applyDir(fillLight, p.fill || p.rim);
            return;
        }
        var groups = ['key','fill','rim'];
        for (var gi=0; gi<groups.length; ++gi) {
            var g = groups[gi];
            if (p[g] && typeof p[g] === 'object') {
                applyDir(g === 'key' ? keyLight : fillLight, p[g]);
            }
        }
    }

    function applyEnvironmentUpdates(p) {
        if (!p) return;
        // Цвет фона/режим
        if (p.background_color) root.backgroundColor = p.background_color;
        if (typeof p.skybox_enabled === 'boolean') root.iblBackgroundEnabled = p.skybox_enabled;
        if (typeof p.ibl_enabled === 'boolean') root.iblLightingEnabled = p.ibl_enabled;

        // IBL источники — ожидаем пути относительно assets/qml (../hdr/*.hdr)
        if (p.ibl_source) {
            iblProbe.primarySource = Qt.resolvedUrl(p.ibl_source);
        }
        if (p.ibl_fallback) {
            iblProbe.fallbackSource = Qt.resolvedUrl(p.ibl_fallback);
        }

        // Интенсивность/поворот
        if (typeof p.ibl_intensity === 'number') setIfExists(env, 'probeExposure', p.ibl_intensity);
        if (typeof p.ibl_rotation === 'number') setIfExists(env, 'probeOrientation', Qt.vector3d(0, p.ibl_rotation, 0));

        // Туман
        if (typeof p.fog_enabled === 'boolean') setIfExists(env, 'fogEnabled', p.fog_enabled);
        if (p.fog_color) setIfExists(env, 'fogColor', p.fog_color);
        if (typeof p.fog_density === 'number') setIfExists(env, 'fogDensity', p.fog_density);
        if (typeof p.fog_near === 'number') setIfExists(env, 'fogDepthNear', p.fog_near);
        if (typeof p.fog_far === 'number') setIfExists(env, 'fogDepthFar', p.fog_far);
    }

    function applyQualityUpdates(p) {
        if (!p) return;
        // Антиалиасинг
        if (p.antialiasing && p.antialiasing.primary) {
            switch (p.antialiasing.primary) {
            case 'off': env.antialiasingMode = SceneEnvironment.NoAA; break;
            case 'msaa': env.antialiasingMode = SceneEnvironment.MSAA; break;
            case 'ssaa': env.antialiasingMode = SceneEnvironment.SSAA; break;
            }
        }
        if (p.antialiasing && p.antialiasing.quality) {
            switch (p.antialiasing.quality) {
            case 'low': env.antialiasingQuality = SceneEnvironment.Low; break;
            case 'medium': env.antialiasingQuality = SceneEnvironment.Medium; break;
            case 'high': env.antialiasingQuality = SceneEnvironment.High; break;
            }
        }
        if (typeof p.dithering === 'boolean') setIfExists(env, 'ditheringEnabled', p.dithering);
        // Тени — глобальный переключатель
        if (p.shadows && typeof p.shadows.enabled === 'boolean') {
            setIfExists(keyLight, 'castsShadow', p.shadows.enabled);
            setIfExists(fillLight, 'castsShadow', p.shadows.enabled);
        }
        if (p.shadows && typeof p.shadows.resolution === 'string') {
            setIfExists(env, 'shadowMapQuality', p.shadows.resolution);
        }
    }

    function applyMaterialUpdates(p) {
        if (!p) return;
        var key = p.current_material || Object.keys(p)[0];
        var s = p[key];
        if (!s) return;
        var target = null;
        switch (key) {
        case 'frame': target = frameMat; break;
        case 'lever': target = leverMat; break;
        case 'tail': target = tailRodMat; break;
        case 'cylinder': target = cylinderMat; break;
        case 'piston_body': target = pistonBodyMat; break;
        case 'piston_rod': target = pistonRodMat; break;
        case 'joint_tail': target = jointTailMat; break;
        case 'joint_arm': target = jointArmMat; break;
        case 'joint_rod': target = jointRodMat; break;
        default: target = null;
        }
        if (!target) return;
        // Базовые
        if (s.base_color) setIfExists(target, 'baseColor', s.base_color);
        if (typeof s.metalness === 'number') setIfExists(target, 'metalness', s.metalness);
        if (typeof s.roughness === 'number') setIfExists(target, 'roughness', s.roughness);
        if (typeof s.specular === 'number') setIfExists(target, 'specularAmount', s.specular);
        if (typeof s.opacity === 'number') setIfExists(target, 'opacity', s.opacity);
        // Расширенные
        if (typeof s.clearcoat === 'number') setIfExists(target, 'clearcoatAmount', s.clearcoat);
        if (typeof s.clearcoat_roughness === 'number') setIfExists(target, 'clearcoatRoughness', s.clearcoat_roughness);
        if (typeof s.ior === 'number') setIfExists(target, 'indexOfRefraction', s.ior);
        if (s.emissive_color) setIfExists(target, 'emissiveColor', s.emissive_color);
        if (typeof s.emissive_intensity === 'number') setIfExists(target, 'emissivePower', s.emissive_intensity);
        if (typeof s.alpha_mode === 'string') setIfExists(target, 'alphaMode', s.alpha_mode);
    }

    function applyEffectsUpdates(p) {
        if (!p) return;
        // Bloom
        if (typeof p.bloom_enabled === 'boolean') setIfExists(env, 'glowEnabled', p.bloom_enabled);
        if (typeof p.bloom_intensity === 'number') setIfExists(env, 'glowIntensity', p.bloom_intensity);
        if (typeof p.bloom_threshold === 'number') setIfExists(env, 'glowHDRMinimumValue', p.bloom_threshold);
        if (typeof p.bloom_spread === 'number') setIfExists(env, 'glowBloom', p.bloom_spread);
        if (typeof p.bloom_glow_strength === 'number') setIfExists(env, 'glowStrength', p.bloom_glow_strength);
        if (typeof p.bloom_hdr_max === 'number') setIfExists(env, 'glowHDRMaximumValue', p.bloom_hdr_max);
        if (typeof p.bloom_hdr_scale === 'number') setIfExists(env, 'glowHDRScale', p.bloom_hdr_scale);
        if (typeof p.bloom_quality_high === 'boolean') setIfExists(env, 'glowQualityHigh', p.bloom_quality_high);
        if (typeof p.bloom_bicubic_upscale === 'boolean') setIfExists(env, 'glowUseBicubicUpscale', p.bloom_bicubic_upscale);
        // Tonemap
        if (typeof p.tonemap_enabled === 'boolean') setIfExists(env, 'tonemapEnabled', p.tonemap_enabled);
        if (p.tonemap_mode) {
            switch (p.tonemap_mode) {
            case 'filmic': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapFilmic); break;
            case 'aces': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapAces); break;
            case 'reinhard': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapReinhard); break;
            case 'gamma': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapGamma); break;
            case 'linear': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapLinear); break;
            }
        }
        if (typeof p.tonemap_exposure === 'number') setIfExists(env, 'tonemapExposure', p.tonemap_exposure);
        if (typeof p.tonemap_white_point === 'number') setIfExists(env, 'tonemapWhitePoint', p.tonemap_white_point);
        // DoF
        if (typeof p.depth_of_field === 'boolean') setIfExists(env, 'depthOfFieldEnabled', p.depth_of_field);
        if (typeof p.dof_focus_distance === 'number') setIfExists(env, 'depthOfFieldFocusDistance', p.dof_focus_distance);
        if (typeof p.dof_blur === 'number') setIfExists(env, 'depthOfFieldBlurAmount', p.dof_blur);
        // Motion blur
        if (typeof p.motion_blur === 'boolean') setIfExists(env, 'motionBlurEnabled', p.motion_blur);
        if (typeof p.motion_blur_amount === 'number') setIfExists(env, 'motionBlurAmount', p.motion_blur_amount);
        // Lens flare
        if (typeof p.lens_flare === 'boolean') setIfExists(env, 'lensFlareEnabled', p.lens_flare);
        if (typeof p.lens_flare_ghost_count === 'number') setIfExists(env, 'lensFlareGhostCount', p.lens_flare_ghost_count);
        if (typeof p.lens_flare_ghost_dispersal === 'number') setIfExists(env, 'lensFlareGhostDispersal', p.lens_flare_ghost_dispersal);
        if (typeof p.lens_flare_halo_width === 'number') setIfExists(env, 'lensFlareHaloWidth', p.lens_flare_halo_width);
        if (typeof p.lens_flare_bloom_bias === 'number') setIfExists(env, 'lensFlareBloomBias', p.lens_flare_bloom_bias);
        if (typeof p.lens_flare_stretch_to_aspect === 'boolean') setIfExists(env, 'lensFlareStretchToAspect', p.lens_flare_stretch_to_aspect);
        // Vignette
        if (typeof p.vignette === 'boolean') setIfExists(env, 'vignetteEnabled', p.vignette);
        if (typeof p.vignette_strength === 'number') setIfExists(env, 'vignetteStrength', p.vignette_strength);
        if (typeof p.vignette_radius === 'number') setIfExists(env, 'vignetteRadius', p.vignette_radius);
        // Color adjustments
        if (typeof p.adjustment_brightness === 'number') setIfExists(env, 'colorAdjustmentBrightness', p.adjustment_brightness);
        if (typeof p.adjustment_contrast === 'number') setIfExists(env, 'colorAdjustmentContrast', p.adjustment_contrast);
        if (typeof p.adjustment_saturation === 'number') setIfExists(env, 'colorAdjustmentSaturation', p.adjustment_saturation);
    }

    // === Анимация: обновления из Python/панелей ===
    function applyAnimationUpdates(params) {
        if (!params) return;
        if (typeof params.amplitude === 'number') root.userAmplitude = params.amplitude;  // в градусах
        if (typeof params.frequency === 'number') root.userFrequency = params.frequency;
        if (typeof params.phase === 'number') root.userPhaseGlobal = params.phase;
        if (typeof params.lf_phase === 'number') root.userPhaseFL = params.lf_phase;
        if (typeof params.rf_phase === 'number') root.userPhaseFR = params.rf_phase;
        if (typeof params.lr_phase === 'number') root.userPhaseRL = params.lr_phase;
        if (typeof params.rr_phase === 'number') root.userPhaseRR = params.rr_phase;
        updateLeverAngles();
    }

    function updatePistonPositions(positions) {
        if (!positions) return;
        if (positions.fl !== undefined) root.userPistonPositionFL = Number(positions.fl);
        if (positions.fr !== undefined) root.userPistonPositionFR = Number(positions.fr);
        if (positions.rl !== undefined) root.userPistonPositionRL = Number(positions.rl);
        if (positions.rr !== undefined) root.userPistonPositionRR = Number(positions.rr);
    }

    // ===============================================================
    // МИНИМАЛЬНЫЕ СВОЙСТВА ДЛЯ СЦЕНЫ
    // ===============================================================

    // Geometry parameters (мм)
    property real userBeamSize: 120
    property real userFrameHeight: 650
    property real userFrameLength: 3200
    property real userLeverLength: 800
    property real userCylinderLength: 500
    property real userTrackWidth: 1600      // «Колея»: влияет на РАМА→ОСЬ ХВОСТОВИКА ЦИЛИНДРА
    property real userFrameToPivot: 600     // «Рама→ось рычага»: НЕ зависит от «колеи»
    property real userRodPosition: 0.6
    property real userBoreHead: 80
    property real userRodDiameter: 35
    property real userPistonThickness: 25
    property real userPistonRodLength: 200

    // Camera
    property real cameraFov: 60.0
    property real cameraNear: 10.0
    property real cameraFar: 50000.0

    // Автонастройка камеры
    property bool autoFitCameraOnGeometryChange: true

    // Lighting
    property real keyLightBrightness: 1.2
    property color keyLightColor: "#ffffff"
    property real keyLightAngleX: -35
    property real keyLightAngleY: -40

    // Materials (defaults; будут переопределены из панели)
    property color frameBaseColor: "#c53030"
    property real frameMetalness: 0.85
    property real frameRoughness: 0.35
    property real frameSpecular: 0.8

    property color leverBaseColor: "#9ea4ab"
    property real leverMetalness: 1.0
    property real leverRoughness: 0.28
    property real leverSpecular: 0.9

    property color cylinderBaseColor: "#e1f5ff"
    property real cylinderOpacity: 0.3
    property real cylinderRoughness: 0.2
    property real cylinderSpecular: 0.6

    property color pistonBodyBaseColor: "#ff3c6e"
    property real pistonBodyMetalness: 1.0
    property real pistonBodyRoughness: 0.26
    property real pistonBodySpecular: 0.9

    property color pistonRodBaseColor: "#ececec"
    property real pistonRodMetalness: 1.0
    property real pistonRodRoughness: 0.18
    property real pistonRodSpecular: 1.0

    property color tailRodBaseColor: "#d5d9df"
    property real tailRodMetalness: 1.0
    property real tailRodRoughness: 0.3
    property real tailRodSpecular: 0.8

    property color jointTailBaseColor: "#2a82ff"
    property real jointTailMetalness: 0.9
    property real jointTailRoughness: 0.35
    property real jointTailSpecular: 0.7

    property color jointArmBaseColor: "#ff9c3a"
    property real jointArmMetalness: 0.9
    property real jointArmRoughness: 0.32
    property real jointArmSpecular: 0.7

    property color jointRodBaseColor: "#00ff55"
    property real jointRodMetalness: 0.9
    property real jointRodRoughness: 0.3
    property real jointRodSpecular: 0.7

    // Environment / IBL
    property bool iblLightingEnabled: true
    property bool iblBackgroundEnabled: true
    property real iblRotationDeg: 0.0
    property real iblIntensity: 1.0
    property color backgroundColor: "#1f242c"

    // Quality
    property bool shadowsEnabled: true
    property string shadowResolution: "2048"
    property int cylinderSegments: 32
    property int cylinderRings: 4

    // Auto-rotate camera (optional)
    property bool autoRotateEnabled: false
    property real autoRotateSpeed: 8.0  // deg/sec

    // ================================================================
    // ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КАМЕРЫ
    // ================================================================

    // Центр модели (по X/Z = 0, по Y = середина высоты рамы)
    function getModelCenter() {
        return Qt.vector3d(0, root.userBeamSize + root.userFrameHeight / 2.0, 0)
    }

    // Приближённый радиус модели для подгонки под FOV
    function getModelRadius() {
        var halfX = Math.max(root.userTrackWidth/2.0, root.userFrameToPivot + root.userLeverLength)
        var halfY = (root.userBeamSize + root.userFrameHeight) * 0.6 // центрированная половина высоты
        var halfZ = root.userFrameLength/2.0
        var r = Math.sqrt(halfX*halfX + halfY*halfY + halfZ*halfZ)
        return r * 1.05 // небольшой запас
    }

    // Подогнать камеру под модель (центрировать + выставить расстояние по FOV)
    function fitCameraToModel(adjustDistance) {
        var center = getModelCenter()
        // Обновляем цель орбиты
        mouseControls.orbitTarget = center
        // Опционально обновляем дистанцию
        if (adjustDistance) {
            var r = getModelRadius()
            var fovRad = (root.cameraFov || 60) * Math.PI / 180.0
            var dist = r / Math.sin(Math.min(Math.PI/3, fovRad/2.0)) + 300 // доп. отступ
            mouseControls.orbitDistance = Math.max(500, Math.min(30000, dist))
        }
        mouseControls.updateCameraOrbit()
    }

    // ================================================================
    // MATERIALS - Создаём ЗАРАНЕЕ для передачи в компоненты
    // ================================================================

    PrincipledMaterial {
        id: leverMat
        baseColor: root.leverBaseColor
        metalness: root.leverMetalness
        roughness: root.leverRoughness
        specularAmount: root.leverSpecular
    }

    PrincipledMaterial {
        id: tailRodMat
        baseColor: root.tailRodBaseColor
        metalness: root.tailRodMetalness
        roughness: root.tailRodRoughness
        specularAmount: root.tailRodSpecular
    }

    PrincipledMaterial {
        id: cylinderMat
        baseColor: root.cylinderBaseColor
        opacity: root.cylinderOpacity
        alphaMode: PrincipledMaterial.Blend
        roughness: root.cylinderRoughness
        specularAmount: root.cylinderSpecular
    }

    PrincipledMaterial {
        id: pistonBodyMat
        baseColor: root.pistonBodyBaseColor
        metalness: root.pistonBodyMetalness
        roughness: root.pistonBodyRoughness
        specularAmount: root.pistonBodySpecular
    }

    PrincipledMaterial {
        id: pistonRodMat
        baseColor: root.pistonRodBaseColor
        metalness: root.pistonRodMetalness
        roughness: root.pistonRodRoughness
        specularAmount: root.pistonRodSpecular
    }

    PrincipledMaterial {
        id: jointTailMat
        baseColor: root.jointTailBaseColor
        metalness: root.jointTailMetalness
        roughness: root.jointTailRoughness
        specularAmount: root.jointTailSpecular
    }

    PrincipledMaterial {
        id: jointArmMat
        baseColor: root.jointArmBaseColor
        metalness: root.jointArmMetalness
        roughness: root.jointArmRoughness
        specularAmount: root.jointArmSpecular
    }

    PrincipledMaterial {
        id: jointRodMat
        baseColor: root.jointRodBaseColor
        metalness: root.jointRodMetalness
        roughness: root.jointRodRoughness
        specularAmount: root.jointRodSpecular
    }

    PrincipledMaterial {
        id: frameMat
        baseColor: root.frameBaseColor
        metalness: root.frameMetalness
        roughness: root.frameRoughness
        specularAmount: root.frameSpecular
    }

    // ===============================================================
    // VIEW3D - 3D СЦЕНА + IBL PROBE
    // ===============================================================

    // Загрузчик HDR проба (IBL)
    IblProbeLoader {
        id: iblProbe
        // Стартовые значения из контекстных свойств, если заданы из Python
        primarySource: typeof startIblSource !== 'undefined' ? Qt.resolvedUrl(startIblSource) : ""
        fallbackSource: typeof startIblFallback !== 'undefined' ? Qt.resolvedUrl(startIblFallback) : ""
    }

    View3D {
        id: view3d
        anchors.fill: parent

        environment: ExtendedSceneEnvironment {
            id: env
            backgroundMode: root.iblBackgroundEnabled ? SceneEnvironment.SkyBox : SceneEnvironment.Color
            clearColor: root.backgroundColor
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
            // ВАЖНО: Skybox независим от положения камеры; поворот управляется только iblRotationDeg
            lightProbe: iblProbe.ready ? iblProbe.probe : null
            probeExposure: root.iblLightingEnabled ? root.iblIntensity : 0.0
            probeOrientation: Qt.vector3d(0, root.iblRotationDeg, 0)
        }

        // ===============================================================
        // WORLD ROOT - СЦЕНА (центрируем вокруг (0,0,0))
        // ===============================================================

        Node {
            id: worldRoot

            // Камера нацелена в центр сцены (центр модели)
            Node {
                id: cameraRig
                position: getModelCenter()

                PerspectiveCamera {
                    id: camera
                    position: Qt.vector3d(0, 0, 4000)
                    eulerRotation: Qt.vector3d(-20, 0, 0)
                    fieldOfView: root.cameraFov
                    clipNear: root.cameraNear
                    clipFar: root.cameraFar
                }
            }

            // ОСВЕЩЕНИЕ
            DirectionalLight {
                id: keyLight
                eulerRotation.x: root.keyLightAngleX
                eulerRotation.y: root.keyLightAngleY
                brightness: root.keyLightBrightness
                color: root.keyLightColor
                castsShadow: root.shadowsEnabled
            }

            DirectionalLight {
                id: fillLight
                eulerRotation.x: -60
                eulerRotation.y: 135
                brightness: 0.7
                color: "#dfe7ff"
            }

            // FRAME — центрирована по Z
            Frame {
                id: frameGeometry
                worldRoot: worldRoot
                beamSize: root.userBeamSize
                frameHeight: root.userFrameHeight
                frameLength: root.userFrameLength
                frameMaterial: frameMat
            }

            // Плоскости подвесок совпадают с рогами рамы (см. Frame.qml)
            readonly property real pivotZFront: -root.userFrameLength/2 + root.userBeamSize/2
            readonly property real pivotZRear:   root.userFrameLength/2 - root.userBeamSize/2

            // === Поперечные координаты X ===
            function armXLeft()  { return -root.userFrameToPivot }
            function armXRight() { return  root.userFrameToPivot }
            function tailXLeft() { return -root.userTrackWidth/2 }
            function tailXRight(){ return  root.userTrackWidth/2 }

            // FL (Front Left)
            SuspensionCorner {
                id: flCorner

                j_arm: Qt.vector3d(
                    worldRoot.armXLeft(),
                    root.userBeamSize,
                    worldRoot.pivotZFront
                )
                j_tail: Qt.vector3d(
                    worldRoot.tailXLeft(),
                    root.userBeamSize + root.userFrameHeight,
                    worldRoot.pivotZFront
                )

                leverAngle: root.fl_angle
                pistonPositionFromPython: root.userPistonPositionFL

                leverLength: root.userLeverLength
                rodPosition: root.userRodPosition
                cylinderLength: root.userCylinderLength
                boreHead: root.userBoreHead
                rodDiameter: root.userRodDiameter
                pistonThickness: root.userPistonThickness
                pistonRodLength: root.userPistonRodLength
                cylinderSegments: root.cylinderSegments
                cylinderRings: root.cylinderRings

                leverMaterial: leverMat
                tailRodMaterial: tailRodMat
                cylinderMaterial: cylinderMat
                pistonBodyMaterial: pistonBodyMat
                pistonRodMaterial: pistonRodMat
                jointTailMaterial: jointTailMat
                jointArmMaterial: jointArmMat
                jointRodMaterial: jointRodMat
            }

            // FR (Front Right)
            SuspensionCorner {
                id: frCorner

                j_arm: Qt.vector3d(
                    worldRoot.armXRight(),
                    root.userBeamSize,
                    worldRoot.pivotZFront
                )
                j_tail: Qt.vector3d(
                    worldRoot.tailXRight(),
                    root.userBeamSize + root.userFrameHeight,
                    worldRoot.pivotZFront
                )

                leverAngle: root.fr_angle
                pistonPositionFromPython: root.userPistonPositionFR

                leverLength: root.userLeverLength
                rodPosition: root.userRodPosition
                cylinderLength: root.userCylinderLength
                boreHead: root.userBoreHead
                rodDiameter: root.userRodDiameter
                pistonThickness: root.userPistonThickness
                pistonRodLength: root.userPistonRodLength
                cylinderSegments: root.cylinderSegments
                cylinderRings: root.cylinderRings

                leverMaterial: leverMat
                tailRodMaterial: tailRodMat
                cylinderMaterial: cylinderMat
                pistonBodyMaterial: pistonBodyMat
                pistonRodMaterial: pistonRodMat
                jointTailMaterial: jointTailMat
                jointArmMaterial: jointArmMat
                jointRodMaterial: jointRodMat
            }

            // RL (Rear Left)
            SuspensionCorner {
                id: rlCorner

                j_arm: Qt.vector3d(
                    worldRoot.armXLeft(),
                    root.userBeamSize,
                    worldRoot.pivotZRear
                )
                j_tail: Qt.vector3d(
                    worldRoot.tailXLeft(),
                    root.userBeamSize + root.userFrameHeight,
                    worldRoot.pivotZRear
                )

                leverAngle: root.rl_angle
                pistonPositionFromPython: root.userPistonPositionRL

                leverLength: root.userLeverLength
                rodPosition: root.userRodPosition
                cylinderLength: root.userCylinderLength
                boreHead: root.userBoreHead
                rodDiameter: root.userRodDiameter
                pistonThickness: root.userPistonThickness
                pistonRodLength: root.userPistonRodLength
                cylinderSegments: root.cylinderSegments
                cylinderRings: root.cylinderRings

                leverMaterial: leverMat
                tailRodMaterial: tailRodMat
                cylinderMaterial: cylinderMat
                pistonBodyMaterial: pistonBodyMat
                pistonRodMaterial: pistonRodMat
                jointTailMaterial: jointTailMat
                jointArmMaterial: jointArmMat
                jointRodMaterial: jointRodMat
            }

            // RR (Rear Right)
            SuspensionCorner {
                id: rrCorner

                j_arm: Qt.vector3d(
                    worldRoot.armXRight(),
                    root.userBeamSize,
                    worldRoot.pivotZRear
                )
                j_tail: Qt.vector3d(
                    worldRoot.tailXRight(),
                    root.userBeamSize + root.userFrameHeight,
                    worldRoot.pivotZRear
                )

                leverAngle: root.rr_angle
                pistonPositionFromPython: root.userPistonPositionRR

                leverLength: root.userLeverLength
                rodPosition: root.userRodPosition
                cylinderLength: root.userCylinderLength
                boreHead: root.userBoreHead
                rodDiameter: root.userRodDiameter
                pistonThickness: root.userPistonThickness
                pistonRodLength: root.userPistonRodLength
                cylinderSegments: root.cylinderSegments
                cylinderRings: root.cylinderRings

                leverMaterial: leverMat
                tailRodMaterial: tailRodMat
                cylinderMaterial: cylinderMat
                pistonBodyMaterial: pistonBodyMat
                pistonRodMaterial: pistonRodMat
                jointTailMaterial: jointTailMat
                jointArmMaterial: jointArmMat
                jointRodMaterial: jointRodMat
            }

        }  // end worldRoot
    }  // end View3D

    // ===============================================================
    // INFO PANEL
    // ===============================================================

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 450
        height: 200
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 8

        Column {
            anchors.centerIn: parent
            spacing: 5

            Text { text: "PneumoStabSim - FULL MODEL + ORBIT"; color: "#ffffff"; font.pixelSize: 14; font.bold: true }
            Text { text: "✅ Frame centered (U-shape, 3 beams)"; color: "#00ff88"; font.pixelSize: 10 }
            Text { text: "✅ 4 Suspension corners (FL, FR, RL, RR)"; color: "#00ff88"; font.pixelSize: 10 }
            Text { text: "✅ IBL loader expects ../hdr/*.hdr relative to assets/qml"; color: "#00ff88"; font.pixelSize: 9 }
            Text { text: "🖱️ Управление: ЛКМ-орбита, ПКМ-панорама, колесо-зум"; color: "#aaddff"; font.pixelSize: 9 }
        }
    }

    // ===============================================================
    // MOUSE CONTROLS (ПОЛНАЯ ОРБИТА + ЗУМ + ПАНОРАМА)
    // ===============================================================

    MouseArea {
        id: mouseControls
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        property real lastX: 0
        property real lastY: 0
        property bool isDragging: false
        property int dragButton: 0

        // Орбитальные параметры
        property real orbitYaw: 30        // Горизонтальный угол (вокруг Y)
        property real orbitPitch: -20     // Вертикальный угол (вокруг X)
        property real orbitDistance: 4000 // Расстояние камеры
        property vector3d orbitTarget: getModelCenter()

        // Скорости управления
        property real rotateSpeed: 0.35
        property real panSpeed: 2.0

        onPressed: (mouse) => {
            isDragging = true
            dragButton = mouse.button
            lastX = mouse.x
            lastY = mouse.y

            if (mouse.button === Qt.LeftButton) {
                cursorShape = Qt.SizeAllCursor
            } else if (mouse.button === Qt.RightButton) {
                cursorShape = Qt.ClosedHandCursor
            }
        }

        onReleased: {
            isDragging = false
            dragButton = 0
            cursorShape = Qt.ArrowCursor
        }

        onPositionChanged: (mouse) => {
            if (!isDragging) return

            var dx = mouse.x - lastX
            var dy = mouse.y - lastY

            if (dragButton === Qt.LeftButton) {
                // ЛКМ: Орбитальное вращение
                orbitYaw += dx * rotateSpeed
                orbitPitch = Math.max(-85, Math.min(85, orbitPitch - dy * rotateSpeed))

                updateCameraOrbit()
            } else if (dragButton === Qt.RightButton) {
                // ПКМ: Панорамирование
                var right = Qt.vector3d(
                    Math.cos(orbitYaw * Math.PI / 180),
                    0,
                    -Math.sin(orbitYaw * Math.PI / 180)
                )
                var up = Qt.vector3d(0, 1, 0)

                var moveX = -dx * panSpeed
                var moveY = dy * panSpeed

                orbitTarget.x += right.x * moveX + up.x * moveY
                orbitTarget.y += right.y * moveX + up.y * moveY
                orbitTarget.z += right.z * moveX + up.z * moveY

                updateCameraOrbit()
            }

            lastX = mouse.x
            lastY = mouse.y
        }

        onWheel: (wheel) => {
            var delta = wheel.angleDelta.y
            var factor = delta > 0 ? 0.9 : 1.1

            orbitDistance = Math.max(500, Math.min(20000, orbitDistance * factor))

            updateCameraOrbit()
        }

        function updateCameraOrbit() {
            // Вычисляем позицию камеры на орбите
            var yawRad = orbitYaw * Math.PI / 180
            var pitchRad = orbitPitch * Math.PI / 180

            var x = orbitDistance * Math.cos(pitchRad) * Math.sin(yawRad)
            var y = orbitDistance * Math.sin(pitchRad)
            var z = orbitDistance * Math.cos(pitchRad) * Math.cos(yawRad)

            cameraRig.position = orbitTarget
            camera.position = Qt.vector3d(x, y, z)

            // Направляем камеру на цель
            var lookX = -x
            var lookY = -y
            var lookZ = -z
            var lookLen = Math.sqrt(lookX*lookX + lookY*lookY + lookZ*lookZ)
            lookX /= lookLen
            lookY /= lookLen
            lookZ /= lookLen

            camera.eulerRotation.x = Math.atan2(lookY, Math.sqrt(lookX*lookX + lookZ*lookZ)) * 180 / Math.PI
            camera.eulerRotation.y = Math.atan2(lookX, -lookZ) * 180 / Math.PI
            camera.eulerRotation.z = 0
        }

        Component.onCompleted: {
            // Автоцентрирование камеры на старте
            fitCameraToModel(true)
        }

        // Автовращение камеры
        Timer {
            interval: 16
            running: root.autoRotateEnabled
            repeat: true
            onTriggered: {
                orbitYaw += (root.autoRotateSpeed / 60.0)
                updateCameraOrbit()
            }
        }
    }

    // ===============================================================
    // АНИМАЦИЯ РЫЧАГОВ по animationTime/частоте/фазам
    // ===============================================================

    function updateLeverAngles() {
        var t = root.animationTime
        var A = root.userAmplitude
        var w = 2.0 * Math.PI * root.userFrequency
        var g = root.userPhaseGlobal * Math.PI / 180
        fl_angle = A * Math.sin(w * t + g + root.userPhaseFL * Math.PI / 180)
        fr_angle = A * Math.sin(w * t + g + root.userPhaseFR * Math.PI / 180)
        rl_angle = A * Math.sin(w * t + g + root.userPhaseRL * Math.PI / 180)
        rr_angle = A * Math.sin(w * t + g + root.userPhaseRR * Math.PI / 180)
    }

    onAnimationTimeChanged: if (isRunning) updateLeverAngles()
    onUserAmplitudeChanged: updateLeverAngles()
    onUserFrequencyChanged: updateLeverAngles()
    onUserPhaseGlobalChanged: updateLeverAngles()
    onUserPhaseFLChanged: updateLeverAngles()
    onUserPhaseFRChanged: updateLeverAngles()
    onUserPhaseRLChanged: updateLeverAngles()
    onUserPhaseRRChanged: updateLeverAngles()

    Component.onCompleted: {
        console.log("=".repeat(60))
        console.log("🚀 FULL MODEL LOADED - MODULAR ARCHITECTURE + IBL (centered) + auto camera fit")
        console.log("=".repeat(60))
    }
}
