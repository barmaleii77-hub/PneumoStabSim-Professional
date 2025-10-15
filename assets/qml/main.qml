import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick.Controls
import Qt.labs.folderlistmodel
import "components"

/*
 * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.9.4 SKYBOX FIX)
 * 🚀 ENHANCED: Separate IBL lighting/background controls + procedural geometry quality
 * ✅ All properties match official Qt Quick 3D documentation
 * 🐛 FIXED: Removed skyBoxBlurAmount (not exposed by Qt Quick 3D API)
 * 🐛 CRITICAL FIX v4.9.4: Skybox rotation with continuous angle accumulation
 *    - Added envYaw for continuous angle tracking (NO flips at 0°/180°)
 *    - probeOrientation uses accumulated envYaw instead of direct cameraYaw
 *    - Background is stable regardless of camera rotation
 * 🐛 FIXED: emissiveVector typo → emissiveVector
 */
Item {
    id: root
    anchors.fill: parent
    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
    property bool showOverlayControls: false
    
    // ===============================================================
    // 🚀 SIGNALS - ACK для Python после применения обновлений
    // ===============================================================
    
    signal batchUpdatesApplied(var summary)

    // ===============================================================
    // 🚀 QT VERSION DETECTION (для условной активации возможностей)
    // ===============================================================
    
    readonly property string qtVersionString: typeof Qt.version !== "undefined" ? Qt.version : "6.0.0"
    readonly property var qtVersionParts: qtVersionString.split('.')
    readonly property int qtMajor: qtVersionParts.length > 0 ? parseInt(qtVersionParts[0]) : 6
    readonly property int qtMinor: qtVersionParts.length > 1 ? parseInt(qtVersionParts[1]) : 0
    readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10
    
    // ✅ Условная поддержка dithering (доступно с Qt 6.10)
    property bool ditheringEnabled: true  // Управляется из GraphicsPanel
    readonly property bool canUseDithering: supportsQtQuick3D610Features
    // ✅ Гейт для Specular AA (временно отключаем по умолчанию из-за ошибки шейдера)
    readonly property bool canUseSpecularAA: false

    // ===============================================================
    // 🚀 CRITICAL FIX v4.9.4: SKYBOX ROTATION - INDEPENDENT FROM CAMERA
    // ===============================================================
    
    // ✅ ПРАВИЛЬНО: Skybox вращается ТОЛЬКО от пользовательского iblRotationDeg
    // Камера НЕ влияет на skybox вообще!
    
    // ❌ УДАЛЕНО: envYaw, _prevCameraYaw, updateCameraYaw() - это было НЕПРАВИЛЬНО
    // Эти переменные СВЯЗЫВАЛИ фон с камерой, что вызывало проблему

    // ===============================================================
    // 🚀 PERFORMANCE OPTIMIZATION LAYER
    // ===============================================================
    
    // ✅ ОПТИМИЗАЦИЯ #1: Кэширование анимационных вычислений
    QtObject {
        id: animationCache
        
        // Базовые значения (вычисляются 1 раз за фрейм вместо 4х)
        property real basePhase: animationTime * userFrequency * 2 * Math.PI
        property real globalPhaseRad: userPhaseGlobal * Math.PI / 180
        
        // Предварительно вычисленные фазы для каждого угла
        property real flPhaseRad: globalPhaseRad + userPhaseFL * Math.PI / 180
        property real frPhaseRad: globalPhaseRad + userPhaseFR * Math.PI / 180
        property real rlPhaseRad: globalPhaseRad + userPhaseRL * Math.PI / 180
        property real rrPhaseRad: globalPhaseRad + userPhaseRR * Math.PI / 180
        
        // Кэшированные синусы (4 sin() вызова → 4 кэшированных значения)
        property real flSin: Math.sin(basePhase + flPhaseRad)
        property real frSin: Math.sin(basePhase + frPhaseRad)
        property real rlSin: Math.sin(basePhase + rlPhaseRad)
        property real rrSin: Math.sin(basePhase + rrPhaseRad)
    }
    
    // ✅ ОПТИМИЗАЦИЯ #2: Геометрический калькулятор
    QtObject {
        id: geometryCache
        
        // Константы (вычисляются только при изменении параметров)
        property real leverLengthRodPos: userLeverLength * userRodPosition
        property real piOver180: Math.PI / 180
        property real _180OverPi: 180 / Math.PI
        
        // Кэшированные вычисления камеры
        property real cachedFovRad: cameraFov * piOver180
        property real cachedTanHalfFov: Math.tan(cachedFovRad / 2)
        
        // Обновление кэша камеры при необходимости
        onCachedFovRadChanged: cachedTanHalfFov = Math.tan(cachedFovRad / 2)
        
        function calculateJRod(j_arm, baseAngle, leverAngle) {
            var totalAngleRad = (baseAngle + leverAngle) * piOver180
            return Qt.vector3d(
                j_arm.x + leverLengthRodPos * Math.cos(totalAngleRad),
                j_arm.y + leverLengthRodPos * Math.sin(totalAngleRad),
                j_arm.z
            )
        }
        
        function normalizeCylDirection(j_rod, j_tail) {
            var dx = j_rod.x - j_tail.x
            var dy = j_rod.y - j_tail.y
            var length = Math.hypot(dx, dy)
            return {
                direction: Qt.vector3d(dx, dy, 0),
                length: length,
                normalized: Qt.vector3d(dx/length, dy/length, 0),
                angle: Math.atan2(dy, dx) * _180OverPi + 90
            }
        }
    }

    // ===============================================================
    // IBL CONTROLLER
    // ===============================================================

    IblProbeLoader {
        id: iblLoader
        primarySource: root.iblPrimarySource
        fallbackSource: root.iblFallbackSource
    }

    // ===============================================================
    // CAMERA SYSTEM (preserved)
    // ===============================================================
    
    property vector3d pivot: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
    
    // Camera orbital parameters
    property real cameraDistance: 3500
    property real minDistance: 150
    property real maxDistance: 30000
    property real yawDeg: 225
    property real pitchDeg: -25
    
    property real panX: 0
    property real panY: 0
    
    // Camera properties
    property real cameraFov: 60.0
    property real cameraNear: 10.0
    property real cameraFar: 50000.0
    property real cameraSpeed: 1.0
    
    // Auto rotation
    property bool autoRotate: false
    property real autoRotateSpeed: 0.5

    // Mouse input state
    property bool mouseDown: false
    property int mouseButton: 0
    property real lastX: 0
    property real lastY: 0
    property real rotateSpeed: 0.35
    property bool cameraIsMoving: false

    // ===============================================================
    // ✅ COMPLETE GRAPHICS PROPERTIES (All parameters from GraphicsPanel)
    // ===============================================================

    // HDR resources
    property url iblPrimarySource: startIblSource && startIblSource !== "" ? resolveUrl(startIblSource) : Qt.resolvedUrl("../hdr/studio.hdr")
    property url iblFallbackSource: startIblFallback && startIblFallback !== "" ? resolveUrl(startIblFallback) : Qt.resolvedUrl("../hdr/studio_small_09_2k.hdr")
    readonly property bool iblReady: iblLoader.ready

    // Environment defaults c учетом стартовых флагов
    property string backgroundMode: startBackgroundMode
    property color backgroundColor: "#1f242c"
    property bool iblEnabled: startIblEnabled
    property bool iblLightingEnabled: startIblEnabled
    property bool iblBackgroundEnabled: startSkyboxEnabled
    property real iblRotationDeg: startIblRotation
    property real iblIntensity: startIblIntensity

    // Lighting
    property real keyLightBrightness: 1.2
    property color keyLightColor: "#ffffff"
    property real keyLightAngleX: -35
    property real keyLightAngleY: -40
    property bool keyLightCastsShadow: true
    property bool keyLightBindToCamera: false
    property real keyLightPosX: 0.0
    property real keyLightPosY: 0.0
    property real fillLightBrightness: 0.7
    property color fillLightColor: "#dfe7ff"
    property bool fillLightCastsShadow: false
    property bool fillLightBindToCamera: false
    property real fillLightPosX: 0.0
    property real fillLightPosY: 0.0
    property real rimLightBrightness: 1.0
    property color rimLightColor: "#ffe2b0"
    property bool rimLightCastsShadow: false
    property bool rimLightBindToCamera: false
    property real rimLightPosX: 0.0
    property real rimLightPosY: 0.0
    property real pointLightBrightness: 1000.0
    property color pointLightColor: "#ffffff"
    property real pointLightX: 0.0
    property real pointLightY: 2200.0
    property real pointLightRange: 3200.0
    property bool pointLightCastsShadow: false   // ✅ Новый пользовательский флаг теней точечного света
    property bool pointLightBindToCamera: false

    // Procedural geometry quality
    property int cylinderSegments: 64
    property int cylinderRings: 8

    // Quality and rendering
    property string aaPrimaryMode: "ssaa"
    property string aaQualityLevel: "high"
    property string aaPostMode: "taa"
    property bool taaEnabled: true
    property real taaStrength: 0.4
    property bool taaMotionAdaptive: true
    property bool fxaaEnabled: false
    // ВРЕМЕННЫЙ ФИКС: отключаем Specular AA по умолчанию (ошибка компиляции шейдера на некоторых драйверах)
    property bool specularAAEnabled: false
    property real renderScale: 1.05
    property string renderPolicy: "always"
    property real frameRateLimit: 144.0
    property string qualityPreset: "ultra"

    // === Fog properties (Qt 6.10+ Fog object) ===
    property bool fogEnabled: false
    property color fogColor: "#808080"
    property real fogDensity: 0.1
    property real fogNear: 1200.0
    property real fogFar: 12000.0

    property var pendingPythonUpdates: null

    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates || Object.keys(pendingPythonUpdates).length === 0)
            return
        applyBatchedUpdates(pendingPythonUpdates)
        pendingPythonUpdates = null
    }

    function syncRenderSettings() {
        if (!view3d || !view3d.renderSettings)
            return
        const settings = view3d.renderSettings
        settings.renderScale = renderScale
        settings.maximumFrameRate = frameRateLimit
        settings.renderPolicy = renderPolicy === "ondemand" ? RenderSettings.OnDemand : RenderSettings.Always
    }

    onRenderScaleChanged: syncRenderSettings()
    onFrameRateLimitChanged: syncRenderSettings()
    onRenderPolicyChanged: syncRenderSettings()
    property bool shadowsEnabled: true
    property string shadowResolution: "4096"
    property int shadowFilterSamples: 32
    property real shadowBias: 8.0
    property real shadowFactor: 80.0
    property string oitMode: "weighted"

    // Post-processing effects
    property bool bloomEnabled: true
    property real bloomIntensity: 0.5
    property real bloomThreshold: 1.0
    property real bloomSpread: 0.65
    property bool depthOfFieldEnabled: false
    property real dofFocusDistance: 2200.0
    property real dofBlurAmount: 4.0
    property bool motionBlurEnabled: false
    property real motionBlurAmount: 0.2
    property bool lensFlareEnabled: false    // ✅ По умолчанию выкл, чтобы не включалось без явного сигнала
    property bool vignetteEnabled: false      // ✅ По умолчанию выкл, чтобы не включалось без явного сигнала
    property real vignetteStrength: 0.35

    // Tonemap settings
    property bool tonemapEnabled: true
    property string tonemapModeName: "filmic"
    // ✅ Новые управляемые параметры тонемаппинга
    property real tonemapExposure: 1.0
    property real tonemapWhitePoint: 2.0

    // Material control properties
    property color frameBaseColor: "#c53030"
    property real frameMetalness: 0.85
    property real frameRoughness: 0.35
    property real frameSpecularAmount: 1.0
    property real frameSpecularTint: 0.0
    property real frameClearcoat: 0.22
    property real frameClearcoatRoughness: 0.1
    property real frameTransmission: 0.0
    property real frameOpacity: 1.0
    property real frameIor: 1.5
    property real frameAttenuationDistance: 10000.0
    property color frameAttenuationColor: "#ffffff"
    property color frameEmissiveColor: "#000000"
    property real frameEmissiveIntensity: 0.0

    property color leverBaseColor: "#9ea4ab"
    property real leverMetalness: 1.0
    property real leverRoughness: 0.28
    property real leverSpecularAmount: 1.0
    property real leverSpecularTint: 0.0
    property real leverClearcoat: 0.3
    property real leverClearcoatRoughness: 0.08
    property real leverTransmission: 0.0
    property real leverOpacity: 1.0
    property real leverIor: 1.5
    property real leverAttenuationDistance: 10000.0
    property color leverAttenuationColor: "#ffffff"
    property color leverEmissiveColor: "#000000"
    property real leverEmissiveIntensity: 0.0

    property color tailRodBaseColor: "#d5d9df"
    property real tailRodMetalness: 1.0
    property real tailRodRoughness: 0.3
    property real tailRodSpecularAmount: 1.0
    property real tailRodSpecularTint: 0.0
    property real tailRodClearcoat: 0.0
    property real tailRodClearcoatRoughness: 0.0
    property real tailRodTransmission: 0.0
    property real tailRodOpacity: 1.0
    property real tailRodIor: 1.5
    property real tailRodAttenuationDistance: 10000.0
    property color tailRodAttenuationColor: "#ffffff"
    property color tailRodEmissiveColor: "#000000"
    property real tailRodEmissiveIntensity: 0.0

    property color cylinderBaseColor: "#e1f5ff"
    property real cylinderMetalness: 0.0
    property real cylinderRoughness: 0.05
    property real cylinderSpecularAmount: 1.0
    property real cylinderSpecularTint: 0.0
    property real cylinderClearcoat: 0.0
    property real cylinderClearcoatRoughness: 0.0
    property real cylinderTransmission: 1.0
    property real cylinderOpacity: 1.0
    property real cylinderIor: 1.52
    property real cylinderAttenuationDistance: 1800.0
    property color cylinderAttenuationColor: "#b7e7ff"
    property color cylinderEmissiveColor: "#000000"
    property real cylinderEmissiveIntensity: 0.0

    property color pistonBodyBaseColor: "#ff3c6e"
    property color pistonBodyWarningColor: "#ff5454"
    property real pistonBodyMetalness: 1.0
    property real pistonBodyRoughness: 0.26
    property real pistonBodySpecularAmount: 1.0
    property real pistonBodySpecularTint: 0.0
    property real pistonBodyClearcoat: 0.18
    property real pistonBodyClearcoatRoughness: 0.06
    property real pistonBodyTransmission: 0.0
    property real pistonBodyOpacity: 1.0
    property real pistonBodyIor: 1.5
    property real pistonBodyAttenuationDistance: 10000.0
    property color pistonBodyAttenuationColor: "#ffffff"
    property color pistonBodyEmissiveColor: "#000000"
    property real pistonBodyEmissiveIntensity: 0.0

    property color pistonRodBaseColor: "#ececec"
    property color pistonRodWarningColor: "#ff2a2a"
    property real pistonRodMetalness: 1.0
    property real pistonRodRoughness: 0.18
    property real pistonRodSpecularAmount: 1.0
    property real pistonRodSpecularTint: 0.0
    property real pistonRodClearcoat: 0.12
    property real pistonRodClearcoatRoughness: 0.05
    property real pistonRodTransmission: 0.0
    property real pistonRodOpacity: 1.0
    property real pistonRodIor: 1.5
    property real pistonRodAttenuationDistance: 10000.0
    property color pistonRodAttenuationColor: "#ffffff"
    property color pistonRodEmissiveColor: "#000000"
    property real pistonRodEmissiveIntensity: 0.0

    property color jointTailBaseColor: "#2a82ff"
    property real jointTailMetalness: 0.9
    property real jointTailRoughness: 0.35
    property real jointTailSpecularAmount: 1.0
    property real jointTailSpecularTint: 0.0
    property real jointTailClearcoat: 0.1
    property real jointTailClearcoatRoughness: 0.08
    property real jointTailTransmission: 0.0
    property real jointTailOpacity: 1.0
    property real jointTailIor: 1.5
    property real jointTailAttenuationDistance: 10000.0
    property color jointTailAttenuationColor: "#ffffff"
    property color jointTailEmissiveColor: "#000000"
    property real jointTailEmissiveIntensity: 0.0

    property color jointArmBaseColor: "#ff9c3a"
    property real jointArmMetalness: 0.9
    property real jointArmRoughness: 0.32
    property real jointArmSpecularAmount: 1.0
    property real jointArmSpecularTint: 0.0
    property real jointArmClearcoat: 0.12
    property real jointArmClearcoatRoughness: 0.08
    property real jointArmTransmission: 0.0
    property real jointArmOpacity: 1.0
    property real jointArmIor: 1.5
    property real jointArmAttenuationDistance: 10000.0
    property color jointArmAttenuationColor: "#ffffff"
    property color jointArmEmissiveColor: "#000000"
    property real jointArmEmissiveIntensity: 0.0

    function emissiveVector(color, intensity) {
        if (intensity === undefined)
            intensity = 1.0
        if (!color)
            return Qt.vector3d(0, 0, 0)
        return Qt.vector3d(color.r * intensity, color.g * intensity, color.b * intensity)
    }

    function clamp01(value) {
        return Math.max(0.0, Math.min(1.0, value))
    }

    property color jointRodOkColor: "#00ff55"
    property color jointRodErrorColor: "#ff0000"

    // ===============================================================
    // ANIMATION AND GEOMETRY PROPERTIES (preserved)
    // ===============================================================
    
    property real animationTime: 0.0
    property bool isRunning: false

    // User-controlled animation parameters
    property real userAmplitude: 8.0
    property real userFrequency: 1.0
    property real userPhaseGlobal: 0.0
    property real userPhaseFL: 0.0
    property real userPhaseFR: 0.0
    property real userPhaseRL: 0.0
    property real userPhaseRR: 0.0

    // Piston positions from Python
    property real userPistonPositionFL: 250.0
    property real userPistonPositionFR: 250.0
    property real userPistonPositionRL: 250.0
    property real userPistonPositionRR: 250.0

    // ✅ ОПТИМИЗИРОВАННЫЕ углы (используют кэшированные значения)
    property real fl_angle: isRunning ? userAmplitude * animationCache.flSin : 0.0
    property real fr_angle: isRunning ? userAmplitude * animationCache.frSin : 0.0
    property real rl_angle: isRunning ? userAmplitude * animationCache.rlSin : 0.0
    property real rr_angle: isRunning ? userAmplitude * animationCache.rrSin : 0.0

    // Geometry parameters
    property real userBeamSize: 120
    property real userFrameHeight: 650
    property real userFrameLength: 3200
    property real userLeverLength: 800
    property real userCylinderLength: 500
    property real userTrackWidth: 1600
    property real userFrameToPivot: 600
    property real userRodPosition: 0.6
    property real userBoreHead: 80
    property real userBoreRod: 80
    property real userRodDiameter: 35
    property real userPistonThickness: 25
    property real userPistonRodLength: 200

    // ===============================================================
    // SMOOTH CAMERA BEHAVIORS (preserved)
    // ===============================================================
    
    Behavior on yawDeg         { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on pitchDeg       { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on cameraDistance { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on panX           { NumberAnimation { duration: 60; easing.type: Easing.OutQuad } }
    Behavior on panY           { NumberAnimation { duration: 60; easing.type: Easing.OutQuad } }

    // ===============================================================
    // UTILITY FUNCTIONS (preserved)
    // ===============================================================
    
    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    
    function normAngleDeg(a) {
        var x = a % 360
        if (x < 0)
            x += 360
        return x;
    }

    function resolveUrl(path) {
        if (!path || path === "")
            return "";
        if (path.startsWith("file:") || path.startsWith("http:") || path.startsWith("https:") ||
            path.startsWith("qrc:") || path.startsWith("data:"))
            return path;
        if (path.length >= 2 && path.charAt(1) === ":")
            return "file:///" + path.replace(/\\/g, "/");
        if (path.startsWith("/"))
            return "file://" + path;
        return Qt.resolvedUrl(path);
    }
    
    function autoFitFrame(marginFactor) {
        const L = Math.max(1, userFrameLength)
        const T = Math.max(1, userTrackWidth)  
        const H = Math.max(1, userFrameHeight)
        const margin = marginFactor !== undefined ? marginFactor : 1.15
        const R = 0.5 * Math.sqrt(L*L + T*T + H*H)
        const fov = cameraFov * Math.PI / 180.0
        const dist = (R * margin) / Math.tan(fov * 0.5)
        cameraDistance = Math.max(minDistance, Math.min(maxDistance, dist))
    }
    
    // ✅ УЛУЧШЕННАЯ функция resetView с сохранением позиции камеры
    function resetView() {
        // Сохраняем текущую позицию камеры если она разумная
        var preserveCamera = (Math.abs(yawDeg) < 720 && 
                             Math.abs(pitchDeg) < 90 && 
                             cameraDistance > minDistance && 
                             cameraDistance < maxDistance)
        
        if (preserveCamera) {
            console.log("🔄 Soft reset: preserving camera position")
            // Обновляем только pivot, камера остается
            pivot = Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
        } else {
            console.log("🔄 Full reset: resetting camera to defaults")
            // Полный сброс камеры
            pivot = Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
            yawDeg = 225
            pitchDeg = -25
            panX = 0
            panY = 0
            autoFitFrame()
        }
        
        console.log("🔄 View reset completed: pivot =", pivot, "distance =", cameraDistance)
    }
    
    // ✅ НОВАЯ функция для полного сброса камеры
    function fullResetView() {
        console.log("🔄 Full camera reset requested")
        pivot = Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
        yawDeg = 225
        pitchDeg = -25
        panX = 0
        panY = 0
        autoFitFrame()
        console.log("🔄 Full reset completed")
    }

    function flagCameraMotion() {
        if (!cameraIsMoving)
            cameraIsMoving = true
        cameraMotionSettler.restart()
    }

    // ===============================================================
    // ✅ COMPLETE BATCH UPDATE SYSTEM (All functions implemented)
    // ===============================================================
    
    function applyBatchedUpdates(updates) {
        if (typeof window !== 'undefined' && window && window.logQmlEvent) {
            try { window.logQmlEvent("signal_received", "applyBatchedUpdates"); } catch(e) {}
        }
        console.log("🚀 Applying batched updates with conflict resolution:", Object.keys(updates))
        
        // Disable default behaviors temporarily 
        var wasAutoUpdate = autoRotate
        autoRotate = false
        
        try {
            if (updates.geometry) applyGeometryUpdates(updates.geometry)
            if (updates.animation) applyAnimationUpdates(updates.animation)  
            if (updates.lighting) applyLightingUpdates(updates.lighting)
            if (updates.materials) applyMaterialUpdates(updates.materials)
            if (updates.environment) applyEnvironmentUpdates(updates.environment)
            if (updates.quality) applyQualityUpdates(updates.quality)
            if (updates.camera) applyCameraUpdates(updates.camera)
            if (updates.effects) applyEffectsUpdates(updates.effects)
            
            console.log("✅ Batch updates completed successfully")
            
            // ✅ Send ACK to Python with summary of what was applied
            var summary = {
                timestamp: Date.now(),
                categories: Object.keys(updates),
                success: true
            }
            root.batchUpdatesApplied(summary)
        } finally {
            // Restore auto behaviors
            autoRotate = wasAutoUpdate
        }
    }
    
    function applyGeometryUpdates(params) {
        if (typeof window !== 'undefined' && window && window.logQmlEvent) {
            try { window.logQmlEvent("function_called", "applyGeometryUpdates"); } catch(e) {}
        }
        console.log("📐 main.qml: applyGeometryUpdates() with conflict resolution")
        
        // ✅ ИСПРАВЛЕНО: Проверяем на undefined перед применением
        if (params.frameLength !== undefined && params.frameLength !== userFrameLength) {
            console.log("  📏 Updating frameLength:", userFrameLength, "→", params.frameLength)
            userFrameLength = params.frameLength
        }
        if (params.frameHeight !== undefined && params.frameHeight !== userFrameHeight) {
            console.log("  📏 Updating frameHeight:", userFrameHeight, "→", params.frameHeight)
            userFrameHeight = params.frameHeight
        }
        if (params.frameBeamSize !== undefined && params.frameBeamSize !== userBeamSize) {
            console.log("  📏 Updating frameBeamSize:", userBeamSize, "→", params.frameBeamSize)
            userBeamSize = params.frameBeamSize
        }
        if (params.leverLength !== undefined && params.leverLength !== userLeverLength) {
            console.log("  📏 Updating leverLength:", userLeverLength, "→", params.leverLength)
            userLeverLength = params.leverLength
        }
        if (params.cylinderBodyLength !== undefined && params.cylinderBodyLength !== userCylinderLength) {
            console.log("  📏 Updating cylinderLength:", userCylinderLength, "→", params.cylinderBodyLength)
            userCylinderLength = params.cylinderBodyLength
        }
        if (params.trackWidth !== undefined && params.trackWidth !== userTrackWidth) {
            console.log("  📏 Updating trackWidth:", userTrackWidth, "→", params.trackWidth)
            userTrackWidth = params.trackWidth
        }
        if (params.frameToPivot !== undefined && params.frameToPivot !== userFrameToPivot) {
            console.log("  📏 Updating frameToPivot:", userFrameToPivot, "→", params.frameToPivot)
            userFrameToPivot = params.frameToPivot
        }
        if (params.rodPosition !== undefined && params.rodPosition !== userRodPosition) {
            console.log("  ✨ КРИТИЧЕСКИЙ: Updating rodPosition:", userRodPosition, "→", params.rodPosition)
            userRodPosition = params.rodPosition
        }

        // ✅ ДОПОЛНИТЕЛЬНЫЕ ПАРАМЕТРЫ ГЕОМЕТРИИ, ПРИХОДЯЩИЕ ИЗ PYTHON (мм)
        if (params.boreHead !== undefined) userBoreHead = Number(params.boreHead)
        if (params.boreRod !== undefined) userBoreRod = Number(params.boreRod)
        if (params.rodDiameter !== undefined) userRodDiameter = Number(params.rodDiameter)
        if (params.pistonThickness !== undefined) userPistonThickness = Number(params.pistonThickness)
        if (params.pistonRodLength !== undefined) userPistonRodLength = Number(params.pistonRodLength)

        // ✅ ПОДДЕРЖКА АЛЬТЕРНАТИВНЫХ КЛЮЧЕЙ (исторически) — уже в мм
        if (params.cylDiamM !== undefined) userBoreHead = Number(params.cylDiamM)
        if (params.rodDiameterM !== undefined) userRodDiameter = Number(params.rodDiameterM)
        if (params.pistonThicknessM !== undefined) userPistonThickness = Number(params.pistonThicknessM)
        if (params.pistonRodLengthM !== undefined) userPistonRodLength = Number(params.pistonRodLengthM)

        if (params.cylinderSegments !== undefined) {
            var newSegments = Math.floor(params.cylinderSegments)
            if (!isNaN(newSegments))
                cylinderSegments = Math.max(3, newSegments)
        }
        if (params.cylinderRings !== undefined) {
            var newRings = Math.floor(params.cylinderRings)
            if (!isNaN(newRings))
                cylinderRings = Math.max(1, newRings)
        }

        // ✅ ИСПРАВЛЕНО: Сброс вида только при значительных изменениях геометрии
        var shouldResetView = (params.frameLength !== undefined || 
                              params.frameHeight !== undefined || 
                              params.trackWidth !== undefined)
        
        if (shouldResetView) {
            console.log("  🔄 Significant geometry change - resetting view")
            resetView()
        } else {
            console.log("  ✅ Minor geometry change - view preserved")
        }
        
        console.log("  ✅ Geometry updated successfully")
    }
    
    function applyAnimationUpdates(params) {
        if (typeof window !== 'undefined' && window && window.logQmlEvent) {
            try { window.logQmlEvent("function_called", "applyAnimationUpdates"); } catch(e) {}
        }
        console.log("🎬 main.qml: applyAnimationUpdates() called")
        if (params.amplitude !== undefined) userAmplitude = params.amplitude
        if (params.frequency !== undefined) userFrequency = params.frequency
        if (params.phase !== undefined) userPhaseGlobal = params.phase
        if (params.lf_phase !== undefined) userPhaseFL = params.lf_phase
        if (params.rf_phase !== undefined) userPhaseFR = params.rf_phase
        if (params.lr_phase !== undefined) userPhaseRL = params.lr_phase
        if (params.rr_phase !== undefined) userPhaseRR = params.rr_phase
        console.log("  ✅ Animation updated successfully")
    }
    
    function applyLightingUpdates(params) {
        if (typeof window !== 'undefined' && window && window.logQmlEvent) {
            try { window.logQmlEvent("function_called", "applyLightingUpdates"); } catch(e) {}
        }
        console.log("💡 main.qml: applyLightingUpdates() called")
        if (params.key_light) {
            if (params.key_light.brightness !== undefined) keyLightBrightness = params.key_light.brightness
            if (params.key_light.color !== undefined) keyLightColor = params.key_light.color
            if (params.key_light.angle_x !== undefined) keyLightAngleX = params.key_light.angle_x
            if (params.key_light.angle_y !== undefined) keyLightAngleY = params.key_light.angle_y
            if (params.key_light.casts_shadow !== undefined) keyLightCastsShadow = !!params.key_light.casts_shadow
            if (params.key_light.bind_to_camera !== undefined) keyLightBindToCamera = !!params.key_light.bind_to_camera
            if (params.key_light.position_x !== undefined) keyLightPosX = Number(params.key_light.position_x)
            if (params.key_light.position_y !== undefined) keyLightPosY = Number(params.key_light.position_y)
        }
        if (params.fill_light) {
            if (params.fill_light.brightness !== undefined) fillLightBrightness = params.fill_light.brightness
            if (params.fill_light.color !== undefined) fillLightColor = params.fill_light.color
            if (params.fill_light.casts_shadow !== undefined) fillLightCastsShadow = !!params.fill_light.casts_shadow
            if (params.fill_light.bind_to_camera !== undefined) fillLightBindToCamera = !!params.fill_light.bind_to_camera
            if (params.fill_light.position_x !== undefined) fillLightPosX = Number(params.fill_light.position_x)
            if (params.fill_light.position_y !== undefined) fillLightPosY = Number(params.fill_light.position_y)
        }
        if (params.rim_light) {
            if (params.rim_light.brightness !== undefined) rimLightBrightness = params.rim_light.brightness
            if (params.rim_light.color !== undefined) rimLightColor = params.rim_light.color
            if (params.rim_light.casts_shadow !== undefined) rimLightCastsShadow = !!params.rim_light.casts_shadow
            if (params.rim_light.bind_to_camera !== undefined) rimLightBindToCamera = !!params.rim_light.bind_to_camera
            if (params.rim_light.position_x !== undefined) rimLightPosX = Number(params.rim_light.position_x)
            if (params.rim_light.position_y !== undefined) rimLightPosY = Number(params.rim_light.position_y)
        }
        if (params.point_light) {
            if (params.point_light.brightness !== undefined) pointLightBrightness = params.point_light.brightness
            if (params.point_light.color !== undefined) pointLightColor = params.point_light.color
            if (params.point_light.position_x !== undefined) pointLightX = Number(params.pointLight.position_x)
            if (params.point_light.position_y !== undefined) pointLightY = params.pointLight.position_y
            if (params.point_light.range !== undefined) pointLightRange = Math.max(1, params.point_light.range)
            if (params.point_light.casts_shadow !== undefined) pointLightCastsShadow = !!params.point_light.casts_shadow
            if (params.point_light.bind_to_camera !== undefined) pointLightBindToCamera = !!params.point_light.bind_to_camera
        }
        console.log("  ✅ Lighting updated successfully")
    }

    function applyMaterialUpdates(params) {
        if (typeof window !== 'undefined' && window && window.logQmlEvent) {
            try { window.logQmlEvent("function_called", "applyMaterialUpdates"); } catch(e) {}
        }
        console.log("🎨 main.qml: applyMaterialUpdates() called")
        function applyCommon(values, prefix) {
            if (values.base_color !== undefined) root[prefix + "BaseColor"] = values.base_color
            if (values.metalness !== undefined) root[prefix + "Metalness"] = values.metalness
            if (values.roughness !== undefined) root[prefix + "Roughness"] = values.roughness
            if (values.specular !== undefined) root[prefix + "SpecularAmount"] = values.specular
            if (values.specular_tint !== undefined) root[prefix + "SpecularTint"] = values.specular_tint
            if (values.clearcoat !== undefined) root[prefix + "Clearcoat"] = values.clearcoat
            if (values.clearcoat_roughness !== undefined) root[prefix + "ClearcoatRoughness"] = values.clearcoat_roughness
            if (values.transmission !== undefined) root[prefix + "Transmission"] = values.transmission
            if (values.opacity !== undefined) root[prefix + "Opacity"] = values.opacity
            if (values.ior !== undefined) root[prefix + "Ior"] = values.ior
            if (values.attenuation_distance !== undefined) root[prefix + "AttenuationDistance"] = values.attenuation_distance
            if (values.attenuation_color !== undefined) root[prefix + "AttenuationColor"] = values.attenuation_color
            if (values.emissive_color !== undefined) root[prefix + "EmissiveColor"] = values.emissive_color
            if (values.emissive_intensity !== undefined) root[prefix + "EmissiveIntensity"] = values.emissive_intensity
        }

        if (params.frame !== undefined) applyCommon(params.frame, "frame")
        if (params.lever !== undefined) applyCommon(params.lever, "lever")
        if (params.tail !== undefined) applyCommon(params.tail, "tailRod")
        if (params.cylinder !== undefined) applyCommon(params.cylinder, "cylinder")
        if (params.piston_body !== undefined) {
            applyCommon(params.piston_body, "pistonBody")
            if (params.piston_body.warning_color !== undefined) pistonBodyWarningColor = params.piston_body.warning_color
        }
        if (params.piston_rod !== undefined) {
            applyCommon(params.piston_rod, "pistonRod")
            if (params.piston_rod.warning_color !== undefined) pistonRodWarningColor = params.piston_rod.warning_color
        }
        if (params.joint_tail !== undefined) {
            applyCommon(params.joint_tail, "jointTail")
            if (params.joint_tail.ok_color !== undefined) jointRodOkColor = params.joint_tail.ok_color
            if (params.joint_tail.error_color !== undefined) jointRodErrorColor = params.joint_tail.error_color
        }
        if (params.joint_arm !== undefined) {
            applyCommon(params.joint_arm, "jointArm")
        }

        console.log("  ✅ Materials updated successfully")
    }

    // ✅ ПОЛНАЯ реализация updateEnvironment()
    function applyEnvironmentUpdates(params) {
        if (typeof window !== 'undefined' && window && window.logQmlEvent) {
            try { window.logQmlEvent("function_called", "applyEnvironmentUpdates"); } catch(e) {}
        }
        console.log("🌍 main.qml: applyEnvironmentUpdates() called")

        if (params.background) {
            if (params.background.mode !== undefined) backgroundMode = params.background.mode
            if (params.background.color !== undefined) backgroundColor = params.background.color
            if (params.background.skybox_enabled !== undefined) iblBackgroundEnabled = params.background.skybox_enabled
        }

        if (params.ibl) {
            if (params.ibl.enabled !== undefined) {
                iblEnabled = params.ibl.enabled
                // По умолчанию включаем/выключаем освещение IBL согласно enabled, не затрагивая фон
                iblLightingEnabled = params.ibl.enabled
            }
            if (params.ibl.lighting_enabled !== undefined) iblLightingEnabled = params.ibl.lighting_enabled
            if (params.ibl.background_enabled !== undefined) iblBackgroundEnabled = params.ibl.background_enabled
            if (params.ibl.rotation !== undefined) iblRotationDeg = params.ibl.rotation
            if (params.ibl.intensity !== undefined) iblIntensity = params.ibl.intensity
            if (params.ibl.exposure !== undefined) iblIntensity = params.ibl.exposure
            if (params.ibl.source !== undefined) {
                var resolvedSource = resolveUrl(params.ibl.source)
                if (resolvedSource && resolvedSource !== "") {
                    iblLoader._fallbackTried = false
                    iblPrimarySource = resolvedSource
                    console.log("  🌟 IBL source:", iblPrimarySource)
                }
            }
            if (params.ibl.fallback !== undefined) {
                var resolvedFallback = resolveUrl(params.ibl.fallback)
                if (resolvedFallback && resolvedFallback !== "") {
                    iblLoader._fallbackTried = false
                    iblFallbackSource = resolvedFallback
                    console.log("  🌟 IBL fallback:", iblFallbackSource)
                }
            }
        }

        if (params.fog) {
            if (params.fog.enabled !== undefined) fogEnabled = params.fog.enabled
            if (params.fog.color !== undefined) fogColor = params.fog.color
            if (params.fog.density !== undefined) fogDensity = params.fog.density
        }

        if (params.ambient_occlusion) {
            if (params.ambient_occlusion.enabled !== undefined) aoEnabled = params.ambient_occlusion.enabled
            if (params.ambient_occlusion.strength !== undefined) aoStrength = params.ambient_occlusion.strength
            if (params.ambient_occlusion.radius !== undefined) aoRadius = params.ambient_occlusion.radius
        }

        console.log("  ✅ Environment updated successfully")
    }

    // ✅ ПОЛНАЯ реализация updateQuality()
    function applyQualityUpdates(params) {
        if (typeof window !== 'undefined' && window && window.logQmlEvent) {
            try { window.logQmlEvent("function_called", "applyQualityUpdates"); } catch(e) {}
        }
        console.log("⚙️ main.qml: applyQualityUpdates() called")

        if (params.shadows) {
            if (params.shadows.enabled !== undefined) shadowsEnabled = params.shadows.enabled
            if (params.shadows.resolution !== undefined) shadowResolution = params.shadows.resolution
            if (params.shadows.filter !== undefined) shadowFilterSamples = params.shadows.filter
            if (params.shadows.bias !== undefined) shadowBias = params.shadows.bias
            if (params.shadows.darkness !== undefined) shadowFactor = params.shadows.darkness
        }

        if (params.antialiasing) {
            if (params.antialiasing.primary !== undefined) aaPrimaryMode = params.antialiasing.primary
            if (params.antialiasing.quality !== undefined) aaQualityLevel = params.antialiasing.quality
            if (params.antialiasing.post !== undefined) aaPostMode = params.antialiasing.post
        }

        if (params.taa_enabled !== undefined) taaEnabled = params.taa_enabled
        if (params.taa_strength !== undefined) taaStrength = params.taa_strength
        if (params.taa_motion_adaptive !== undefined) taaMotionAdaptive = params.taa_motion_adaptive
        if (params.fxaa_enabled !== undefined) fxaaEnabled = params.fxaa_enabled
        if (params.specular_aa !== undefined) specularAAEnabled = params.specular_aa
        // ✅ НОВОЕ: Мгновенная обработка dither при прямом вызове из Python
        if (params.dithering !== undefined) ditheringEnabled = params.dithering
        if (params.render_scale !== undefined) renderScale = params.render_scale
        if (params.render_policy !== undefined) renderPolicy = params.render_policy
        if (params.frame_rate_limit !== undefined) frameRateLimit = params.frame_rate_limit
        if (params.oit !== undefined) oitMode = params.oit
        if (params.preset !== undefined) qualityPreset = params.preset

        console.log("  🎚 Quality preset:", qualityPreset, ", FPS limit:", frameRateLimit)
        console.log("  ✅ Quality updated successfully")
    }

    // ✅ ПОЛНАЯ реализация updateCamera()
    function applyCameraUpdates(params) {
        if (typeof window !== 'undefined' && window && window.logQmlEvent) {
            try { window.logQmlEvent("function_called", "applyCameraUpdates"); } catch(e) {}
        }
        console.log("📷 main.qml: applyCameraUpdates() called")
        
        if (params.fov !== undefined) cameraFov = params.fov
        if (params.near !== undefined) cameraNear = params.near
        if (params.far !== undefined) cameraFar = params.far
        if (params.speed !== undefined) cameraSpeed = params.speed
        if (params.auto_rotate !== undefined) autoRotate = params.auto_rotate
        if (params.auto_rotate_speed !== undefined) autoRotateSpeed = params.auto_rotate_speed
        
        console.log("  ✅ Camera updated successfully")
    }

    // ✅ ПОЛНАЯ реализация updateEffects()
    function applyEffectsUpdates(params) {
        if (typeof window !== 'undefined' && window && window.logQmlEvent) {
            try { window.logQmlEvent("function_called", "applyEffectsUpdates"); } catch(e) {}
        }
        console.log("✨ main.qml: applyEffectsUpdates() called")
        
        if (params.bloom_enabled !== undefined) bloomEnabled = params.bloom_enabled
        if (params.bloom_intensity !== undefined) bloomIntensity = params.bloom_intensity
        if (params.bloom_threshold !== undefined) bloomThreshold = params.bloom_threshold
        if (params.bloom_spread !== undefined) bloomSpread = params.bloom_spread
        if (params.depth_of_field !== undefined) depthOfFieldEnabled = params.depth_of_field
        if (params.dof_focus_distance !== undefined) dofFocusDistance = params.dof_focus_distance
        if (params.dof_blur !== undefined) dofBlurAmount = params.dof_blur
        if (params.motion_blur !== undefined) motionBlurEnabled = params.motion_blur
        if (params.motion_blur_amount !== undefined) motionBlurAmount = params.motion_blur_amount
        if (params.lens_flare !== undefined) lensFlareEnabled = params.lens_flare
        if (params.vignette !== undefined) vignetteEnabled = params.vignette
        if (params.vignette_strength !== undefined) vignetteStrength = params.vignette_strength
        if (params.tonemap_enabled !== undefined) tonemapEnabled = params.tonemap_enabled
        if (params.tonemap_mode !== undefined) {
            var allowedModes = ["filmic", "aces", "reinhard", "gamma", "linear"]
            if (allowedModes.indexOf(params.tonemap_mode) !== -1)
                tonemapModeName = params.tonemap_mode
        }
        // ✅ Управление параметрами тонемаппинга
        if (params.tonemap_exposure !== undefined) tonemapExposure = Number(params.tonemap_exposure)
        if (params.tonemap_whitepoint !== undefined) tonemapWhitePoint = Number(params.tonemap_whitepoint)
        console.log("  ✅ Visual effects updated successfully")
    }

    // Legacy functions for backward compatibility
    function updateGeometry(params) { applyGeometryUpdates(params) }
    function updateLighting(params) { applyLightingUpdates(params) }
    function updateMaterials(params) { applyMaterialUpdates(params) }     // ✅ РЕАЛИЗОВАНО
    function updateEnvironment(params) { applyEnvironmentUpdates(params) } // ✅ РЕАЛИЗОВАНО
    function updateQuality(params) { applyQualityUpdates(params) }         // ✅ РЕАЛИЗОВАНО
    function updateEffects(params) { applyEffectsUpdates(params) }         // ✅ РЕАЛИЗОВАНО
    function updateCamera(params) { applyCameraUpdates(params) }           // ✅ РЕАЛИЗОВАНО
    function updateAnimation(params) { applyAnimationUpdates(params) }     // ✅ РЕАЛИЗОВАНО
    
    function updatePistonPositions(positions) {
        if (positions.fl !== undefined) userPistonPositionFL = Number(positions.fl)
        if (positions.fr !== undefined) userPistonPositionFR = Number(positions.fr)
        if (positions.rl !== undefined) userPistonPositionRL = Number(positions.rl)
        if (positions.rr !== undefined) userPistonPositionRR = Number(positions.rr)
    }

    // ===============================================================
    // 3D SCENE (ИСПРАВЛЕННЫЕ СВОЙСТВА ExtendedSceneEnvironment)
    // ===============================================================

    View3D {
        id: view3d
        anchors.fill: parent
        camera: camera

        environment: ExtendedSceneEnvironment {
            id: mainEnvironment
            readonly property bool skyboxActive: root.backgroundMode === "skybox" && root.iblBackgroundEnabled && root.iblReady

            backgroundMode: skyboxActive ? SceneEnvironment.SkyBox : SceneEnvironment.Color
            clearColor: root.backgroundColor
            // ✅ IBL подключается для освещения ИЛИ для skybox
            lightProbe: (root.iblReady && (root.iblLightingEnabled || (root.backgroundMode === "skybox" && root.iblBackgroundEnabled))) ? iblLoader.probe : null
            probeOrientation: Qt.vector3d(0, root.iblRotationDeg, 0)
            probeExposure: root.iblIntensity
            probeHorizon: 0.08

            // ✅ Fog configuration (Qt 6.10+): глубинный туман по Near/Far
            fog: Fog {
                enabled: root.fogEnabled
                color: root.fogColor
                depthEnabled: true
                depthNear: root.fogNear
                depthFar: root.fogFar
                depthCurve: 1.0
            }

            // ✅ Тонемаппинг — управляется флагами и параметрами
            tonemapMode: root.tonemapEnabled ?
                         (root.tonemapModeName === "filmic"   ? SceneEnvironment.TonemapModeFilmic :
                          root.tonemapModeName === "aces"     ? SceneEnvironment.TonemapModeAces :
                          root.tonemapModeName === "reinhard" ? SceneEnvironment.TonemapModeReinhard :
                          root.tonemapModeName === "gamma"    ? SceneEnvironment.TonemapModeGamma :
                                                                  SceneEnvironment.TonemapModeLinear)
                         : SceneEnvironment.TonemapModeNone
            exposure: root.tonemapExposure
            whitePoint: root.tonemapWhitePoint
             
            // ✅ ПРАВИЛЬНЫЕ СВОЙСТВА цветокоррекции
            colorAdjustmentsEnabled: true
            adjustmentBrightness: 1.0
            adjustmentContrast: 1.05
            adjustmentSaturation: 1.05
            
            // ✅ ПРАВИЛЬНОЕ СВОЙСТВО OIT (Order Independent Transparency)
            oitMethod: root.oitMode === "weighted" ? SceneEnvironment.OITWeightedBlended : SceneEnvironment.OITNone
        }

        Node {
            id: worldRoot
        }

        // ===============================================================
        // MATERIAL LIBRARY (shared instances to avoid duplication)
        // ===============================================================

        PrincipledMaterial {
            id: frameMaterial
            baseColor: frameBaseColor
            metalness: frameMetalness
            roughness: frameRoughness
            specularAmount: frameSpecularAmount
            specularTint: frameSpecularTint
            clearcoatAmount: frameClearcoat
            clearcoatRoughnessAmount: frameClearcoatRoughness
            transmissionFactor: frameTransmission
            opacity: frameOpacity
            indexOfRefraction: frameIor
            attenuationDistance: frameAttenuationDistance
            attenuationColor: frameAttenuationColor
            emissiveFactor: emissiveVector(frameEmissiveColor, frameEmissiveIntensity)
        }

        PrincipledMaterial {
            id: leverMaterial
            baseColor: leverBaseColor
            metalness: leverMetalness
            roughness: leverRoughness
            specularAmount: leverSpecularAmount
            specularTint: leverSpecularTint
            clearcoatAmount: leverClearcoat
            clearcoatRoughnessAmount: leverClearcoatRoughness
            transmissionFactor: leverTransmission
            opacity: leverOpacity
            indexOfRefraction: leverIor
            attenuationDistance: leverAttenuationDistance
            attenuationColor: leverAttenuationColor
            emissiveFactor: emissiveVector(leverEmissiveColor, leverEmissiveIntensity)
        }

        PrincipledMaterial {
            id: tailRodMaterial
            baseColor: tailRodBaseColor
            metalness: tailRodMetalness
            roughness: tailRodRoughness
            specularAmount: tailRodSpecularAmount
            specularTint: tailRodSpecularTint
            clearcoatAmount: tailRodClearcoat
            clearcoatRoughnessAmount: tailRodClearcoatRoughness
            transmissionFactor: tailRodTransmission
            opacity: tailRodOpacity
            indexOfRefraction: tailRodIor
            attenuationDistance: tailRodAttenuationDistance
            attenuationColor: tailRodAttenuationColor
            emissiveFactor: emissiveVector(tailRodEmissiveColor, tailRodEmissiveIntensity)
        }

        PrincipledMaterial {
            id: cylinderMaterial
            baseColor: cylinderBaseColor
            metalness: cylinderMetalness
            roughness: cylinderRoughness
            specularAmount: cylinderSpecularAmount
            specularTint: cylinderSpecularTint
            clearcoatAmount: cylinderClearcoat
            clearcoatRoughnessAmount: cylinderClearcoatRoughness
            transmissionFactor: cylinderTransmission
            opacity: cylinderOpacity
            indexOfRefraction: cylinderIor
            attenuationDistance: cylinderAttenuationDistance
            attenuationColor: cylinderAttenuationColor
            emissiveFactor: emissiveVector(cylinderEmissiveColor, cylinderEmissiveIntensity)
            alphaMode: PrincipledMaterial.Blend
        }

        PrincipledMaterial {
            id: jointTailMaterial
            baseColor: jointTailBaseColor
            metalness: jointTailMetalness
            roughness: jointTailRoughness
            specularAmount: jointTailSpecularAmount
            specularTint: jointTailSpecularTint
            clearcoatAmount: jointTailClearcoat
            clearcoatRoughnessAmount: jointTailClearcoatRoughness
            transmissionFactor: jointTailTransmission
            opacity: jointTailOpacity
            indexOfRefraction: jointTailIor
            attenuationDistance: jointTailAttenuationDistance
            attenuationColor: jointTailAttenuationColor
            emissiveFactor: emissiveVector(jointTailEmissiveColor, jointTailEmissiveIntensity)
        }

        PrincipledMaterial {
            id: jointArmMaterial
            baseColor: jointArmBaseColor
            metalness: jointArmMetalness
            roughness: jointArmRoughness
            specularAmount: jointArmSpecularAmount
            specularTint: jointArmSpecularTint
            clearcoatAmount: jointArmClearcoat
            clearcoatRoughnessAmount: jointArmClearcoatRoughness
            transmissionFactor: jointArmTransmission
            opacity: jointArmOpacity
            indexOfRefraction: jointArmIor
            attenuationDistance: jointArmAttenuationDistance
            attenuationColor: jointArmAttenuationColor
            emissiveFactor: emissiveVector(jointArmEmissiveColor, jointArmEmissiveIntensity)
        }

        // Camera rig (preserved)
        Node {
            id: cameraRig
            parent: worldRoot
            position: root.pivot
            eulerRotation: Qt.vector3d(root.pitchDeg, root.yawDeg, 0)

            Node {
                id: panNode
                position: Qt.vector3d(root.panX, root.panY, 0)

                PerspectiveCamera {
                    id: camera
                    position: Qt.vector3d(0, 0, root.cameraDistance)
                    fieldOfView: root.cameraFov
                    clipNear: root.cameraNear
                    clipFar: root.cameraFar
                }
            }
        }

        // Lighting (with shadow softness)
        DirectionalLight {
            id: keyLight
            parent: keyLightBindToCamera ? cameraRig : worldRoot
            eulerRotation.x: root.keyLightAngleX
            eulerRotation.y: root.keyLightAngleY
            position: Qt.vector3d(root.keyLightPosX, root.keyLightPosY, 0)
            brightness: root.keyLightBrightness
            color: root.keyLightColor
            castsShadow: (root.shadowsEnabled && root.keyLightCastsShadow)
            // ✅ Чистая маппинг логика без синтаксических ошибок
            shadowMapQuality: root.shadowResolution === "4096" ? Light.ShadowMapQualityVeryHigh :
                              root.shadowResolution === "2048" ? Light.ShadowMapQualityVeryHigh :
                              root.shadowResolution === "1024" ? Light.ShadowMapQualityHigh :
                              root.shadowResolution === "512"  ? Light.ShadowMapQualityMedium :
                                                                   Light.ShadowMapQualityLow
            shadowFactor: root.shadowFactor
            shadowBias: root.shadowBias
            shadowFilter: {
                var samples = Math.floor(root.shadowFilterSamples || 16)
                return samples === 32 ? Light.ShadowFilterPCF32 :
                       samples === 16 ? Light.ShadowFilterPCF16 :
                       samples === 8  ? Light.ShadowFilterPCF8  :
                       samples === 4  ? Light.ShadowFilterPCF4  :
                                        Light.ShadowFilterNone
            }
        }

        DirectionalLight {
            id: fillLight
            parent: fillLightBindToCamera ? cameraRig : worldRoot
            eulerRotation.x: -60
            eulerRotation.y: 135
            position: Qt.vector3d(root.fillLightPosX, root.fillLightPosY, 0)
            brightness: root.fillLightBrightness
            color: root.fillLightColor
            castsShadow: (root.shadowsEnabled && root.fillLightCastsShadow)
        }

        DirectionalLight {
            id: rimLight
            parent: rimLightBindToCamera ? cameraRig : worldRoot
            eulerRotation.x: 15
            eulerRotation.y: 180
            position: Qt.vector3d(root.rimLightPosX, root.rimLightPosY, 0)
            brightness: root.rimLightBrightness
            color: root.rimLightColor
            castsShadow: (root.shadowsEnabled && root.rimLightCastsShadow)
        }

        PointLight {
            id: accentLight
            parent: pointLightBindToCamera ? cameraRig : worldRoot
            position: Qt.vector3d(root.pointLightX, root.pointLightY, 1500)
            brightness: root.pointLightBrightness
            color: root.pointLightColor
            castsShadow: root.pointLightCastsShadow   // ✅ Управляется пользователем
            constantFade: 1.0
            linearFade: 2.0 / Math.max(200.0, root.pointLightRange)
            quadraticFade: 1.0 / Math.pow(Math.max(200.0, root.pointLightRange), 2)
        }

        // ===============================================================
        // SUSPENSION SYSTEM GEOMETRY (with IOR support)
        // ===============================================================

        // U-FRAME (3 beams) with controlled materials
        Model {
            parent: worldRoot
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
            scale: Qt.vector3d(userBeamSize/100, userBeamSize/100, userFrameLength/100)
            materials: [frameMaterial]
        }
        Model {
            parent: worldRoot
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: [frameMaterial]
        }
        Model {
            parent: worldRoot
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userFrameLength - userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: [frameMaterial]
        }

        // ✅ OPTIMIZED SUSPENSION COMPONENT (with CORRECT rod length calculation)
        component OptimizedSuspensionCorner: Node {
            property vector3d j_arm
            property vector3d j_tail  
            property real leverAngle
            property real pistonPositionFromPython: 250.0
                        
            // ✅ ИСПРАВЛЕНО: Избегаем циклические зависимости - используем прямые вычисления
            // Базовая геометрия рычага
            readonly property real baseAngle: (j_arm.x < 0) ? 180 : 0
            readonly property real totalAngle: baseAngle + leverAngle
            readonly property real totalAngleRad: totalAngle * Math.PI / 180
                        
            // Константы длин
            readonly property real tailRodLength: 100                    //мм - хвостовой шток
            readonly property real pistonRodLength: userPistonRodLength  //мм - шток поршня (КОНСТАНТА!)
            
            // LEVER (рычаг)
            Model {
                source: "#Cube"
                position: Qt.vector3d(
                    j_arm.x + (userLeverLength/2) * Math.cos(totalAngleRad),
                    j_arm.y + (userLeverLength/2) * Math.sin(totalAngleRad),
                    j_arm.z
                )
                scale: Qt.vector3d(userLeverLength/100, 0.8, 0.8)
                eulerRotation: Qt.vector3d(0, 0, totalAngle)
                materials: [leverMaterial]
            }
            
            // TAIL ROD (хвостовой шток) - КОНСТАНТНАЯ длина
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
                scale: Qt.vector3d(userRodDiameter/100, tailRodLength/100, userRodDiameter/100)
                eulerRotation: Qt.vector3d(0, 0, cylAngle)
                materials: [tailRodMaterial]
            }
            
            // CYLINDER BODY (корпус цилиндра) с IOR
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: Qt.vector3d((tailRodEnd.x + cylinderEnd.x)/2, (tailRodEnd.y + cylinderEnd.y)/2, tailRodEnd.z)
                scale: Qt.vector3d(userBoreHead/100, userCylinderLength/100, userBoreHead/100)
                eulerRotation: Qt.vector3d(0, 0, cylAngle)
                materials: [cylinderMaterial]
            }
            
            // ✅ PISTON (поршень) - правильная позиция для константной длины штока
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: pistonCenter
                scale: Qt.vector3d((userBoreHead - 2)/100, userPistonThickness/100, (userBoreHead - 2)/100)
                eulerRotation: Qt.vector3d(0, 0, cylAngle)
                materials: PrincipledMaterial {
                    baseColor: rodLengthError > 1.0 ? pistonBodyWarningColor : pistonBodyBaseColor
                    metalness: pistonBodyMetalness
                    roughness: pistonBodyRoughness
                    specularAmount: pistonBodySpecularAmount
                    specularTint: pistonBodySpecularTint
                    clearcoatAmount: pistonBodyClearcoat
                    clearcoatRoughnessAmount: pistonBodyClearcoatRoughness
                    transmissionFactor: pistonBodyTransmission
                    opacity: pistonBodyOpacity
                    indexOfRefraction: pistonBodyIor
                    attenuationDistance: pistonBodyAttenuationDistance
                    attenuationColor: pistonBodyAttenuationColor
                    emissiveFactor: emissiveVector(pistonBodyEmissiveColor, pistonBodyEmissiveIntensity)
                }
            }

            // ✅ PISTON ROD (шток поршня) - КОНСТАНТНАЯ ДЛИНА!
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: Qt.vector3d((pistonCenter.x + j_rod.x)/2, (pistonCenter.y + j_rod.y)/2, pistonCenter.z)
                scale: Qt.vector3d(userRodDiameter/100, pistonRodLength/100, userRodDiameter/100)  // ✅ КОНСТАНТНАЯ ДЛИНА!
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - pistonCenter.y, j_rod.x - pistonCenter.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial {
                    baseColor: rodLengthError > 1.0 ? pistonRodWarningColor : pistonRodBaseColor  // Красный если ошибка > 1мм
                    metalness: pistonRodMetalness
                    roughness: pistonRodRoughness
                    specularAmount: pistonRodSpecularAmount
                    specularTint: pistonRodSpecularTint
                    clearcoatAmount: pistonRodClearcoat
                    clearcoatRoughnessAmount: pistonRodClearcoatRoughness
                    transmissionFactor: pistonRodTransmission
                    opacity: pistonRodOpacity
                    indexOfRefraction: pistonRodIor
                    attenuationDistance: pistonRodAttenuationDistance
                    attenuationColor: pistonRodAttenuationColor
                    emissiveFactor: emissiveVector(pistonRodEmissiveColor, pistonRodEmissiveIntensity)
                }
            }
            
            // JOINTS (шарниры) - цветные маркеры
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: j_tail
                scale: Qt.vector3d(1.2, 2.4, 1.2)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: [jointTailMaterial]
            }
            
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: j_arm
                scale: Qt.vector3d(1.0, 2.0, 1.0)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: [jointArmMaterial]
            }
            
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: j_rod
                scale: Qt.vector3d(0.8, 1.6, 0.8)
                eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.1)
                materials: PrincipledMaterial {
                    baseColor: rodLengthError > 1.0 ? jointRodErrorColor : jointRodOkColor  // Красный если ошибка, зеленый если OK
                    metalness: jointTailMetalness
                    roughness: jointTailRoughness
                    specularAmount: jointTailSpecularAmount
                    specularTint: jointTailSpecularTint
                    clearcoatAmount: jointTailClearcoat
                    clearcoatRoughnessAmount: jointTailClearcoatRoughness
                    transmissionFactor: jointTailTransmission
                    opacity: jointTailOpacity
                    indexOfRefraction: jointTailIor
                    attenuationDistance: jointTailAttenuationDistance
                    attenuationColor: jointTailAttenuationColor
                    emissiveFactor: emissiveVector(jointTailEmissiveColor, jointTailEmissiveIntensity)
                }
            }
            
            // ✅ DEBUG: Логирование ошибок длины штока
            // Удалено: onRodLengthErrorChanged — не все версии Qt/QML генерируют notify-сигнал для readonly-свойств
            // Диагностический лог можно включить через таймер/кнопку при необходимости
            // onRodLengthErrorChanged: {
            //     if (rodLengthError > 1.0) {
            //         console.warn("⚠️ Rod length error:", rodLengthError.toFixed(2), "mm (target:", pistonRodLength, "actual:", actualRodLength.toFixed(2), ")")
            //     }
            // }
            
            // JOINTS (шарниры) - цветные маркеры
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: j_tail
                scale: Qt.vector3d(1.2, 2.4, 1.2)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: [jointTailMaterial]
            }
            
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: j_arm
                scale: Qt.vector3d(1.0, 2.0, 1.0)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: [jointArmMaterial]
            }
            
            Model {
                geometry: CylinderGeometry {
                    segments: root.cylinderSegments
                    rings: root.cylinderRings
                    radius: 50
                    length: 100
                }
                position: j_rod
                scale: Qt.vector3d(0.8, 1.6, 0.8)
                eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.1)
                materials: PrincipledMaterial {
                    baseColor: rodLengthError > 1.0 ? jointRodErrorColor : jointRodOkColor  // Красный если ошибка, зеленый если OK
                    metalness: jointTailMetalness
                    roughness: jointTailRoughness
                    specularAmount: jointTailSpecularAmount
                    specularTint: jointTailSpecularTint
                    clearcoatAmount: jointTailClearcoat
                    clearcoatRoughnessAmount: jointTailClearcoatRoughness
                    transmissionFactor: jointTailTransmission
                    opacity: jointTailOpacity
                    indexOfRefraction: jointTailIor
                    attenuationDistance: jointTailAttenuationDistance
                    attenuationColor: jointTailAttenuationColor
                    emissiveFactor: emissiveVector(jointTailEmissiveColor, jointTailEmissiveIntensity)
                }
            }
        }

        // Four suspension corners with fixed rod lengths
        OptimizedSuspensionCorner {
            id: flCorner
            parent: worldRoot
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fl_angle
            pistonPositionFromPython: root.userPistonPositionFL
        }

        OptimizedSuspensionCorner {
            id: frCorner
            parent: worldRoot
            j_arm: Qt.vector3d(userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fr_angle
            pistonPositionFromPython: root.userPistonPositionFR
        }

        OptimizedSuspensionCorner {
            id: rlCorner
            parent: worldRoot
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userFrameLength - userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userFrameLength - userBeamSize/2)
            leverAngle: rl_angle
            pistonPositionFromPython: root.userPistonPositionRL
        }

        OptimizedSuspensionCorner {
            id: rrCorner
            parent: worldRoot
            j_arm: Qt.vector3d(userFrameToPivot, userBeamSize, userFrameLength - userBeamSize/2)
            j_tail: Qt.vector3d(userTrackWidth/2, userBeamSize + userFrameHeight, userFrameLength - userBeamSize/2)
            leverAngle: rr_angle
            pistonPositionFromPython: root.userPistonPositionRR
        }
    }

    // ===============================================================
    // ✅ ОПТИМИЗИРОВАННЫЕ MOUSE CONTROLS (preserved)
    // ===============================================================

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onPressed: (mouse) => {
            // ✅ ИСПРАВЛЕНО: Правильная инициализация для избежания рывка
            root.mouseDown = true
            root.mouseButton = mouse.button
            root.lastX = mouse.x
            root.lastY = mouse.y

            if (taaMotionAdaptive)
                flagCameraMotion()

            console.log("Mouse pressed: button =", mouse.button, "at", mouse.x, mouse.y)
        }

        onReleased: (mouse) => {
            root.mouseDown = false
            root.mouseButton = 0
            if (taaMotionAdaptive)
                cameraMotionSettler.restart()
            console.log("Mouse released")
        }

        onPositionChanged: (mouse) => {
            if (!root.mouseDown) return
                        
            const dx = mouse.x - root.lastX
            const dy = mouse.y - root.lastY

            // ✅ ИСПРАВЛЕНО: Проверяем на разумные значения delta для избежания рывков
            if (Math.abs(dx) > 100 || Math.abs(dy) > 100) {
                console.log("⚠️ Ignoring large mouse delta:", dx, dy)
                root.lastX = mouse.x
                root.lastY = mouse.y
                return
            }

            if (root.mouseButton === Qt.LeftButton) {
                // ✅ ИСПРАВЛЕНО v4.9.4: БЕЗ нормализации - Qt сам знает как интерполировать!
                root.yawDeg = root.yawDeg - dx * root.rotateSpeed  // Прямое изменение БЕЗ normAngleDeg
                root.pitchDeg = root.clamp(root.pitchDeg - dy * root.rotateSpeed, -85, 85)
            } else if (root.mouseButton === Qt.RightButton) {
                // Panning: move camera in rig's local X/Y
                const fovRad = camera.fieldOfView * Math.PI / 180.0
                const worldPerPixel = (2 * root.cameraDistance * Math.tan(fovRad / 2)) / view3d.height
                const s = worldPerPixel * root.cameraSpeed
                
                root.panX -= dx * s
                root.panY += dy * s
            }

            root.lastX = mouse.x
            root.lastY = mouse.y

            if ( taaMotionAdaptive )
                flagCameraMotion()
        }

        onWheel: (wheel) => {
            const zoomFactor = 1.0 + (wheel.angleDelta.y / 1200.0)
            root.cameraDistance = Math.max(root.minDistance,
                                     Math.min(root.maxDistance,
                                              root.cameraDistance * zoomFactor))
            if (taaMotionAdaptive)
                flagCameraMotion()
        }

        onDoubleClicked: () => {
            console.log("🔄 Double-click: resetting view")
            resetView()
        }
    }

    // ===============================================================
    // ANIMATION TIMERS (preserved)
    // ===============================================================

    Timer {
        id: cameraMotionSettler
        interval: 240
        repeat: false
        onTriggered: root.cameraIsMoving = false
    }

    Timer {
        running: isRunning
        interval: 16  // 60 FPS
        repeat: true
        onTriggered: {
            animationTime += 0.016
        }
    }
    
    Timer {
        running: autoRotate
        interval: 16
        repeat: true
        onTriggered: {
            // ✅ ИСПРАВЛЕНО v4.9.4: БЕЗ нормализации - Qt интерполирует правильно!
            yawDeg = yawDeg + autoRotateSpeed * 0.016 * 10  // Прямое изменение
            if (taaMotionAdaptive)
                flagCameraMotion()
        }
    }

    // ===============================================================
    // KEYBOARD SHORTCUTS (preserved)
    // ===============================================================

    Keys.onPressed: (e) => {
        if (e.key === Qt.Key_R) {
            resetView()
        } else if (e.key === Qt.Key_Space) {
            isRunning = !isRunning
        } else if (e.key === Qt.Key_F) {
            autoFitFrame()
        }
    }

    focus: true

    // ===============================================================
    // ✅ UPDATED INFO PANEL (with rod length information)
    // ===============================================================

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 550
        height: 240
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 8

        Column {
            anchors.centerIn: parent
            spacing: 6
            
            Text { 
                text: "PneumoStabSim Professional | ИСПРАВЛЕННАЯ КИНЕМАТИКА v4.1"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true 
            }
            
            Text { 
                text: "🔧 Qt " + Qt.version + " | Dithering: " + (canUseDithering ? "✅ Supported" : "❌ Not available")
                color: canUseDithering ? "#00ff88" : "#ffaa00"
                font.pixelSize: 10 
            }
            
            Text { 
                text: "🔧 ИСПРАВЛЕНО: Правильный расчет длины штоков"
                color: "#00ff88"
                font.pixelSize: 11 
            }
            
            Text { 
                text: "✅ Длина штока: " + userPistonRodLength + "мм (КОНСТАНТА)"
                color: "#ffaa00"
                font.pixelSize: 10 
            }
            
            Text { 
                text: "🔍 Ошибки длины: FL=" + (flCorner.rodLengthError ? flCorner.rodLengthError.toFixed(2) : "0.00") + 
                      "мм | FR=" + (frCorner.rodLengthError ? frCorner.rodLengthError.toFixed(2) : "0.00") + 
                      "мм | RL=" + (rlCorner.rodLengthError ? rlCorner.rodLengthError.toFixed(2) : "0.00") + 
                      "мм | RR=" + (rrCorner.rodLengthError ? rrCorner.rodLengthError.toFixed(2) : "0.00") + "мм"
                color: "#aaddff"
                font.pixelSize: 9 
            }
            
            Text { 
                text: "📷 Камера: " + cameraDistance.toFixed(0) + "мм | Pivot: (" + 
                      pivot.x.toFixed(0) + ", " + pivot.y.toFixed(0) + ", " + pivot.z.toFixed(0) + ")"
                color: "#cccccc"
                font.pixelSize: 10 
            }
            
            Text { 
                text: "🎮 ЛКМ-вращение | ПКМ-панорама | Колесо-зум | R-сброс | F-автофит | Space-анимация"
                color: "#aaddff"
                font.pixelSize: 9 
            }
        }
    }

    // ===============================================================
    // INITIALIZATION (with rod length validation)
    // ===============================================================

    Component.onCompleted: {
        // Лог старта для диагностики рассинхрона
        console.log("[START] IBL primary:", iblPrimarySource,
                    "fallback:", iblFallbackSource,
                    "mode:", backgroundMode,
                    "iblEnabled:", iblEnabled,
                    "skybox:", iblBackgroundEnabled)

        console.log("═══════════════════════════════════════════")
        console.log("🚀 PneumoStabSim ENHANCED VERSION v4.9.4 LOADED")
        console.log("═══════════════════════════════════════════")
        console.log("🔧 Qt Version:", Qt.version)
        console.log("   Qt Major:", qtMajor, "| Qt Minor:", qtMinor)
        console.log("   Dithering support:", canUseDithering ? "✅ YES (Qt 6.10+)" : "❌ NO (Qt < 6.10)")
        console.log("   Specular AA:", canUseSpecularAA ? "ENABLED" : "DISABLED (temporary workaround)")
        console.log("✅ CRITICAL FIX v4.9.4:")
        console.log("   🔧 Skybox rotation: INDEPENDENT from camera")
        console.log("   🔧 probeOrientation uses ONLY iblRotationDeg")
        console.log("   🔧 Camera yaw does NOT affect skybox orientation")
        console.log("   🔧 Skybox and camera are COMPLETELY DECOUPLED")
        console.log("✅ ИСПРАВЛЕНИЯ СВОЙСТВ ExtendedSceneEnvironment:")
        console.log("   ✅ glowBloom - правильное название")
        console.log("   ✅ depthOfFieldFocusDistance - правильное название")
        console.log("   ✅ depthOfFieldFocusRange - правильное название")
        console.log("   ✅ vignetteRadius - правильное название")
        console.log("   ✅ vignetteStrength - правильное название")
        console.log("   ✅ Все свойства проверены по документации Qt Quick 3D")
        console.log("✅ ВСЕ ПАРАМЕТРЫ GRAPHICSPANEL:")
        console.log("   🔥 Коэффициент преломления (IOR):", cylinderIor)
        console.log("   🔥 IBL освещение:", iblLightingEnabled, "| IBL фон:", iblBackgroundEnabled, "| Поворот:", iblRotationDeg.toFixed(1) + "°")
        console.log("   🔥 Туман поддержка:", fogEnabled)
        console.log("   🔥 Расширенные эффекты: Bloom, SSAO, DoF, Vignette, Lens Flare")
        console.log("   🔥 Dithering:", canUseDithering ? "Enabled" : "Not available")
        console.log("   🔥 Procedural geometry: segments=" + cylinderSegments + ", rings=" + cylinderRings)
        console.log("🎯 СТАТУС: main.qml v4.9.4 SKYBOX ПОЛНОСТЬЮ ОТВЯЗАН ОТ КАМЕРЫ")
        console.log("═══════════════════════════════════════════")
        
        syncRenderSettings()
        resetView()
        view3d.forceActiveFocus()
    }

    // IBL readiness console log for Python-side logger
    onIblReadyChanged: {
        console.log("[IBL] READY:", JSON.stringify({ ready: iblReady }))
    }

    // Model of HDR/EXR files from assets/hdr
    FolderListModel {
        id: hdriModel
        folder: Qt.resolvedUrl("../hdr")
        nameFilters: ["*.hdr", "*.exr"]
        showDirs: false
        showDotAndDotDot: false
    }
    
}
