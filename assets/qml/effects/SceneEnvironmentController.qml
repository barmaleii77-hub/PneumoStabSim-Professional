import QtQuick 6.10
import QtQuick.Window
import QtQuick3D 6.10
import QtQuick3D.Helpers 6.10 // ✅ CRITICAL: Required for ExtendedSceneEnvironment
import "." // Local helpers (QualityPresets)

/*
 * SceneEnvironmentController - Полное управление ExtendedSceneEnvironment
 * Все эффекты, качество, IBL, туман в ОДНОМ компоненте
 */
ExtendedSceneEnvironment {
 id: root

    readonly property var initialSceneDefaults: typeof initialSceneSettings !== "undefined" ? initialSceneSettings : null
    readonly property var initialAnimationDefaults: typeof initialAnimationSettings !== "undefined" ? initialAnimationSettings : null
    readonly property var initialGeometryDefaults: typeof initialGeometrySettings !== "undefined" ? initialGeometrySettings : null
    readonly property var contextMaterialsDefaults: typeof materialsDefaults !== "undefined" ? materialsDefaults : (initialSceneDefaults && typeof initialSceneDefaults === "object" && initialSceneDefaults.materials !== undefined ? initialSceneDefaults.materials : (initialSceneDefaults && typeof initialSceneDefaults === "object" && initialSceneDefaults.graphics && typeof initialSceneDefaults.graphics === "object" ? initialSceneDefaults.graphics.materials : null))
    readonly property var contextEnvironmentDefaults: {
        var source = initialSceneDefaults
        if (source && typeof source === "object") {
            if (source.environment && typeof source.environment === "object" && !Array.isArray(source.environment))
                return source.environment
            if (source.graphics && typeof source.graphics === "object" && source.graphics.environment && typeof source.graphics.environment === "object")
                return source.graphics.environment
        }
        return null
    }
    readonly property var contextQualityDefaults: {
        var source = initialSceneDefaults
        if (source && typeof source === "object") {
            if (source.quality && typeof source.quality === "object" && !Array.isArray(source.quality))
                return source.quality
            if (source.graphics && typeof source.graphics === "object" && source.graphics.quality && typeof source.graphics.quality === "object")
                return source.graphics.quality
        }
        return null
    }
    readonly property var contextEffectsDefaults: {
        var source = initialSceneDefaults
        if (source && typeof source === "object") {
            if (source.effects && typeof source.effects === "object" && !Array.isArray(source.effects))
                return source.effects
            if (source.graphics && typeof source.graphics === "object" && source.graphics.effects && typeof source.graphics.effects === "object")
                return source.graphics.effects
        }
        return null
    }
    readonly property var contextLightingDefaults: typeof lightingAccess !== "undefined" ? lightingAccess : (initialSceneDefaults && typeof initialSceneDefaults === "object" && initialSceneDefaults.lighting !== undefined ? initialSceneDefaults.lighting : (initialSceneDefaults && typeof initialSceneDefaults === "object" && initialSceneDefaults.graphics && typeof initialSceneDefaults.graphics === "object" ? initialSceneDefaults.graphics.lighting : null))

    QualityPresets {
        id: qualityProfiles
    }

    // ===============================================================
    // QUALITY PRESET MANAGEMENT
    // ===============================================================

    readonly property var availableQualityPresets: qualityProfiles.availablePresets
    property string qualityPreset: qualityProfiles.defaultKey
    property string activeQualityPreset: qualityProfiles.defaultKey
    property bool _applyingQualityPreset: false

    onQualityPresetChanged: {
        if (_applyingQualityPreset)
            return
        if (!applyQualityPresetInternal(qualityPreset)) {
            var fallback = qualityProfiles.fallbackKey()
            if (fallback && fallback !== qualityPreset)
                applyQualityPresetInternal(fallback)
        }
    }

 // ===============================================================
 // BACKGROUND & IBL
 // ===============================================================

    property bool iblBackgroundEnabled: environmentBoolDefault("iblBackgroundEnabled", "ibl_background_enabled", false)
    property bool iblLightingEnabled: environmentBoolDefault("iblLightingEnabled", "ibl_lighting_enabled", false)
    property bool iblMasterEnabled: environmentBoolDefault("iblMasterEnabled", "ibl_master_enabled", iblLightingEnabled || iblBackgroundEnabled)
    property color backgroundColor: environmentStringDefault("backgroundColor", "background_color", "#1f242c")
    property string backgroundModeKey: environmentStringDefault("backgroundMode", "background_mode", "skybox")
    property bool skyboxToggleFlag: environmentBoolDefault("skyboxEnabled", "skybox_enabled", true)
    readonly property bool backgroundIsTransparent: backgroundModeForKey(backgroundModeKey) === SceneEnvironment.Transparent
    property color resolvedClearColor: {
        var base = backgroundColor
        if (backgroundIsTransparent)
            return Qt.rgba(base.r, base.g, base.b, 0.0)
        if (backgroundModeForKey(backgroundModeKey) === SceneEnvironment.Color)
            return Qt.rgba(base.r, base.g, base.b, 1.0)
        return base
    }
    property var iblProbe: null
    property real iblIntensity: environmentNumberDefault("iblIntensity", "ibl_intensity", 1.0)
    property real skyboxBrightnessValue: environmentNumberDefault(
            "skyboxBrightness",
            "skybox_brightness",
            environmentNumberDefault("probeBrightness", "probe_brightness", 1.0)
        )
    property alias probeBrightnessValue: root.skyboxBrightnessValue
    property real probeHorizonValue: environmentNumberDefault("probeHorizon", "probe_horizon", 0.0)
    property real iblRotationPitchDeg: environmentNumberDefault("iblRotationPitchDeg", "ibl_offset_x", 0.0)
    property real iblRotationDeg: environmentNumberDefault("iblRotationDeg", "ibl_rotation", 0.0)
    property real iblRotationRollDeg: environmentNumberDefault("iblRotationRollDeg", "ibl_offset_y", 0.0)
    property bool iblBindToCamera: environmentBoolDefault("iblBindToCamera", "ibl_bind_to_camera", false)
    property real skyboxBlurValue: environmentNumberDefault("skyboxBlur", "skybox_blur", 0.0)

 /**
 * Python SceneBridge instance injected via context property.
 */
 property var sceneBridge: null

    function _syncSkyboxBackground() {
        var targetMode = backgroundModeForKey(backgroundModeKey)
        var wantsSkybox = targetMode === SceneEnvironment.SkyBox
        if (!wantsSkybox) {
            if (iblBackgroundEnabled)
                iblBackgroundEnabled = false
            return
        }
        var enableBackground = skyboxToggleFlag && iblMasterEnabled
        if (iblBackgroundEnabled !== enableBackground)
            iblBackgroundEnabled = enableBackground
    }

    onBackgroundModeKeyChanged: _syncSkyboxBackground()
    onSkyboxToggleFlagChanged: _syncSkyboxBackground()
    onIblMasterEnabledChanged: _syncSkyboxBackground()

    backgroundMode: {
        var targetMode = backgroundModeForKey(backgroundModeKey)
        if (targetMode === SceneEnvironment.SkyBox)
            return (iblBackgroundEnabled && iblProbe) ? SceneEnvironment.SkyBox : SceneEnvironment.Color
        return targetMode
    }
    clearColor: resolvedClearColor
    skyBoxCubeMap: (iblBackgroundEnabled && iblProbe) ? iblProbe : null
    lightProbe: (iblLightingEnabled && iblProbe) ? iblProbe : null
    probeExposure: skyboxBrightnessValue
    probeOrientation: Qt.vector3d(iblRotationPitchDeg, iblRotationDeg, iblRotationRollDeg)
    probeHorizon: probeHorizonValue

 // ===============================================================
 // ANTIALIASING
 // ===============================================================

 property string aaPrimaryMode: "ssaa"
 property string aaQualityLevel: "high"
 property string aaPostMode: "taa"
 property bool taaEnabled: true
 property real taaStrength:0.4
 property bool taaMotionAdaptive: true
 property bool fxaaEnabled: false
 property bool specularAAEnabled: false
 property bool cameraIsMoving: false

    antialiasingMode: {
        if (aaPrimaryMode === "ssaa")
            return SceneEnvironment.SSAA
        if (aaPrimaryMode === "msaa")
            return SceneEnvironment.MSAA
        if (aaPrimaryMode === "progressive")
            return SceneEnvironment.ProgressiveAA
        return SceneEnvironment.NoAA
    }

    // qmllint disable missing-property
    antialiasingQuality: {
        if (aaQualityLevel === "high" && typeof SceneEnvironment.AntialiasingQualityHigh !== "undefined")
            return SceneEnvironment.AntialiasingQualityHigh
        if (aaQualityLevel === "medium" && typeof SceneEnvironment.AntialiasingQualityMedium !== "undefined")
            return SceneEnvironment.AntialiasingQualityMedium
        if (aaQualityLevel === "low" && typeof SceneEnvironment.AntialiasingQualityLow !== "undefined")
            return SceneEnvironment.AntialiasingQualityLow
        if (typeof SceneEnvironment.AntialiasingQualityMedium !== "undefined")
            return SceneEnvironment.AntialiasingQualityMedium
        if (typeof SceneEnvironment.AntialiasingQualityHigh !== "undefined")
            return SceneEnvironment.AntialiasingQualityHigh
        if (typeof SceneEnvironment.AntialiasingQualityLow !== "undefined")
            return SceneEnvironment.AntialiasingQualityLow
        return SceneEnvironment.NoAA
    }
    // qmllint enable missing-property

 // ✅ ИСПРАВЛЕНО: fxaaEnabled и specularAAEnabled уже установлены выше
 temporalAAEnabled: (aaPostMode === "taa" && taaEnabled && (!taaMotionAdaptive || cameraIsMoving))
 temporalAAStrength: taaStrength
    onTemporalAAEnabledChanged: _updateBufferRequirements()

 // ===============================================================
 // DITHERING (Qt6.10+)
 // ===============================================================

 property bool ditheringEnabled: true
 property bool canUseDithering: false
 property real sceneScaleFactor:1.0

    // Camera parameters required by custom fog shaders
    property real cameraClipNear: 0.1
    property real cameraClipFar: 10000.0
    property real cameraFieldOfView: 60.0
    property real cameraAspectRatio: 1.0

    function qtVersionAtLeast(requiredMajor, requiredMinor) {
        var versionString = "";
        if (Qt.application && Qt.application.version !== undefined)
            versionString = String(Qt.application.version);
        if (!versionString)
            return false;
        var parts = versionString.split(".");
        if (parts.length < 2)
            return false;
        var major = Number(parts[0]);
        var minor = Number(parts[1]);
        if (!isFinite(major) || !isFinite(minor))
            return false;
        if (major > requiredMajor)
            return true;
        if (major < requiredMajor)
            return false;
        return minor >= requiredMinor;
    }

    function toSceneLength(value) {
        var numeric = Number(value)
        if (!isFinite(numeric))
            return 0.0
        var scale = Number(sceneScaleFactor)
        if (!isFinite(scale) || scale <= 0)
            return numeric
        return numeric * scale
    }

    function valueFromKeys(params, primaryKey, secondaryKey) {
        if (!params)
            return undefined
        if (primaryKey && params.hasOwnProperty(primaryKey))
            return params[primaryKey]
        if (secondaryKey && params.hasOwnProperty(secondaryKey))
            return params[secondaryKey]
        return undefined
    }

    function boolFromKeys(params, primaryKey, secondaryKey) {
        var raw = valueFromKeys(params, primaryKey, secondaryKey)
        if (raw === undefined)
            return undefined
        if (typeof raw === "boolean")
            return raw
        if (typeof raw === "number")
            return raw !== 0
        if (typeof raw === "string") {
            var lowered = raw.trim().toLowerCase()
            if (lowered === "true" || lowered === "1" || lowered === "yes" || lowered === "on")
                return true
            if (lowered === "false" || lowered === "0" || lowered === "no" || lowered === "off")
                return false
        }
        return !!raw
    }

    function numberFromKeys(params, primaryKey, secondaryKey) {
        var raw = valueFromKeys(params, primaryKey, secondaryKey)
        if (raw === undefined)
            return undefined
        var numeric = Number(raw)
        return isFinite(numeric) ? numeric : undefined
    }

    function stringFromKeys(params, primaryKey, secondaryKey) {
        var raw = valueFromKeys(params, primaryKey, secondaryKey)
        if (raw === undefined)
            return undefined
        return String(raw)
    }

    function environmentBoolDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEnvironmentDefaults)
            return fallback
        var value = boolFromKeys(root.contextEnvironmentDefaults, primaryKey, secondaryKey)
        return value === undefined ? fallback : value
    }

    function environmentNumberDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEnvironmentDefaults)
            return fallback
        var value = numberFromKeys(root.contextEnvironmentDefaults, primaryKey, secondaryKey)
        return value === undefined ? fallback : value
    }

    function environmentStringDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEnvironmentDefaults)
            return fallback
        var value = stringFromKeys(root.contextEnvironmentDefaults, primaryKey, secondaryKey)
        return value === undefined ? fallback : value
    }

    function _cloneContextPayload(payload) {
        if (!payload || typeof payload !== "object")
            return null
        try {
            return JSON.parse(JSON.stringify(payload))
        } catch (error) {
            console.warn("SceneEnvironmentController: failed to clone payload", error)
        }
        return payload
    }

    function _qualityContextPayload() {
        if (!root.contextQualityDefaults || typeof root.contextQualityDefaults !== "object")
            return null
        var source = root.contextQualityDefaults
        var payload = {}
        if (source.antialiasing && typeof source.antialiasing === "object") {
            if (source.antialiasing.primary !== undefined)
                payload.aaPrimaryMode = source.antialiasing.primary
            if (source.antialiasing.quality !== undefined)
                payload.aaQualityLevel = source.antialiasing.quality
            if (source.antialiasing.post !== undefined)
                payload.aaPostMode = source.antialiasing.post
        }
        if (source.taa_enabled !== undefined)
            payload.taaEnabled = source.taa_enabled
        if (source.taa_strength !== undefined)
            payload.taaStrength = source.taa_strength
        if (source.taa_motion_adaptive !== undefined)
            payload.taaMotionAdaptive = source.taa_motion_adaptive
        if (source.fxaa_enabled !== undefined)
            payload.fxaaEnabled = source.fxaa_enabled
        if (source.specular_aa !== undefined)
            payload.specularAAEnabled = source.specular_aa
        if (source.dithering !== undefined)
            payload.ditheringEnabled = source.dithering
        if (source.oit !== undefined)
            payload.oitMode = source.oit
        return payload
    }

    function _applyInitialContextDefaults() {
        var environmentPayload = _cloneContextPayload(root.contextEnvironmentDefaults)
        if (environmentPayload && Object.keys(environmentPayload).length)
            root.applyEnvironmentPayload(environmentPayload)

        var qualityPayload = _qualityContextPayload()
        if (qualityPayload && Object.keys(qualityPayload).length)
            root.applyQualityPayload(qualityPayload)

        var effectsPayload = _cloneContextPayload(root.contextEffectsDefaults)
        if (effectsPayload && Object.keys(effectsPayload).length)
            root.applyEffectsPayload(effectsPayload)
    }

    function backgroundModeForKey(key) {
        var normalized = String(key || "skybox").trim().toLowerCase()
        if (normalized === "color")
            return SceneEnvironment.Color
        if (normalized === "transparent")
            return (SceneEnvironment["Transparent"] !== undefined)
                    ? SceneEnvironment["Transparent"]
                    : SceneEnvironment.Color
        return SceneEnvironment.SkyBox
    }

    function sceneEnvironmentEnum(name, fallbackName) {
        if (SceneEnvironment && SceneEnvironment[name] !== undefined)
            return SceneEnvironment[name]
        if (fallbackName && SceneEnvironment && SceneEnvironment[fallbackName] !== undefined)
            return SceneEnvironment[fallbackName]
        return undefined
    }

    function _applySceneBridgeState() {
        if (!root.sceneBridge)
            return

        if (root.sceneBridge.environment && Object.keys(root.sceneBridge.environment).length)
            root._applyEnvironmentPayload(root.sceneBridge.environment)

        if (root.sceneBridge.quality && Object.keys(root.sceneBridge.quality).length)
            root._applyQualityPayload(root.sceneBridge.quality)

        if (root.sceneBridge.effects && Object.keys(root.sceneBridge.effects).length)
            root._applyEffectsPayload(root.sceneBridge.effects)
    }

    function _applyEnvironmentPayload(payload) {
        root.applyEnvironmentPayload(payload)
    }

    function _applyQualityPayload(payload) {
        root.applyQualityPayload(payload)
    }

    function _applyEffectsPayload(payload) {
        root.applyEffectsPayload(payload)
    }

    function _logFogEvent(level, message) {
        var normalizedLevel = String(level || "info").toLowerCase()
        var normalizedMessage = ""
        if (message !== undefined && message !== null)
            normalizedMessage = String(message)
        if (!normalizedMessage.length)
            normalizedMessage = qsTr("Fog effect fallback active")

        if (normalizedLevel === "error") {
            console.error("❌ SceneEnvironmentController:", normalizedMessage)
        } else if (normalizedLevel === "warn" || normalizedLevel === "warning") {
            console.warn("⚠️ SceneEnvironmentController:", normalizedMessage)
        } else {
            console.log("ℹ️ SceneEnvironmentController:", normalizedMessage)
        }

        if (root.sceneBridge && typeof root.sceneBridge.logGraphicsEvent === "function") {
            try {
                root.sceneBridge.logGraphicsEvent("fog", normalizedLevel, normalizedMessage)
            } catch (error) {
                console.debug("SceneEnvironmentController: failed to forward fog log", error)
            }
        }
    }

    onSceneBridgeChanged: root._applySceneBridgeState()

    Connections {
        target: root.sceneBridge
        enabled: !!root.sceneBridge

        function onEnvironmentChanged(payload) {
            if (payload)
                root._applyEnvironmentPayload(payload)
        }

        function onQualityChanged(payload) {
            if (payload)
                root._applyQualityPayload(payload)
        }

        function onEffectsChanged(payload) {
            if (payload)
                root._applyEffectsPayload(payload)
        }
    }

    Component.onCompleted: {
        root._applyInitialContextDefaults()
        root.canUseDithering = qtVersionAtLeast(6,10)
        if (canUseDithering) {
            root.ditheringEnabled = Qt.binding(function() { return ditheringEnabled })
        }
        console.log("✅ SceneEnvironmentController loaded (dithering "
                    + (root.canUseDithering ? "enabled" : "disabled") + ")")
        var depthPropertyAvailable = _hasEnvironmentProperty("depthTextureEnabled")
        var velocityPropertyAvailable = _hasEnvironmentProperty("velocityTextureEnabled")
        if (!depthPropertyAvailable)
            console.warn("⚠️ SceneEnvironmentController: ExtendedSceneEnvironment.depthTextureEnabled property is unavailable; depth buffer requests will be skipped")
        if (!velocityPropertyAvailable)
            console.warn("⚠️ SceneEnvironmentController: ExtendedSceneEnvironment.velocityTextureEnabled property is unavailable; velocity buffer requests will be skipped")
        root._applySceneBridgeState()
        applyQualityPresetInternal(qualityPreset)
        _syncSkyboxBackground()
        Qt.callLater(_updateBufferRequirements)
    }

    function applyEnvironmentPayload(params) {
        if (!params)
            return

    var bgColor = stringFromKeys(params, "backgroundColor", "background_color")
    if (bgColor !== undefined)
        backgroundColor = bgColor
    if (params.clearColor)
        backgroundColor = params.clearColor

    if (params.background && params.background.color)
        backgroundColor = params.background.color

    var modeValue = stringFromKeys(params, "backgroundMode", "background_mode")
    if (modeValue !== undefined)
        backgroundModeKey = modeValue

    var skyboxFlag = boolFromKeys(params, "skyboxEnabled", "skybox_enabled")
    var backgroundFlag = boolFromKeys(params, "iblBackgroundEnabled", "ibl_background_enabled")
    if (backgroundFlag !== undefined)
        skyboxFlag = backgroundFlag
    if (skyboxFlag !== undefined)
        skyboxToggleFlag = !!skyboxFlag

    var resolvedSkybox = !!skyboxToggleFlag
    if (skyboxFlag !== undefined)
        resolvedSkybox = !!skyboxFlag

    var iblEnabledFlag = boolFromKeys(params, "iblEnabled", "ibl_enabled")
    var lightingFlag = boolFromKeys(params, "iblLightingEnabled", "ibl_lighting_enabled")

    var resolvedLighting = !!iblLightingEnabled
    if (iblEnabledFlag !== undefined)
        resolvedLighting = !!iblEnabledFlag
    if (lightingFlag !== undefined)
        resolvedLighting = !!lightingFlag

    iblLightingEnabled = resolvedLighting
    iblMasterEnabled = resolvedLighting || resolvedSkybox

    _syncSkyboxBackground()

    var directSkyboxBrightnessProvided = valueFromKeys(
        params,
        "skyboxBrightness",
        "skybox_brightness"
    ) !== undefined
    var directProbeBrightnessProvided = valueFromKeys(
        params,
        "probeBrightness",
        "probe_brightness"
    ) !== undefined
    var nestedSkyboxBrightnessProvided = false
    var nestedProbeBrightnessProvided = false
    if (params.ibl && typeof params.ibl === "object") {
        nestedSkyboxBrightnessProvided = valueFromKeys(
            params.ibl,
            "skyboxBrightness",
            "skybox_brightness"
        ) !== undefined
        nestedProbeBrightnessProvided = valueFromKeys(
            params.ibl,
            "probeBrightness",
            "probe_brightness"
        ) !== undefined
    }
    var shouldMirrorIntensity = !(
        directSkyboxBrightnessProvided ||
        directProbeBrightnessProvided ||
        nestedSkyboxBrightnessProvided ||
        nestedProbeBrightnessProvided
    )

    var intensityValue = numberFromKeys(params, "iblIntensity", "ibl_intensity")
    if (intensityValue !== undefined) {
        iblIntensity = intensityValue
        if (shouldMirrorIntensity)
            skyboxBrightnessValue = intensityValue
    }

    var skyboxBrightness = numberFromKeys(
        params,
        "skyboxBrightness",
        "skybox_brightness"
    )
    if (skyboxBrightness === undefined)
        skyboxBrightness = numberFromKeys(params, "probeBrightness", "probe_brightness")
    if (skyboxBrightness !== undefined)
        skyboxBrightnessValue = skyboxBrightness

    var probeHorizon = numberFromKeys(params, "probeHorizon", "probe_horizon")
    if (probeHorizon !== undefined)
        probeHorizonValue = probeHorizon

    var rotationYaw = numberFromKeys(params, "iblRotationDeg", "ibl_rotation")
    if (rotationYaw !== undefined)
        iblRotationDeg = rotationYaw

    var rotationPitch = numberFromKeys(params, "iblRotationPitchDeg", "ibl_offset_x")
    if (rotationPitch !== undefined)
        iblRotationPitchDeg = rotationPitch

    var rotationRoll = numberFromKeys(params, "iblRotationRollDeg", "ibl_offset_y")
    if (rotationRoll !== undefined)
        iblRotationRollDeg = rotationRoll

    var bindFlag = boolFromKeys(params, "iblBindToCamera", "ibl_bind_to_camera")
    if (bindFlag !== undefined)
        iblBindToCamera = bindFlag

    var blurValue = numberFromKeys(params, "skyboxBlur", "skybox_blur")
    if (blurValue !== undefined)
        skyboxBlurValue = blurValue

    if (params.ibl) {
        var ibl = params.ibl
        var nestedEnabled = boolFromKeys(ibl, "enabled", "enabled")
        if (nestedEnabled !== undefined) {
            iblBackgroundEnabled = nestedEnabled
            iblLightingEnabled = nestedEnabled
        }
        var nestedBackground = boolFromKeys(ibl, "backgroundEnabled", "background_enabled")
        if (nestedBackground !== undefined)
            iblBackgroundEnabled = nestedBackground
        var nestedLighting = boolFromKeys(ibl, "lightingEnabled", "lighting_enabled")
        if (nestedLighting !== undefined)
            iblLightingEnabled = nestedLighting
        var nestedIntensity = numberFromKeys(ibl, "intensity", "intensity")
        if (nestedIntensity !== undefined) {
            iblIntensity = nestedIntensity
            if (shouldMirrorIntensity)
                skyboxBrightnessValue = nestedIntensity
        }
        var nestedSkyboxBrightness = numberFromKeys(
            ibl,
            "skyboxBrightness",
            "skybox_brightness"
        )
        if (nestedSkyboxBrightness === undefined)
            nestedSkyboxBrightness = numberFromKeys(
                ibl,
                "probeBrightness",
                "probe_brightness"
            )
        if (nestedSkyboxBrightness !== undefined)
            skyboxBrightnessValue = nestedSkyboxBrightness
        var nestedHorizon = numberFromKeys(ibl, "probeHorizon", "probe_horizon")
        if (nestedHorizon !== undefined)
            probeHorizonValue = nestedHorizon
        var nestedRotation = numberFromKeys(ibl, "rotation", "rotation")
        if (nestedRotation !== undefined)
            iblRotationDeg = nestedRotation
        var nestedPitch = numberFromKeys(ibl, "rotationX", "rotation_x")
        if (nestedPitch !== undefined)
            iblRotationPitchDeg = nestedPitch
        var nestedRoll = numberFromKeys(ibl, "rotationZ", "rotation_z")
        if (nestedRoll !== undefined)
            iblRotationRollDeg = nestedRoll
        var nestedBind = boolFromKeys(ibl, "bindToCamera", "bind_to_camera")
        if (nestedBind !== undefined)
            iblBindToCamera = nestedBind
    }

    var tonemapEnabledKey = boolFromKeys(params, "tonemapEnabled", "tonemap_enabled")
    if (tonemapEnabledKey !== undefined)
        setTonemapEnabledFlag(tonemapEnabledKey)
    var tonemapActiveKey = boolFromKeys(params, "tonemapActive", "tonemap_active")
    if (tonemapActiveKey !== undefined)
        setTonemapEnabledFlag(tonemapActiveKey)
    var tonemapModeKey = stringFromKeys(params, "tonemapModeName", "tonemap_mode")
    if (tonemapModeKey !== undefined)
        tonemapModeName = tonemapModeKey
    var tonemapExposureKey = numberFromKeys(params, "tonemapExposure", "tonemap_exposure")
    if (tonemapExposureKey !== undefined)
        tonemapExposure = tonemapExposureKey
    var tonemapWhitePointKey = numberFromKeys(params, "tonemapWhitePoint", "tonemap_white_point")
    if (tonemapWhitePointKey !== undefined)
        tonemapWhitePoint = tonemapWhitePointKey

    if (params.tonemap) {
        var tonemap = params.tonemap
        if (tonemap.enabled !== undefined)
            setTonemapEnabledFlag(tonemap.enabled)
        if (tonemap.mode)
            tonemapModeName = String(tonemap.mode)
        if (tonemap.exposure !== undefined)
            tonemapExposure = Number(tonemap.exposure)
        if (tonemap.white_point !== undefined)
            tonemapWhitePoint = Number(tonemap.white_point)
    }

    var fogEnabledValue = boolFromKeys(params, "fogEnabled", "fog_enabled")
    if (fogEnabledValue !== undefined)
        fogEnabled = fogEnabledValue
    var fogColorValue = valueFromKeys(params, "fogColor", "fog_color")
    if (fogColorValue !== undefined)
        fogColor = fogColorValue
    var fogDensityValue = numberFromKeys(params, "fogDensity", "fog_density")
    if (fogDensityValue !== undefined)
        fogDensity = fogDensityValue
    var fogNearValue = numberFromKeys(params, "fogNear", "fog_near")
    if (fogNearValue !== undefined && isFinite(fogNearValue))
        fogNear = toSceneLength(fogNearValue)
    var fogFarValue = numberFromKeys(params, "fogFar", "fog_far")
    if (fogFarValue !== undefined && isFinite(fogFarValue))
        fogFar = toSceneLength(fogFarValue)
    var fogHeightFlag = boolFromKeys(params, "fogHeightEnabled", "fog_height_enabled")
    if (fogHeightFlag !== undefined)
        fogHeightEnabled = !!fogHeightFlag
    var fogLeastValue = numberFromKeys(params, "fogLeastIntenseY", "fog_least_intense_y")
    if (fogLeastValue !== undefined && isFinite(fogLeastValue))
        fogLeastIntenseY = toSceneLength(fogLeastValue)
    var fogMostValue = numberFromKeys(params, "fogMostIntenseY", "fog_most_intense_y")
    if (fogMostValue !== undefined && isFinite(fogMostValue))
        fogMostIntenseY = toSceneLength(fogMostValue)
    var fogHeightCurveValue = numberFromKeys(params, "fogHeightCurve", "fog_height_curve")
    if (fogHeightCurveValue !== undefined && isFinite(fogHeightCurveValue))
        fogHeightCurve = fogHeightCurveValue
    var fogTransmitFlag = boolFromKeys(params, "fogTransmitEnabled", "fog_transmit_enabled")
    if (fogTransmitFlag !== undefined)
        fogTransmitEnabled = !!fogTransmitFlag
    var fogTransmitCurveValue = numberFromKeys(params, "fogTransmitCurve", "fog_transmit_curve")
    if (fogTransmitCurveValue !== undefined && isFinite(fogTransmitCurveValue))
        fogTransmitCurve = fogTransmitCurveValue

    if (params.fog) {
        var fog = params.fog
        if (fog.enabled !== undefined)
            fogEnabled = !!fog.enabled
        if (fog.color)
            fogColor = fog.color
        if (fog.near !== undefined) {
            var fogNestedNear = Number(fog.near)
            if (isFinite(fogNestedNear))
                fogNear = toSceneLength(fogNestedNear)
        }
        if (fog.far !== undefined) {
            var fogNestedFar = Number(fog.far)
            if (isFinite(fogNestedFar))
                fogFar = toSceneLength(fogNestedFar)
        }
        if (fog.density !== undefined)
            fogDensity = Number(fog.density)
        if (fog.height_enabled !== undefined)
            fogHeightEnabled = !!fog.height_enabled
        if (fog.least_intense_y !== undefined) {
            var fogLeastNested = Number(fog.least_intense_y)
            if (isFinite(fogLeastNested))
                fogLeastIntenseY = toSceneLength(fogLeastNested)
        }
        if (fog.most_intense_y !== undefined) {
            var fogMostNested = Number(fog.most_intense_y)
            if (isFinite(fogMostNested))
                fogMostIntenseY = toSceneLength(fogMostNested)
        }
        if (fog.height_curve !== undefined) {
            var fogHeightCurveNested = Number(fog.height_curve)
            if (isFinite(fogHeightCurveNested))
                fogHeightCurve = fogHeightCurveNested
        }
        if (fog.transmit_enabled !== undefined)
            fogTransmitEnabled = !!fog.transmit_enabled
        if (fog.transmit_curve !== undefined) {
            var fogTransmitCurveNested = Number(fog.transmit_curve)
            if (isFinite(fogTransmitCurveNested))
                fogTransmitCurve = fogTransmitCurveNested
        }
    }

    var aoEnabledValue = boolFromKeys(params, "ssaoEnabled", "ao_enabled")
    if (aoEnabledValue !== undefined)
        ssaoEnabled = aoEnabledValue

    var aoRadiusValue = numberFromKeys(params, "ssaoRadius", "ao_radius")
    if (aoRadiusValue !== undefined && isFinite(aoRadiusValue))
        ssaoRadius = Math.max(0.0001, toSceneLength(aoRadiusValue))

    var aoIntensityValue = numberFromKeys(params, "ssaoIntensity", "ao_strength")
    if (aoIntensityValue !== undefined)
        ssaoIntensity = aoIntensityValue

    var aoSoftnessValue = numberFromKeys(params, "ssaoSoftness", "ao_softness")
    if (aoSoftnessValue !== undefined)
        ssaoSoftness = aoSoftnessValue

    var aoDitherValue = boolFromKeys(params, "ssaoDither", "ao_dither")
    if (aoDitherValue !== undefined)
        ssaoDither = aoDitherValue

    var aoSampleRateValue = numberFromKeys(params, "ssaoSampleRate", "ao_sample_rate")
    if (aoSampleRateValue !== undefined) {
        var roundedRate = Math.max(1, Math.round(aoSampleRateValue))
        ssaoSampleRate = roundedRate
    }

    if (params.ssao) {
        var ssao = params.ssao
        if (ssao.enabled !== undefined)
            ssaoEnabled = !!ssao.enabled
        if (ssao.radius !== undefined) {
            var nestedRadius = Number(ssao.radius)
            if (isFinite(nestedRadius))
                ssaoRadius = Math.max(0.0001, toSceneLength(nestedRadius))
        }
        if (ssao.intensity !== undefined)
            ssaoIntensity = Number(ssao.intensity)
        if (ssao.softness !== undefined)
            ssaoSoftness = Number(ssao.softness)
        if (ssao.dither !== undefined)
            ssaoDither = !!ssao.dither
        if (ssao.sample_rate !== undefined) {
            var nestedRate = Number(ssao.sample_rate)
            if (isFinite(nestedRate))
                ssaoSampleRate = Math.max(1, Math.round(nestedRate))
        }
    }

    if (params.ambient_occlusion && typeof params.ambient_occlusion === "object") {
        var ambientOcclusion = params.ambient_occlusion
        if (ambientOcclusion.enabled !== undefined)
            ssaoEnabled = !!ambientOcclusion.enabled
        if (ambientOcclusion.strength !== undefined) {
            var ambientStrength = Number(ambientOcclusion.strength)
            if (isFinite(ambientStrength))
                ssaoIntensity = ambientStrength
        }
        if (ambientOcclusion.radius !== undefined) {
            var ambientRadius = Number(ambientOcclusion.radius)
            if (isFinite(ambientRadius))
                ssaoRadius = Math.max(0.0001, toSceneLength(ambientRadius))
        }
        if (ambientOcclusion.samples !== undefined) {
            var ambientSamples = Number(ambientOcclusion.samples)
            if (isFinite(ambientSamples))
                ssaoSampleRate = Math.max(1, Math.round(ambientSamples))
        }
    }

    if (params.depthOfFieldEnabled !== undefined)
        internalDepthOfFieldEnabled = !!params.depthOfFieldEnabled
    if (params.dofFocusDistance !== undefined) {
        var dofDistance = Number(params.dofFocusDistance)
        if (isFinite(dofDistance))
            dofFocusDistance = toSceneLength(dofDistance)
    }
    if (params.dofFocusRange !== undefined) {
        var dofRange = Number(params.dofFocusRange)
        if (isFinite(dofRange))
            dofFocusRange = toSceneLength(dofRange)
    }
    if (params.dofBlurAmount !== undefined) {
        var blurAmount = Number(params.dofBlurAmount)
        if (isFinite(blurAmount))
            dofBlurAmount = Math.max(0.0, blurAmount)
    }

    if (params.depthOfField) {
        var dof = params.depthOfField
        if (dof.enabled !== undefined)
            internalDepthOfFieldEnabled = !!dof.enabled
        if (dof.focus_distance !== undefined) {
            var dofNestedDistance = Number(dof.focus_distance)
            if (isFinite(dofNestedDistance))
                dofFocusDistance = toSceneLength(dofNestedDistance)
        }
        if (dof.focus_range !== undefined) {
            var dofNestedRange = Number(dof.focus_range)
            if (isFinite(dofNestedRange))
                dofFocusRange = toSceneLength(dofNestedRange)
        }
        if (dof.blur_amount !== undefined) {
            var dofNestedBlur = Number(dof.blur_amount)
            if (isFinite(dofNestedBlur))
                dofBlurAmount = Math.max(0.0, dofNestedBlur)
        }
        if (dof.auto_focus !== undefined)
            depthOfFieldAutoFocus = !!dof.auto_focus
    }

 if (params.vignetteEnabled !== undefined)
 internalVignetteEnabled = !!params.vignetteEnabled
 if (params.vignetteStrength !== undefined)
 internalVignetteStrength = Number(params.vignetteStrength)

 if (params.vignette) {
 var vignette = params.vignette
 if (vignette.enabled !== undefined)
 internalVignetteEnabled = !!vignette.enabled
 if (vignette.strength !== undefined)
 internalVignetteStrength = Number(vignette.strength)
 }

 if (params.oitMode)
 oitMode = String(params.oitMode)
 if (params.ditheringEnabled !== undefined) {
 var dith = !!params.ditheringEnabled
 if (canUseDithering)
 root.ditheringEnabled = dith
 }
 }

    function applyQualityPayload(params) {
        if (!params)
            return

        var presetValue = stringFromKeys(params, "qualityPreset", "preset")
        if (presetValue !== undefined && presetValue !== "")
            applyQualityPresetInternal(presetValue)

        if (params.aaPrimaryMode)
            aaPrimaryMode = String(params.aaPrimaryMode)
        if (params.aaQualityLevel)
            aaQualityLevel = String(params.aaQualityLevel)
        if (params.aaPostMode)
            aaPostMode = String(params.aaPostMode)
        if (params.taaEnabled !== undefined)
            taaEnabled = !!params.taaEnabled
        if (params.taaStrength !== undefined)
            taaStrength = Number(params.taaStrength)
        if (params.taaMotionAdaptive !== undefined)
            taaMotionAdaptive = !!params.taaMotionAdaptive
        if (params.fxaaEnabled !== undefined)
            fxaaEnabled = !!params.fxaaEnabled
        if (params.specularAAEnabled !== undefined)
            specularAAEnabled = !!params.specularAAEnabled
        if (params.ditheringEnabled !== undefined) {
            var dithQ = !!params.ditheringEnabled
            if (canUseDithering)
                root.ditheringEnabled = dithQ
        }
    }

