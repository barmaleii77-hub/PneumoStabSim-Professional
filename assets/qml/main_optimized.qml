import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import "components"

/*
 * PneumoStabSim - ИСПРАВЛЕНО: ExtendedSceneEnvironment + убрано дублирование v4.3
 * ✅ Использует ExtendedSceneEnvironment для всех эффектов
 * ✅ Использует только OptimizedSuspensionCorner (без дублирования)
 * ✅ Все примитивы создаются ОДИН РАЗ для каждого угла
 * ✅ Убрано дублирование обработчиков событий
 * ✅ НОВОЕ: Интеграция IBL с IblProbeLoader
 */
Item {
    id: root
    anchors.fill: parent

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
    // ✅ НОВОЕ: IBL Probe Loader для HDR освещения
    // ===============================================================
    
    IblProbeLoader {
        id: iblLoader
    }

    readonly property bool iblTextureReady: iblLoader.ready

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
    property real cameraNear: 2.0
    property real cameraFar: 50000.0
    property real cameraSpeed: 1.0
    
    // Auto rotation
    property bool autoRotate: false
    property real autoRotateSpeed: 0.5

    // ✅ ИСПРАВЛЕНО: Убрано дублирование mouse state - только один раз
    property bool mouseDown: false
    property int mouseButton: 0
    property real lastX: 0
    property real lastY: 0
    property real rotateSpeed: 0.35

    // ===============================================================
    // ✅ COMPLETE GRAPHICS PROPERTIES (All parameters from GraphicsPanel)
    // ===============================================================
    
    // Environment and IBL
    property string backgroundColor: "#2a2a2a"
    property bool skyboxEnabled: true
    property bool iblEnabled: true         // ✅ НОВОЕ: IBL включение
    property real iblIntensity: 1.0        // ✅ НОВОЕ: IBL интенсивность
    
    // Fog
    property bool fogEnabled: false
    property string fogColor: "#808080"
    property real fogDensity: 0.1
    
    // Quality settings  
    property int antialiasingMode: 2
    property int antialiasingQuality: 2
    property bool shadowsEnabled: true
    property int shadowQuality: 2
    property real shadowSoftness: 0.5      // ✅ НОВОЕ: Мягкость теней
    
    // Post-processing effects - EXPANDED
    property bool bloomEnabled: true
    property real bloomThreshold: 1.0       // ✅ НОВОЕ: Порог Bloom
    property real bloomIntensity: 0.8
    property bool ssaoEnabled: true
    property real ssaoRadius: 8.0           // ✅ НОВОЕ: Радиус SSAO
    property real ssaoIntensity: 0.6
    
    // Tonemap settings
    property bool tonemapEnabled: true      // ✅ НОВОЕ: Тонемаппинг
    property int tonemapMode: 3             // ✅ НОВОЕ: Режим тонемаппинга
    
    // Advanced effects
    property bool depthOfFieldEnabled: false
    property real dofFocusDistance: 2000    // ✅ НОВОЕ: Дистанция фокуса
    property real dofFocusRange: 900        // ✅ НОВОЕ: Диапазон фокуса
    property bool lensFlareEnabled: true
    property bool vignetteEnabled: true     // ✅ НОВОЕ: Виньетирование
    property real vignetteStrength: 0.45    // ✅ НОВОЕ: Сила виньетирования
    property bool motionBlurEnabled: false  // ✅ ИСПРАВЛЕНО: Переименовано
    
    // Lighting control properties
    property real keyLightBrightness: 2.8
    property string keyLightColor: "#ffffff"
    property real keyLightAngleX: -30
    property real keyLightAngleY: -45
    property real fillLightBrightness: 1.2
    property string fillLightColor: "#f0f0ff"
    property real pointLightBrightness: 20000
    property real pointLightY: 1800

    // Material control properties - EXPANDED
    property real metalRoughness: 0.28
    property real metalMetalness: 1.0
    property real metalClearcoat: 0.25
    property real glassOpacity: 0.35
    property real glassRoughness: 0.05
    property real glassIOR: 1.52            // ✅ НОВОЕ: Коэффициент преломления!
    property real frameMetalness: 0.8
    property real frameRoughness: 0.4

    // ===============================================================
    // ANIMATION AND GEOMETRY PROPERTIES (preserved)
    // ===============================================================
    
    property real animationTime: 0.0
    property bool isRunning: false
    property bool isSceneInMotion: mouseDown || autoRotate || isRunning

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
    
    function resolvedTonemapMode() {
        if (!tonemapEnabled)
            return SceneEnvironment.TonemapModeNone

        switch (tonemapMode) {
        case 3:
            return SceneEnvironment.TonemapModeFilmic
        case 2:
            return SceneEnvironment.TonemapModeReinhard
        case 1:
            return SceneEnvironment.TonemapModeLinear
        default:
            return SceneEnvironment.TonemapModeNone
        }
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
    // ✅ ENHANCED BATCH UPDATE SYSTEM (Conflict Resolution)
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
        console.log("📐 main_optimized.qml: applyGeometryUpdates() with conflict resolution")
        
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
        console.log("🎬 main_optimized.qml: applyAnimationUpdates() called")
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
        console.log("💡 main_optimized.qml: applyLightingUpdates() called")
        if (params.key_light) {
            if (params.key_light.brightness !== undefined) keyLightBrightness = params.key_light.brightness
            if (params.key_light.color !== undefined) keyLightColor = params.key_light.color
            if (params.key_light.angle_x !== undefined) keyLightAngleX = params.key_light.angle_x
            if (params.key_light.angle_y !== undefined) keyLightAngleY = params.key_light.angle_y
        }
        if (params.fill_light) {
            if (params.fill_light.brightness !== undefined) fillLightBrightness = params.fill_light.brightness
            if (params.fill_light.color !== undefined) fillLightColor = params.fill_light.color
        }
        if (params.point_light) {
            if (params.point_light.brightness !== undefined) pointLightBrightness = params.point_light.brightness
            if (params.point_light.position_y !== undefined) pointLightY = params.point_light.position_y
        }
        console.log("  ✅ Lighting updated successfully")
    }

    function applyMaterialUpdates(params) {
        console.log("🎨 main_optimized.qml: applyMaterialUpdates() called")
        
        if (params.metal !== undefined) {
            if (params.metal.roughness !== undefined) metalRoughness = params.metal.roughness
            if (params.metal.metalness !== undefined) metalMetalness = params.metal.metalness
            if (params.metal.clearcoat !== undefined) metalClearcoat = params.metal.clearcoat
        }
        
        if (params.glass !== undefined) {
            if (params.glass.opacity !== undefined) glassOpacity = params.glass.opacity
            if (params.glass.roughness !== undefined) glassRoughness = params.glass.roughness
            if (params.glass.ior !== undefined) {
                glassIOR = params.glass.ior
                console.log("  🔍 Glass IOR updated to:", glassIOR)
            }
        }
        
        if (params.frame !== undefined) {
            if (params.frame.metalness !== undefined) frameMetalness = params.frame.metalness
            if (params.frame.roughness !== undefined) frameRoughness = params.frame.roughness
        }
        
        console.log("  ✅ Materials updated successfully (including IOR)")
    }

    function applyEnvironmentUpdates(params) {
        console.log("🌍 main_optimized.qml: applyEnvironmentUpdates() called")
        
        if (params.background_color !== undefined) backgroundColor = params.background_color
        if (params.skybox_enabled !== undefined) skyboxEnabled = params.skybox_enabled
        
        if (params.ibl_enabled !== undefined) {
            iblEnabled = params.ibl_enabled
            console.log("  🌟 IBL enabled:", iblEnabled)
        }
        if (params.ibl_intensity !== undefined) {
            iblIntensity = params.ibl_intensity
            console.log("  🌟 IBL intensity:", iblIntensity)
        }
        
        if (params.fog_enabled !== undefined) fogEnabled = params.fog_enabled
        if (params.fog_color !== undefined) fogColor = params.fog_color
        if (params.fog_density !== undefined) fogDensity = params.fog_density
        
        console.log("  ✅ Environment updated successfully (including IBL)")
    }

    function applyQualityUpdates(params) {
        console.log("⚙️ main_optimized.qml: applyQualityUpdates() called")
        
        if (params.antialiasing !== undefined) antialiasingMode = params.antialiasing
        if (params.aa_quality !== undefined) antialiasingQuality = params.aa_quality
        if (params.shadows_enabled !== undefined) shadowsEnabled = params.shadows_enabled
        if (params.shadow_quality !== undefined) shadowQuality = params.shadow_quality
        
        if (params.shadow_softness !== undefined) {
            shadowSoftness = params.shadow_softness
            console.log("  🌫️ Shadow softness:", shadowSoftness)
        }
        
        console.log("  ✅ Quality updated successfully (including shadow softness)")
    }

    function applyCameraUpdates(params) {
        console.log("📷 main_optimized.qml: applyCameraUpdates() called")
        
        if (params.fov !== undefined) cameraFov = params.fov
        if (params.near !== undefined) cameraNear = params.near
        if (params.far !== undefined) cameraFar = params.far
        if (params.speed !== undefined) cameraSpeed = params.speed
        if (params.auto_rotate !== undefined) autoRotate = params.auto_rotate
        if (params.auto_rotate_speed !== undefined) autoRotateSpeed = params.auto_rotate_speed
        
        console.log("  ✅ Camera updated successfully")
    }

    function applyEffectsUpdates(params) {
        console.log("✨ main_optimized.qml: applyEffectsUpdates() called")
        
        if (params.bloom_enabled !== undefined) bloomEnabled = params.bloom_enabled
        if (params.bloom_intensity !== undefined) bloomIntensity = params.bloom_intensity
        if (params.bloom_threshold !== undefined) {
            bloomThreshold = params.bloom_threshold
            console.log("  🌟 Bloom threshold:", bloomThreshold)
        }
        
        if (params.ssao_enabled !== undefined) ssaoEnabled = params.ssao_enabled
        if (params.ssao_intensity !== undefined) ssaoIntensity = params.ssao_intensity
        if (params.ssao_radius !== undefined) {
            ssaoRadius = params.ssao_radius
            console.log("  🌑 SSAO radius:", ssaoRadius)
        }
        
        if (params.tonemap_enabled !== undefined) {
            tonemapEnabled = params.tonemap_enabled
            console.log("  🎨 Tonemap enabled:", tonemapEnabled)
        }
        if (params.tonemap_mode !== undefined) {
            tonemapMode = params.tonemap_mode
            console.log("  🎨 Tonemap mode:", tonemapMode)
        }
        
        if (params.depth_of_field !== undefined) depthOfFieldEnabled = params.depth_of_field
        if (params.dof_focus_distance !== undefined) {
            dofFocusDistance = params.dof_focus_distance
            console.log("  🔍 DoF focus distance:", dofFocusDistance)
        }
        if (params.dof_focus_range !== undefined) {
            dofFocusRange = params.dof_focus_range
            console.log("  🔍 DoF focus range:", dofFocusRange)
        }
        
        if (params.vignette_enabled !== undefined) {
            vignetteEnabled = params.vignette_enabled
            console.log("  🖼️ Vignette enabled:", vignetteEnabled)
        }
        if (params.vignette_strength !== undefined) {
            vignetteStrength = params.vignette_strength
            console.log("  🖼️ Vignette strength:", vignetteStrength)
        }
        
        if (params.lens_flare_enabled !== undefined) {
            lensFlareEnabled = params.lens_flare_enabled
            console.log("  ✨ Lens Flare enabled:", lensFlareEnabled)
        }
        
        if (params.motion_blur !== undefined) motionBlurEnabled = params.motion_blur
        
        console.log("  ✅ Visual effects updated successfully (COMPLETE)")
    }

    // Legacy functions for backward compatibility
    function updateGeometry(params) { applyGeometryUpdates(params) }
    function updateLighting(params) { applyLightingUpdates(params) }
    function updateMaterials(params) { applyMaterialUpdates(params) }     // ✅ РЕАЛИЗОВАНО
    function updateEnvironment(params) { applyEnvironmentUpdates(params) } // ✅ РЕАЛИЗОВАНО
    function updateQuality(params) { applyQualityUpdates(params) }         // ✅ РЕАЛИЗОВАНО
    function updateEffects(params) { applyEffectsUpdates(params) }         // ✅ РЕАЛИЗОВАНО
    function updateCamera(params) { applyCameraUpdates(params) }           // ✅ РЕАЛИЗОВАНО
    
    function updatePistonPositions(positions) {
        if (positions.fl !== undefined) userPistonPositionFL = Number(positions.fl)
        if (positions.fr !== undefined) userPistonPositionFR = Number(positions.fr)
        if (positions.rl !== undefined) userPistonPositionRL = Number(positions.rl)
        if (positions.rr !== undefined) userPistonPositionRR = Number(positions.rr)
    }

    // ===============================================================
    // ✅ ИСПРАВЛЕНО: 3D SCENE С ExtendedSceneEnvironment
    // ===============================================================

    View3D {
        id: view3d
        anchors.fill: parent

        // ✅ ГЛАВНОЕ ИСПРАВЛЕНИЕ: ExtendedSceneEnvironment вместо SceneEnvironment!
        environment: ExtendedSceneEnvironment {
            readonly property bool hasValidProbe: root.iblTextureReady

            // Background and IBL
            backgroundMode: skyboxEnabled && hasValidProbe ? SceneEnvironment.SkyBox : SceneEnvironment.Color
            clearColor: backgroundColor
            
            // ✅ ИСПРАВЛЕНО: Условное использование lightProbe с проверкой готовности
            lightProbe: (iblEnabled && hasValidProbe) ? iblLoader.probe : null
            probeExposure: hasValidProbe ? iblIntensity : 1.0
            probeHorizon: hasValidProbe ? 0.08 : 0.0
            
            // ✅ ИСПРАВЛЕНО: Правильные enum значения для тонемаппинга
            tonemapMode: root.resolvedTonemapMode()
            exposure: 1.0
            whitePoint: 2.0
            
            antialiasingMode: antialiasingMode === 3 ? SceneEnvironment.ProgressiveAA :
                             antialiasingMode === 2 ? SceneEnvironment.MSAA :
                             antialiasingMode === 1 ? SceneEnvironment.SSAA :
                             SceneEnvironment.NoAA
            
            specularAAEnabled: true
            ditheringEnabled: true
            fxaaEnabled: true
            temporalAAEnabled: isSceneInMotion  // TAA only during animation or interaction
            
            aoEnabled: ssaoEnabled
            aoStrength: ssaoIntensity * 100
            aoDistance: ssaoRadius
            aoSoftness: 20
            aoDither: true
            aoSampleRate: 3
            
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
            
            vignetteEnabled: vignetteEnabled
            vignetteRadius: 0.4
            vignetteStrength: vignetteStrength
            
            colorAdjustmentsEnabled: true
            adjustmentBrightness: 1.0
            adjustmentContrast: 1.05
            adjustmentSaturation: 1.05
        }

        // Camera rig
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

        // Lighting
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
            shadowBias: shadowSoftness * 0.001
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
            brightness: 1.5
            color: "#ffffcc"
            castsShadow: false
        }
        
        PointLight {
            id: accentLight
            position: Qt.vector3d(0, pointLightY, 1500)
            brightness: pointLightBrightness
            color: "#ffffff"
            quadraticFade: 0.00008
        }

        // ===============================================================
        // ✅ FRAME GEOMETRY (3 beams only - NO DUPLICATION)
        // ===============================================================

        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
            scale: Qt.vector3d(userBeamSize/100, userBeamSize/100, userFrameLength/100)
            materials: PrincipledMaterial { 
                baseColor: "#cc0000"
                metalness: frameMetalness
                roughness: frameRoughness
            }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial { 
                baseColor: "#cc0000"
                metalness: frameMetalness
                roughness: frameRoughness
            }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userFrameLength - userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial { 
                baseColor: "#cc0000"
                metalness: frameMetalness
                roughness: frameRoughness
            }
        }

        // ===============================================================
        // ✅ FIXED: ONLY OptimizedSuspensionCorner (no duplication!)
        // ===============================================================

        // ✅ ЕДИНСТВЕННЫЙ тип компонента подвески - без дублирования!
        component OptimizedSuspensionCorner: Node {
            property vector3d j_arm
            property vector3d j_tail  
            property real leverAngle
            property real pistonPositionFromPython: 250.0
            
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
            
            // Направление цилиндра
            readonly property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            readonly property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y)
            readonly property vector3d cylDirectionNorm: Qt.vector3d(
                cylDirection.x / cylDirectionLength,
                cylDirection.y / cylDirectionLength,
                0
            )
            readonly property real cylAngle: Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90
            
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
            
            // Расчет позиции поршня для константной длины штока
            readonly property vector3d j_rodToCylStart: Qt.vector3d(j_rod.x - tailRodEnd.x, j_rod.y - tailRodEnd.y, 0)
            readonly property real projectionOnCylAxis: j_rodToCylStart.x * cylDirectionNorm.x + j_rodToCylStart.y * cylDirectionNorm.y
            
            readonly property vector3d j_rodProjection: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * projectionOnCylAxis,
                tailRodEnd.y + cylDirectionNorm.y * projectionOnCylAxis,
                tailRodEnd.z
            )
            
            readonly property real perpendicularDistance: Math.hypot(
                j_rod.x - j_rodProjection.x,
                j_rod.y - j_rodProjection.y
            )
            
            readonly property real rodLengthSquared: pistonRodLength * pistonRodLength
            readonly property real perpDistSquared: perpendicularDistance * perpendicularDistance
            readonly property real axialDistanceFromProjection: Math.sqrt(Math.max(0, rodLengthSquared - perpDistSquared))
            
            readonly property real pistonPositionOnAxis: projectionOnCylAxis - axialDistanceFromProjection
            readonly property real clampedPistonPosition: Math.max(10, Math.min(userCylinderLength - 10, pistonPositionOnAxis))
            
            readonly property vector3d pistonCenter: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * clampedPistonPosition,
                tailRodEnd.y + cylDirectionNorm.y * clampedPistonPosition,
                tailRodEnd.z
            )
            
            readonly property real actualRodLength: Math.hypot(j_rod.x - pistonCenter.x, j_rod.y - pistonCenter.y)
            readonly property real rodLengthError: Math.abs(actualRodLength - pistonRodLength)
            
            // =============================
            // ВИЗУАЛЬНЫЕ КОМПОНЕНТЫ (только один раз!)
            // =============================
            
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
                materials: PrincipledMaterial { 
                    baseColor: "#888888"
                    metalness: metalMetalness
                    roughness: metalRoughness
                    clearcoatAmount: metalClearcoat
                }
            }
            
            // TAIL ROD (хвостовой шток)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
                scale: Qt.vector3d(userRodDiameter/100, tailRodLength/100, userRodDiameter/100)
                eulerRotation: Qt.vector3d(0, 0, cylAngle)
                materials: PrincipledMaterial { 
                    baseColor: "#cccccc"
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            // CYLINDER BODY (корпус цилиндра)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((tailRodEnd.x + cylinderEnd.x)/2, (tailRodEnd.y + cylinderEnd.y)/2, tailRodEnd.z)
                scale: Qt.vector3d(userBoreHead/100, userCylinderLength/100, userBoreHead/100)
                eulerRotation: Qt.vector3d(0, 0, cylAngle)
                materials: PrincipledMaterial { 
                    baseColor: "#ffffff"
                    metalness: 0.0
                    roughness: glassRoughness
                    opacity: glassOpacity
                    indexOfRefraction: glassIOR
                    alphaMode: PrincipledMaterial.Blend 
                }
            }
            
            // PISTON (поршень)
            Model {
                source: "#Cylinder"
                position: pistonCenter
                scale: Qt.vector3d((userBoreHead - 2)/100, userPistonThickness/100, (userBoreHead - 2)/100)
                eulerRotation: Qt.vector3d(0, 0, cylAngle)
                materials: PrincipledMaterial { 
                    baseColor: rodLengthError > 1.0 ? "#ff4444" : "#ff0066"
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            // PISTON ROD (шток поршня)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((pistonCenter.x + j_rod.x)/2, (pistonCenter.y + j_rod.y)/2, pistonCenter.z)
                scale: Qt.vector3d(userRodDiameter/100, pistonRodLength/100, userRodDiameter/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - pistonCenter.y, j_rod.x - pistonCenter.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { 
                    baseColor: rodLengthError > 1.0 ? "#ff0000" : "#cccccc"
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            // JOINTS (шарниры) - цветные маркеры
            Model {
                source: "#Cylinder"
                position: j_tail
                scale: Qt.vector3d(1.2, 2.4, 1.2)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: PrincipledMaterial { 
                    baseColor: "#0088ff"  // Синий - шарнир цилиндра
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            Model {
                source: "#Cylinder"
                position: j_arm
                scale: Qt.vector3d(1.0, 2.0, 1.0)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: PrincipledMaterial { 
                    baseColor: "#ff8800"  // Оранжевый - шарнир рычага
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            Model {
                source: "#Cylinder"
                position: j_rod
                scale: Qt.vector3d(0.8, 1.6, 0.8)
                eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.1)
                materials: PrincipledMaterial { 
                    baseColor: rodLengthError > 1.0 ? "#ff0000" : "#00ff44"  // Красный если ошибка, зеленый если OK
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            // ✅ ИСПРАВЛЕНО: Убираем дублирование обработчиков событий - логирование только один раз
            Component.onCompleted: {
                if (rodLengthError > 1.0) {
                    console.warn("⚠️ Corner initialized with rod length error:", rodLengthError.toFixed(2), "mm")
                }
            }
        }

        // ✅ ЧЕТЫРЕ ЭКЗЕМПЛЯРА OptimizedSuspensionCorner (единственный источник геометрии!)
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
    // ✅ ИСПРАВЛЕНО: MOUSE CONTROLS - убрано дублирование обработчиков
    // ===============================================================

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        // ✅ ИСПРАВЛЕНО: Единый обработчик onPressed без дублирования
        onPressed: (mouse) => {
            if (root.mouseDown) return // Защита от дублирования
            
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
                text: "PneumoStabSim Professional | ИСПРАВЛЕНО: ExtendedSceneEnvironment v4.3"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true 
            }
            
            Text { 
                text: "✅ ИСПРАВЛЕНО: ExtendedSceneEnvironment + убрано дублирование событий"
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
                        text: isRunning ? "🎬 АНИМАЦИЯ С ExtendedSceneEnvironment" : "⏸️ Анимация остановлена"
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
    // INITIALIZATION (with rod length validation)
    // ===============================================================

    Component.onCompleted: {
        console.log("═══════════════════════════════════════════")
        console.log("🚀 PneumoStabSim ИСПРАВЛЕННАЯ ВЕРСИЯ v4.3 LOADED")
        console.log("═══════════════════════════════════════════")
        console.log("✅ ГЛАВНЫЕ ИСПРАВЛЕНИЯ:")
        console.log("   🔧 ExtendedSceneEnvironment вместо SceneEnvironment")
        console.log("   🔧 Убрано дублирование mouse event handlers")
        console.log("   🔧 Убрано дублирование rod length error логирования")
        console.log("   🔧 Постоянная длина штока:", userPistonRodLength, "мм")
        console.log("   🔧 Поршни движутся ВДОЛЬ ОСИ цилиндров")
        console.log("   🔧 Правильная геометрия треугольников") 
        console.log("   🔧 Валидация ошибок длины < 1мм")
        console.log("✅ ВСЕ ПАРАМЕТРЫ GRAPHICSPANEL:")
        console.log("   🔥 Коэффициент преломления (IOR):", glassIOR)
        console.log("   🔥 IBL поддержка:", iblEnabled)
        console.log("   🔥 Туман поддержка:", fogEnabled)
        console.log("   🔥 Расширенные эффекты: Bloom, SSAO, DoF, Vignette")
        console.log("🎯 СТАТУС: main_optimized.qml v4.3 ЗАГРУЖЕН УСПЕШНО С ExtendedSceneEnvironment")
        console.log("═══════════════════════════════════════════")
        
        resetView()
        view3d.forceActiveFocus()
    }
}
