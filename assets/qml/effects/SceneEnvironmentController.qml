import QtQuick 6.10
import QtQuick3D 6.10
import QtQuick3D.Helpers 6.10 // ✅ CRITICAL: Required for ExtendedSceneEnvironment

/*
 * SceneEnvironmentController - Полное управление ExtendedSceneEnvironment
 * Все эффекты, качество, IBL, туман в ОДНОМ компоненте
 */
ExtendedSceneEnvironment {
 id: root

 // ===============================================================
 // BACKGROUND & IBL
 // ===============================================================

    property bool iblBackgroundEnabled: false
    property bool iblLightingEnabled: false
    property color backgroundColor: "#1f242c"
    property string backgroundModeKey: "skybox"
    property bool transparentBackground: (String(backgroundModeKey || "skybox").trim().toLowerCase() === "transparent")
    readonly property color effectiveBackgroundColor: transparentBackground
        ? Qt.rgba(backgroundColor.r, backgroundColor.g, backgroundColor.b, 0)
        : backgroundColor
    property Texture iblProbe: null
    property real iblIntensity:1.0
    property real probeBrightnessValue:1.0
    property real probeHorizonValue:0.0
    property real iblRotationPitchDeg:0.0
    property real iblRotationDeg:0.0
    property real iblRotationRollDeg:0.0
    property bool iblBindToCamera: false
    property real skyboxBlurValue:0.0

 /**
 * Python SceneBridge instance injected via context property.
 */
 property var sceneBridge: null

    backgroundMode: {
        var targetMode = backgroundModeForKey(backgroundModeKey)
        if (targetMode === SceneEnvironment.SkyBox)
            return (iblBackgroundEnabled && iblProbe) ? SceneEnvironment.SkyBox : SceneEnvironment.Color
        return targetMode
    }
    clearColor: effectiveBackgroundColor
    skyBoxCubeMap: (iblBackgroundEnabled && iblProbe) ? iblProbe : null
    lightProbe: (iblLightingEnabled && iblProbe) ? iblProbe : null
    probeExposure: probeBrightnessValue
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
 if (aaPrimaryMode === "ssaa") return SceneEnvironment.SSAA
 if (aaPrimaryMode === "msaa") return SceneEnvironment.MSAA
 if (aaPrimaryMode === "progressive") return SceneEnvironment.ProgressiveAA
 return SceneEnvironment.NoAA
 }

 antialiasingQuality: {
 if (aaQualityLevel === "high") return SceneEnvironment.High
 if (aaQualityLevel === "medium") return SceneEnvironment.Medium
 if (aaQualityLevel === "low") return SceneEnvironment.Low
 return SceneEnvironment.Medium
 }

 // ✅ ИСПРАВЛЕНО: fxaaEnabled и specularAAEnabled уже установлены выше
 temporalAAEnabled: (aaPostMode === "taa" && taaEnabled && (!taaMotionAdaptive || cameraIsMoving))
 temporalAAStrength: taaStrength

 // ===============================================================
 // DITHERING (Qt6.10+)
 // ===============================================================

 property bool ditheringEnabled: true
 property bool canUseDithering: false
 property real sceneScaleFactor:1.0

    function qtVersionAtLeast(requiredMajor, requiredMinor) {
        var versionString = "";
        if (Qt.application && Qt.application.qtVersion)
            versionString = String(Qt.application.qtVersion);
        else if (Qt.version)
            versionString = String(Qt.version);
 var parts = versionString.split(".");
 if (parts.length <2)
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

    function backgroundModeForKey(key) {
        var normalized = String(key || "skybox").trim().toLowerCase()
        if (normalized === "color")
            return SceneEnvironment.Color
        if (normalized === "transparent")
            return (SceneEnvironment.Transparent !== undefined)
                    ? SceneEnvironment.Transparent
                    : SceneEnvironment.Color
        return SceneEnvironment.SkyBox
    }

 function _normalizeBackgroundMode(value) {
 if (value === undefined || value === null)
 return backgroundModeSetting;
 var text = String(value).trim().toLowerCase();
 if (text === "transparent")
 return "transparent";
 if (text === "color" || text === "colour")
 return "color";
 if (text === "skybox")
 return "skybox";
 return backgroundModeSetting;
 }

 function setBackgroundMode(value) {
 var normalized = _normalizeBackgroundMode(value);
 if (backgroundModeSetting !== normalized)
 backgroundModeSetting = normalized;
 if (normalized !== "skybox")
 iblBackgroundEnabled = false;
 else
 iblBackgroundEnabled = skyboxToggleFlag;
 }

 function setSkyboxEnabled(value) {
 var enabled = !!value;
 if (skyboxToggleFlag !== enabled)
 skyboxToggleFlag = enabled;
 if (backgroundModeSetting === "skybox")
 iblBackgroundEnabled = enabled;
 }

 function _applySceneBridgeState() {
 if (!sceneBridge)
 return

 if (sceneBridge.environment && Object.keys(sceneBridge.environment).length)
 _applyEnvironmentPayload(sceneBridge.environment)

 if (sceneBridge.quality && Object.keys(sceneBridge.quality).length)
 _applyQualityPayload(sceneBridge.quality)

 if (sceneBridge.effects && Object.keys(sceneBridge.effects).length)
 _applyEffectsPayload(sceneBridge.effects)
 }

 function _applyEnvironmentPayload(payload) {
 applyEnvironmentPayload(payload)
 }

 function _applyQualityPayload(payload) {
 applyQualityPayload(payload)
 }

 function _applyEffectsPayload(payload) {
 applyEffectsPayload(payload)
 }

 onSceneBridgeChanged: _applySceneBridgeState()

 Connections {
 target: sceneBridge
 enabled: !!sceneBridge

 function onEnvironmentChanged(payload) {
 if (payload)
 _applyEnvironmentPayload(payload)
 }

 function onQualityChanged(payload) {
 if (payload)
 _applyQualityPayload(payload)
 }

 function onEffectsChanged(payload) {
 if (payload)
 _applyEffectsPayload(payload)
 }
 }

 Component.onCompleted: {
 root.canUseDithering = qtVersionAtLeast(6,10)
 if (canUseDithering) {
 root.ditheringEnabled = Qt.binding(function() { return ditheringEnabled })
 }
 _applySceneBridgeState()
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
        backgroundModeKey = String(modeValue).trim().toLowerCase()

    var skyboxFlag = boolFromKeys(params, "skyboxEnabled", "skybox_enabled")
    if (skyboxFlag !== undefined)
        iblBackgroundEnabled = skyboxFlag

    var iblEnabledFlag = boolFromKeys(params, "iblEnabled", "ibl_enabled")
    if (iblEnabledFlag !== undefined) {
        iblLightingEnabled = iblEnabledFlag
        iblBackgroundEnabled = iblEnabledFlag
    }

    var backgroundFlag = boolFromKeys(params, "iblBackgroundEnabled", "ibl_background_enabled")
    if (backgroundFlag !== undefined)
        iblBackgroundEnabled = backgroundFlag

    var lightingFlag = boolFromKeys(params, "iblLightingEnabled", "ibl_lighting_enabled")
    if (lightingFlag !== undefined)
        iblLightingEnabled = lightingFlag

    var intensityValue = numberFromKeys(params, "iblIntensity", "ibl_intensity")
    if (intensityValue !== undefined) {
        iblIntensity = intensityValue
        probeBrightnessValue = intensityValue
    }

    var probeBrightness = numberFromKeys(params, "probeBrightness", "probe_brightness")
    if (probeBrightness !== undefined)
        probeBrightnessValue = probeBrightness

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
            probeBrightnessValue = nestedIntensity
        }
        var nestedBrightness = numberFromKeys(ibl, "probeBrightness", "probe_brightness")
        if (nestedBrightness !== undefined)
            probeBrightnessValue = nestedBrightness
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

    if (params.fogEnabled !== undefined)
        fogEnabled = !!params.fogEnabled
    if (params.fogColor)
        fogColor = params.fogColor
    if (params.fogDensity !== undefined)
        fogDensity = Number(params.fogDensity)
    if (params.fogNear !== undefined) {
        var fogNearValue = Number(params.fogNear)
        if (isFinite(fogNearValue))
            fogNear = toSceneLength(fogNearValue)
    }
    if (params.fogFar !== undefined) {
        var fogFarValue = Number(params.fogFar)
        if (isFinite(fogFarValue))
            fogFar = toSceneLength(fogFarValue)
    }

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
    }

 if (params.ssaoEnabled !== undefined)
 ssaoEnabled = !!params.ssaoEnabled
 if (params.ssaoRadius !== undefined)
 ssaoRadius = Number(params.ssaoRadius)
 if (params.ssaoIntensity !== undefined)
 ssaoIntensity = Number(params.ssaoIntensity)

 if (params.ssao) {
 var ssao = params.ssao
 if (ssao.enabled !== undefined)
 ssaoEnabled = !!ssao.enabled
 if (ssao.radius !== undefined)
 ssaoRadius = Number(ssao.radius)
 if (ssao.intensity !== undefined)
 ssaoIntensity = Number(ssao.intensity)
 }

 if (params.depthOfFieldEnabled !== undefined)
 internalDepthOfFieldEnabled = !!params.depthOfFieldEnabled
 if (params.dofFocusDistance !== undefined) {
 var dofDistance = Number(params.dofFocusDistance)
 if (isFinite(dofDistance))
 dofFocusDistance = toSceneLength(dofDistance)
 }
 if (params.dofBlurAmount !== undefined)
 dofBlurAmount = Number(params.dofBlurAmount)

 if (params.depthOfField) {
 var dof = params.depthOfField
 if (dof.enabled !== undefined)
 internalDepthOfFieldEnabled = !!dof.enabled
 if (dof.focus_distance !== undefined) {
 var dofNestedDistance = Number(dof.focus_distance)
 if (isFinite(dofNestedDistance))
 dofFocusDistance = toSceneLength(dofNestedDistance)
 }
 if (dof.blur_amount !== undefined)
 dofBlurAmount = Number(dof.blur_amount)
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
    var dofBlurValue = numberFromKeys(params, "dofBlurAmount", "dof_blur")
    if (dofBlurValue !== undefined)
        dofBlurAmount = dofBlurValue

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

 fog: Fog {
 enabled: root.fogEnabled
 color: root.fogColor
 depthEnabled: true
 depthNear: root.fogNear
 depthFar: root.fogFar
 depthCurve:1.0
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
    readonly property var tonemapModeLookup: ({
        "filmic": SceneEnvironment.TonemapModeFilmic,
        "aces": SceneEnvironment.TonemapModeAces,
        "reinhard": SceneEnvironment.TonemapModeReinhard,
        "gamma": SceneEnvironment.TonemapModeLinear,
        "linear": SceneEnvironment.TonemapModeLinear,
        "none": SceneEnvironment.TonemapModeNone
    })

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

 aoEnabled: ssaoEnabled
 aoDistance: ssaoRadius
 aoStrength: ssaoIntensity *100
 aoSoftness:20
 aoDither: true
 aoSampleRate:3

 // ===============================================================
 // DEPTH OF FIELD
 // ===============================================================

 property bool internalDepthOfFieldEnabled: false
 property real dofFocusDistance:2200.0
 property real dofBlurAmount:4.0

 // ✅ ИСПРАВЛЕНО: используем внутреннее свойство для избежания конфликта
 depthOfFieldEnabled: internalDepthOfFieldEnabled
 depthOfFieldFocusDistance: dofFocusDistance
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
