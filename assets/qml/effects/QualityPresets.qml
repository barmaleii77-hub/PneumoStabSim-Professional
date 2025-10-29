import QtQml

QtObject {
    id: presets

    readonly property string defaultKey: "balanced"
    readonly property var definitions: ({
        "performance": {
            antialiasing: {
                aaPrimaryMode: "msaa",
                aaQualityLevel: "medium",
                aaPostMode: "fxaa",
                taaEnabled: false,
                fxaaEnabled: true,
                specularAAEnabled: false,
                ditheringEnabled: false
            },
            environment: {
                backgroundModeKey: "color",
                iblMasterEnabled: true,
                iblLightingEnabled: true,
                iblBackgroundEnabled: false,
                iblIntensity: 0.8,
                skyboxBrightness: 0.8,
                skyboxBlur: 0.6
            },
            effects: {
                depthOfFieldEnabled: false,
                dofBlurAmount: 2.5,
                dofAutoFocus: true,
                bloomEnabled: false,
                ssaoEnabled: false,
                ssaoDither: true,
                vignetteEnabled: false,
                lensFlareEnabled: false,
                tonemapEnabled: true,
                tonemapModeName: "filmic",
                tonemapExposure: 0.0,
                tonemapWhitePoint: 10.0,
                adjustmentBrightness: 0.0,
                adjustmentContrast: 0.0,
                adjustmentSaturation: 0.0
            }
        },
        "balanced": {
            antialiasing: {
                aaPrimaryMode: "ssaa",
                aaQualityLevel: "high",
                aaPostMode: "taa",
                taaEnabled: true,
                taaStrength: 0.45,
                taaMotionAdaptive: true,
                fxaaEnabled: false,
                specularAAEnabled: true,
                ditheringEnabled: true
            },
            environment: {
                backgroundModeKey: "skybox",
                iblMasterEnabled: true,
                iblLightingEnabled: true,
                iblBackgroundEnabled: true,
                iblIntensity: 1.0,
                skyboxBrightness: 1.0,
                skyboxBlur: 0.25
            },
            effects: {
                depthOfFieldEnabled: true,
                dofBlurAmount: 3.2,
                dofAutoFocus: true,
                dofFocusDistance: 2.4,
                bloomEnabled: true,
                bloomIntensity: 0.45,
                bloomThreshold: 1.0,
                bloomSpread: 0.7,
                bloomGlowStrength: 1.0,
                bloomHdrMax: 8.0,
                bloomHdrScale: 1.6,
                bloomQualityHigh: true,
                bloomBicubicUpscale: true,
                ssaoEnabled: true,
                ssaoRadius: 6.5,
                ssaoIntensity: 0.85,
                ssaoSoftness: 18.0,
                ssaoSampleRate: 3,
                ssaoDither: true,
                vignetteEnabled: true,
                vignetteStrength: 0.28,
                vignetteRadius: 0.68,
                lensFlareEnabled: false,
                lensFlareGhostCount: 3,
                lensFlareGhostDispersal: 0.55,
                lensFlareHaloWidth: 0.22,
                lensFlareBloomBias: 0.35,
                lensFlareStretchToAspect: true,
                tonemapEnabled: true,
                tonemapModeName: "filmic",
                tonemapExposure: 0.0,
                tonemapWhitePoint: 11.0,
                adjustmentBrightness: 0.0,
                adjustmentContrast: 0.05,
                adjustmentSaturation: 0.02
            }
        },
        "cinematic": {
            antialiasing: {
                aaPrimaryMode: "ssaa",
                aaQualityLevel: "high",
                aaPostMode: "taa",
                taaEnabled: true,
                taaStrength: 0.55,
                taaMotionAdaptive: false,
                fxaaEnabled: false,
                specularAAEnabled: true,
                ditheringEnabled: true
            },
            environment: {
                backgroundModeKey: "skybox",
                iblMasterEnabled: true,
                iblLightingEnabled: true,
                iblBackgroundEnabled: true,
                iblIntensity: 1.25,
                skyboxBrightness: 1.2,
                skyboxBlur: 0.1
            },
            effects: {
                depthOfFieldEnabled: true,
                dofBlurAmount: 6.0,
                dofAutoFocus: false,
                dofFocusDistance: 2.6,
                bloomEnabled: true,
                bloomIntensity: 0.75,
                bloomThreshold: 0.9,
                bloomSpread: 0.82,
                bloomGlowStrength: 1.25,
                bloomHdrMax: 10.0,
                bloomHdrScale: 2.4,
                bloomQualityHigh: true,
                bloomBicubicUpscale: true,
                ssaoEnabled: true,
                ssaoRadius: 7.5,
                ssaoIntensity: 1.1,
                ssaoSoftness: 22.0,
                ssaoSampleRate: 4,
                ssaoDither: true,
                vignetteEnabled: true,
                vignetteStrength: 0.35,
                vignetteRadius: 0.6,
                lensFlareEnabled: true,
                lensFlareGhostCount: 5,
                lensFlareGhostDispersal: 0.58,
                lensFlareHaloWidth: 0.27,
                lensFlareBloomBias: 0.4,
                lensFlareStretchToAspect: true,
                tonemapEnabled: true,
                tonemapModeName: "aces",
                tonemapExposure: 0.25,
                tonemapWhitePoint: 12.5,
                adjustmentBrightness: 0.02,
                adjustmentContrast: 0.08,
                adjustmentSaturation: 0.04
            }
        }
    })

    readonly property var availablePresets: Object.keys(definitions)

    function canonicalKey(name) {
        var normalized = String(name || "").trim().toLowerCase()
        if (!normalized)
            return defaultKey
        if (definitions.hasOwnProperty(normalized))
            return normalized
        return ""
    }

    function presetFor(name) {
        var key = canonicalKey(name)
        if (!key)
            return null
        return definitions[key]
    }

    function fallbackKey() {
        return defaultKey
    }
}
