import QtQuick
import QtQuick3D
import QtQuick3D.Helpers  // ✅ CRITICAL: Required for ExtendedSceneEnvironment

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
    property real iblIntensity: 1.0
    property real iblRotationDeg: 0.0
    
    backgroundMode: (iblBackgroundEnabled && iblProbe) ? SceneEnvironment.SkyBox : SceneEnvironment.Color
    clearColor: backgroundColor
    skyBoxCubeMap: (iblBackgroundEnabled && iblProbe) ? iblProbe : null
    lightProbe: (iblLightingEnabled && iblProbe) ? iblProbe : null
    probeExposure: iblIntensity
    probeOrientation: Qt.vector3d(0, iblRotationDeg, 0)
    
    // ===============================================================
    // ANTIALIASING
    // ===============================================================
    
    property string aaPrimaryMode: "ssaa"
    property string aaQualityLevel: "high"
    property string aaPostMode: "taa"
    property bool taaEnabled: true
    property real taaStrength: 0.4
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
    // DITHERING (Qt 6.10+)
    // ===============================================================
    
    property bool ditheringEnabled: true
    property bool canUseDithering: false
    
    Component.onCompleted: {
        if (canUseDithering) {
            root.ditheringEnabled = Qt.binding(function() { return ditheringEnabled })
        }
    }
    
    // ===============================================================
    // FOG (Qt 6.10+)
    // ===============================================================
    
    property bool fogEnabled: false
    property color fogColor: "#808080"
    property real fogDensity: 0.1
    property real fogNear: 1200.0
    property real fogFar: 12000.0
    
    fog: Fog {
        enabled: root.fogEnabled
        color: root.fogColor
        depthEnabled: true
        depthNear: root.fogNear
        depthFar: root.fogFar
        depthCurve: 1.0
    }
    
    // ===============================================================
    // TONEMAP
    // ===============================================================
    
    property bool tonemapEnabled: true
    property string tonemapModeName: "filmic"
    property real tonemapExposure: 1.0
    property real tonemapWhitePoint: 2.0
    
    tonemapMode: tonemapEnabled ? (
        tonemapModeName === "filmic" ? SceneEnvironment.TonemapModeFilmic :
        tonemapModeName === "aces" ? SceneEnvironment.TonemapModeFilmic :
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
    property real bloomIntensity: 0.5
    property real bloomThreshold: 1.0
    property real bloomSpread: 0.65
    
    glowEnabled: bloomEnabled
    glowIntensity: bloomIntensity
    glowHDRMinimumValue: bloomThreshold
    glowBloom: bloomSpread
    glowQualityHigh: true
    glowUseBicubicUpscale: true
    glowHDRMaximumValue: 8.0
    glowHDRScale: 2.0
    
    // ===============================================================
    // SSAO
    // ===============================================================
    
    property bool ssaoEnabled: false
    property real ssaoRadius: 8.0
    property real ssaoIntensity: 1.0
    
    aoEnabled: ssaoEnabled
    aoDistance: ssaoRadius
    aoStrength: ssaoIntensity * 100
    aoSoftness: 20
    aoDither: true
    aoSampleRate: 3
    
    // ===============================================================
    // DEPTH OF FIELD
    // ===============================================================
    
    property bool internalDepthOfFieldEnabled: false
    property real dofFocusDistance: 2200.0
    property real dofBlurAmount: 4.0
    
    // ✅ ИСПРАВЛЕНО: используем внутреннее свойство для избежания конфликта
    depthOfFieldEnabled: internalDepthOfFieldEnabled
    depthOfFieldFocusDistance: dofFocusDistance
    depthOfFieldBlurAmount: dofBlurAmount
    
    // ===============================================================
    // VIGNETTE
    // ===============================================================
    
    property bool internalVignetteEnabled: false
    property real internalVignetteStrength: 0.35
    
    // ✅ ИСПРАВЛЕНО: используем внутренние свойства
    vignetteEnabled: internalVignetteEnabled
    vignetteStrength: internalVignetteStrength
    vignetteRadius: 0.4
    
    // ===============================================================
    // LENS FLARE
    // ===============================================================
    
    property bool internalLensFlareEnabled: false
    
    // ✅ ИСПРАВЛЕНО: используем внутреннее свойство
    lensFlareEnabled: internalLensFlareEnabled
    lensFlareGhostCount: 3
    lensFlareGhostDispersal: 0.6
    lensFlareHaloWidth: 0.25
    lensFlareBloomBias: 0.35
    lensFlareStretchToAspect: 1.0
    
    // ===============================================================
    // OIT (Order Independent Transparency)
    // ===============================================================
    
    property string oitMode: "weighted"
    
    oitMethod: oitMode === "weighted" ? SceneEnvironment.OITWeightedBlended : SceneEnvironment.OITNone
    
    // ===============================================================
    // COLOR ADJUSTMENTS
    // ===============================================================
    
    colorAdjustmentsEnabled: true
    adjustmentBrightness: 1.0
    adjustmentContrast: 1.05
    adjustmentSaturation: 1.05
}
