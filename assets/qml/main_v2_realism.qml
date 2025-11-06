import QtQuick
import QtQuick3D
import QtQuick3D.Helpers   // === FIXED: Remove version number for Qt 6.9.3 compatibility
import environment 1.0
import components 1.0
import lighting 1.0

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

    property bool reflectionProbeEnabled: true
    property string reflectionProbeQualitySetting: "veryhigh"
    property string reflectionProbeRefreshMode: "everyframe"
    property string reflectionProbeTimeSlicing: "individualfaces"
    property real reflectionPaddingScene: 0.0

    // --- Environment/quality properties ---
    property color backgroundColor: "#2a2a2a"
    property string backgroundModeSetting: "skybox"
    property bool skyboxEnabled: true
    readonly property bool sceneEnvSupportsTransparent: SceneEnvironment.Transparent !== undefined
    readonly property bool backgroundIsTransparent: backgroundModeSetting === "transparent"
    readonly property bool backgroundUsesSkybox: backgroundModeSetting === "skybox" && skyboxEnabled
    readonly property bool backgroundUsesTransparent: backgroundIsTransparent && sceneEnvSupportsTransparent
    property color effectiveClearColor: {
        var base = Qt.color(backgroundColor)
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

    property alias iblPrimarySource: iblLoader.primarySource
    readonly property Texture iblProbeTexture: iblLoader.probe
    readonly property bool iblProbeReady: iblLoader.ready

    IblProbeLoader {
        id: iblLoader
        visible: false
    }

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
    property real dofBlurAmount: 3.0

    property bool fxaaEnabled: true
    property bool specularAAEnabled: true
    property bool temporalAAEnabled: true
    property real hdrExposure: 1.0
    property real hdrWhitePoint: 2.0

    property bool fogEnabled: false
    property color fogColor: "#d0d8e8"
    property real fogDensity: 0.0008
    property real fogDepthNear: 0.0
    property real fogDepthFar: 20000.0

    property real bloomStrength: 0.8
    property real bloomSecondaryBloom: 0.5
    property bool glowQualityHigh: true
    property bool glowUseBicubic: true
    property real glowHdrMax: 8.0
    property real glowHdrScale: 2.0
    property int glowBlendMode: 0

    property bool lensFlareEnabled: true
    property int lensFlareGhostCount: 3
    property real lensFlareGhostDispersal: 0.6
    property real lensFlareHaloWidth: 0.25
    property real lensFlareBloomBias: 0.35
    property real lensFlareStretchToAspect: 1.0

    property bool vignetteEnabled: true
    property real vignetteRadius: 0.4
    property real vignetteStrength: 0.7
    property real colorAdjustmentBrightness: 1.0
    property real colorAdjustmentContrast: 1.05
    property real colorAdjustmentSaturation: 1.05

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

    readonly property real sceneUnitsPerMeter: 1000.0

    function toScene(value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            return 0
        return numeric
    }

    function metersToScene(value) {
        if (value === undefined || value === null)
            return null
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            return null
        return numeric * sceneUnitsPerMeter
    }

    function _readFirstDefined(object, keys) {
        for (var idx = 0; idx < keys.length; ++idx) {
            var key = keys[idx]
            if (object[key] !== undefined)
                return object[key]
        }
        return undefined
    }

    function resolveIblUrl(path) {
        if (path === undefined || path === null)
            return ""
        var asString = String(path).trim()
        if (!asString)
            return ""
        try {
            return Qt.resolvedUrl(asString)
        } catch (err) {
            console.warn("Realism scene failed to resolve IBL url", asString, err)
            return asString
        }
    }

    function _applyReflectionProbeUpdates(payload) {
        if (!payload)
            return
        if (payload.enabled !== undefined)
            reflectionProbeEnabled = !!payload.enabled
        if (payload.quality !== undefined)
            reflectionProbeQualitySetting = String(payload.quality)
        if (payload.refreshMode !== undefined)
            reflectionProbeRefreshMode = String(payload.refreshMode)
        if (payload.timeSlicing !== undefined)
            reflectionProbeTimeSlicing = String(payload.timeSlicing)
        if (payload.padding !== undefined) {
            var scenePadding = metersToScene(payload.padding)
            if (scenePadding !== null)
                reflectionPaddingScene = Math.max(0, scenePadding)
        }
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
            categories: categories,
            source: "python"
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

        var distanceValue = _readFirstDefined(payload, ["distance", "orbit_distance"])
        var minDistanceValue = _readFirstDefined(payload, ["minDistance", "min_distance"])
        var maxDistanceValue = _readFirstDefined(payload, ["maxDistance", "max_distance"])
        var nearValue = _readFirstDefined(payload, ["near", "clip_near"])
        var farValue = _readFirstDefined(payload, ["far", "clip_far"])
        var yawValue = _readFirstDefined(payload, ["yaw", "orbit_yaw"])
        var pitchValue = _readFirstDefined(payload, ["pitch", "orbit_pitch"])
        var panXValue = _readFirstDefined(payload, ["panX", "pan_x"])
        var panYValue = _readFirstDefined(payload, ["panY", "pan_y"])
        var autoRotateValue = _readFirstDefined(payload, ["autoRotate", "auto_rotate"])
        var autoRotateSpeedValue = _readFirstDefined(payload, ["autoRotateSpeed", "auto_rotate_speed"])
        var fovValue = _readFirstDefined(payload, ["fov", "fieldOfView"])

        var sceneDistance = metersToScene(distanceValue)
        if (sceneDistance !== null)
            cameraDistance = sceneDistance

        var sceneMinDistance = metersToScene(minDistanceValue)
        if (sceneMinDistance !== null)
            minDistance = Math.max(0, sceneMinDistance)

        var sceneMaxDistance = metersToScene(maxDistanceValue)
        if (sceneMaxDistance !== null)
            maxDistance = Math.max(minDistance, sceneMaxDistance)

        var sceneNear = metersToScene(nearValue)
        if (sceneNear !== null)
            cameraNear = Math.max(0.001, sceneNear)

        var sceneFar = metersToScene(farValue)
        if (sceneFar !== null)
            cameraFar = Math.max(cameraNear + 1, sceneFar)

        if (yawValue !== undefined)
            yawDeg = Number(yawValue)
        if (pitchValue !== undefined)
            pitchDeg = Number(pitchValue)

        var scenePanX = metersToScene(panXValue)
        if (scenePanX !== null)
            panX = scenePanX

        var scenePanY = metersToScene(panYValue)
        if (scenePanY !== null)
            panY = scenePanY

        if (autoRotateValue !== undefined)
            autoRotate = !!autoRotateValue
        if (autoRotateSpeedValue !== undefined)
            autoRotateSpeed = Number(autoRotateSpeedValue)
        if (fovValue !== undefined)
            cameraFov = Number(fovValue)
        if (payload.speed !== undefined)
            cameraSpeed = Number(payload.speed)
    }

    function applyEffectsUpdates(params) {
        var payload = _normalizePayload(params)
        if (payload.bloomEnabled !== undefined)
            bloomEnabled = !!payload.bloomEnabled
        if (payload.bloomIntensity !== undefined)
            bloomIntensity = Number(payload.bloomIntensity)
        if (payload.bloomThreshold !== undefined)
            bloomThreshold = Number(payload.bloomThreshold)
        if (payload.bloomStrength !== undefined)
            bloomStrength = Number(payload.bloomStrength)
        if (payload.bloomSecondaryBloom !== undefined)
            bloomSecondaryBloom = Number(payload.bloomSecondaryBloom)
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
        var blurValue = _readFirstDefined(payload, ["dofBlurAmount", "depthOfFieldBlurAmount"])
        if (blurValue !== undefined)
            dofBlurAmount = Number(blurValue)
        if (payload.fogEnabled !== undefined)
            fogEnabled = !!payload.fogEnabled
        if (payload.fogColor !== undefined)
            fogColor = payload.fogColor
        if (payload.fogDensity !== undefined)
            fogDensity = Number(payload.fogDensity)
        if (payload.fogDepthNear !== undefined)
            fogDepthNear = Number(payload.fogDepthNear)
        if (payload.fogDepthFar !== undefined)
            fogDepthFar = Number(payload.fogDepthFar)
        if (payload.fxaaEnabled !== undefined)
            fxaaEnabled = !!payload.fxaaEnabled
        if (payload.specularAAEnabled !== undefined)
            specularAAEnabled = !!payload.specularAAEnabled
        if (payload.temporalAAEnabled !== undefined)
            temporalAAEnabled = !!payload.temporalAAEnabled
        if (payload.exposure !== undefined)
            hdrExposure = Number(payload.exposure)
        if (payload.whitePoint !== undefined)
            hdrWhitePoint = Number(payload.whitePoint)
        if (payload.lensFlareEnabled !== undefined)
            lensFlareEnabled = !!payload.lensFlareEnabled
        if (payload.lensFlareGhostCount !== undefined) {
            var ghostCountValue = Number(payload.lensFlareGhostCount)
            if (!isNaN(ghostCountValue) && isFinite(ghostCountValue))
                lensFlareGhostCount = Math.max(0, Math.round(ghostCountValue))
        }
        if (payload.lensFlareGhostDispersal !== undefined)
            lensFlareGhostDispersal = Number(payload.lensFlareGhostDispersal)
        if (payload.lensFlareHaloWidth !== undefined)
            lensFlareHaloWidth = Number(payload.lensFlareHaloWidth)
        if (payload.lensFlareBloomBias !== undefined)
            lensFlareBloomBias = Number(payload.lensFlareBloomBias)
        if (payload.lensFlareStretchToAspect !== undefined)
            lensFlareStretchToAspect = Number(payload.lensFlareStretchToAspect)
        if (payload.vignetteEnabled !== undefined)
            vignetteEnabled = !!payload.vignetteEnabled
        if (payload.vignetteRadius !== undefined)
            vignetteRadius = Number(payload.vignetteRadius)
        if (payload.vignetteStrength !== undefined)
            vignetteStrength = Number(payload.vignetteStrength)
        if (payload.adjustmentBrightness !== undefined)
            colorAdjustmentBrightness = Number(payload.adjustmentBrightness)
        if (payload.adjustmentContrast !== undefined)
            colorAdjustmentContrast = Number(payload.adjustmentContrast)
        if (payload.adjustmentSaturation !== undefined)
            colorAdjustmentSaturation = Number(payload.adjustmentSaturation)
        if (payload.glowQualityHigh !== undefined)
            glowQualityHigh = !!payload.glowQualityHigh
        if (payload.glowUseBicubic !== undefined)
            glowUseBicubic = !!payload.glowUseBicubic
        if (payload.glowHdrMax !== undefined)
            glowHdrMax = Number(payload.glowHdrMax)
        if (payload.glowHdrScale !== undefined)
            glowHdrScale = Number(payload.glowHdrScale)
        if (payload.glowBlendMode !== undefined)
            glowBlendMode = Number(payload.glowBlendMode)
    }

    function applySimulationUpdates(params) {
        _logUnsupported("simulation", params)
    }

    function applyThreeDUpdates(params) {
        var payload = _normalizePayload(params)
        if (payload.reflectionProbe !== undefined)
            _applyReflectionProbeUpdates(_normalizePayload(payload.reflectionProbe))
        else
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
            if (pl.position_y !== undefined) {
                var pointYScene = metersToScene(pl.position_y)
                if (pointYScene !== null)
                    pointLightY = pointYScene
            }
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
        if (params.exposure !== undefined) hdrExposure = Number(params.exposure)
        if (params.whitePoint !== undefined) hdrWhitePoint = Number(params.whitePoint)
        if (params.white_point !== undefined) hdrWhitePoint = Number(params.white_point)
        if (params.fog_enabled !== undefined) fogEnabled = !!params.fog_enabled
        if (params.fogColor !== undefined) fogColor = params.fogColor
        if (params.fog_color !== undefined) fogColor = params.fog_color
        if (params.fogDensity !== undefined) fogDensity = Number(params.fogDensity)
        if (params.fog_density !== undefined) fogDensity = Number(params.fog_density)
        if (params.fogDepthNear !== undefined) fogDepthNear = Number(params.fogDepthNear)
        if (params.fog_depth_near !== undefined) fogDepthNear = Number(params.fog_depth_near)
        if (params.fogDepthFar !== undefined) fogDepthFar = Number(params.fogDepthFar)
        if (params.fog_depth_far !== undefined) fogDepthFar = Number(params.fog_depth_far)
        if (params.fxaa_enabled !== undefined) fxaaEnabled = !!params.fxaa_enabled
        if (params.specular_aa_enabled !== undefined) specularAAEnabled = !!params.specular_aa_enabled
        if (params.temporal_aa_enabled !== undefined) temporalAAEnabled = !!params.temporal_aa_enabled

        var primarySource = _readFirstDefined(params, [
            "ibl_source",
            "iblSource",
            "ibl_primary",
            "iblPrimary",
            "hdr_source",
            "hdrSource"
        ])
        if (params.ibl && typeof params.ibl === "object") {
            var nestedPrimary = _readFirstDefined(params.ibl, [
                "source",
                "primary",
                "path"
            ])
            if (nestedPrimary !== undefined)
                primarySource = nestedPrimary
        }
        if (primarySource !== undefined)
            iblPrimarySource = resolveIblUrl(primarySource)

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
        var L = Math.max(1, userFrameLength)
        var T = Math.max(1, userTrackWidth)
        var H = Math.max(1, userFrameHeight)
        var margin = marginFactor !== undefined ? marginFactor : 1.15
        var R = 0.5 * Math.sqrt(L*L + T*T + H*H)
        var fov = cameraFov * Math.PI / 180.0
        var dist = (R * margin) / Math.tan(fov * 0.5)
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
        environment: RealismEnvironment {
            id: realismEnvironment
            resolvedBackgroundMode: root.resolvedBackgroundMode()
            sceneClearColor: root.effectiveClearColor
            useSkybox: root.backgroundUsesSkybox && root.iblProbeReady
            useLightProbe: root.iblEnabled && root.iblProbeReady
            hdrTexture: root.iblProbeReady ? root.iblProbeTexture : null
            iblExposure: root.iblIntensity
            tonemapEnabled: root.tonemapActive
            tonemapModeSetting: root.resolveTonemapMode(root.tonemapModeIndex)
            sceneExposure: root.hdrExposure
            sceneWhitePoint: root.hdrWhitePoint
            enableFxaa: root.fxaaEnabled
            specularAntialiasingEnabled: root.specularAAEnabled
            temporalAntialiasingEnabled: root.temporalAAEnabled
            bloomEnabled: root.bloomEnabled
            bloomIntensity: root.bloomIntensity
            bloomThreshold: root.bloomThreshold
            bloomStrength: root.bloomStrength
            bloomSecondaryBloom: root.bloomSecondaryBloom
            glowQualityHighEnabled: root.glowQualityHigh
            glowUseBicubic: root.glowUseBicubic
            glowHdrMaximumValue: root.glowHdrMax
            glowHdrScale: root.glowHdrScale
            glowBlendModeValue: root.glowBlendMode
            ssaoEnabled: root.ssaoEnabled
            ssaoRadius: root.ssaoRadius
            ssaoIntensity: root.ssaoIntensity
            depthOfFieldActive: root.depthOfFieldEnabled
            depthOfFieldFocusDistanceValue: root.dofFocusDistance
            depthOfFieldFocusRangeValue: root.dofFocusRange
            depthOfFieldBlurAmountValue: root.dofBlurAmount
            fogEnabled: root.fogEnabled
            fogColor: root.fogColor
            fogDensity: root.fogDensity
            fogDepthNear: root.fogDepthNear
            fogDepthFar: root.fogDepthFar
            lensFlareActive: root.lensFlareEnabled
            lensFlareGhosts: root.lensFlareGhostCount
            lensFlareGhostDispersalValue: root.lensFlareGhostDispersal
            lensFlareHaloWidthValue: root.lensFlareHaloWidth
            lensFlareBloomBiasValue: root.lensFlareBloomBias
            lensFlareStretchValue: root.lensFlareStretchToAspect
            vignetteActive: root.vignetteEnabled
            vignetteRadiusValue: root.vignetteRadius
            vignetteStrengthValue: root.vignetteStrength
            adjustmentBrightness: root.colorAdjustmentBrightness
            adjustmentContrast: root.colorAdjustmentContrast
            adjustmentSaturation: root.colorAdjustmentSaturation
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
        ReflectionProbeVolume {
            id: probeMain
            pivot: root.pivot
            probeEnabled: root.reflectionProbeEnabled
            trackWidth: toScene(Math.max(1, root.userTrackWidth))
            frameHeight: toScene(Math.max(1, root.userFrameHeight))
            frameLength: toScene(Math.max(1, root.userFrameLength))
            padding: root.reflectionPaddingScene
            qualitySetting: root.reflectionProbeQualitySetting
            refreshModeSetting: root.reflectionProbeRefreshMode
            timeSlicingSetting: root.reflectionProbeTimeSlicing
        }

        // === Lighting setup ===
        RealismLightingRig {
            id: lightingRig
            keyLightAngleX: root.keyLightAngleX
            keyLightAngleY: root.keyLightAngleY
            keyLightBrightness: root.keyLightBrightness
            keyLightColor: root.keyLightColor
            shadowsEnabled: root.shadowsEnabled
            shadowQualityIndex: root.shadowQuality
            shadowSoftness: root.shadowSoftness
            fillLightBrightness: root.fillLightBrightness
            fillLightColor: root.fillLightColor
            pointLightBrightness: root.pointLightBrightness
            pointLightHeight: toScene(root.pointLightY)
            pointLightZOffset: toScene(1.5)
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
            var dx = m.x - lastX
            var dy = m.y - lastY

            if (m.buttons & Qt.LeftButton) {
                // Rotation around pivot (bottom beam center)
                root.yawDeg = (root.yawDeg + dx * 0.35) % 360
                root.pitchDeg = Math.max(-85, Math.min(85, root.pitchDeg - dy * 0.35))
            } else if (m.buttons & Qt.RightButton) {
                // Panning: move camera in rig's local X/Y
                var fovRad = camera.fieldOfView * Math.PI / 180
                var worldPerPixel = (2 * root.cameraDistance * Math.tan(fovRad / 2)) / view3d.height
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
   var frame = params.frame;
        if (frame.heave !== undefined) frameHeave = Number(frame.heave);
  if (frame.roll !== undefined) frameRollRad = Number(frame.roll);
  if (frame.pitch !== undefined) framePitchRad = Number(frame.pitch);
    }
    if (params.leverAngles) {
   var angles = params.leverAngles;
   if (angles.fl !== undefined) flAngleRad = Number(angles.fl);
    if (angles.fr !== undefined) frAngleRad = Number(angles.fr);
  if (angles.rl !== undefined) rlAngleRad = Number(angles.rl);
   if (angles.rr !== undefined) rrAngleRad = Number(angles.rr);
    }
    if (params.pistonPositions) {
  var pist = params.pistonPositions;
        var updated = Object.assign({}, pistonPositions || {});
   if (pist.fl !== undefined) updated.fl = Number(pist.fl);
  if (pist.fr !== undefined) updated.fr = Number(pist.fr);
    if (pist.rl !== undefined) updated.rl = Number(pist.rl);
        if (pist.rr !== undefined) updated.rr = Number(pist.rr);
    pistonPositions = updated;
    }
    if (params.linePressures) {
    var lp = params.linePressures;
  var updatedPressures = Object.assign({}, linePressures || {});
  if (lp.a1 !== undefined) updatedPressures.a1 = Number(lp.a1);
   if (lp.b1 !== undefined) updatedPressures.b1 = Number(lp.b1);
    if (lp.a2 !== undefined) updatedPressures.a2 = Number(lp.a2);
    if (lp.b2 !== undefined) updatedPressures.b2 = Number(lp.b2);
  linePressures = updatedPressures;
    }
    if (params.tankPressure !== undefined) tankPressure = Number(params.tankPressure);
}
}
