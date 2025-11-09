import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

ExtendedSceneEnvironment {
    id: env

    // Settings plumbing
    property var sceneBridge: null
    property var diagnosticsTrace: sceneBridge && sceneBridge.signalTrace ? sceneBridge.signalTrace : null
    property var environmentSettings: sceneBridge && sceneBridge.environment ? sceneBridge.environment : ({})
    property var effectsSettings: sceneBridge && sceneBridge.effects ? sceneBridge.effects : ({})
    property var qualitySettings: sceneBridge && sceneBridge.quality ? sceneBridge.quality : ({})
    property var _warningCache: ({})

    function _sectionPayload(section) {
        if (section === "environment")
            return environmentSettings
        if (section === "effects")
            return effectsSettings
        if (section === "quality")
            return qualitySettings
        return null
    }

    function _primaryKey(keys) {
        if (Array.isArray(keys))
            return keys.length > 0 ? keys[0] : ""
        return keys
    }

    function _valueFromSection(section, keys) {
        var payload = _sectionPayload(section)
        if (!payload || typeof payload !== "object")
            return undefined
        var keyList = Array.isArray(keys) ? keys : [keys]
        for (var i = 0; i < keyList.length; ++i) {
            var key = keyList[i]
            if (Object.prototype.hasOwnProperty.call(payload, key)) {
                var candidate = payload[key]
                if (candidate !== undefined && candidate !== null)
                    return candidate
            }
        }
        return undefined
    }

    function _sceneScaleFactor() {
        if (sceneBridge && sceneBridge.sceneScaleFactor !== undefined) {
            var numeric = Number(sceneBridge.sceneScaleFactor)
            if (Number.isFinite(numeric) && numeric > 0)
                return numeric
        }
        return 1.0
    }

    function toSceneLength(value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            return 0.0
        return numeric * _sceneScaleFactor()
    }

    function _recordOverlayWarning(entry) {
        var overlay = diagnosticsTrace
        if (!overlay || typeof overlay.recordObservation !== "function")
            return
        try {
            overlay.recordObservation("settings.graphicsFallback", entry, "qml", "RealismEnvironment")
        } catch (error) {
            console.debug("RealismEnvironment: overlay record failed", error)
        }
    }

    function _warn(section, keys, reason, fallback) {
        var keyName = _primaryKey(keys)
        var cacheKey = section + ":" + keyName + ":" + reason
        if (_warningCache[cacheKey])
            return
        _warningCache[cacheKey] = true

        var fallbackText = fallback === undefined ? "<undefined>" : String(fallback)
        var message = "Missing graphics." + section + "." + keyName + " (" + reason + "); using " + fallbackText
        console.warn("RealismEnvironment:", message)

        if (sceneBridge && typeof sceneBridge.logQmlEvent === "function") {
            try {
                sceneBridge.logQmlEvent("warning", "RealismEnvironment." + section + "." + keyName)
            } catch (error) {
                console.debug("RealismEnvironment: logQmlEvent failed", error)
            }
        }

        try {
            var structured = {
                level: "warning",
                logger: "qml.realism_environment",
                event: "settings_fallback",
                section: section,
                key: keyName,
                reason: reason,
                fallback: fallbackText,
                timestamp: new Date().toISOString()
            }
            console.log(JSON.stringify(structured))
        } catch (error) {
            console.debug("RealismEnvironment: structured log failed", error)
        }

        _recordOverlayWarning({
            section: section,
            key: keyName,
            reason: reason,
            fallback: fallbackText
        })
    }

    function _bool(section, keys, fallback) {
        var value = _valueFromSection(section, keys)
        if (value === undefined) {
            _warn(section, keys, "missing", fallback)
            return fallback
        }
        if (typeof value === "boolean")
            return value
        if (typeof value === "number")
            return value !== 0
        if (typeof value === "string") {
            var normalized = value.trim().toLowerCase()
            if (normalized === "true" || normalized === "1" || normalized === "on" || normalized === "yes")
                return true
            if (normalized === "false" || normalized === "0" || normalized === "off" || normalized === "no")
                return false
        }
        _warn(section, keys, "invalid", fallback)
        return fallback
    }

    function _number(section, keys, fallback) {
        var fallbackValue = fallback
        if (!isFinite(fallbackValue)) {
            console.error(
                        "RealismEnvironment:",
                        "Invalid numeric fallback for",
                        section + "." + _primaryKey(keys) + ":",
                        fallbackValue,
                        "- using 0 instead")
            fallbackValue = 0
        }
        var value = _valueFromSection(section, keys)
        if (value === undefined) {
            _warn(section, keys, "missing", fallbackValue)
            return Number(fallbackValue)
        }
        var numeric = Number(value)
        if (isFinite(numeric))
            return numeric
        _warn(section, keys, "invalid", fallbackValue)
        return Number(fallbackValue)
    }

    function _string(section, keys, fallback) {
        var value = _valueFromSection(section, keys)
        if (value === undefined) {
            _warn(section, keys, "missing", fallback)
            return String(fallback)
        }
        if (typeof value === "string")
            return value
        _warn(section, keys, "invalid", fallback)
        return String(fallback)
    }

    function _color(section, keys, fallback) {
        var fallbackColor = Qt.color(fallback)
        var value = _valueFromSection(section, keys)
        if (value === undefined) {
            _warn(section, keys, "missing", fallback)
            return fallbackColor
        }
        if (typeof value === "string") {
            try {
                return Qt.color(value)
            } catch (error) {
                console.debug("RealismEnvironment: invalid color", value, error)
            }
        }
        _warn(section, keys, "invalid", fallback)
        return fallbackColor
    }

    function _resolvedBackgroundMode() {
        var mode = _string("environment", ["background_mode", "backgroundMode"], "color").toLowerCase()
        if (mode === "skybox")
            return SceneEnvironment.SkyBox
        if (mode === "transparent")
            return SceneEnvironment.Transparent
        if (mode === "color")
            return SceneEnvironment.Color
        _warn("environment", "background_mode", "invalid", "color")
        return SceneEnvironment.Color
    }

    function _tonemapMode() {
        var name = _string("effects", "tonemap_mode", "filmic").toLowerCase()
        switch (name) {
        case "linear":
            return SceneEnvironment.TonemapModeLinear
        case "reinhard":
            _warn("effects", "tonemap_mode", "unsupported", "filmic")
            return SceneEnvironment.TonemapModeFilmic
        case "filmic":
            return SceneEnvironment.TonemapModeFilmic
        case "none":
            return SceneEnvironment.TonemapModeNone
        default:
            _warn("effects", "tonemap_mode", "invalid", "filmic")
            return SceneEnvironment.TonemapModeFilmic
        }
    }

    function _resolveAntialiasingMode() {
        var quality = qualitySettings
        if (quality && typeof quality === "object" && quality.antialiasing && typeof quality.antialiasing === "object") {
            var primary = quality.antialiasing.primary
            if (typeof primary === "string") {
                var normalized = primary.trim().toLowerCase()
                if (normalized === "noaa" || normalized === "none")
                    return SceneEnvironment.NoAA
                if (normalized === "ssaa")
                    return SceneEnvironment.SSAA
                if (normalized === "msaa")
                    return SceneEnvironment.MSAA
            }
        }
        var rawTaa = _valueFromSection("quality", ["taa_enabled", "taa"])
        if (rawTaa !== undefined) {
            if (typeof rawTaa === "boolean")
                return rawTaa ? SceneEnvironment.ProgressiveAA : SceneEnvironment.NoAA
            if (typeof rawTaa === "number")
                return rawTaa !== 0 ? SceneEnvironment.ProgressiveAA : SceneEnvironment.NoAA
            if (typeof rawTaa === "string") {
                var taaNormalized = rawTaa.trim().toLowerCase()
                if (taaNormalized === "true" || taaNormalized === "1" || taaNormalized === "on")
                    return SceneEnvironment.ProgressiveAA
                if (taaNormalized === "false" || taaNormalized === "0" || taaNormalized === "off")
                    return SceneEnvironment.NoAA
            }
        }
        return SceneEnvironment.ProgressiveAA
    }

    // Background & probes
    property int resolvedBackgroundMode: _resolvedBackgroundMode()
    property color sceneClearColor: _color("environment", ["background_color", "backgroundColor"], "#2a2a2a")
    property bool useSkybox: _bool("environment", "skybox_enabled", false)
    property bool useLightProbe: _bool("environment", ["ibl_enabled", "ibl_lighting_enabled"], false)
    property var hdrTexture: null
    property real iblExposure: _number("environment", ["ibl_intensity", "probe_intensity"], 1.0)
    property real environmentProbeHorizon: _number("environment", ["probe_horizon", "skybox_blur"], 0.08)

    // Tonemapping & exposure
    property bool tonemapEnabled: _bool("effects", ["tonemap_enabled", "tonemapActive"], true)
    property int tonemapModeSetting: _tonemapMode()
    property real sceneExposure: _number("effects", ["tonemap_exposure", "exposure"], 1.0)
    property real sceneWhitePoint: _number("effects", ["tonemap_white_point", "white_point"], 2.0)
    property int environmentAntialiasingMode: _resolveAntialiasingMode()

    // Antialiasing toggles
    property bool enableFxaa: _bool("quality", ["fxaa_enabled", "fxaa"], true)
    property bool specularAntialiasingEnabled: _bool("quality", ["specular_aa", "specularAA"], true)
    property bool temporalAntialiasingEnabled: _bool("quality", ["taa_enabled", "taa"], true)
    property bool dithering: _bool("quality", "dithering", true)

    // Ambient occlusion
    property bool ssaoEnabled: _bool("environment", ["ao_enabled", "ssao_enabled"], true)
    property int ssaoSampleRate: Math.round(_number("environment", ["ao_sample_rate", "ssao_sample_rate"], 4))
    property real ssaoRadius: _number("environment", ["ao_radius", "ssao_radius"], 0.008)
    property real ssaoIntensity: _number("environment", ["ao_strength", "ssao_intensity"], 1.0)
    property real ssaoSoftness: _number("environment", ["ao_softness", "ssao_softness"], 20.0)

    // Bloom/glow
    property bool bloomEnabled: _bool("effects", ["bloom_enabled", "glow_enabled"], true)
    property real bloomIntensity: _number("effects", ["bloom_intensity", "glow_intensity"], 0.6)
    property real bloomThreshold: _number("effects", ["bloom_threshold", "glow_hdr_minimum"], 1.0)
    property real bloomStrength: _number("effects", ["bloom_glow_strength", "glow_strength"], 0.8)
    property real bloomSecondaryBloom: _number("effects", ["bloom_spread", "glow_bloom"], 0.5)
    property bool glowQualityHighEnabled: _bool("effects", ["bloom_quality_high", "glow_quality_high"], true)
    property bool glowUseBicubic: _bool("effects", ["bloom_bicubic_upscale", "glow_use_bicubic"], true)
    property real glowHdrMaximumValue: _number("effects", ["bloom_hdr_max", "glow_hdr_maximum"], 8.0)
    property real glowHdrScale: _number("effects", ["bloom_hdr_scale", "glow_hdr_scale"], 2.0)
    property int glowBlendModeValue: Math.round(_number("effects", ["glow_blend_mode", "blend_mode"], 0))

    // Lens flare
    property bool lensFlareActive: _bool("effects", ["lens_flare", "lens_flare_enabled"], true)
    property int lensFlareGhosts: Math.round(_number("effects", ["lens_flare_ghost_count", "lens_flare_ghosts"], 3))
    property real lensFlareGhostDispersalValue: _number("effects", ["lens_flare_ghost_dispersal"], 0.6)
    property real lensFlareHaloWidthValue: _number("effects", ["lens_flare_halo_width"], 0.25)
    property real lensFlareBloomBiasValue: _number("effects", ["lens_flare_bloom_bias"], 0.35)
    property real lensFlareStretchValue: _number("effects", ["lens_flare_stretch_to_aspect"], 1.0)

    // Depth of field
    property bool depthOfFieldActive: _bool("effects", ["depth_of_field", "dof_enabled"], false)
    property real depthOfFieldFocusDistanceValue: _number("effects", ["dof_focus_distance", "focus_distance"], 2.5)
    property real depthOfFieldFocusRangeValue: _number("effects", ["dof_focus_range", "focus_range"], 0.9)
    property real depthOfFieldBlurAmountValue: _number("effects", ["dof_blur", "blur_amount"], 3.0)

    // Fog
    property bool fogEnabled: _bool("environment", ["fog_enabled", "fog_active"], false)
    property color fogColor: _color("environment", ["fog_color", "fogColor"], "#d0d8e8")
    property real fogDensity: _number("environment", ["fog_density", "fogDensity"], 0.06)
    property real fogDepthNear: _number("environment", ["fog_depth_near", "fog_near"], 2.0)
    property real fogDepthFar: _number("environment", ["fog_depth_far", "fog_far"], 20.0)

    // Vignette & color adjustments
    property bool vignetteActive: _bool("effects", ["vignette", "vignette_enabled"], true)
    property real vignetteRadiusValue: _number("effects", ["vignette_radius"], 0.4)
    property real vignetteStrengthValue: _number("effects", ["vignette_strength"], 0.7)
    property bool colorAdjustmentsActive: _bool("effects", ["color_adjustments_active", "colorAdjustmentsEnabled"], true)
    property real adjustmentBrightnessValue: _number("effects", ["adjustment_brightness"], 1.0)
    property real adjustmentContrastValue: _number("effects", ["adjustment_contrast"], 1.05)
    property real adjustmentSaturationValue: _number("effects", ["adjustment_saturation"], 1.05)

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
    aoDistance: env.toSceneLength(env.ssaoRadius)
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
    depthOfFieldFocusDistance: env.toSceneLength(env.depthOfFieldFocusDistanceValue)
    depthOfFieldFocusRange: env.toSceneLength(env.depthOfFieldFocusRangeValue)
    depthOfFieldBlurAmount: env.depthOfFieldBlurAmountValue

    fog: Fog {
        enabled: env.fogEnabled
        color: env.fogColor
        density: env.fogDensity
        depthNear: env.toSceneLength(env.fogDepthNear)
        depthFar: env.toSceneLength(env.fogDepthFar)
    }

    vignetteEnabled: env.vignetteActive
    vignetteRadius: env.vignetteRadiusValue
    vignetteStrength: env.vignetteStrengthValue

    colorAdjustmentsEnabled: env.colorAdjustmentsActive
    adjustmentBrightness: env.adjustmentBrightnessValue
    adjustmentContrast: env.adjustmentContrastValue
    adjustmentSaturation: env.adjustmentSaturationValue
}
