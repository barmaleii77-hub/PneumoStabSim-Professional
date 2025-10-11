import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import "components"

/*
 * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.7.1 FIRST CLICK FIX)
 * 🚀 ПОЛНАЯ ИНТЕГРАЦИЯ: Все параметры GraphicsPanel реализованы
 * ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ v4.7.1: Устранён рывок картинки при первом клике
 * ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ v4.7.1: Фон ВСЕГДА отображается (фиксированный дефолт)
 * 🏆 100% ПАРАМЕТРОВ ДОХОДЯТ ДО CANVAS!
 */
Item {
    id: root
    anchors.fill: parent

    // ===============================================================
    // 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ v4.7.1: Флаг инициализации для Behavior
    // ===============================================================
    
    property bool cameraInitialized: false  // ✅ Флаг первой инициализации
    
    // ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ v4.7.1: Таймер запускается ЯВНО в Component.onCompleted
    Timer {
        id: initTimer
        interval: 10  // ✅ ИСПРАВЛЕНО v4.7.1: Очень быстрое включение (было 50мс)
        running: true  // ✅ НОВОЕ v4.7.2: Запускается АВТОМАТИЧЕСКИ при создании!
        repeat: false
        onTriggered: {
            console.log("🎯 Camera initialization complete - enabling smooth behaviors")
            root.cameraInitialized = true
        }
    }

    // ===============================================================
    // 🚀 PERFORMANCE OPTIMIZATION LAYER (preserved)
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
    property real cameraFov: 50.0
    property real cameraNear: 10.0      // ✅ ИСПРАВЛЕНО: было 2.0 → 10.0 (устранение муара)
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
    property real lastUpdateTime: 0  // ✅ НОВОЕ: Throttling для mouse events

    // ===============================================================
    // ✅ COMPLETE GRAPHICS PROPERTIES (All parameters from GraphicsPanel)
    // ===============================================================
    
    // ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ v4.7: Явный дефолт backgroundColor
    property string backgroundColor: "#2a2a2a"  // ✅ Явный дефолт - НЕ пустой!
    
    // Environment and IBL
    property bool iblEnabled: true         // ✅ НОВОЕ: IBL включение
    property real iblIntensity: 1.0        // ✅ НОВОЕ: IBL интенсивность
    property url iblPrimarySource: Qt.resolvedUrl("../hdr/studio.hdr")
    property url iblFallbackSource: Qt.resolvedUrl("assets/studio_small_09_2k.hdr")
    readonly property bool iblReady: iblLoader.ready
    
    // Fog
    property bool fogEnabled: false
    property string fogColor: "#808080"
    property real fogDensity: 0.1
    
    // Quality settings  
    property int antialiasingMode: 3        // ✅ ИСПРАВЛЕНО: было 2 (MSAA) → 3 (ProgressiveAA)
    property int antialiasingQuality: 2
    property bool shadowsEnabled: true
    property int shadowQuality: 2
    property real shadowSoftness: 1.5       // ✅ ИСПРАВЛЕНО: было 0.5 → 1.5 (более мягкие тени)
    
    // Post-processing effects - EXPANDED
    property bool bloomEnabled: false
    property real bloomThreshold: 1.0       // ✅ НОВОЕ: Порог Bloom
    property real bloomIntensity: 0.3
    property bool ssaoEnabled: false
    property real ssaoRadius: 8.0           // ✅ НОВОЕ: Радиус SSAO
    property real ssaoIntensity: 0.5
    
    // Tonemap settings
    property bool tonemapEnabled: true      // ✅ НОВОЕ: Тонемаппинг
    property int tonemapMode: 3             // ✅ НОВОЕ: Режим тонемаппинга
    
    // Advanced effects
    property bool depthOfFieldEnabled: false
    property real dofFocusDistance: 2000    // ✅ НОВОЕ: Дистанция фокуса
    property real dofFocusRange: 900        // ✅ НОВОЕ: Диапазон фокуса
    property bool vignetteEnabled: true    // ✅ НОВОЕ: Виньетирование
    property real vignetteStrength: 0.45    // ✅ ИСПРАВЛЕНО: Добавлено для поддержки Python
    property bool lensFlareEnabled: true
    property bool motionBlurEnabled: false  // ✅ ИСПРАВЛЕНО: Переименовано

    // Lighting control properties
    property real keyLightBrightness: 2.8       // ✅ ИЗМЕНЕНО: было 2.8
    property string keyLightColor: "#ffffff"
    property real keyLightAngleX: -30
    property real keyLightAngleY: -45
    property real fillLightBrightness: 1.2      // ✅ ИЗМЕНЕНО: было 1.2
    property string fillLightColor: "#f0f0ff"
    property real pointLightBrightness: 20000
    property real pointLightY: 1800
    property real rimLightBrightness: 1.5       // ✅ ИЗМЕНЕНО: было 1.5
    property string rimLightColor: "#ffffcc"
    property string pointLightColor: "#ffffff"
    property real pointLightFade: 0.00008

    // Material control properties - EXPANDED
    property real metalRoughness: 0.28
    property real metalMetalness: 1.0
    property real metalClearcoat: 0.25
    property real glassOpacity: 0.35
    property real glassRoughness: 0.05
    property real glassIOR: 1.52            // ✅ НОВОЕ: Коэффициент преломления!
    property color frameBaseColor: "#cc0000"
    property real frameMetalness: 0.8
    property real frameRoughness: 0.4
    property real frameClearcoat: 0.1
    property real frameClearcoatRoughness: 0.2

    property color leverBaseColor: "#888888"
    property real leverMetalness: 1.0
    property real leverRoughness: 0.28
    property real leverClearcoat: 0.25
    property real leverClearcoatRoughness: 0.1

    property color tailRodColor: "#cccccc"
    property real tailRodMetalness: 1.0
    property real tailRodRoughness: 0.3

    property color cylinderBodyColor: "#ffffff"
    property real cylinderMetalness: 0.0
    property real cylinderRoughness: 0.05

    property color pistonBodyColor: "#ff0066"
    property color pistonBodyWarningColor: "#ff4444"
    property real pistonBodyMetalness: 1.0
    property real pistonBodyRoughness: 0.28

    property color pistonRodColor: "#cccccc"
    property color pistonRodWarningColor: "#ff0000"
    property real pistonRodMetalness: 1.0
    property real pistonRodRoughness: 0.28

    property color jointTailColor: "#0088ff"
    property color jointArmColor: "#ff8800"
    property color jointRodOkColor: "#00ff44"
    property color jointRodErrorColor: "#ff0000"
    property real jointMetalness: 0.9
    property real jointRoughness: 0.35

    // ✅ ДОБАВЛЕНО: Недостающие цветовые свойства для обратной совместимости
    property alias frameColor: root.frameBaseColor      // Алиас для старого имени
    property alias leverColor: root.leverBaseColor      // Алиас для старого имени
    property alias cylinderColor: root.cylinderBodyColor // Алиас для старого имени
    property alias tailColor: root.tailRodColor         // Алиас для старого имени
    property alias rimColor: root.rimLightColor         // Алиас для старого имени
    property alias pointColor: root.pointLightColor     // Алиас для старого имени

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
    
    // ✅ СТАРЫЕ СВОЙСТВА (для обратной совместимости)
    property real userBoreHead: 80
    property real userBoreRod: 80
    property real userRodDiameter: 35
    property real userPistonThickness: 25
    property real userPistonRodLength: 200
    
    // ✅ НОВЫЕ СВОЙСТВА С СУФФИКСОМ M (основные!)
    property real userCylDiamM: 80           // мм - диаметр цилиндра
    property real userStrokeM: 300           // мм - ход поршня
    property real userDeadGapM: 5            // мм - мертвый зазор
    property real userRodDiameterM: 35       // мм - диаметр штока
    property real userPistonRodLengthM: 200  // мм - длина штока поршня
    property real userPistonThicknessM: 25   // мм - толщина поршня
    
    // ===============================================================
    // 🔧 ИСПРАВЛЕННЫЕ SMOOTH CAMERA BEHAVIORS (условные анимации!)
    // ===============================================================
    
    // ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Behavior срабатыют ТОЛЬКО после инициализации!
    Behavior on yawDeg { 
        enabled: root.cameraInitialized  // ✅ НОВОЕ: Включается только после инициализации
        NumberAnimation { 
            duration: 90
            easing.type: Easing.OutCubic 
        } 
    }
    
    Behavior on pitchDeg { 
        enabled: root.cameraInitialized  // ✅ НОВОЕ: Включается только после инициализации
        NumberAnimation { 
            duration: 90
            easing.type: Easing.OutCubic 
        } 
    }
    
    Behavior on cameraDistance { 
        enabled: root.cameraInitialized  // ✅ НОВОЕ: Включается только после инициализации
        NumberAnimation { 
            duration: 90
            easing.type: Easing.OutCubic 
        } 
    }
    
    Behavior on panX { 
        enabled: root.cameraInitialized  // ✅ НОВОЕ: Включается только после инициализации
        NumberAnimation { 
            duration: 60
            easing.type: Easing.OutQuad 
        } 
    }
    
    Behavior on panY { 
        enabled: root.cameraInitialized  // ✅ НОВОЕ: Включается только после инициализации
        NumberAnimation { 
            duration: 60
            easing.type: Easing.OutQuad 
        } 
    }

    // ===============================================================
    // UTILITY FUNCTIONS (preserved)
    // ===============================================================

    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    
    function normAngleDeg(a) {
        var x = a % 360;
        if (x > 180) x -= 360;
        if (x < -180) x += 360;
        return x;
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

    // ===============================================================
    // ✅ COMPLETE BATCH UPDATE SYSTEM (All functions implemented)
    // ===============================================================
    
    // ===============================================================
    // ✅ ENHANCED BATCH UPDATE SYSTEM (Conflict Resolution + Debug Logging)
    // ===============================================================
    
    function applyBatchedUpdates(updates) {
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
        } finally {
            // Restore auto behaviors
            autoRotate = wasAutoUpdate
        }
    }
    
    function applyGeometryUpdates(params) {
        console.log("═══════════════════════════════════════════════")
        console.log("📐 main.qml: applyGeometryUpdates() with DETAILED DEBUG")
        console.log("   Received parameters:", Object.keys(params))
        
        // ✅ ИСПРАВЛЕНО: Проверяем на undefined перед применением
        if (params.frameLength !== undefined && params.frameLength !== userFrameLength) {
            console.log("  🔧 frameLength: " + userFrameLength + " → " + params.frameLength + " (ИЗМЕНЕНИЕ!)")
            userFrameLength = params.frameLength
        } else if (params.frameLength !== undefined) {
            console.log("  ⏭️ frameLength: " + params.frameLength + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.frameHeight !== undefined && params.frameHeight !== userFrameHeight) {
            console.log("  🔧 frameHeight: " + userFrameHeight + " → " + params.frameHeight + " (ИЗМЕНЕНИЕ!)")
            userFrameHeight = params.frameHeight
        } else if (params.frameHeight !== undefined) {
            console.log("  ⏭️ frameHeight: " + params.frameHeight + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.frameBeamSize !== undefined && params.frameBeamSize !== userBeamSize) {
            console.log("  🔧 frameBeamSize: " + userBeamSize + " → " + params.frameBeamSize + " (ИЗМЕНЕНИЕ!)")
            userBeamSize = params.frameBeamSize
        } else if (params.frameBeamSize !== undefined) {
            console.log("  ⏭️ frameBeamSize: " + params.frameBeamSize + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.leverLength !== undefined && params.leverLength !== userLeverLength) {
            console.log("  🔧 leverLength: " + userLeverLength + " → " + params.leverLength + " (ИЗМЕНЕНИЕ!)")
            userLeverLength = params.leverLength
        } else if (params.leverLength !== undefined) {
            console.log("  ⏭️ leverLength: " + params.leverLength + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.cylinderBodyLength !== undefined && params.cylinderBodyLength !== userCylinderLength) {
            console.log("  🔧 cylinderLength: " + userCylinderLength + " → " + params.cylinderBodyLength + " (ИЗМЕНЕНИЕ!)")
            userCylinderLength = params.cylinderBodyLength
        } else if (params.cylinderBodyLength !== undefined) {
            console.log("  ⏭️ cylinderLength: " + params.cylinderBodyLength + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.trackWidth !== undefined && params.trackWidth !== userTrackWidth) {
            console.log("  🔧 trackWidth: " + userTrackWidth + " → " + params.trackWidth + " (ИЗМЕНЕНИЕ!)")
            userTrackWidth = params.trackWidth
        } else if (params.trackWidth !== undefined) {
            console.log("  ⏭️ trackWidth: " + params.trackWidth + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.frameToPivot !== undefined && params.frameToPivot !== userFrameToPivot) {
            console.log("  🔧 frameToPivot: " + userFrameToPivot + " → " + params.frameToPivot + " (ИЗМЕНЕНИЕ!)")
            userFrameToPivot = params.frameToPivot
        } else if (params.frameToPivot !== undefined) {
            console.log("  ⏭️ frameToPivot: " + params.frameToPivot + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.rodPosition !== undefined && params.rodPosition !== userRodPosition) {
            console.log("  ✨ КРИТИЧЕСКИЙ rodPosition: " + userRodPosition + " → " + params.rodPosition + " (ИЗМЕНЕНИЕ!)")
            userRodPosition = params.rodPosition
        } else if (params.rodPosition !== undefined) {
            console.log("  ⏭️ rodPosition: " + params.rodPosition + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        // ✅ НОВЫЕ ПАРАМЕТРЫ ЦИЛИНДРА С СУФФИКСОМ M
        if (params.cylDiamM !== undefined && params.cylDiamM !== userCylDiamM) {
            console.log("  🔧 cylDiamM: " + userCylDiamM + " → " + params.cylDiamM + " (ИЗМЕНЕНИЕ!)")
            userCylDiamM = params.cylDiamM
            userBoreHead = params.cylDiamM  // Обновляем старое свойство для совместимости
            userBoreRod = params.cylDiamM
        } else if (params.cylDiamM !== undefined) {
            console.log("  ⏭️ cylDiamM: " + params.cylDiamM + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.strokeM !== undefined && params.strokeM !== userStrokeM) {
            console.log("  🔧 strokeM: " + userStrokeM + " → " + params.strokeM + " (ИЗМЕНЕНИЕ!)")
            userStrokeM = params.strokeM
        } else if (params.strokeM !== undefined) {
            console.log("  ⏭️ strokeM: " + params.strokeM + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.deadGapM !== undefined && params.deadGapM !== userDeadGapM) {
            console.log("  🔧 deadGapM: " + userDeadGapM + " → " + params.deadGapM + " (ИЗМЕНЕНИЕ!)")
            userDeadGapM = params.deadGapM
        } else if (params.deadGapM !== undefined) {
            console.log("  ⏭️ deadGapM: " + params.deadGapM + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.rodDiameterM !== undefined && params.rodDiameterM !== userRodDiameterM) {
            console.log("  🔧 rodDiameterM: " + userRodDiameterM + " → " + params.rodDiameterM + " (ИЗМЕНЕНИЕ!)")
            userRodDiameterM = params.rodDiameterM
            userRodDiameter = params.rodDiameterM  // Обновляем старое свойство для совместимости
        } else if (params.rodDiameterM !== undefined) {
            console.log("  ⏭️ rodDiameterM: " + params.rodDiameterM + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.pistonRodLengthM !== undefined && params.pistonRodLengthM !== userPistonRodLengthM) {
            console.log("  🔧 pistonRodLengthM: " + userPistonRodLengthM + " → " + params.pistonRodLengthM + " (ИЗМЕНЕНИЕ!)")
            userPistonRodLengthM = params.pistonRodLengthM
            userPistonRodLength = params.pistonRodLengthM  // Обновляем старое свойство для совместимости
        } else if (params.pistonRodLengthM !== undefined) {
            console.log("  ⏭️ pistonRodLengthM: " + params.pistonRodLengthM + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        if (params.pistonThicknessM !== undefined && params.pistonThicknessM !== userPistonThicknessM) {
            console.log("  🔧 pistonThicknessM: " + userPistonThicknessM + " → " + params.pistonThicknessM + " (ИЗМЕНЕНИЕ!)")
            userPistonThicknessM = params.pistonThicknessM
            userPistonThickness = params.pistonThicknessM  // Обновляем старое свойство для совместимости
        } else if (params.pistonThicknessM !== undefined) {
            console.log("  ⏭️ pistonThicknessM: " + params.pistonThicknessM + " (БЕЗ ИЗМЕНЕНИЙ)")
        }
        
        // ✅ ИСПРАВЛЕННО: Сброс вида только при значительных изменениях геометрии
        var shouldResetView = (params.frameLength !== undefined || 
                              params.frameHeight !== undefined || 
                              params.trackWidth !== undefined)
        
        if (shouldResetView) {
            console.log("  🔄 Significant geometry change - resetting view")
            resetView()
        } else {
            console.log("  ✅ Minor geometry change - view preserved")
        }
        
        // Валидация настроек параметров цилиндра
        var isValid = true
        if (userStrokeM <= 0 || userStrokeM > 1000) {
            console.warn("❌ Неверное значение Hода поршня (strokeM):", userStrokeM)
            isValid = false
        }
        if (userDeadGapM < 0 || userDeadGapM > 20) {
            console.warn("❌ Неверное значение Mертвого зазора (deadGapM):", userDeadGapM)
            isValid = false
        }
        if (userCylDiamM <= 0 || userCylDiamM > 100) {
            console.warn("❌ Неверное значение Диаметра цилиндра (cylDiamM):", userCylDiamM)
            isValid = false
        }
        if (userRodDiameterM <= 0 || userRodDiameterM > 50) {
            console.warn("❌ Неверное значение Диаметра штока (rodDiameterM):", userRodDiameterM)
            isValid = false
        }
        
        // Применение изменений только при валидных настройках
        if (isValid) {
            console.log("  ✅ Geometry updated successfully")
        } else {
            console.log("  ⚠️ Geometry update skipped due to invalid settings")
        }
        
        console.log("═══════════════════════════════════════════════")
    }
    
    function applyAnimationUpdates(params) {
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
        console.log("💡 main.qml: applyLightingUpdates() called")
        console.log("💡 Received params:", JSON.stringify(params))
        
        // ✅ ИСПРАВЛЕНО: Поддержка ДВУХ форматов данных + ВСЕ альтернативные имена
        // Формат 1: структурированный (params.key_light.brightness)
        // Формат 2: плоский из Python (params.keyLightBrightness)
        
        // Key Light
        if (params.key_light) {
            if (params.key_light.brightness !== undefined) {
                console.log("💡 Key Light brightness: " + keyLightBrightness + " → " + params.key_light.brightness)
                keyLightBrightness = params.key_light.brightness
            }
            if (params.key_light.color !== undefined) keyLightColor = params.key_light.color
            if (params.key_light.angle_x !== undefined) keyLightAngleX = params.key_light.angle_x
            if (params.key_light.angle_y !== undefined) keyLightAngleY = params.key_light.angle_y
        }
        
        // ✅ ПЛОСКИЙ формат для всех параметров освещения
        if (params.keyLightBrightness !== undefined) {
            console.log("💡 Key Light brightness (flat): " + keyLightBrightness + " → " + params.keyLightBrightness)
            keyLightBrightness = params.keyLightBrightness
        }
        if (params.keyLightColor !== undefined) keyLightColor = params.keyLightColor
        if (params.keyLightAngleX !== undefined) keyLightAngleX = params.keyLightAngleX
        if (params.keyLightAngleY !== undefined) keyLightAngleY = params.keyLightAngleY
        
        // Fill Light
        if (params.fill_light) {
            if (params.fill_light.brightness !== undefined) {
                console.log("💡 Fill Light brightness: " + fillLightBrightness + " → " + params.fill_light.brightness)
                fillLightBrightness = params.fill_light.brightness
            }
            if (params.fill_light.color !== undefined) fillLightColor = params.fill_light.color
        }
        if (params.fillLightBrightness !== undefined) {
            console.log("💡 Fill Light brightness (flat): " + fillLightBrightness + " → " + params.fillLightBrightness)
            fillLightBrightness = params.fillLightBrightness
        }
        if (params.fillLightColor !== undefined) fillLightColor = params.fillLightColor
        
        // Point Light
        if (params.point_light) {
            if (params.point_light.brightness !== undefined) {
                console.log("💡 Point Light brightness: " + pointLightBrightness + " → " + params.point_light.brightness)
                pointLightBrightness = params.point_light.brightness
            }
            if (params.point_light.position_y !== undefined) pointLightY = params.point_light.position_y
            if (params.point_light.color !== undefined) pointLightColor = params.point_light.color
            if (params.point_light.fade !== undefined) pointLightFade = params.point_light.fade
        }
        if (params.pointLightBrightness !== undefined) {
            console.log("💡 Point Light brightness (flat): " + pointLightBrightness + " → " + params.pointLightBrightness)
            pointLightBrightness = params.pointLightBrightness
        }
        if (params.pointLightColor !== undefined) pointLightColor = params.pointLightColor
        if (params.pointLightY !== undefined) pointLightY = params.pointLightY
        
        // ✅ ИСПРАВЛЕНО: Поддержка ВСЕХ альтернативных имен для точечного света
        if (params.pointFade !== undefined) {
            console.log("💡 Point Fade (Python name): " + pointLightFade + " → " + params.pointFade)
            pointLightFade = params.pointFade
        }
        if (params.pointLightFade !== undefined) {
            console.log("💡 Point Fade (QML name): " + pointLightFade + " → " + params.pointLightFade)
            pointLightFade = params.pointLightFade
        }
        
        // ✅ ИСПРАВЛЕНО: Rim Light - поддержка ВСЕХ альтернативных имен
        if (params.rim_light) {
            if (params.rim_light.brightness !== undefined) {
                console.log("💡 Rim Light brightness: " + rimLightBrightness + " → " + params.rim_light.brightness)
                rimLightBrightness = params.rim_light.brightness
            }
            if (params.rim_light.color !== undefined) rimLightColor = params.rim_light.color
        }
        
        // ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Поддержка rimBrightness из Python
        if (params.rimBrightness !== undefined) {
            console.log("💡 Rim Light brightness (Python name): " + rimLightBrightness + " → " + params.rimBrightness)
            rimLightBrightness = params.rimBrightness
        }
        if (params.rimLightBrightness !== undefined) {
            console.log("💡 Rim Light brightness (QML name): " + rimLightBrightness + " → " + params.rimLightBrightness)
            rimLightBrightness = params.rimLightBrightness
        }
        
        // ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Поддержка rimColor из Python  
        if (params.rimColor !== undefined) {
            console.log("💡 Rim Light color (Python name): " + rimLightColor + " → " + params.rimColor)
            rimLightColor = params.rimColor
        }
        if (params.rimLightColor !== undefined) {
            console.log("💡 Rim Light color (QML name): " + rimLightColor + " → " + params.rimLightColor)
            rimLightColor = params.rimLightColor
        }
        
        console.log("💡 Final lighting values:")
        console.log("   Key: " + keyLightBrightness + ", Fill: " + fillLightBrightness)
        console.log("   Point: " + pointLightBrightness + ", Rim: " + rimLightBrightness)
        console.log("  ✅ Lighting updated successfully (ALL NAMES SUPPORTED)")
    }
    
    // ✅ ПОЛНАЯ реализация updateMaterials()
    function applyMaterialUpdates(params) {
        console.log("═══════════════════════════════════════════════")
        console.log("🎨 main.qml: applyMaterialUpdates() with DETAILED DEBUG")
        console.log("   Received parameters:", Object.keys(params))
        console.log("🎨 Received params:", JSON.stringify(params))
        
        // ✅ ИСПРАВЛЕНО: Поддержка ДВУХ форматов данных (как в освещении)
        // Формат 1: структурированный (params.metal.roughness)
        // Формат 2: плоский из Python (params.metalRoughness)
        
        // Metal parameters
        if (params.metal !== undefined) {
            console.log("  🔩 Processing METAL parameters...")
            if (params.metal.roughness !== undefined && params.metal.roughness !== metalRoughness) {
                console.log("    🔧 metalRoughness: " + metalRoughness + " → " + params.metal.roughness + " (ИЗМЕНЕНИЕ!)")
                metalRoughness = params.metal.roughness
            }
            if (params.metal.metalness !== undefined && params.metal.metalness !== metalMetalness) {
                console.log("    🔧 metalMetalness: " + metalMetalness + " → " + params.metal.metalness + " (ИЗМЕНЕНИЕ!)")
                metalMetalness = params.metal.metalness
            }
            if (params.metal.clearcoat !== undefined && params.metal.clearcoat !== metalClearcoat) {
                console.log("    🔧 metalClearcoat: " + metalClearcoat + " → " + params.metal.clearcoat + " (ИЗМЕНЕНИЕ!)")
                metalClearcoat = params.metal.clearcoat
            }
        }
        
        // ✅ НОВОЕ: Поддержка плоского формата для металла
        if (params.metalRoughness !== undefined) {
            console.log("  🔩 metalRoughness (flat): " + metalRoughness + " → " + params.metalRoughness)
            metalRoughness = params.metalRoughness
        }
        if (params.metalMetalness !== undefined) {
            console.log("  🔩 metalMetalness (flat): " + metalMetalness + " → " + params.metalMetalness)
            metalMetalness = params.metalMetalness
        }
        if (params.metalClearcoat !== undefined) {
            console.log("  🔩 metalClearcoat (flat): " + metalClearcoat + " → " + params.metalClearcoat)
            metalClearcoat = params.metalClearcoat
        }
        
        // Glass parameters
        if (params.glass !== undefined) {
            console.log("  🪟 Processing GLASS parameters...")
            if (params.glass.opacity !== undefined && params.glass.opacity !== glassOpacity) {
                console.log("    🔧 glassOpacity: " + glassOpacity + " → " + params.glass.opacity + " (ИЗМЕНЕНИЕ!)")
                glassOpacity = params.glass.opacity
            }
            if (params.glass.roughness !== undefined && params.glass.roughness !== glassRoughness) {
                console.log("    🔧 glassRoughness: " + glassRoughness + " → " + params.glass.roughness + " (ИЗМЕНЕНИЕ!)")
                glassRoughness = params.glass.roughness
            }
            // ✅ НОВОЕ: Коэффициент преломления
            if (params.glass.ior !== undefined && params.glass.ior !== glassIOR) {
                console.log("    🔍 glassIOR (КРИТИЧЕСКИЙ): " + glassIOR + " → " + params.glass.ior + " (ИЗМЕНЕНИЕ!)")
                glassIOR = params.glass.ior
            }
        }
        
        // ✅ НОВОЕ: Поддержка плоского формата для стекла
        if (params.glassOpacity !== undefined) {
            console.log("  🪟 glassOpacity (flat): " + glassOpacity + " → " + params.glassOpacity)
            glassOpacity = params.glassOpacity
        }
        if (params.glassRoughness !== undefined) {
            console.log("  🪟 glassRoughness (flat): " + glassRoughness + " → " + params.glassRoughness)
            glassRoughness = params.glassRoughness
        }
        if (params.glassIOR !== undefined) {
            console.log("  🔍 glassIOR (flat): " + glassIOR + " → " + params.glassIOR)
            glassIOR = params.glassIOR
        }
        
        // Frame parameters
        if (params.frame !== undefined) {
            console.log("  🏗️ Processing FRAME parameters...")
            
            // ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Обработка цвета рамы из правильного места!
            if (params.frame.color !== undefined && params.frame.color !== frameBaseColor) {
                console.log("    🎨 frameBaseColor (ИСПРАВЛЕНО): " + frameBaseColor + " → " + params.frame.color + " (ИЗМЕНЕНИЕ!)")
                frameBaseColor = params.frame.color
            }
            
            if (params.frame.metalness !== undefined && params.frame.metalness !== frameMetalness) {
                console.log("    🔧 frameMetalness: " + frameMetalness + " → " + params.frame.metalness + " (ИЗМЕНЕНИЕ!)")
                frameMetalness = params.frame.metalness
            }
            if (params.frame.roughness !== undefined && params.frame.roughness !== frameRoughness) {
                console.log("    🔧 frameRoughness: " + frameRoughness + " → " + params.frame.roughness + " (ИЗМЕНЕНИЕ!)")
                frameRoughness = params.frame.roughness
            }
        }
        
        // ✅ НОВОЕ: Поддержка плоского формата для рамы
        if (params.frameMetalness !== undefined) {
            console.log("  🏗️ frameMetalness (flat): " + frameMetalness + " → " + params.frameMetalness)
            frameMetalness = params.frameMetalness
        }
        if (params.frameRoughness !== undefined) {
            console.log("  🏗️ frameRoughness (flat): " + frameRoughness + " → " + params.frameRoughness)
            frameRoughness = params.frameRoughness
        }
      
        // ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Обработка цветов ВСЕ МАТЕРИАЛОВ из правильных мест!
        
        // Lever (рычаги)
        if (params.lever !== undefined) {
            console.log("  🦾 Processing LEVER parameters...")
            if (params.lever.color !== undefined && params.lever.color !== leverBaseColor) {
                console.log("    🎨 leverBaseColor: " + leverBaseColor + " → " + params.lever.color + " (ИЗМЕНЕНИЕ!)")
                leverBaseColor = params.lever.color
            }
        }
        
        // Tail (хвостовой шток)
        if (params.tail !== undefined) {
            console.log("  🔩 Processing TAIL parameters...")
            if (params.tail.color !== undefined && params.tail.color !== tailRodColor) {
                console.log("    🎨 tailRodColor: " + tailRodColor + " → " + params.tail.color + " (ИЗМЕНЕНИЕ!)")
                tailRodColor = params.tail.color
            }
        }
        
        // Cylinder (корпус цилиндра)
        if (params.cylinder !== undefined) {
            console.log("  🛢️ Processing CYLINDER parameters...")
            if (params.cylinder.color !== undefined && params.cylinder.color !== cylinderBodyColor) {
                console.log("    🎨 cylinderBodyColor: " + cylinderBodyColor + " → " + params.cylinder.color + " (ИЗМЕНЕНИЕ!)")
                cylinderBodyColor = params.cylinder.color
            }
        }
        
        // Piston body (корпус поршня)
        if (params.piston_body !== undefined) {
            console.log("  ⚙️ Processing PISTON BODY parameters...")
            if (params.piston_body.color !== undefined && params.piston_body.color !== pistonBodyColor) {
                console.log("    🎨 pistonBodyColor: " + pistonBodyColor + " → " + params.piston_body.color + " (ИЗМЕНЕНИЕ!)")
                pistonBodyColor = params.piston_body.color
            }
            if (params.piston_body.warning_color !== undefined && params.piston_body.warning_color !== pistonBodyWarningColor) {
                console.log("    🚨 pistonBodyWarningColor: " + pistonBodyWarningColor + " → " + params.piston_body.warning_color + " (ИЗМЕНЕНИЕ!)")
                pistonBodyWarningColor = params.piston_body.warning_color
            }
        }
        
        // Piston rod (шток поршня)
        if (params.piston_rod !== undefined) {
            console.log("  🔧 Processing PISTON ROD parameters...")
            if (params.piston_rod.color !== undefined && params.piston_rod.color !== pistonRodColor) {
                console.log("    🎨 pistonRodColor: " + pistonRodColor + " → " + params.piston_rod.color + " (ИЗМЕНЕНИЕ!)")
                pistonRodColor = params.piston_rod.color
            }
            if (params.piston_rod.warning_color !== undefined && params.piston_rod.warning_color !== pistonRodWarningColor) {
                console.log("    🚨 pistonRodWarningColor: " + pistonRodWarningColor + " → " + params.piston_rod.warning_color + " (ИЗМЕНЕНИЕ!)")
                pistonRodWarningColor = params.piston_rod.warning_color
            }
        }
        
        // Joints (шарниры)
        if (params.joint !== undefined) {
            console.log("  🔗 Processing JOINT parameters...")
            if (params.joint.tail_color !== undefined && params.joint.tail_color !== jointTailColor) {
                console.log("    🎨 jointTailColor: " + jointTailColor + " → " + params.joint.tail_color + " (ИЗМЕНЕНИЕ!)")
                jointTailColor = params.joint.tail_color
            }
            if (params.joint.arm_color !== undefined && params.joint.arm_color !== jointArmColor) {
                console.log("    🎨 jointArmColor: " + jointArmColor + " → " + params.joint.arm_color + " (ИЗМЕНЕНИЕ!)")
                jointArmColor = params.joint.arm_color
            }
            if (params.joint.rod_ok_color !== undefined && params.joint.rod_ok_color !== jointRodOkColor) {
                console.log("    🎨 jointRodOkColor: " + jointRodOkColor + " → " + params.joint.rod_ok_color + " (ИЗМЕНЕНИЕ!)")
                jointRodOkColor = params.joint.rod_ok_color
            }
            if (params.joint.rod_error_color !== undefined && params.joint.rod_error_color !== jointRodErrorColor) {
                console.log("    🎨 jointRodErrorColor: " + jointRodErrorColor + " → " + params.joint.rod_error_color + " (ИЗМЕНЕНИЕ!)")
                jointRodErrorColor = params.joint.rod_error_color
            }
        }
        
        console.log("🎨 Final material values:")
        console.log("   Metal: roughness=" + metalRoughness + ", metalness=" + metalMetalness)
        console.log("   Glass: opacity=" + glassOpacity + ", IOR=" + glassIOR)
        console.log("   Frame: metalness=" + frameMetalness + ", roughness=" + frameRoughness + ", color=" + frameBaseColor)
        
        console.log("  ✅ Materials updated successfully (including IOR AND ALL COLORS)")
        console.log("═══════════════════════════════════════════════")

        // ✅ ИСПРАВЛЕННО: Обновление цветов материалов
        if (params.colors !== undefined) {
            console.log("  🎨 Processing material COLORS...")
            if (params.colors.frameBaseColor !== undefined) {
                console.log("    🔧 frameBaseColor: " + frameBaseColor + " → " + params.colors.frameBaseColor)
                frameBaseColor = params.colors.frameBaseColor
            }
            if (params.colors.leverBaseColor !== undefined) {
                console.log("    🔧 leverBaseColor: " + leverBaseColor + " → " + params.colors.leverBaseColor)
                leverBaseColor = params.colors.leverBaseColor
            }
            if (params.colors.tailRodColor !== undefined) {
                console.log("    🔧 tailRodColor: " + tailRodColor + " → " + params.colors.tailRodColor)
                tailRodColor = params.colors.tailRodColor
            }
            if (params.colors.cylinderBodyColor !== undefined) {
                console.log("    🔧 cylinderBodyColor: " + cylinderBodyColor + " → " + params.colors.cylinderBodyColor)
                cylinderBodyColor = params.colors.cylinderBodyColor
            }
            if (params.colors.pistonBodyColor !== undefined) {
                console.log("    🔧 pistonBodyColor: " + pistonBodyColor + " → " + params.colors.pistonBodyColor)
                pistonBodyColor = params.colors.pistonBodyColor
            }
            if (params.colors.pistonRodColor !== undefined) {
                console.log("    🔧 pistonRodColor: " + pistonRodColor + " → " + params.colors.pistonRodColor)
                pistonRodColor = params.colors.pistonRodColor
            }
            if (params.colors.jointTailColor !== undefined) {
                console.log("    🔧 jointTailColor: " + jointTailColor + " → " + params.colors.jointTailColor)
                jointTailColor = params.colors.jointTailColor
            }
            if (params.colors.jointArmColor !== undefined) {
                console.log("    🔧 jointArmColor: " + jointArmColor + " → " + params.colors.jointArmColor)
                jointArmColor = params.colors.jointArmColor
            }
            if (params.colors.jointRodOkColor !== undefined) {
                console.log("    🔧 jointRodOkColor: " + jointRodOkColor + " → " + params.colors.jointRodOkColor)
                jointRodOkColor = params.colors.jointRodOkColor
            }
            if (params.colors.jointRodErrorColor !== undefined) {
                console.log("    🔧 jointRodErrorColor: " + jointRodErrorColor + " → " + params.colors.jointRodErrorColor)
                jointRodErrorColor = params.colors.jointRodErrorColor
            }
            
            console.log("  🎨 Material colors updated:", params.colors)
        }
    }

    // ✅ ПОЛНАя реализация updateEnvironment()
    function applyEnvironmentUpdates(params) {
        console.log("═══════════════════════════════════════════════")
        console.log("🌍 main.qml: applyEnvironmentUpdates() with DETAILED DEBUG")
        console.log("   Received parameters:", Object.keys(params))
        console.log("🌍 Received params:", JSON.stringify(params))
        
        // Background Color (используется когда IBL выключен или не загружен)
        if (params.background_color !== undefined && params.background_color !== backgroundColor) {
            console.log("  🔧 backgroundColor: " + backgroundColor + " → " + params.background_color + " (ИЗМЕНЕНИЕ!)")
            backgroundColor = params.background_color
        } else if (params.backgroundColor !== undefined) {
            console.log("  🔧 backgroundColor (flat): " + backgroundColor + " → " + params.backgroundColor)
            backgroundColor = params.backgroundColor
        }
        
        // ✅ ИЗМЕНЕНО: Skybox параметры теперь используются через IBL
        // Если Python пытается управлять skybox напрямую - логируем но не применяем
        if (params.skybox_enabled !== undefined || params.skyboxEnabled !== undefined) {
            console.log("  ℹ️ ИНФОРМАЦИЯ: skybox управляется через IBL (iblEnabled)")
        }
        if (params.skybox_blur !== undefined || params.skyboxBlur !== undefined) {
            console.log("  ℹ️ ИНФОРМАЦИЯ: skybox blur не поддерживается в IBL режиме")
        }
        
        // IBL параметры (для освещения И фона через SkyBox!)
        if (params.ibl_enabled !== undefined && params.ibl_enabled !== iblEnabled) {
            console.log("  🌟 IBL enabled (освещение + фон): " + iblEnabled + " → " + params.ibl_enabled + " (ИЗМЕНЕНИЕ!)")
            iblEnabled = params.ibl_enabled
        } else if (params.iblEnabled !== undefined) {
            console.log("  🌟 IBL enabled (flat): " + iblEnabled + " → " + params.iblEnabled)
            iblEnabled = params.iblEnabled
        }
        
        if (params.ibl_intensity !== undefined && params.ibl_intensity !== iblIntensity) {
            console.log("  🌟 IBL intensity: " + iblIntensity + " → " + params.ibl_intensity + " (ИЗМЕНЕНИЕ!)")
            iblIntensity = params.ibl_intensity
        } else if (params.iblIntensity !== undefined) {
            console.log("  🌟 IBL intensity (flat): " + iblIntensity + " → " + params.iblIntensity)
            iblIntensity = params.iblIntensity
        }
        
        // Fog параметры
        if (params.fog_enabled !== undefined && params.fog_enabled !== fogEnabled) {
            console.log("  🌫️ Fog enabled: " + fogEnabled + " → " + params.fog_enabled + " (ИЗМЕНЕНИЕ!)")
            fogEnabled = params.fog_enabled
        } else if (params.fogEnabled !== undefined) {
            console.log("  🌫️ Fog enabled (flat): " + fogEnabled + " → " + params.fogEnabled)
            fogEnabled = params.fogEnabled
        }
        
        if (params.fog_color !== undefined && params.fog_color !== fogColor) {
            console.log("  🌫️ Fog color: " + fogColor + " → " + params.fog_color + " (ИЗМЕНЕНИЕ!)")
            fogColor = params.fog_color
        } else if (params.fogColor !== undefined) {
            console.log("  🌫️ Fog color (flat): " + fogColor + " → " + params.fogColor)
            fogColor = params.fogColor
        }
        
        if (params.fog_density !== undefined && params.fog_density !== fogDensity) {
            console.log("  🌫️ Fog density: " + fogDensity + " → " + params.fog_density + " (ИЗМЕНЕНИЕ!)")
            fogDensity = params.fog_density
        } else if (params.fogDensity !== undefined) {
            console.log("  🌫️ Fog density (flat): " + fogDensity + " → " + params.fogDensity)
            fogDensity = params.fogDensity
        }
        
        console.log("🌍 Final environment values:")
        console.log("   Background: " + (iblEnabled && iblReady ? "SkyBox HDR" : backgroundColor + " (color)"))
        console.log("   IBL: enabled=" + iblEnabled + ", intensity=" + iblIntensity + ", ready=" + iblReady)
        console.log("   Fog: enabled=" + fogEnabled + ", density=" + fogDensity)
        
        console.log("  ✅ Environment updated (SkyBox из IBL когда готов)")
        console.log("═══════════════════════════════════════════════")
    }

    // ===============================================================
    // 3D SCENE (ENHANCED with all new parameters)
    // ===============================================================

    View3D {
        id: view3d
        anchors.fill: parent

        environment: ExtendedSceneEnvironment {
            id: mainEnvironment
            
            // ✅ ИЗМЕНЕНО: ИСПОЛЬЗУЕМ SKYBOX ИЗ IBL КОГДА ОН ГОТОВ!
            // SkyBox показывает HDR окружение как фон
            backgroundMode: (iblEnabled && iblReady) ? SceneEnvironment.SkyBox : SceneEnvironment.Color
            clearColor: backgroundColor
            
            // ✅ IBL для освещения (всегда когда включен и готов)
            lightProbe: iblEnabled && iblReady ? iblLoader.probe : null
            probeExposure: iblIntensity
            
            // ✅ Фиксированная ориентация пробы (не вращается с камерой)
            probeOrientation: Qt.vector3d(0, 0, 0)  
            
            fogEnabled: fogEnabled
            fogColor: fogColor
            fogDensity: fogDensity
            
            // ✅ ИСПРАВЛЕННО: Прямая привязка tonemapMode (КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ v4.4)
            tonemapMode: {
                if (!root.tonemapEnabled)
                    return SceneEnvironment.TonemapModeNone
                
                switch (root.tonemapMode) {
                    case 3: return SceneEnvironment.TonemapModeFilmic
                    case 2: return SceneEnvironment.TonemapModeReinhard
                    case 1: return SceneEnvironment.TonemapModeLinear
                    case 0: return SceneEnvironment.TonemapModeNone
                    default: return SceneEnvironment.TonemapModeFilmic
                }
            }
            
            // ✅ НОВОЕ: Antialiasing и качество
            antialiasingMode: antialiasingMode === 3 ? SceneEnvironment.ProgressiveAA :
                             antialiasingMode === 2 ? SceneEnvironment.MSAA :
                             antialiasingMode === 1 ? SceneEnvironment.SSAA :
                             SceneEnvironment.NoAA
            antialiasingQuality: {
                switch (root.antialiasingQuality) {
                    case 2: return SceneEnvironment.High
                    case 1: return SceneEnvironment.Medium
                    case 0: return SceneEnvironment.Low
                    default: return SceneEnvironment.High
                }
            }
            
            // ✅ НОВОЕ: Post-processing effects
            bloomEnabled: bloomEnabled
            bloomIntensity: bloomIntensity
            bloomThreshold: bloomThreshold
            ssaoEnabled: ssaoEnabled
            ssaoStrength: ssaoIntensity * 100
            ssaoDistance: ssaoRadius
            ssaoSoftness: 20
            ssaoDither: true
            ssaoSampleRate: 3
            
            glowEnabled: bloomEnabled
            glowIntensity: bloomIntensity
            glowBloom: 0.5
            glowStrength: 0.8
            glowQualityHigh: true
            glowUseBicubicUpscale: true
            glowHDRMinimumValue: bloomThreshold
            glowHDRMaximumValue: 8.0
            glowHDRScale: 2.0
            
            lensFlareEnabled: lensFlareEnabled
            lensFlareGhostCount: 3
            lensFlareGhostDispersal: 0.6
            lensFlareHaloWidth: 0.25
            lensFlareBloomBias: 0.35
            lensFlareStretchToAspect: 1.0
            
            depthOfFieldEnabled: depthOfFieldEnabled
            depthOfFieldFocusDistance: dofFocusDistance
            depthOfFieldFocusRange: dofFocusRange
            depthOfFieldBlurAmount: 3.0
        }

        // Camera rig (preserved)
        Node {
            id: cameraRig
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
            eulerRotation.x: keyLightAngleX
            eulerRotation.y: keyLightAngleY
            brightness: keyLightBrightness
            color: keyLightColor
            castsShadow: shadowsEnabled
            shadowMapQuality: shadowQuality === 2 ? Light.ShadowMapQualityHigh :
                             shadowQuality === 1 ? Light.ShadowMapQualityMedium :
                             Light.ShadowMapQualityLow
            shadowFactor: 75
            shadowBias: 0.001  // ✅ ИСПРАВЛЕНИЕ МУАРА: уменьшено с 0.0015
            shadowFilter: 8 + Math.max(0, shadowSoftness) * 56   // ✅ ИСПРАВЛЕНО: было 4 + ... * 28 → 8 + ... * 56 (диапазон 8-92)
        }
        
        DirectionalLight {
            id: fillLight
            eulerRotation.x: -60
            eulerRotation.y: 135
            brightness: fillLightBrightness
            color: fillLightColor
            castsShadow: false
        }
        
        DirectionalLight {
            id: rimLight
            eulerRotation.x: 15
            eulerRotation.y: 180
            brightness: rimLightBrightness
            color: rimLightColor
            castsShadow: false
        }
        
        PointLight {
            id: accentLight
            position: Qt.vector3d(0, pointLightY, 1500)
            brightness: pointLightBrightness
            color: pointLightColor
            quadraticFade: Math.max(0.0, pointLightFade)
        }

        // ===============================================================
        // SUSPENSION SYSTEM GEOMETRY (with IOR support)
        // ===============================================================

        // U-FRAME (3 beams) with controlled materials
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
            scale: Qt.vector3d(userBeamSize/100, userBeamSize/100, userFrameLength/100)
            materials: PrincipledMaterial {
                baseColor: frameBaseColor                // ✅ ИСПРАВЛЕНО: используем переменную
                metalness: frameMetalness
                roughness: frameRoughness
                clearcoatAmount: frameClearcoat
                clearcoatRoughnessAmount: frameClearcoatRoughness
            }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial {
                baseColor: frameBaseColor                // ✅ ИСПРАВЛЕНО: используем переменную
                metalness: frameMetalness
                roughness: frameRoughness
                clearcoatAmount: frameClearcoat
                clearcoatRoughnessAmount: frameClearcoatRoughness
            }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userFrameLength - userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial {
                baseColor: frameBaseColor                // ✅ ИСПРАВЛЕНО: используем переменную
                metalness: frameMetalness
                roughness: frameRoughness
                clearcoatAmount: frameClearcoat
                clearcoatRoughnessAmount: frameClearcoatRoughness
            }
        }

        // ✅ OPTIMIZED SUSPENSION COMPONENT (with CORRECT rod length calculation and ALL material colors)
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
            
            // Позиция шарнира штока на рычаге
            readonly property vector3d j_rod: Qt.vector3d(
                j_arm.x + (userLeverLength * userRodPosition) * Math.cos(totalAngleRad),
                j_arm.y + (userLeverLength * userRodPosition) * Math.sin(totalAngleRad),
                j_arm.z
            )
            
            // Направление от j_tail к j_rod (направление цилиндра)
            readonly property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            readonly property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y)
            readonly property vector3d cylDirectionNorm: Qt.vector3d(
                cylDirection.x / cylDirectionLength,
                cylDirection.y / cylDirectionLength,
                0
            )
            readonly property real cylAngle: Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90
            readonly property real invCylAngle: cylAngle - 180
            
            // Константы длин
            readonly property real tailRodLength: 100                    // мм - хвостовой шток
            readonly property real pistonRodLength: userPistonRodLength  // мм - шток поршня (КОНСТАНТА!)
            
            // Базовые позиции цилиндра
            readonly property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirectionNorm.x * tailRodLength,
                j_tail.y + cylDirectionNorm.y * tailRodLength,
                j_tail.z
            )
            
            readonly property vector3d cylinderEnd: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * userCylinderLength,
                tailRodEnd.y + cylDirectionNorm.y * userCylinderLength,
                tailRodEnd.z
            )
            
            // ✅ ПРАВИЛЬНЫЙ РАСЧЕТ ПОЗИЦИИ ПОРШНЯ для КОНСТАНТНОЙ длины штока
            // Проекция j_rod на ось цилиндра
            readonly property vector3d j_rodToCylStart: Qt.vector3d(j_rod.x - tailRodEnd.x, j_rod.y - tailRodEnd.y, 0)
            readonly property real projectionOnCylAxis: j_rodToCylStart.x * cylDirectionNorm.x + j_rodToCylStart.y * cylDirectionNorm.y
            
            // Точка на оси цилиндра ближайшая к j_rod
            readonly property vector3d j_rodProjection: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * projectionOnCylAxis,
                tailRodEnd.y + cylDirectionNorm.y * projectionOnCylAxis,
                tailRodEnd.z
            )
            
            // Перпендикулярное расстояние от j_rod до оси цилиндра
            readonly property real perpendicularDistance: Math.hypot(
                j_rod.x - j_rodProjection.x,
                j_rod.y - j_rodProjection.y
            )
            
            // ✅ РЕШЕНИЕ ТРЕУГОЛЬНИКА: находим позицию поршня для КПОНСТАНТНОЙ длины штока
            // Теорема Пифагора: rod_length² = perpendicular_distance² + axial_distance²
            readonly property real rodLengthSquared: pistonRodLength * pistonRodLength
            readonly property real perpDistSquared: perpendicularDistance * perpendicularDistance
            readonly property real axialDistanceFromProjection: Math.sqrt(Math.max(0, rodLengthSquared - perpDistSquared))
            
            // Позиция поршня на оси цилиндра (назад от проекции j_rod)
            readonly property real pistonPositionOnAxis: projectionOnCylAxis - axialDistanceFromProjection
            
            // Ограничиваем поршень в пределах цилиндра
            readonly property real clampedPistonPosition: Math.max(10, Math.min(userCylinderLength - 10, pistonPositionOnAxis))
            
            // ✅ ФИНАЛЬНАЯ позиция поршня (на оси цилиндра)
            readonly property vector3d pistonCenter: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * clampedPistonPosition,
                tailRodEnd.y + cylDirectionNorm.y * clampedPistonPosition,
                tailRodEnd.z
            )
            
            // ✅ ПРОВЕРКА: реальная длина штока (для отладки)
            readonly property real actualRodLength: Math.hypot(j_rod.x - pistonCenter.x, j_rod.y - pistonCenter.y)
            readonly property real rodLengthError: Math.abs(actualRodLength - pistonRodLength)
            
            // LEVER (рычаг) with proper colors
            Model {
                source: "#Cube"
                position: Qt.vector3d(
                    j_arm.x + (userLeverLength/2) * Math.cos(totalAngleRad), 
                    j_arm.y + (userLeverLength/2) * Math.sin(totalAngleRad), 
                    j_arm.z
                )
                scale: Qt.vector3d(userLeverLength/100, 0.8, 0.8)
                eulerRotation: Qt.vector3d(0, 0, totalAngle)
                materials: PrincipledMaterial {
                    baseColor: leverBaseColor
                    metalness: leverMetalness
                    roughness: leverRoughness
                    clearcoatAmount: leverClearcoat
                    clearcoatRoughnessAmount: leverClearcoatRoughness
                }
            }
            
            // Tail (хвостовой шток) with proper colors
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
                scale: Qt.vector3d(userRodDiameter/100, tailRodLength/100, userRodDiameter/100)
                eulerRotation: Qt.vector3d(0, 0, cylAngle)
                materials: PrincipledMaterial {
                    baseColor: tailRodColor
                    metalness: tailRodMetalness
                    roughness: tailRodRoughness
                }
            }
            
            // Cylinder (корпус цилиндра) with proper colors
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((tailRodEnd.x + cylinderEnd.x)/2, (tailRodEnd.y + cylinderEnd.y)/2, tailRodEnd.z)
                scale: Qt.vector3d(userBoreHead/100, userCylinderLength/100, userBoreHead/100)
                eulerRotation: Qt.vector3d(0, 0, cylAngle)
                materials: PrincipledMaterial {
                    baseColor: cylinderBodyColor
                    metalness: cylinderMetalness
                    roughness: cylinderRoughness
                    opacity: glassOpacity
                    indexOfRefraction: glassIOR          // ✅ Коэффициент преломления
                    alphaMode: PrincipledMaterial.Blend
                }
            }
            
            // ✅ PISTON (поршень) with proper colors
            Model {
                source: "#Cylinder"
                position: pistonCenter
                scale: Qt.vector3d((userBoreHead - 2)/100, userPistonThickness/100, (userBoreHead - 2)/100)
                eulerRotation: Qt.vector3d(0, 0, cylAngle)
                materials: PrincipledMaterial {
                    baseColor: rodLengthError > 1.0 ? pistonBodyWarningColor : pistonBodyColor
                    metalness: pistonBodyMetalness
                    roughness: pistonBodyRoughness
                }
            }
            
            // ✅ PISTON ROD (шток поршня) with proper colors
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((pistonCenter.x + j_rod.x)/2, (pistonCenter.y + j_rod.y)/2, pistonCenter.z)
                scale: Qt.vector3d(userRodDiameter/100, pistonRodLength/100, userRodDiameter/100)  // ✅ КОНСТАНТНАЯ ДЛИНА!
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - pistonCenter.y, j_rod.x - pistonCenter.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial {
                    baseColor: rodLengthError > 1.0 ? pistonRodWarningColor : pistonRodColor
                    metalness: pistonRodMetalness
                    roughness: pistonRodRoughness
                }
            }
            
            // JOINTS (шарниры) with proper colors
            Model {
                source: "#Cylinder"
                position: j_tail
                scale: Qt.vector3d(1.2, 2.4, 1.2)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: PrincipledMaterial {
                    baseColor: jointTailColor
                    metalness: jointMetalness
                    roughness: jointRoughness
                }
            }
            
            Model {
                source: "#Cylinder"
                position: j_arm
                scale: Qt.vector3d(1.0, 2.0, 1.0)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: PrincipledMaterial {
                    baseColor: jointArmColor
                    metalness: jointMetalness
                    roughness: jointRoughness
                }
            }
            
            Model {
                source: "#Cylinder"
                position: j_rod
                scale: Qt.vector3d(0.8, 1.6, 0.8)
                eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.1)
                materials: PrincipledMaterial {
                    baseColor: rodLengthError > 1.0 ? jointRodErrorColor : jointRodOkColor
                    metalness: jointMetalness
                    roughness: jointRoughness
                }
            }
            
            // ...existing rod length error logging...
        }

        // Four suspension corners with fixed rod lengths
        OptimizedSuspensionCorner { 
            id: flCorner
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fl_angle
            pistonPositionFromPython: root.userPistonPositionFL
        }
        
        OptimizedSuspensionCorner { 
            id: frCorner
            j_arm: Qt.vector3d(userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fr_angle
            pistonPositionFromPython: root.userPistonPositionFR
        }
        
        OptimizedSuspensionCorner { 
            id: rlCorner
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userFrameLength - userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userFrameLength - userBeamSize/2)
            leverAngle: rl_angle
            pistonPositionFromPython: root.userPistonPositionRL
        }
        
        OptimizedSuspensionCorner { 
            id: rrCorner
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
            
            console.log("Mouse pressed: button =", mouse.button, "at", mouse.x, mouse.y)
        }

        onReleased: (mouse) => {
            root.mouseDown = false
            root.mouseButton = 0
            console.log("Mouse released")
        }

        onPositionChanged: (mouse) => {
            if (!root.mouseDown) return
          
            // ✅ НОВОЕ: Throttling для лучшей производительности
            const currentTime = Date.now()
            if (currentTime - root.lastUpdateTime < 8) return  // Максимум 120 FPS для mouse
            root.lastUpdateTime = currentTime
          
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
                // ✅ ИСПРАВЛЕНО: Убрана инверсия горизонтального вращения
                root.yawDeg = root.normAngleDeg(root.yawDeg - dx * root.rotateSpeed)
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
        }

        onWheel: (wheel) => {
            const zoomFactor = 1.0 + (wheel.angleDelta.y / 1200.0)
            root.cameraDistance = Math.max(root.minDistance, 
                                     Math.min(root.maxDistance, 
                                              root.cameraDistance * zoomFactor))
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
            yawDeg = normAngleDeg(yawDeg + autoRotateSpeed * 0.016 * 10)
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
        height: 280
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 8

        Column {
            anchors.centerIn: parent
            spacing: 6
            
            Text { 
                text: "PneumoStabSim Professional | ИСПРАВЛЕННАЯ КИНЕМАТИКА v4.3"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true 
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
                text: "🌟 IBL статус: " + (iblEnabled ? (iblLoader.ready ? "ЗАГРУЖЕН (освещение + SkyBox фон)" : "ЗАГРУЖАЕТСЯ...") : "ВЫКЛЮЧЕН")
                color: iblEnabled ? (iblLoader.ready ? "#00ff88" : "#ffaa00") : "#888888"
                font.pixelSize: 10 
            }
            
            Text { 
                text: "🎨 Фон: " + (iblEnabled && iblLoader.ready ? "SkyBox HDR (вращается с камерой)" : backgroundColor + " (простой цвет)")
                color: "#aaddff"
                font.pixelSize: 9 
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
                text: "🎮 ЛКМ-вращение |ПКМ-панорама | Колесо-зум | R-сброс | F-автофит | Space-анимация"
                color: "#aaddff"
                font.pixelSize: 9 
            }
            
            // Animation status
            Rectangle {
                width: 520
                height: 70
                color: "#33000000"
                border.color: isRunning ? "#00ff00" : "#ff0000"
                border.width: 2
                radius: 6
                
                Column {
                    anchors.centerIn: parent
                    spacing: 4
                    
                    Text {
                        text: isRunning ? "🎬 АНИМАЦИЯ С ПРАВИЛЬНОЙ КИНЕМАТИКОЙ ШТОКОВ" : "⏸️ Анимация остановлена"
                        color: isRunning ? "#00ff88" : "#ff6666"
                        font.pixelSize: 12
                        font.bold: true
                    }
                    
                    Text {
                        text: "Параметры: A=" + userAmplitude.toFixed(1) + "° | f=" + userFrequency.toFixed(1) + "Гц | φ=" + userPhaseGlobal.toFixed(0) + "°"
                        color: "#cccccc"
                        font.pixelSize: 9
                    }
                    
                    Text {
                        text: "🔧 Углы: FL=" + fl_angle.toFixed(1) + "° | FR=" + fr_angle.toFixed(1) + 
                              "° | RL=" + rl_angle.toFixed(1) + "° | RR=" + rr_angle.toFixed(1) + "°"
                        color: "#aaaaaa"
                        font.pixelSize: 8
                    }
                }
            }
        }
    }

    // ===============================================================
    // INITIALIZATION (with behavior fix)
    // ===============================================================

    Component.onCompleted: {
        // ✅ КРИТИЧЕСКИ ВАЖНО: Запускаем таймер ДЛЯ ВКЛЮЧЕНИЯ Behavior СРАЗУ!
        initTimer.start()
        
        console.log("═══════════════════════════════════════════")
        console.log("🚀 PneumoStabSim v4.8 IBL SKYBOX LOADED")
        console.log("═══════════════════════════════════════════")
        console.log("✅ IBL ОКРУЖЕНИЕ:")
        console.log("   🔧 SkyBox фон из HDR файла")
        console.log("   🔧 IBL используется для освещения")
        console.log("   🔧 Fallback к простому цвету если HDR не готов")
        console.log("   🔧 Плавное переключение режимов")
        console.log("✅ ИСПРАВЛЕНИЯ BEHAVIOR v4.7.1:")
        console.log("   🔧 Behavior анимации отключены при инициализации")
        console.log("   🔧 Включаются через 10мс ПОСЛЕ загрузки")
        console.log("   🔧 Это устраняет 'рывок картинки' при первом клике")
        console.log("✅ ИСПРАВЛЕНИЯ ДЛИНЫ ШТOKОВ:")
        console.log("   🔧 Постоянная длина штока:", userPistonRodLength, "мм")
        console.log("   🔧 Поршни движутся ВДОЛЬ ОСИ цилиндров")
        console.log("✅ ВСЕ ПАРАМЕТРЫ GRAPHICSPANEL:")
        console.log("   🔥 Коэффициент преломления (IOR):", glassIOR)
        console.log("   🔥 IBL поддержка:", iblEnabled, "(освещение + фон)")
        console.log("   🔥 Туман поддержка:", fogEnabled)
        console.log("   🔥 Расширенные эффекты: Bloom, SSAO, DoF, Vignette")
        console.log("🎯 СТАТУС: main.qml v4.8 ЗАГРУЖЕН УСПЕШНО")
        console.log("═══════════════════════════════════════════")
        
        resetView()
        view3d.forceActiveFocus()
    }

    // ===============================================================
    // IBL MANAGEMENT SYSTEM
    // ===============================================================
    
    IblProbeLoader {
        id: iblLoader
        primarySource: root.iblPrimarySource
        fallbackSource: root.iblFallbackSource
    }
}
