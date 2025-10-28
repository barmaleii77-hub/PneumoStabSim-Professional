import QtQuick
import QtQuick3D
import QtQuick3D.Helpers   // === FIXED: Remove version number for Qt 6.9.3 compatibility

Item {
    id: root
    anchors.fill: parent

    signal batchUpdatesApplied(var summary)

    property var pendingPythonUpdates: ({})
    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates || typeof pendingPythonUpdates !== "object") {
            return
        }
        applyBatchedUpdates(pendingPythonUpdates)
    }

    readonly property var _updateHandlers: ({
        "geometry": applyGeometryUpdates,
        "animation": applyAnimationUpdates,
        "lighting": applyLightingUpdates,
        "materials": applyMaterialUpdates,
        "environment": applyEnvironmentUpdates,
        "quality": applyQualityUpdates,
        "camera": applyCameraUpdates,
        "effects": applyEffectsUpdates,
        "simulation": applySimulationUpdates,
        "threeD": applyThreeDUpdates,
        "render": applyRenderSettings
    })

    // --- Camera/control properties with fixed orbit around bottom beam center ---
    property real cameraDistance: 3200
    property real minDistance: 150
    property real maxDistance: 30000
    property real yawDeg: 30            // === CHANGED: Better initial angle
    property real pitchDeg: -10
    property vector3d pivot: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)   // === FIXED: Center of bottom beam
    property real panX: 0               // === ADDED: Pan offset in rig's local X
    property real panY: 0               // === ADDED: Pan offset in rig's local Y
    property bool autoRotate: false
    property real autoRotateSpeed: 0.5
    property real cameraFov: 50.0
    property real cameraNear: 5.0       // === CHANGED: Better near clip
    property real cameraFar: 50000.0
    property real cameraSpeed: 1.0

    // === Lighting properties ===
    property real keyLightBrightness: 2.5
    property string keyLightColor: "#ffffff"
    property real keyLightAngleX: -45
    property real keyLightAngleY: 45
    property real fillLightBrightness: 0.8
    property string fillLightColor: "#f0f0ff"
    property real pointLightBrightness: 1.5
    property real pointLightY: 2000

    // --- Environment/quality properties ---
    property color backgroundColor: "#2a2a2a"
    property string backgroundModeSetting: "skybox"
    property bool skyboxEnabled: true
    readonly property bool sceneEnvSupportsTransparent: SceneEnvironment.Transparent !== undefined
    readonly property bool backgroundIsTransparent: backgroundModeSetting === "transparent"
    readonly property bool backgroundUsesSkybox: backgroundModeSetting === "skybox" && skyboxEnabled
    readonly property bool backgroundUsesTransparent: backgroundIsTransparent && sceneEnvSupportsTransparent
    property color effectiveClearColor: {
        const base = Qt.color(backgroundColor)
        if (backgroundUsesTransparent)
            return Qt.rgba(base.r, base.g, base.b, 0.0)
        if (backgroundIsTransparent)
            return Qt.rgba(base.r, base.g, base.b, 0.0)
        if (backgroundModeSetting === "color")
            return Qt.rgba(base.r, base.g, base.b, 1.0)
        return base
    }
    property bool iblEnabled: true
    property real iblIntensity: 1.3     // === CHANGED: Better exposure

    property int antialiasingMode: 2     // 0 NoAA, 1 SSAA, 2 MSAA
    property int antialiasingQuality: 2  // 0 Low, 1 Medium, 2 High
    property bool shadowsEnabled: true
    property int shadowQuality: 2
    property real shadowSoftness: 0.5

    // --- Effects properties ---
    property bool bloomEnabled: true
    property real bloomThreshold: 1.0
    property real bloomIntensity: 0.6    // === CHANGED: More balanced for filmic
    property bool ssaoEnabled: true
    property real ssaoRadius: 200        // === CHANGED: Scene units for better visibility
    property real ssaoIntensity: 70      // === CHANGED: Proper strength value
    property bool tonemapActive: true
    property int tonemapModeIndex: 3     // 0=None, 1=Linear, 2=Reinhard, 3=Filmic
    readonly property var tonemapModeTable: [
        SceneEnvironment.TonemapModeNone,
        SceneEnvironment.TonemapModeLinear,
        SceneEnvironment.TonemapModeReinhard,
        SceneEnvironment.TonemapModeFilmic
    ]

    function resolveTonemapMode(index) {
        var numericIndex = Number(index)
        if (!Number.isFinite(numericIndex))
            numericIndex = tonemapModeIndex
        numericIndex = Math.max(0, Math.min(tonemapModeTable.length - 1, Math.round(numericIndex)))
        return tonemapModeTable[numericIndex]
    }

    property bool depthOfFieldEnabled: false
    property real dofFocusDistance: 2000
    property real dofFocusRange: 900

    // --- Geometry/animation properties (unchanged) ---
    property real userFrameLength: 3200
    property real userFrameHeight: 650
    property real userBeamSize: 120
    property real userLeverLength: 800
    property real userCylinderLength: 500
    property real userTrackWidth: 1600
    property real userFrameToPivot: 600
    property real userRodPosition: 0.6
    property real userBoreHead: 80
    property real userRodDiameter: 35
    property real userPistonThickness: 25
    property real userPistonRodLength: 200
    property bool isRunning: false
    property real animationTime: 0.0
    property real userAmplitude: 8.0
    property real userFrequency: 1.0
    property real userPhaseGlobal: 0.0
    property real userPhaseFL: 0.0
    property real userPhaseFR: 0.0
    property real userPhaseRL: 0.0
    property real userPhaseRR: 0.0
