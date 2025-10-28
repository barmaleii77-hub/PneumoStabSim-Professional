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
 property bool skyboxToggleFlag: true
 property color backgroundColor: "#1f242c"
 property string backgroundModeSetting: "skybox"
 property Texture iblProbe: null
 property real iblIntensity:1.0
 property real iblRotationDeg:0.0

 /**
 * Python SceneBridge instance injected via context property.
 */
 property var sceneBridge: null

 backgroundMode: {
     if (backgroundModeSetting === "transparent") {
         return SceneEnvironment.Transparent
     }
     if (backgroundModeSetting === "color") {
         return SceneEnvironment.Color
     }
     return (iblBackgroundEnabled && iblProbe) ? SceneEnvironment.SkyBox : SceneEnvironment.Color
 }
 clearColor: backgroundModeSetting === "transparent"
             ? Qt.rgba(backgroundColor.r, backgroundColor.g, backgroundColor.b, 0)
             : backgroundColor
 skyBoxCubeMap: (iblBackgroundEnabled && iblProbe) ? iblProbe : null
 lightProbe: (iblLightingEnabled && iblProbe) ? iblProbe : null
 probeExposure: iblIntensity
 probeOrientation: Qt.vector3d(0, iblRotationDeg,0)

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

 var backgroundPayload = (
     params.background && typeof params.background === "object"
 ) ? params.background : null

 var backgroundModeValue = undefined
 if (params.background_mode !== undefined)
 backgroundModeValue = params.background_mode
 else if (params.backgroundMode !== undefined)
 backgroundModeValue = params.backgroundMode
 if (backgroundPayload && backgroundPayload.mode !== undefined)
 backgroundModeValue = backgroundPayload.mode
 if (backgroundModeValue !== undefined)
 setBackgroundMode(backgroundModeValue)

 var skyboxValue = undefined
 if (params.skybox_enabled !== undefined)
 skyboxValue = params.skybox_enabled
 else if (params.skyboxEnabled !== undefined)
 skyboxValue = params.skyboxEnabled
 if (backgroundPayload && backgroundPayload.skybox_enabled !== undefined)
 skyboxValue = backgroundPayload.skybox_enabled
 if (skyboxValue !== undefined)
 setSkyboxEnabled(skyboxValue)

 var colorValue = undefined
 if (params.clearColor !== undefined)
 colorValue = params.clearColor
 if (params.backgroundColor !== undefined)
 colorValue = params.backgroundColor
 if (params.background_color !== undefined)
 colorValue = params.background_color
 if (backgroundPayload && backgroundPayload.color !== undefined)
 colorValue = backgroundPayload.color
 if (colorValue !== undefined)
 backgroundColor = colorValue

 var iblEnabledValue = undefined
 if (params.ibl_enabled !== undefined)
 iblEnabledValue = params.ibl_enabled
 else if (params.iblEnabled !== undefined)
 iblEnabledValue = params.iblEnabled
 if (iblEnabledValue !== undefined)
 iblLightingEnabled = !!iblEnabledValue

 if (params.iblBackgroundEnabled !== undefined)
 setSkyboxEnabled(params.iblBackgroundEnabled)
 if (params.iblLightingEnabled !== undefined)
 iblLightingEnabled = !!params.iblLightingEnabled

 var iblIntensityValue = params.iblIntensity
 if (iblIntensityValue === undefined && params.ibl_intensity !== undefined)
 iblIntensityValue = params.ibl_intensity
 if (iblIntensityValue !== undefined)
 iblIntensity = Number(iblIntensityValue)

 var iblRotationValue = params.iblRotationDeg
 if (iblRotationValue === undefined && params.ibl_rotation !== undefined)
 iblRotationValue = params.ibl_rotation
 if (iblRotationValue !== undefined)
 iblRotationDeg = Number(iblRotationValue)

 if (params.ibl) {
 var ibl = params.ibl
 if (ibl.enabled !== undefined) {
 iblLightingEnabled = !!ibl.enabled
 }
 if (ibl.background_enabled !== undefined)
 setSkyboxEnabled(ibl.background_enabled)
 if (ibl.lighting_enabled !== undefined)
 iblLightingEnabled = !!ibl.lighting_enabled
 if (ibl.intensity !== undefined)
 iblIntensity = Number(ibl.intensity)
 if (ibl.rotation !== undefined)
  iblRotationDeg = Number(ibl.rotation)
 }

 if (params.tonemapEnabled !== undefined)
 setTonemapEnabledFlag(params.tonemapEnabled)
 if (params.tonemapActive !== undefined)
 setTonemapEnabledFlag(params.tonemapActive)
 if (params.tonemapModeName)
 tonemapModeName = String(params.tonemapModeName)
 if (params.tonemap_mode)
 tonemapModeName = String(params.tonemap_mode)
 if (params.tonemapExposure !== undefined)
 tonemapExposure = Number(params.tonemapExposure)
 if (params.tonemapWhitePoint !== undefined)
 tonemapWhitePoint = Number(params.tonemapWhitePoint)

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

 if (params.bloomEnabled !== undefined)
 bloomEnabled = !!params.bloomEnabled
 if (params.bloomIntensity !== undefined)
 bloomIntensity = Number(params.bloomIntensity)
 if (params.bloomThreshold !== undefined)
 bloomThreshold = Number(params.bloomThreshold)
 if (params.bloomSpread !== undefined)
 bloomSpread = Number(params.bloomSpread)
 if (params.depthOfFieldEnabled !== undefined)
 internalDepthOfFieldEnabled = !!params.depthOfFieldEnabled
 if (params.dofFocusDistance !== undefined) {
 var effectsFocusDistance = Number(params.dofFocusDistance)
 if (isFinite(effectsFocusDistance))
 dofFocusDistance = toSceneLength(effectsFocusDistance)
 }
 if (params.dofBlurAmount !== undefined)
 dofBlurAmount = Number(params.dofBlurAmount)
 if (params.vignetteEnabled !== undefined)
 internalVignetteEnabled = !!params.vignetteEnabled
 if (params.vignetteStrength !== undefined)
 internalVignetteStrength = Number(params.vignetteStrength)
 if (params.lensFlareEnabled !== undefined)
 internalLensFlareEnabled = !!params.lensFlareEnabled
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

 glowEnabled: bloomEnabled
 glowIntensity: bloomIntensity
 glowHDRMinimumValue: bloomThreshold
 glowBloom: bloomSpread
 glowQualityHigh: true
 glowUseBicubicUpscale: true
 glowHDRMaximumValue:8.0
 glowHDRScale:2.0

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

 // ✅ ИСПРАВЛЕНО: используем внутренние свойства
 vignetteEnabled: internalVignetteEnabled
 vignetteStrength: internalVignetteStrength
 vignetteRadius:0.4

 // ===============================================================
 // LENS FLARE
 // ===============================================================

 property bool internalLensFlareEnabled: false

 // ✅ ИСПРАВЛЕНО: используем внутреннее свойство
 lensFlareEnabled: internalLensFlareEnabled
 lensFlareGhostCount:3
 lensFlareGhostDispersal:0.6
 lensFlareHaloWidth:0.25
 lensFlareBloomBias:0.35
 lensFlareStretchToAspect:1.0

 // ===============================================================
 // OIT (Order Independent Transparency)
 // ===============================================================

 property string oitMode: "weighted"

 oitMethod: oitMode === "weighted" ? SceneEnvironment.OITWeightedBlended : SceneEnvironment.OITNone

 // ===============================================================
 // COLOR ADJUSTMENTS
 // ===============================================================

 colorAdjustmentsEnabled: true
 adjustmentBrightness:1.0
 adjustmentContrast:1.05
 adjustmentSaturation:1.05

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