function applyEffectsPayload(params) {
if (!params)
return

    var bloomEnabledValue = boolFromKeys(params, "bloomEnabled", "bloom_enabled")
    if (bloomEnabledValue !== undefined)
        bloomEnabled = bloomEnabledValue
    var bloomIntensityValue = numberFromKeys(params, "bloomIntensity", "bloom_intensity")
    if (bloomIntensityValue !== undefined)
        bloomIntensity = bloomIntensityValue
    var bloomThresholdValue = numberFromKeys(params, "bloomThreshold", "bloom_threshold")
    if (bloomThresholdValue !== undefined)
        bloomThreshold = bloomThresholdValue
    var bloomSpreadValue = numberFromKeys(params, "bloomSpread", "bloom_spread")
    if (bloomSpreadValue !== undefined)
        bloomSpread = bloomSpreadValue
    var bloomStrengthValue = numberFromKeys(params, "bloomGlowStrength", "bloom_glow_strength")
    if (bloomStrengthValue !== undefined)
        bloomGlowStrength = bloomStrengthValue
    var bloomHdrMaxValue = numberFromKeys(params, "bloomHdrMax", "bloom_hdr_max")
    if (bloomHdrMaxValue !== undefined)
        bloomHdrMaximum = bloomHdrMaxValue
    var bloomHdrScaleValue = numberFromKeys(params, "bloomHdrScale", "bloom_hdr_scale")
    if (bloomHdrScaleValue !== undefined)
        bloomHdrScale = bloomHdrScaleValue
    var bloomQualityValue = boolFromKeys(params, "bloomQualityHigh", "bloom_quality_high")
    if (bloomQualityValue !== undefined)
        bloomQualityHigh = bloomQualityValue
    var bloomBicubicValue = boolFromKeys(params, "bloomBicubicUpscale", "bloom_bicubic_upscale")
    if (bloomBicubicValue !== undefined)
        bloomUseBicubicUpscale = bloomBicubicValue

    var tonemapEnabledValue = boolFromKeys(params, "tonemapEnabled", "tonemap_enabled")
    if (tonemapEnabledValue !== undefined)
        setTonemapEnabledFlag(tonemapEnabledValue)
    var tonemapModeValue = stringFromKeys(params, "tonemapModeName", "tonemap_mode")
    if (tonemapModeValue !== undefined)
        tonemapModeName = tonemapModeValue
    var tonemapExposureValue = numberFromKeys(params, "tonemapExposure", "tonemap_exposure")
    if (tonemapExposureValue !== undefined)
        tonemapExposure = tonemapExposureValue
    var tonemapWhitePointValue = numberFromKeys(params, "tonemapWhitePoint", "tonemap_white_point")
    if (tonemapWhitePointValue !== undefined)
        tonemapWhitePoint = tonemapWhitePointValue

    var dofEnabledValue = boolFromKeys(params, "depthOfFieldEnabled", "depth_of_field")
    if (dofEnabledValue !== undefined)
        internalDepthOfFieldEnabled = dofEnabledValue
    var dofFocusValue = numberFromKeys(params, "dofFocusDistance", "dof_focus_distance")
    if (dofFocusValue !== undefined && isFinite(dofFocusValue))
        dofFocusDistance = toSceneLength(dofFocusValue)
    var dofRangeValue = numberFromKeys(params, "dofFocusRange", "dof_focus_range")
    if (dofRangeValue !== undefined && isFinite(dofRangeValue))
        dofFocusRange = toSceneLength(dofRangeValue)
    var dofBlurValue = numberFromKeys(params, "dofBlurAmount", "dof_blur")
    if (dofBlurValue !== undefined && isFinite(dofBlurValue))
        dofBlurAmount = Math.max(0.0, dofBlurValue)

    var dofAutoFocusValue = boolFromKeys(params, "dofAutoFocus", "dof_auto_focus")
    if (dofAutoFocusValue !== undefined)
        depthOfFieldAutoFocus = dofAutoFocusValue

    var vignetteEnabledValue = boolFromKeys(params, "vignetteEnabled", "vignette")
    if (vignetteEnabledValue !== undefined)
        internalVignetteEnabled = vignetteEnabledValue
    var vignetteStrengthValue = numberFromKeys(params, "vignetteStrength", "vignette_strength")
    if (vignetteStrengthValue !== undefined)
        internalVignetteStrength = vignetteStrengthValue
    var vignetteRadiusUpdate = numberFromKeys(params, "vignetteRadius", "vignette_radius")
    if (vignetteRadiusUpdate !== undefined)
        vignetteRadiusValue = vignetteRadiusUpdate

    var lensFlareEnabledValue = boolFromKeys(params, "lensFlareEnabled", "lens_flare")
    if (lensFlareEnabledValue !== undefined)
        internalLensFlareEnabled = lensFlareEnabledValue
    var lensGhostCount = numberFromKeys(params, "lensFlareGhostCount", "lens_flare_ghost_count")
    if (lensGhostCount !== undefined)
        lensFlareGhostCountValue = Math.max(0, Math.round(lensGhostCount))
    var lensGhostDispersal = numberFromKeys(params, "lensFlareGhostDispersal", "lens_flare_ghost_dispersal")
    if (lensGhostDispersal !== undefined)
        lensFlareGhostDispersalValue = lensGhostDispersal
    var lensHaloWidth = numberFromKeys(params, "lensFlareHaloWidth", "lens_flare_halo_width")
    if (lensHaloWidth !== undefined)
        lensFlareHaloWidthValue = lensHaloWidth
    var lensBloomBias = numberFromKeys(params, "lensFlareBloomBias", "lens_flare_bloom_bias")
    if (lensBloomBias !== undefined)
        lensFlareBloomBiasValue = lensBloomBias
    var lensStretch = numberFromKeys(params, "lensFlareStretchToAspect", "lens_flare_stretch_to_aspect")
    if (lensStretch !== undefined)
        lensFlareStretchValue = lensStretch
    else {
        var lensStretchBool = boolFromKeys(params, "lensFlareStretchToAspect", "lens_flare_stretch_to_aspect")
        if (lensStretchBool !== undefined)
            lensFlareStretchValue = lensStretchBool ? 1.0 : 0.0
    }

    var brightnessAdjust = numberFromKeys(params, "adjustmentBrightness", "adjustment_brightness")
    if (brightnessAdjust !== undefined)
        adjustmentBrightnessValue = brightnessAdjust
    var contrastAdjust = numberFromKeys(params, "adjustmentContrast", "adjustment_contrast")
    if (contrastAdjust !== undefined)
        adjustmentContrastValue = contrastAdjust
    var saturationAdjust = numberFromKeys(params, "adjustmentSaturation", "adjustment_saturation")
    if (saturationAdjust !== undefined)
        adjustmentSaturationValue = saturationAdjust

    var adjustmentsMagnitude = Math.abs(adjustmentBrightnessValue) + Math.abs(adjustmentContrastValue) + Math.abs(adjustmentSaturationValue)
    colorAdjustmentsActive = adjustmentsMagnitude > 0.0001
}

 // ===============================================================
 // FOG (Qt6.10+)
 // ===============================================================

 property bool fogEnabled: false
 property color fogColor: "#808080"
 property real fogDensity:0.1
 property real fogNear:1200.0
 property real fogFar:12000.0
 property bool fogHeightEnabled: false
 property real fogLeastIntenseY:0.0
 property real fogMostIntenseY:3.0
 property real fogHeightCurve:1.0
 property bool fogTransmitEnabled: true
    property real fogTransmitCurve:1.0

    property bool fogCompilationErrorActive: false
    property bool _fogAutoDisabled: false
    property string _fogLastFallbackReason: ""

    // Дополнительные эффекты (например, постобработка View3D)
    property list<Effect> externalEffects: []
    property bool depthTextureSupportActive: false
    property bool velocityTextureSupportActive: false
    property string _depthTexturePropertyName: ""
    property string _velocityTexturePropertyName: ""
    property bool _depthTextureWarningLogged: false
    property bool _velocityTextureWarningLogged: false
    readonly property var _depthTexturePropertyCandidates: [
            "depthTextureEnabled"
        ]
    readonly property var _velocityTexturePropertyCandidates: [
            "velocityTextureEnabled"
        ]

    function _hasEnvironmentProperty(propertyName) {
        if (!propertyName)
            return false

        try {
            return propertyName in root
        } catch (error) {
            console.debug("SceneEnvironmentController: property presence check failed", propertyName, error)
        }
        return false
    }

    function _setEnvironmentProperty(propertyName, value) {
        if (!propertyName)
            return false

        if (!_hasEnvironmentProperty(propertyName))
            return false

        try {
            if (root[propertyName] === value)
                return true
        } catch (error) {
            console.debug("SceneEnvironmentController: property read failed", propertyName, error)
        }

        try {
            root[propertyName] = value
            if (root[propertyName] === value)
                return true
        } catch (error) {
            console.debug("SceneEnvironmentController: direct assignment failed", propertyName, error)
        }

        // qmllint disable missing-property
        try {
            if (typeof root.setProperty === "function" && root.setProperty(propertyName, value))
                return true
        } catch (error) {
            console.debug("SceneEnvironmentController: setProperty fallback failed", propertyName, error)
        }
        // qmllint enable missing-property

        return false
    }

    function _setEnvironmentPropertyCandidates(propertyNames, value) {
        if (!propertyNames)
            return ""

        var list = propertyNames
        if (!Array.isArray(propertyNames))
            list = [propertyNames]

        for (var i = 0; i < list.length; ++i) {
            var propertyName = list[i]
            if (!propertyName)
                continue
            if (_setEnvironmentProperty(propertyName, value))
                return propertyName
        }
        return ""
    }

    function _logBufferToggle(prefix, enabled, propertyName) {
        var suffix = propertyName && propertyName.length ? " (" + propertyName + ")" : ""
        var message
        if (prefix === "Depth")
            message = enabled ? qsTr("Depth texture support enabled") : qsTr("Depth texture support disabled")
        else
            message = enabled ? qsTr("Velocity texture support enabled") : qsTr("Velocity texture support disabled")
        if (suffix.length)
            console.log("SceneEnvironmentController:", message + suffix)
        else
            console.log("SceneEnvironmentController:", message)
    }

    function _effectFlagValue(effect, propertyName) {
        if (!effect || !propertyName)
            return undefined

        try {
            if (propertyName in effect)
                return effect[propertyName]
        } catch (error) {
        }

        return undefined
    }

    function _effectIsOperational(effect, availabilityGuards) {
        if (!effect)
            return false

        var enabledValue = _effectFlagValue(effect, "enabled")
        if (enabledValue === false)
            return false

        var activeValue = _effectFlagValue(effect, "active")
        if (activeValue === false)
            return false

        if (_effectFlagValue(effect, "componentCompleted") === false)
            return false

        if (_effectFlagValue(effect, "fallbackActive"))
            return false

        if (_effectFlagValue(effect, "fallbackDueToRequirements"))
            return false

        if (_effectFlagValue(effect, "fallbackForcedByCompatibility"))
            return false

        if (_effectFlagValue(effect, "forceDepthTextureUnavailable"))
            return false

        if (_effectFlagValue(effect, "forceVelocityTextureUnavailable"))
            return false

        var guards = availabilityGuards
        if (guards !== undefined && guards !== null) {
            if (!Array.isArray(guards))
                guards = [guards]
            for (var i = 0; i < guards.length; ++i) {
                var guardName = guards[i]
                if (!guardName)
                    continue
                var guardValue = _effectFlagValue(effect, guardName)
                if (guardValue !== undefined && guardValue !== null && !guardValue)
                    return false
            }
        }

        return true
    }

    function _descriptorContainsToken(descriptor, tokens) {
        if (!descriptor || !tokens || !tokens.length)
            return false

        if (Array.isArray(descriptor)) {
            for (var i = 0; i < descriptor.length; ++i) {
                if (_descriptorContainsToken(descriptor[i], tokens))
                    return true
            }
            return false
        }

        if (typeof descriptor === "string" || typeof descriptor === "number") {
            var normalized = String(descriptor).toLowerCase()
            for (var t = 0; t < tokens.length; ++t) {
                if (normalized.indexOf(tokens[t]) !== -1)
                    return true
            }
            return false
        }

        if (typeof descriptor === "object") {
            var keys = Object.keys(descriptor)
            for (var k = 0; k < keys.length; ++k) {
                var key = keys[k]
                var normalizedKey = String(key).toLowerCase()
                for (var idx = 0; idx < tokens.length; ++idx) {
                    if (normalizedKey.indexOf(tokens[idx]) !== -1)
                        return true
                }
                try {
                    if (_descriptorContainsToken(descriptor[key], tokens))
                        return true
                } catch (error) {
                }
            }
        }

        return false
    }

    function _effectRequestsBuffer(effect, propertyNames, requirementTokens, availabilityGuards) {
        if (!effect)
            return false

        if (!_effectIsOperational(effect, availabilityGuards))
            return false

        var candidates = propertyNames || []
        if (!Array.isArray(candidates))
            candidates = [candidates]

        for (var i = 0; i < candidates.length; ++i) {
            var candidate = candidates[i]
            if (!candidate)
                continue
            try {
                var value = effect[candidate]
                if (value === true)
                    return true
                if (typeof value === "function") {
                    try {
                        if (value.call(effect) === true)
                            return true
                    } catch (error) {
                    }
                }
            } catch (error) {
            }
        }

        if (!requirementTokens || !requirementTokens.length)
            return false

        var metadataCandidates = [
                    "bufferRequirements",
                    "bufferRequirement",
                    "requiredBuffers",
                    "bufferPassRequirements",
                    "bufferPassRequirement",
                    "requiredBufferPasses",
                    "bufferResourceRequirements",
                    "buffers",
                    "bufferPasses"
                ]

        for (var j = 0; j < metadataCandidates.length; ++j) {
            var metadataName = metadataCandidates[j]
            try {
                var descriptor = effect[metadataName]
                if (descriptor === undefined || descriptor === null)
                    continue
                if (_descriptorContainsToken(descriptor, requirementTokens))
                    return true
            } catch (error) {
            }
        }

        return false
    }

    function _applyDepthTextureState(enabled) {
        var propertyName = _setEnvironmentPropertyCandidates(_depthTexturePropertyCandidates, enabled)

        if (propertyName.length) {
            if (_depthTexturePropertyName !== propertyName) {
                console.log("SceneEnvironmentController:",
                            qsTr("Depth texture binding via %1").arg(propertyName))
                _depthTexturePropertyName = propertyName
            }
            if (depthTextureSupportActive !== enabled) {
                depthTextureSupportActive = enabled
                _logBufferToggle("Depth", enabled, propertyName)
            }
            _depthTextureWarningLogged = false
            return
        }

        depthTextureSupportActive = false
        _depthTexturePropertyName = ""

        if (enabled && !_depthTextureWarningLogged) {
            console.warn("SceneEnvironmentController: depth textures requested but ExtendedSceneEnvironment does not expose compatible properties")
            _depthTextureWarningLogged = true
        }
    }

    function _applyVelocityTextureState(enabled) {
        var propertyName = _setEnvironmentPropertyCandidates(_velocityTexturePropertyCandidates, enabled)

        if (propertyName.length) {
            if (_velocityTexturePropertyName !== propertyName) {
                console.log("SceneEnvironmentController:",
                            qsTr("Velocity texture binding via %1").arg(propertyName))
                _velocityTexturePropertyName = propertyName
            }
            if (velocityTextureSupportActive !== enabled) {
                velocityTextureSupportActive = enabled
                _logBufferToggle("Velocity", enabled, propertyName)
            }
            _velocityTextureWarningLogged = false
            return
        }

        velocityTextureSupportActive = false
        _velocityTexturePropertyName = ""

        if (enabled && !_velocityTextureWarningLogged) {
            console.warn("SceneEnvironmentController: velocity textures requested but ExtendedSceneEnvironment does not expose compatible properties")
            _velocityTextureWarningLogged = true
        }
    }

    function _updateBufferRequirements() {
        var depthPropertyAvailable = _hasEnvironmentProperty("depthTextureEnabled")
        var velocityPropertyAvailable = _hasEnvironmentProperty("velocityTextureEnabled")

        var requiresDepth = false
        var requiresVelocity = false

        if (depthPropertyAvailable && fogEnabled && _effectIsOperational(root._customFogEffect, "depthTextureAvailable"))
            requiresDepth = true

        if (velocityPropertyAvailable && temporalAAEnabled)
            requiresVelocity = true

        var stack = effects
        if (stack && stack.length) {
            for (var i = 0; i < stack.length; ++i) {
                var effect = stack[i]
                if (!effect)
                    continue
                if (depthPropertyAvailable
                        && _effectRequestsBuffer(effect,
                                                  [
                                                      "requiresDepthTexture",
                                                      "depthTextureEnabled"
                                                  ],
                                                  ["depth", "z"],
                                                  ["depthTextureAvailable"]))
                    requiresDepth = true
                if (velocityPropertyAvailable
                        && _effectRequestsBuffer(effect,
                                                  [
                                                      "requiresVelocityTexture",
                                                      "velocityTextureEnabled"
                                                  ],
                                                  ["velocity", "motion"],
                                                  ["velocityTextureAvailable"]))
                    requiresVelocity = true
            }
        }

        _applyDepthTextureState(depthPropertyAvailable && requiresDepth)
        _applyVelocityTextureState(velocityPropertyAvailable && requiresVelocity)

        if (root._customFogEffect) {
            var shouldForceFallback = requiresDepth && !depthTextureSupportActive
            if (root._customFogEffect.forceDepthTextureUnavailable !== shouldForceFallback)
                root._customFogEffect.forceDepthTextureUnavailable = shouldForceFallback
        }
    }

    fog: Fog {
        enabled: root.fogEnabled
        color: root.fogColor
        density: root.fogDensity
        depthEnabled: root.fogEnabled
        depthNear: root.fogNear
        depthFar: root.fogFar
        depthCurve:1.0
    }

    readonly property FogEffect _customFogEffect: FogEffect {
        fogDensity: root.fogDensity
        fogColor: root.fogColor
        fogStartDistance: root.fogNear
        fogEndDistance: root.fogFar
        fogLeastIntenseY: root.fogLeastIntenseY
        fogMostIntenseY: root.fogMostIntenseY
        fogHeightCurve: root.fogHeightCurve
        heightBasedFog: root.fogHeightEnabled
        fogTransmitEnabled: root.fogTransmitEnabled
        fogTransmitCurve: root.fogTransmitCurve
        fogScattering: 0.5
        animatedFog: false
        cameraClipNear: root.cameraClipNear
        cameraClipFar: root.cameraClipFar
        cameraFieldOfView: root.cameraFieldOfView
        cameraAspectRatio: root.cameraAspectRatio
    }

    function _handleFogFallbackState(active, reason, compilationRelated) {
        var message = reason && reason.length ? reason : qsTr("Fog effect fallback active")
        if (active) {
            if (_fogLastFallbackReason !== message) {
                _fogLastFallbackReason = message
                _logFogEvent(compilationRelated ? "error" : "warn", message)
            }
            if (compilationRelated && fogEnabled) {
                fogEnabled = false
                _fogAutoDisabled = true
                _logFogEvent("warn", qsTr("⚠️ Fog effect disabled due to shader compilation failure"))
            }
        } else {
            if (_fogLastFallbackReason.length) {
                _logFogEvent("info", qsTr("✅ Fog fallback cleared"))
                _fogLastFallbackReason = ""
            }
            if (_fogAutoDisabled) {
                _logFogEvent("info", qsTr("ℹ️ Fog effect was disabled after a shader failure; re-enable it manually if needed"))
                _fogAutoDisabled = false
            }
        }
        fogCompilationErrorActive = compilationRelated && active
    }

    effects: {
        var stack = []
        if (externalEffects && externalEffects.length)
            stack = stack.concat(externalEffects)
        if (fogEnabled)
            stack.push(root._customFogEffect)
        return stack
    }

    onExternalEffectsChanged: _updateBufferRequirements()
    onFogEnabledChanged: _updateBufferRequirements()

    Connections {
        target: root._customFogEffect
        ignoreUnknownSignals: true
        function onFallbackActiveChanged(active) {
            root._handleFogFallbackState(active,
                                         root._customFogEffect.fallbackReason,
                                         root._customFogEffect.compilationFallbackActive)
            Qt.callLater(root._updateBufferRequirements)
        }
        function onFallbackReasonChanged(reason) {
            if (root._customFogEffect.fallbackActive)
                root._handleFogFallbackState(true,
                                             reason,
                                             root._customFogEffect.compilationFallbackActive)
            Qt.callLater(root._updateBufferRequirements)
        }
        function onCompilationFallbackActiveChanged(active) {
            root._handleFogFallbackState(root._customFogEffect.fallbackActive,
                                         root._customFogEffect.fallbackReason,
                                         active)
            Qt.callLater(root._updateBufferRequirements)
        }
        function onDepthTextureAvailableChanged() {
            Qt.callLater(root._updateBufferRequirements)
        }
    }

    Connections {
        target: root.externalEffects.length > 1 ? root.externalEffects[1] : null
        ignoreUnknownSignals: true
        function onFallbackActiveChanged() { Qt.callLater(root._updateBufferRequirements) }
        function onDepthTextureAvailableChanged() { Qt.callLater(root._updateBufferRequirements) }
        function onNormalTextureAvailableChanged() { Qt.callLater(root._updateBufferRequirements) }
    }

    Connections {
        target: root.externalEffects.length > 2 ? root.externalEffects[2] : null
        ignoreUnknownSignals: true
        function onFallbackActiveChanged() { Qt.callLater(root._updateBufferRequirements) }
        function onDepthTextureAvailableChanged() { Qt.callLater(root._updateBufferRequirements) }
    }

    Connections {
        target: root.externalEffects.length > 3 ? root.externalEffects[3] : null
        ignoreUnknownSignals: true
        function onFallbackActiveChanged() { Qt.callLater(root._updateBufferRequirements) }
        function onVelocityTextureAvailableChanged() { Qt.callLater(root._updateBufferRequirements) }
    }

 // ===============================================================
 // TONEMAP
 // ===============================================================

    property bool tonemapActive: true
    property alias tonemapEnabled: root.tonemapActive
    property string tonemapModeName: "filmic"
    property string tonemapStoredModeName: "filmic"
    property real tonemapExposure: 1.0
    property real tonemapWhitePoint: 2.0
    // qmllint disable missing-property
    readonly property var tonemapModeLookup: ({
        "filmic": SceneEnvironment.TonemapModeFilmic,
        "aces": typeof SceneEnvironment.TonemapModeAces !== "undefined"
                 ? SceneEnvironment.TonemapModeAces
                 : SceneEnvironment.TonemapModeFilmic,
        "reinhard": typeof SceneEnvironment.TonemapModeReinhard !== "undefined"
                     ? SceneEnvironment.TonemapModeReinhard
                     : SceneEnvironment.TonemapModeLinear,
        "gamma": typeof SceneEnvironment.TonemapModeGamma !== "undefined"
                  ? SceneEnvironment.TonemapModeGamma
                  : (typeof SceneEnvironment.TonemapModeAces !== "undefined"
                     ? SceneEnvironment.TonemapModeAces
                     : SceneEnvironment.TonemapModeLinear),
        "linear": SceneEnvironment.TonemapModeLinear,
        "none": SceneEnvironment.TonemapModeNone
    })
    // qmllint enable missing-property

    function normalizeTonemapModeName(value) {
        if (value === undefined || value === null)
            return ""
        return String(value).trim().toLowerCase()
    }

    function setTonemapEnabledFlag(value) {
        var enabled = !!value
        if (enabled) {
            if (!tonemapActive)
                tonemapActive = true
            if (normalizeTonemapModeName(tonemapModeName) === "none") {
                var restored = tonemapStoredModeName || "filmic"
                if (normalizeTonemapModeName(restored) !== "none")
                    tonemapModeName = restored
            }
        } else {
            if (normalizeTonemapModeName(tonemapModeName) !== "none")
                tonemapStoredModeName = tonemapModeName
            tonemapActive = false
            tonemapModeName = "none"
        }
    }

    function effectiveTonemapModeKey() {
        if (!tonemapActive)
            return "none"
        var normalized = normalizeTonemapModeName(tonemapModeName)
        if (!normalized || normalized === "none") {
            normalized = tonemapStoredModeName || "filmic"
        }
        if (!tonemapModeLookup.hasOwnProperty(normalized))
            return "filmic"
        return normalized
    }

    onTonemapModeNameChanged: {
        var normalized = normalizeTonemapModeName(tonemapModeName)
        if (!normalized)
            normalized = tonemapStoredModeName || "filmic"
        if (!tonemapModeLookup.hasOwnProperty(normalized)) {
            console.warn("SceneEnvironmentController: unsupported tonemap mode", tonemapModeName)
            normalized = tonemapStoredModeName || "filmic"
        }
        if (normalized !== tonemapModeName) {
            tonemapModeName = normalized
            return
        }
        if (normalized === "none") {
            if (tonemapActive)
                tonemapActive = false
        } else {
            tonemapStoredModeName = normalized
            if (!tonemapActive)
                tonemapActive = true
        }
    }

    onTonemapActiveChanged: {
        var normalized = normalizeTonemapModeName(tonemapModeName)
        if (tonemapActive) {
            if (normalized === "none")
                tonemapModeName = tonemapStoredModeName || "filmic"
        } else {
            if (normalized && normalized !== "none")
                tonemapStoredModeName = normalized
            if (normalized !== "none")
                tonemapModeName = "none"
        }
    }

    tonemapMode: {
        var key = effectiveTonemapModeKey()
        if (tonemapModeLookup.hasOwnProperty(key))
            return tonemapModeLookup[key]
        return SceneEnvironment.TonemapModeNone
    }

    exposure: tonemapExposure
    whitePoint: tonemapWhitePoint

 // ===============================================================
 // BLOOM
 // ===============================================================

    property bool bloomEnabled: true
    property real bloomIntensity:0.5
    property real bloomThreshold:1.0
    property real bloomSpread:0.65
    property real bloomGlowStrength:1.0
    property bool bloomQualityHigh: true
    property bool bloomUseBicubicUpscale: true
    property real bloomHdrMaximum:8.0
    property real bloomHdrScale:2.0

    glowEnabled: bloomEnabled
    glowIntensity: bloomIntensity
    glowStrength: bloomGlowStrength
    glowHDRMinimumValue: bloomThreshold
    glowBloom: bloomSpread
    glowQualityHigh: bloomQualityHigh
    glowUseBicubicUpscale: bloomUseBicubicUpscale
    glowHDRMaximumValue: bloomHdrMaximum
    glowHDRScale: bloomHdrScale

 // ===============================================================
 // SSAO
 // ===============================================================

 property bool ssaoEnabled: false
 property real ssaoRadius:8.0
 property real ssaoIntensity:1.0
 property real ssaoSoftness:20.0
 property bool ssaoDither: true
 property int ssaoSampleRate:3
    onSsaoEnabledChanged: _updateBufferRequirements()

 aoEnabled: ssaoEnabled
 aoDistance: ssaoRadius
 aoStrength: ssaoIntensity *100
 aoSoftness: ssaoSoftness
 aoDither: ssaoDither
 aoSampleRate: ssaoSampleRate

 // ===============================================================
 // DEPTH OF FIELD
 // ===============================================================

    property bool internalDepthOfFieldEnabled: false
    property real dofFocusDistance: 2200.0
    property real dofFocusRange: 900.0
    property real dofBlurAmount: 4.0
    property bool depthOfFieldAutoFocus: false
    property real autoFocusDistanceHint: dofFocusDistance
    property real autoFocusRangeHint: dofFocusRange
    onInternalDepthOfFieldEnabledChanged: _updateBufferRequirements()

    onDepthOfFieldAutoFocusChanged: {
        _applyAutoFocusDistance()
        _applyAutoFocusRange()
    }
    onAutoFocusDistanceHintChanged: _applyAutoFocusDistance()
    onAutoFocusRangeHintChanged: _applyAutoFocusRange()

    function _applyAutoFocusDistance() {
        if (!depthOfFieldAutoFocus)
            return
        var numeric = Number(autoFocusDistanceHint)
        if (isFinite(numeric))
            dofFocusDistance = Math.max(0.0, numeric)
    }

    function _applyAutoFocusRange() {
        if (!depthOfFieldAutoFocus)
            return
        var numeric = Number(autoFocusRangeHint)
        if (isFinite(numeric))
            dofFocusRange = Math.max(0.0, numeric)
    }

    // ✅ ИСПРАВЛЕНО: используем внутреннее свойство для избежания конфликта
    depthOfFieldEnabled: internalDepthOfFieldEnabled
    depthOfFieldFocusDistance: dofFocusDistance
    depthOfFieldFocusRange: dofFocusRange
    depthOfFieldBlurAmount: dofBlurAmount

 // ===============================================================
 // VIGNETTE
 // ===============================================================

 property bool internalVignetteEnabled: false
 property real internalVignetteStrength:0.35
 property real vignetteRadiusValue:0.5

 // ✅ ИСПРАВЛЕНО: используем внутренние свойства
 vignetteEnabled: internalVignetteEnabled
 vignetteStrength: internalVignetteStrength
 vignetteRadius: vignetteRadiusValue

 // ===============================================================
 // LENS FLARE
 // ===============================================================

 property bool internalLensFlareEnabled: false
 property int lensFlareGhostCountValue:3
 property real lensFlareGhostDispersalValue:0.6
 property real lensFlareHaloWidthValue:0.25
 property real lensFlareBloomBiasValue:0.35
 property real lensFlareStretchValue:1.0

 // ✅ ИСПРАВЛЕНО: используем внутреннее свойство
 lensFlareEnabled: internalLensFlareEnabled
 lensFlareGhostCount: lensFlareGhostCountValue
 lensFlareGhostDispersal: lensFlareGhostDispersalValue
 lensFlareHaloWidth: lensFlareHaloWidthValue
 lensFlareBloomBias: lensFlareBloomBiasValue
 lensFlareStretchToAspect: lensFlareStretchValue

 // ===============================================================
 // OIT (Order Independent Transparency)
 // ===============================================================

 property string oitMode: "weighted"

 oitMethod: oitMode === "weighted" ? SceneEnvironment.OITWeightedBlended : SceneEnvironment.OITNone

 // ===============================================================
 // COLOR ADJUSTMENTS
 // ===============================================================

 property bool colorAdjustmentsActive: false
 property real adjustmentBrightnessValue:0.0
 property real adjustmentContrastValue:0.0
 property real adjustmentSaturationValue:0.0

 colorAdjustmentsEnabled: colorAdjustmentsActive
 adjustmentBrightness: adjustmentBrightnessValue
 adjustmentContrast: adjustmentContrastValue
 adjustmentSaturation: adjustmentSaturationValue

    function applyQualityPreset(name) {
        return applyQualityPresetInternal(name)
    }

    function applyQualityPresetInternal(requestedName) {
        var canonical = qualityProfiles.canonicalKey(requestedName)
        if (!canonical) {
            console.warn("SceneEnvironmentController: unknown quality preset", requestedName)
            return false
        }
        var preset = qualityProfiles.presetFor(canonical)
        if (!preset) {
            console.warn("SceneEnvironmentController: missing definition for preset", canonical)
            return false
        }

        _applyingQualityPreset = true
        try {
            if (qualityPreset !== canonical)
                qualityPreset = canonical

            activeQualityPreset = canonical
            console.log("SceneEnvironmentController: applying quality preset", canonical)

            if (preset.environment)
                applyEnvironmentPayload(preset.environment)
            if (preset.antialiasing)
                applyQualityPayload(preset.antialiasing)
            if (preset.effects)
                applyEffectsPayload(preset.effects)

            return true
        } finally {
            _applyingQualityPreset = false
        }
    }

    function applyEnvironmentUpdates(params) {
        applyEnvironmentPayload(params)
    }

    function applyQualityUpdates(params) {
        applyQualityPayload(params)
    }

    function applyEffectsUpdates(params) {
        applyEffectsPayload(params)
    }
}