property real flAngleRad: 0.0
property real frAngleRad: 0.0
property real rlAngleRad: 0.0
property real rrAngleRad: 0.0
property real fl_angle: flAngleRad * 180 / Math.PI
property real fr_angle: frAngleRad * 180 / Math.PI
property real rl_angle: rlAngleRad * 180 / Math.PI
property real rr_angle: rrAngleRad * 180 / Math.PI
property real frameHeave: 0.0
property real frameRollRad: 0.0
property real framePitchRad: 0.0
property real frameRollDeg: frameRollRad * 180 / Math.PI
property real framePitchDeg: framePitchRad * 180 / Math.PI
property var pistonPositions: ({ fl: 0.0, fr: 0.0, rl: 0.0, rr: 0.0 })
property var linePressures: ({})
property real tankPressure: 0.0

    // === HDR probe with fallback ===
    Texture {
        id: hdrProbe
        source: "assets/studio_small_09_2k.hdr"  // === FIXED: Relative path
    }

    // === Smooth camera animations ===
    Behavior on yawDeg         { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on pitchDeg       { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on cameraDistance { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on panX           { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    Behavior on panY           { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }

    function _normalizePayload(payload) {
        if (!payload || typeof payload !== "object")
            return {}
        return payload
    }

    function _logUnsupported(category, payload) {
        console.warn("Realism scene received unsupported update", category, payload)
    }

    function applyBatchedUpdates(updates) {
        var normalized = _normalizePayload(updates)
        var categories = []
        for (var key in normalized) {
            if (!normalized.hasOwnProperty(key))
                continue
            var handler = _updateHandlers[key]
            var payload = normalized[key]
            if (typeof handler === "function") {
                try {
                    handler(payload)
                } catch (err) {
                    console.warn("Realism scene failed to process", key, err)
                }
            } else {
                _logUnsupported(key, payload)
            }
            categories.push(key)
        }
        batchUpdatesApplied({
            timestamp: Date.now(),
            categories: categories
        })
    }

    function applyGeometryUpdates(params) {
        updateGeometry(_normalizePayload(params))
    }

    function applyLightingUpdates(params) {
        updateLighting(_normalizePayload(params))
    }

    function applyMaterialUpdates(params) {
        _logUnsupported("materials", params)
    }

    function applyEnvironmentUpdates(params) {
        updateEnvironment(_normalizePayload(params))
    }

    function applyQualityUpdates(params) {
        updateQuality(_normalizePayload(params))
    }

    function applyCameraUpdates(params) {
        var payload = _normalizePayload(params)
        if (payload.distance !== undefined)
            cameraDistance = Number(payload.distance)
        if (payload.minDistance !== undefined)
            minDistance = Number(payload.minDistance)
        if (payload.maxDistance !== undefined)
            maxDistance = Number(payload.maxDistance)
        if (payload.yaw !== undefined)
            yawDeg = Number(payload.yaw)
        if (payload.pitch !== undefined)
            pitchDeg = Number(payload.pitch)
        if (payload.panX !== undefined)
            panX = Number(payload.panX)
        if (payload.panY !== undefined)
            panY = Number(payload.panY)
        if (payload.autoRotate !== undefined)
            autoRotate = !!payload.autoRotate
        if (payload.autoRotateSpeed !== undefined)
            autoRotateSpeed = Number(payload.autoRotateSpeed)
        if (payload.fov !== undefined)
            cameraFov = Number(payload.fov)
        if (payload.near !== undefined)
            cameraNear = Number(payload.near)
        if (payload.far !== undefined)
            cameraFar = Number(payload.far)
    }

    function applyEffectsUpdates(params) {
        var payload = _normalizePayload(params)
        if (payload.bloomEnabled !== undefined)
            bloomEnabled = !!payload.bloomEnabled
        if (payload.bloomIntensity !== undefined)
            bloomIntensity = Number(payload.bloomIntensity)
        if (payload.bloomThreshold !== undefined)
            bloomThreshold = Number(payload.bloomThreshold)
        if (payload.ssaoEnabled !== undefined)
            ssaoEnabled = !!payload.ssaoEnabled
        if (payload.ssaoRadius !== undefined)
            ssaoRadius = Number(payload.ssaoRadius)
        if (payload.ssaoIntensity !== undefined)
            ssaoIntensity = Number(payload.ssaoIntensity)
        if (payload.tonemapActive !== undefined)
            tonemapActive = !!payload.tonemapActive
        if (payload.tonemapMode !== undefined)
            tonemapModeIndex = Number(payload.tonemapMode)
        if (payload.depthOfFieldEnabled !== undefined)
            depthOfFieldEnabled = !!payload.depthOfFieldEnabled
        if (payload.dofFocusDistance !== undefined)
            dofFocusDistance = Number(payload.dofFocusDistance)
        if (payload.dofFocusRange !== undefined)
            dofFocusRange = Number(payload.dofFocusRange)
    }

    function applySimulationUpdates(params) {
        _logUnsupported("simulation", params)
    }

    function applyThreeDUpdates(params) {
        _logUnsupported("threeD", params)
    }

    function applyRenderSettings(params) {
        var payload = _normalizePayload(params)
        if (payload.environment)
            applyEnvironmentUpdates(payload.environment)
        if (payload.effects)
            applyEffectsUpdates(payload.effects)
        if (payload.quality)
            applyQualityUpdates(payload.quality)
        if (payload.camera)
            applyCameraUpdates(payload.camera)
        if (payload.animation)
            applyAnimationUpdates(payload.animation)
        if (payload.geometry)
            applyGeometryUpdates(payload.geometry)
    }

    // === Python integration functions ===
    function updateGeometry(params) {
        console.log("QML: updateGeometry called with", JSON.stringify(params))

        if (params.frameLength !== undefined) userFrameLength = params.frameLength
        if (params.frameHeight !== undefined) userFrameHeight = params.frameHeight
        if (params.frameBeamSize !== undefined) userBeamSize = params.frameBeamSize
        if (params.leverLength !== undefined) userLeverLength = params.leverLength
        if (params.cylinderBodyLength !== undefined) userCylinderLength = params.cylinderBodyLength
        if (params.trackWidth !== undefined) userTrackWidth = params.trackWidth
        if (params.frameToPivot !== undefined) userFrameToPivot = params.frameToPivot
        if (params.rodPosition !== undefined) userRodPosition = params.rodPosition

        resetView() // Update camera after geometry changes
    }

    function updateLighting(params) {
        console.log("QML: updateLighting called with", JSON.stringify(params))

        if (params.key_light) {
            var kl = params.key_light
            if (kl.brightness !== undefined) keyLightBrightness = kl.brightness
            if (kl.color !== undefined) keyLightColor = kl.color
            if (kl.angle_x !== undefined) keyLightAngleX = kl.angle_x
            if (kl.angle_y !== undefined) keyLightAngleY = kl.angle_y
        }

        if (params.fill_light) {
            var fl = params.fill_light
            if (fl.brightness !== undefined) fillLightBrightness = fl.brightness
            if (fl.color !== undefined) fillLightColor = fl.color
        }

        if (params.point_light) {
            var pl = params.point_light
            if (pl.brightness !== undefined) pointLightBrightness = pl.brightness
            if (pl.position_y !== undefined) pointLightY = pl.position_y
        }
    }

    function _normalizeBackgroundMode(modeValue) {
        if (modeValue === undefined || modeValue === null)
            return backgroundModeSetting
        var text = String(modeValue).trim().toLowerCase()
        if (text === "transparent" || text === "color" || text === "skybox")
            return text
        return backgroundModeSetting
    }

    function updateEnvironment(params) {
        console.log("QML: updateEnvironment called with", JSON.stringify(params))

        if (params.background_color !== undefined) backgroundColor = params.background_color
        if (params.backgroundColor !== undefined) backgroundColor = params.backgroundColor
        if (params.skybox_enabled !== undefined) skyboxEnabled = params.skybox_enabled
        if (params.ibl_enabled !== undefined) iblEnabled = params.ibl_enabled
        if (params.ibl_intensity !== undefined) iblIntensity = params.ibl_intensity
        if (params.background_mode !== undefined)
            backgroundModeSetting = _normalizeBackgroundMode(params.background_mode)
        if (params.backgroundMode !== undefined)
            backgroundModeSetting = _normalizeBackgroundMode(params.backgroundMode)
        if (params.tonemap_enabled !== undefined) tonemapActive = !!params.tonemap_enabled
        if (params.tonemap_active !== undefined) tonemapActive = !!params.tonemap_active
        if (params.tonemap_mode !== undefined) {
            var requestedMode = Number(params.tonemap_mode)
            if (Number.isFinite(requestedMode))
                tonemapModeIndex = Math.max(0, Math.min(tonemapModeTable.length - 1, Math.round(requestedMode)))
        }
    }

    function resolvedBackgroundMode() {
        if (backgroundUsesSkybox)
            return SceneEnvironment.SkyBox
        if (backgroundUsesTransparent)
            return SceneEnvironment.Transparent
        return SceneEnvironment.Color
    }

    function updateQuality(params) {
        console.log("QML: updateQuality called with", JSON.stringify(params))

        if (params.antialiasing !== undefined) antialiasingMode = params.antialiasing
        if (params.aa_quality !== undefined) antialiasingQuality = params.aa_quality
        if (params.shadows_enabled !== undefined) shadowsEnabled = params.shadows_enabled
        if (params.shadow_quality !== undefined) shadowQuality = params.shadow_quality
        if (params.shadow_softness !== undefined) shadowSoftness = params.shadow_softness
    }

    // === Fixed camera functions - pivot always at bottom beam center ===
    function computePivot() {
        return Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
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

    function resetView() {
        pivot = computePivot()
        yawDeg = 30       // Front-right view
        pitchDeg = -10
        panX = 0          // Reset pan
        panY = 0
        autoFitFrame()
    }

    View3D {
        id: view3d
        anchors.fill: parent

        // === FIXED: Proper ExtendedSceneEnvironment implementation for Qt 6.9.3 ===
        environment: ExtendedSceneEnvironment {
            // Background and IBL
            backgroundMode: root.resolvedBackgroundMode()
            clearColor: root.effectiveClearColor
            skyBoxCubeMap: root.backgroundUsesSkybox ? hdrProbe : null
            lightProbe: root.iblEnabled ? hdrProbe : null
            probeExposure: root.iblIntensity
            probeHorizon: 0.08

            // Tone mapping and quality (Fixed enum names)
            tonemapMode: root.tonemapActive
                          ? root.resolveTonemapMode(root.tonemapModeIndex)
                          : SceneEnvironment.TonemapModeNone
            exposure: 1.0
            whitePoint: 2.0
            ditheringEnabled: true
            fxaaEnabled: true                         // Additional smoothing from Extended
            specularAAEnabled: true                   // Specular antialiasing (SceneEnv)
            temporalAAEnabled: true                   // TAA for animations
            antialiasingMode: SceneEnvironment.ProgressiveAA  // Better than MSAA for most cases

            // SSAO (part of SceneEnvironment, works with Extended)
            aoEnabled: root.ssaoEnabled
            aoSampleRate: 3
            aoStrength: root.ssaoIntensity
            aoDistance: root.ssaoRadius
            aoSoftness: 20
            aoDither: true

            // OIT for proper transparency sorting (Qt 6.9+)
            oitMethod: SceneEnvironment.OITWeightedBlended

            // Bloom/Glow (Extended properties)
            glowEnabled: root.bloomEnabled
            glowIntensity: root.bloomIntensity
            glowBloom: 0.5
            glowStrength: 0.8
            glowQualityHigh: true
            glowUseBicubicUpscale: true
            glowHDRMinimumValue: root.bloomThreshold
            glowHDRMaximumValue: 8.0
            glowHDRScale: 2.0
            glowBlendMode: 0  // Add

            // Lens flare (Extended)
            lensFlareEnabled: true
            lensFlareGhostCount: 3
            lensFlareGhostDispersal: 0.6
            lensFlareHaloWidth: 0.25
            lensFlareBloomBias: 0.35
            lensFlareStretchToAspect: 1.0

            // Depth of Field (Extended)
            depthOfFieldEnabled: root.depthOfFieldEnabled
            depthOfFieldFocusDistance: root.dofFocusDistance
            depthOfFieldFocusRange: root.dofFocusRange
            depthOfFieldBlurAmount: 3.0

            // Vignette and color correction
            vignetteEnabled: true
            vignetteRadius: 0.4
            vignetteStrength: 0.7

            colorAdjustmentsEnabled: true
            adjustmentBrightness: 1.0
            adjustmentContrast: 1.05
            adjustmentSaturation: 1.05
        }

        // === FIXED: Orbital camera rig - rotation strictly around bottom beam center ===
        Node {
            id: cameraRig
            position: root.pivot                      // Rotation axis at bottom beam center
            eulerRotation: Qt.vector3d(root.pitchDeg, root.yawDeg, 0)

            Node {                                    // Pan node in rig's local system
                id: panNode
                position: Qt.vector3d(root.panX, root.panY, 0)

                PerspectiveCamera {
                    id: camera
                    position: Qt.vector3d(0, 0, root.cameraDistance)   // Zoom only affects Z
                    fieldOfView: root.cameraFov
                    clipNear: root.cameraNear
                    clipFar: root.cameraFar
                }
            }
        }

        // === ReflectionProbe for local reflections ===
        ReflectionProbe {
            id: probeMain
            position: root.pivot
            boxSize: Qt.vector3d(toScene(root.userTrackWidth), toScene(root.userFrameHeight), toScene(root.userFrameLength))
            parallaxCorrection: true
            quality: ReflectionProbe.VeryHigh
            refreshMode: ReflectionProbe.EveryFrame
            timeSlicing: ReflectionProbe.IndividualFaces
        }

        // === Lighting setup ===
        DirectionalLight {
            id: keyLight
            eulerRotation.x: root.keyLightAngleX
            eulerRotation.y: root.keyLightAngleY
            brightness: root.keyLightBrightness
            color: root.keyLightColor
            castsShadow: root.shadowsEnabled
            shadowMapQuality: [Light.ShadowMapQualityLow, Light.ShadowMapQualityMedium, Light.ShadowMapQualityHigh][root.shadowQuality]
            shadowFactor: 75
            shadowBias: root.shadowSoftness * 0.001
        }

        DirectionalLight {
            id: fillLight
            eulerRotation.x: -60
            eulerRotation.y: 135
            brightness: root.fillLightBrightness
            color: root.fillLightColor
            castsShadow: false
        }

        PointLight {
            id: pointLight
            position: Qt.vector3d(0, toScene(root.pointLightY), toScene(1.5))
            brightness: root.pointLightBrightness
            color: "#ffffff"
            quadraticFade: 0.00008
        }

        // === Suspension geometry (basic for testing) ===

        // === ИСПРАВЛЕННАЯ ГЕОМЕТРИЯ: Правильные координаты и масштабирование ===

        // Main frame (центральная балка на земле)
        Model {
            id: mainFrame
            position: Qt.vector3d(0, toScene(root.userBeamSize)/2, toScene(root.userFrameLength)/2)  // ИСПРАВЛЕНО: По центру

            source: "#Cube"
            scale: Qt.vector3d(toScene(root.userTrackWidth), toScene(root.userBeamSize), toScene(root.userFrameLength))

            materials: [
                PrincipledMaterial {
                    baseColor: "#4a4a4a"
                    metalness: 0.8
                    roughness: 0.3
                }
            ]
        }

        // ИСПРАВЛЕННАЯ ПОДВЕСКА: Правильные позиции и масштабы

        // Front left lever (передний левый рычаг)
        Model {
            id: frontLeftLever
            position: Qt.vector3d(-toScene(root.userTrackWidth)/2, toScene(root.userBeamSize), toScene(root.userFrameToPivot))

            source: "#Cube"
            scale: Qt.vector3d(toScene(root.userLeverLength), 8, 8)  // ИСПРАВЛЕНО: Правильный масштаб
            eulerRotation: Qt.vector3d(0, 0, Qt.radiansToDegrees(leverAngleRadFor("fl")))     // ИСПРАВЛЕНО: Правильная ось вращения

            materials: [
                PrincipledMaterial {
                    baseColor: "#ff6b35"
                    metalness: 0.9
                    roughness: 0.2
                }
            ]
        }

        // Front right lever (передний правый рычаг)
        Model {
            id: frontRightLever
            position: Qt.vector3d(toScene(root.userTrackWidth)/2, toScene(root.userBeamSize), toScene(root.userFrameToPivot))

            source: "#Cube"
            scale: Qt.vector3d(toScene(root.userLeverLength), 8, 8)  // ИСПРАВЛЕНО: Правильный масштаб
            eulerRotation: Qt.vector3d(0, 0, Qt.radiansToDegrees(leverAngleRadFor("fr")))     // ИСПРАВЛЕНО: Правильная ось вращения

            materials: [
                PrincipledMaterial {
                    baseColor: "#ff6b35"
                    metalness: 0.9
                    roughness: 0.2
                }
            ]
        }

        // Rear left lever (задний левый рычаг)
        Model {
            id: rearLeftLever
            position: Qt.vector3d(-toScene(root.userTrackWidth)/2, toScene(root.userBeamSize), toScene(root.userFrameLength - root.userFrameToPivot))

            source: "#Cube"
            scale: Qt.vector3d(toScene(root.userLeverLength), 8, 8)  // ИСПРАВЛЕНО: Правильный масштаб
            eulerRotation: Qt.vector3d(0, 0, Qt.radiansToDegrees(leverAngleRadFor("rl")))     // ИСПРАВЛЕНО: Правильная ось вращения

            materials: [
                PrincipledMaterial {
                    baseColor: "#35ff6b"
                    metalness: 0.9
                    roughness: 0.2
                }
            ]
        }

        // Rear right lever (задний правый рычаг)
        Model {
            id: rearRightLever
            position: Qt.vector3d(toScene(root.userTrackWidth)/2, toScene(root.userBeamSize), toScene(root.userFrameLength - root.userFrameToPivot))

            source: "#Cube"
            scale: Qt.vector3d(toScene(root.userLeverLength), 8, 8)  // ИСПРАВЛЕНО: Правильный масштаб
            eulerRotation: Qt.vector3d(0, 0, Qt.radiansToDegrees(leverAngleRadFor("rr")))     // ИСПРАВЛЕНО: Правильная ось вращения

            materials: [
                PrincipledMaterial {
                    baseColor: "#35ff6b"
                    metalness: 0.9
                    roughness: 0.2
                }
            ]
        }

        // Pneumatic cylinder (пневматический цилиндр)
        Model {
            id: cylinderFL
            position: Qt.vector3d(-toScene(root.userTrackWidth)/4, toScene(root.userBeamSize + root.userFrameHeight/2), toScene(root.userFrameToPivot))

            source: "#Cylinder"
            scale: Qt.vector3d(toScene(root.userBoreHead), toScene(root.userCylinderLength), toScene(root.userBoreHead))  // ИСПРАВЛЕНО: Правильные размеры

            materials: [
                PrincipledMaterial {
                    baseColor: "#6b35ff"
                    metalness: 0.95
                    roughness: 0.1
                    clearcoatAmount: 0.8
                }
            ]
        }
    }

    // === FIXED: Mouse controls - proper orbit/pan/zoom around fixed pivot ===
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        property real lastX: 0
        property real lastY: 0

        onPressed: (m) => { lastX = m.x; lastY = m.y }

        onPositionChanged: (m) => {
            const dx = m.x - lastX
            const dy = m.y - lastY

            if (m.buttons & Qt.LeftButton) {
                // Rotation around pivot (bottom beam center)
                root.yawDeg = (root.yawDeg + dx * 0.35) % 360
                root.pitchDeg = Math.max(-85, Math.min(85, root.pitchDeg - dy * 0.35))
            } else if (m.buttons & Qt.RightButton) {
                // Panning: move camera in rig's local X/Y
                const fovRad = camera.fieldOfView * Math.PI / 180
                const worldPerPixel = (2 * root.cameraDistance * Math.tan(fovRad / 2)) / view3d.height
                root.panX -= dx * worldPerPixel
                root.panY += dy * worldPerPixel
            }
            lastX = m.x; lastY = m.y
        }

        onWheel: (w) => {
            root.cameraDistance = Math.max(root.minDistance,
                                     Math.min(root.maxDistance,
                                              root.cameraDistance * Math.exp(-w.angleDelta.y * 0.0016)))
        }

        onDoubleClicked: () => resetView()
    }

    // === Animation timers ===
    Timer { running: isRunning; interval: 16; repeat: true; onTriggered: animationTime += 0.016 }
    Timer { running: autoRotate; interval: 16; repeat: true; onTriggered: yawDeg = (yawDeg + autoRotateSpeed * 0.016 * 10) % 360 }

    Component.onCompleted: {
        console.log("=== PneumoStabSim REALISM v2 (Qt 6.9.3 Fixed) LOADED ===")
        resetView()
        view3d.forceActiveFocus()
    }

    function applyAnimationUpdates(params) {
    if (!params) return;
    if (params.isRunning !== undefined) isRunning = !!params.isRunning;
    if (params.simulationTime !== undefined) animationTime = Number(params.simulationTime);
    if (params.amplitude !== undefined) userAmplitude = Number(params.amplitude);
    if (params.frequency !== undefined) userFrequency = Number(params.frequency);
    if (params.phase_global !== undefined) userPhaseGlobal = Number(params.phase_global);
    if (params.phase_fl !== undefined) userPhaseFL = Number(params.phase_fl);
    if (params.phase_fr !== undefined) userPhaseFR = Number(params.phase_fr);
if (params.phase_rl !== undefined) userPhaseRL = Number(params.phase_rl);
    if (params.phase_rr !== undefined) userPhaseRR = Number(params.phase_rr);
    if (params.frame) {
   const frame = params.frame;
        if (frame.heave !== undefined) frameHeave = Number(frame.heave);
  if (frame.roll !== undefined) frameRollRad = Number(frame.roll);
  if (frame.pitch !== undefined) framePitchRad = Number(frame.pitch);
    }
    if (params.leverAngles) {
   const angles = params.leverAngles;
   if (angles.fl !== undefined) flAngleRad = Number(angles.fl);
    if (angles.fr !== undefined) frAngleRad = Number(angles.fr);
  if (angles.rl !== undefined) rlAngleRad = Number(angles.rl);
   if (angles.rr !== undefined) rrAngleRad = Number(angles.rr);
    }
    if (params.pistonPositions) {
  const pist = params.pistonPositions;
        const updated = Object.assign({}, pistonPositions || {});
   if (pist.fl !== undefined) updated.fl = Number(pist.fl);
  if (pist.fr !== undefined) updated.fr = Number(pist.fr);
    if (pist.rl !== undefined) updated.rl = Number(pist.rl);
        if (pist.rr !== undefined) updated.rr = Number(pist.rr);
    pistonPositions = updated;
    }
    if (params.linePressures) {
    const lp = params.linePressures;
  const updatedPressures = Object.assign({}, linePressures || {});
  if (lp.a1 !== undefined) updatedPressures.a1 = Number(lp.a1);
   if (lp.b1 !== undefined) updatedPressures.b1 = Number(lp.b1);
    if (lp.a2 !== undefined) updatedPressures.a2 = Number(lp.a2);
    if (lp.b2 !== undefined) updatedPressures.b2 = Number(lp.b2);
  linePressures = updatedPressures;
    }
    if (params.tankPressure !== undefined) tankPressure = Number(params.tankPressure);
}
}
