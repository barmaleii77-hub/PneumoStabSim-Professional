import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

ExtendedSceneEnvironment {
    id: env

    // Background & probes
    property int resolvedBackgroundMode: SceneEnvironment.Color
    property color sceneClearColor: "#2a2a2a"
    property bool useSkybox: false
    property bool useLightProbe: false
    property var hdrTexture: null
    property real iblExposure: 1.0
    property real environmentProbeHorizon: 0.08

    // Tonemapping & exposure
    property bool tonemapEnabled: true
    property int tonemapModeSetting: SceneEnvironment.TonemapModeFilmic
    property real sceneExposure: 1.0
    property real sceneWhitePoint: 2.0
    property int environmentAntialiasingMode: SceneEnvironment.ProgressiveAA

    // Antialiasing toggles
    property bool enableFxaa: true
    property bool specularAntialiasingEnabled: true
    property bool temporalAntialiasingEnabled: true
    property bool dithering: true

    // Ambient occlusion
    property bool ssaoEnabled: true
    property int ssaoSampleRate: 3
    property real ssaoRadius: 200.0
    property real ssaoIntensity: 70.0
    property real ssaoSoftness: 20.0

    // Bloom/glow
    property bool bloomEnabled: true
    property real bloomIntensity: 0.6
    property real bloomThreshold: 1.0
    property real bloomStrength: 0.8
    property real bloomSecondaryBloom: 0.5
    property bool glowQualityHighEnabled: true
    property bool glowUseBicubic: true
    property real glowHdrMaximumValue: 8.0
    property real glowHdrScale: 2.0
    property int glowBlendModeValue: 0

    // Lens flare
    property bool lensFlareActive: true
    property int lensFlareGhosts: 3
    property real lensFlareGhostDispersalValue: 0.6
    property real lensFlareHaloWidthValue: 0.25
    property real lensFlareBloomBiasValue: 0.35
    property real lensFlareStretchValue: 1.0

    // Depth of field
    property bool depthOfFieldActive: false
    property real depthOfFieldFocusDistanceValue: 2000.0
    property real depthOfFieldFocusRangeValue: 900.0
    property real depthOfFieldBlurAmountValue: 3.0

    // Fog
    property bool fogEnabled: false
    property color fogColor: "#d0d8e8"
    property real fogDensity: 0.0008
    property real fogDepthNear: 0.0
    property real fogDepthFar: 20000.0

    // Vignette & color adjustments
    property bool vignetteActive: true
    property real vignetteRadiusValue: 0.4
    property real vignetteStrengthValue: 0.7
    property real adjustmentBrightnessValue: 1.0
    property real adjustmentContrastValue: 1.05
    property real adjustmentSaturationValue: 1.05

    backgroundMode: env.resolvedBackgroundMode
    clearColor: env.sceneClearColor
    skyBoxCubeMap: env.useSkybox && env.hdrTexture ? env.hdrTexture : null
    lightProbe: env.useLightProbe && env.hdrTexture ? env.hdrTexture : null
    probeExposure: env.iblExposure
    probeHorizon: env.environmentProbeHorizon

    tonemapMode: env.tonemapEnabled ? env.tonemapModeSetting : SceneEnvironment.TonemapModeNone
    exposure: env.sceneExposure
    whitePoint: env.sceneWhitePoint

    fxaaEnabled: env.enableFxaa
    specularAAEnabled: env.specularAntialiasingEnabled
    temporalAAEnabled: env.temporalAntialiasingEnabled
    ditheringEnabled: env.dithering
    antialiasingMode: env.environmentAntialiasingMode

    aoEnabled: env.ssaoEnabled
    aoSampleRate: env.ssaoSampleRate
    aoDistance: env.ssaoRadius
    aoStrength: env.ssaoIntensity
    aoSoftness: env.ssaoSoftness
    aoDither: true

    oitMethod: SceneEnvironment.OITWeightedBlended

    glowEnabled: env.bloomEnabled
    glowIntensity: env.bloomIntensity
    glowBloom: env.bloomSecondaryBloom
    glowStrength: env.bloomStrength
    glowQualityHigh: env.glowQualityHighEnabled
    glowUseBicubicUpscale: env.glowUseBicubic
    glowHDRMinimumValue: env.bloomThreshold
    glowHDRMaximumValue: env.glowHdrMaximumValue
    glowHDRScale: env.glowHdrScale
    glowBlendMode: env.glowBlendModeValue

    lensFlareEnabled: env.lensFlareActive
    lensFlareGhostCount: env.lensFlareGhosts
    lensFlareGhostDispersal: env.lensFlareGhostDispersalValue
    lensFlareHaloWidth: env.lensFlareHaloWidthValue
    lensFlareBloomBias: env.lensFlareBloomBiasValue
    lensFlareStretchToAspect: env.lensFlareStretchValue

    depthOfFieldEnabled: env.depthOfFieldActive
    depthOfFieldFocusDistance: env.depthOfFieldFocusDistanceValue
    depthOfFieldFocusRange: env.depthOfFieldFocusRangeValue
    depthOfFieldBlurAmount: env.depthOfFieldBlurAmountValue

    fog: Fog {
        enabled: env.fogEnabled
        color: env.fogColor
        density: env.fogDensity
        depthNear: env.fogDepthNear
        depthFar: env.fogDepthFar
    }

    vignetteEnabled: env.vignetteActive
    vignetteRadius: env.vignetteRadiusValue
    vignetteStrength: env.vignetteStrengthValue

    colorAdjustmentsEnabled: true
    adjustmentBrightness: env.adjustmentBrightnessValue
    adjustmentContrast: env.adjustmentContrastValue
    adjustmentSaturation: env.adjustmentSaturationValue
}
