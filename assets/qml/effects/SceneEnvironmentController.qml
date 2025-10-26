import QtQuick6.10
import QtQuick3D6.10
import QtQuick3D.Helpers6.10 // ✅ CRITICAL: Required for ExtendedSceneEnvironment

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
 property Texture iblProbe: null
 property real iblIntensity:1.0
 property real iblRotationDeg:0.0

 /**
 * Python SceneBridge instance injected via context property.
 */
 property var sceneBridge: null

 backgroundMode: (iblBackgroundEnabled && iblProbe) ? SceneEnvironment.SkyBox : SceneEnvironment.Color
 clearColor: backgroundColor
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
 return0
 var scale = Number(sceneScaleFactor)
 if (!isFinite(scale) || scale <=0)
 return numeric
 return numeric * scale
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

 if (params.backgroundColor)
 backgroundColor = params.backgroundColor
 if (params.clearColor)
 backgroundColor = params.clearColor
 if (params.iblBackgroundEnabled !== undefined)
 iblBackgroundEnabled = !!params.iblBackgroundEnabled
 if (params.iblLightingEnabled !== undefined)
 iblLightingEnabled = !!params.iblLightingEnabled
 if (params.iblIntensity !== undefined)
 iblIntensity = Number(params.iblIntensity)
 if (params.iblRotationDeg !== undefined)
 iblRotationDeg = Number(params.iblRotationDeg)
 if (params.tonemapEnabled !== undefined)
 tonemapEnabled = !!params.tonemapEnabled
 if (params.tonemapModeName)
 tonemapModeName = String(params.tonemapModeName)
 if (params.tonemapExposure !== undefined)
 tonemapExposure = Number(params.tonemapExposure)
 if (params.tonemapWhitePoint !== undefined)
 tonemapWhitePoint = Number(params.tonemapWhitePoint)
 if (params.fogEnabled !== undefined)
 fogEnabled = !!params.fogEnabled
 if (params.fogColor)
 fogColor = params.fogColor
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
 if (params.ssaoEnabled !== undefined)
 ssaoEnabled = !!params.ssaoEnabled
 if (params.ssaoRadius !== undefined)
 ssaoRadius = Number(params.ssaoRadius)
 if (params.ssaoIntensity !== undefined)
 ssaoIntensity = Number(params.ssaoIntensity)
 if (params.depthOfFieldEnabled !== undefined)
 internalDepthOfFieldEnabled = !!params.depthOfFieldEnabled
 if (params.dofFocusDistance !== undefined) {
 var dofDistance = Number(params.dofFocusDistance)
 if (isFinite(dofDistance))
 dofFocusDistance = toSceneLength(dofDistance)
 }
 if (params.dofBlurAmount !== undefined)
 dofBlurAmount = Number(params.dofBlurAmount)
 if (params.vignetteEnabled !== undefined)
 internalVignetteEnabled = !!params.vignetteEnabled
 if (params.vignetteStrength !== undefined)
 internalVignetteStrength = Number(params.vignetteStrength)
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

 property bool tonemapEnabled: true
 property string tonemapModeName: "filmic"
 property real tonemapExposure:1.0
 property real tonemapWhitePoint:2.0

 tonemapMode: tonemapEnabled ? (
 tonemapModeName === "filmic" ? SceneEnvironment.TonemapModeFilmic :
 tonemapModeName === "aces" ? SceneEnvironment.TonemapModeAces :
 tonemapModeName === "reinhard" ? SceneEnvironment.TonemapModeReinhard :
 tonemapModeName === "gamma" ? SceneEnvironment.TonemapModeLinear :
 tonemapModeName === "linear" ? SceneEnvironment.TonemapModeLinear :
 SceneEnvironment.TonemapModeNone
 ) : SceneEnvironment.TonemapModeNone

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
}
