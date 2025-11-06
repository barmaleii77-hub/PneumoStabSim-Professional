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

    // Источники контекста, передаются родителем для устранения не квалифицированных обращений
    // materialsDefaultsOverride: позволяет принудительно задать дефолтные материалы
    property var materialsDefaultsOverride: null
    // lightingContextOverride: приоритетный источник доступа к настройкам освещения
    property var lightingContextOverride: null

    readonly property var initialSceneDefaults: typeof initialSceneSettings !== "undefined" ? initialSceneSettings : null
    readonly property var initialAnimationDefaults: typeof initialAnimationSettings !== "undefined" ? initialAnimationSettings : null
    // ✅ FIX: не ссылаться на себя; брать initialGeometrySettings
    readonly property var initialGeometryDefaults: typeof initialGeometrySettings !== "undefined" ? initialGeometrySettings : null

    // ✅ Убираем глобальные идентификаторы, используем root.* свойства
    readonly property var contextMaterialsDefaults: (root.materialsDefaultsOverride !== undefined && root.materialsDefaultsOverride !== null)
                                                   ? root.materialsDefaultsOverride
                                                   : (typeof materialsDefaults !== "undefined" && materialsDefaults !== null
                                                      ? materialsDefaults
                                                      : (initialSceneDefaults && typeof initialSceneDefaults === "object" && initialSceneDefaults.materials !== undefined
                                                         ? initialSceneDefaults.materials
                                                         : (initialSceneDefaults && typeof initialSceneDefaults === "object" && initialSceneDefaults.graphics && typeof initialSceneDefaults.graphics === "object"
                                                            ? initialSceneDefaults.graphics.materials
                                                            : null)))

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

    // ✅ Убираем глобальные обращения — используем lightingContextOverride или lightingAccess
    readonly property var contextLightingDefaults: (root.lightingContextOverride !== undefined && root.lightingContextOverride !== null)
                                                   ? root.lightingContextOverride
                                                   : (typeof lightingAccess !== "undefined" && lightingAccess !== null
                                                      ? lightingAccess
                                                      : (initialSceneDefaults && typeof initialSceneDefaults === "object" && initialSceneDefaults.lighting !== undefined
                                                         ? initialSceneDefaults.lighting
                                                         : (initialSceneDefaults && typeof initialSceneDefaults === "object" && initialSceneDefaults.graphics && typeof initialSceneDefaults.graphics === "object"
                                                            ? initialSceneDefaults.graphics.lighting
                                                            : null)))

    QualityPresets {
        id: qualityProfiles
    }

    // Structured diagnostics toggles (disabled by default)
    property bool diagnosticsLoggingEnabled: false

    function logStructured(eventName, params) {
        if (!diagnosticsLoggingEnabled)
            return

        // ✅ Не используем глобальный window; предпочитаем sceneBridge
        if (root.sceneBridge && typeof root.sceneBridge.logQmlEvent === "function") {
            try {
                root.sceneBridge.logQmlEvent("function_called", eventName)
            } catch (error) {
                console.debug("SceneEnvironmentController", eventName, "sceneBridge.logQmlEvent failed", error)
            }
        }

        function ownKeys(value) {
            if (!value || typeof value !== "object")
                return []
            var keys = []
            for (var key in value) {
                if (Object.prototype.hasOwnProperty.call(value, key))
                    keys.push(key)
            }
            return keys
        }

        function sectionSummary(value) {
            var summary = {}
            if (!value || typeof value !== "object")
                return summary
            for (var key in value) {
                if (!Object.prototype.hasOwnProperty.call(value, key))
                    continue
                var nested = value[key]
                if (nested && typeof nested === "object")
                    summary[key] = ownKeys(nested).length
            }
            return summary
        }

        var payload = {
            level: "info",
            logger: "qml.scene_environment",
            event: eventName,
            keys: ownKeys(params),
            sections: sectionSummary(params),
            timestamp: new Date().toISOString()
        }

        console.log(JSON.stringify(payload))
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

    // ===============================================================
    // COLOR ADJUSTMENTS (Qt 6.10+)
    // ===============================================================

    property alias adjustmentBrightnessValue: root.adjustmentBrightness
    property alias adjustmentContrastValue: root.adjustmentContrast
    property alias adjustmentSaturationValue: root.adjustmentSaturation

    // ---------------------------------------------------------------
    // Legacy compatibility aliases (camelCase + legacy property names)
    // ---------------------------------------------------------------
    property alias bloomEnabled: root.glowEnabled
    property alias bloomIntensity: root.glowIntensity
    property alias bloomThreshold: root.glowHDRMinimumValue
    property alias bloomSpread: root.glowBloom
    property alias bloomGlowStrength: root.glowStrength
    property alias bloomQualityHigh: root.glowQualityHigh
    property alias bloomUseBicubicUpscale: root.glowUseBicubicUpscale
    property alias bloomHdrMaximum: root.glowHDRMaximumValue
    property alias bloomHdrScale: root.glowHDRScale

    property alias internalLensFlareEnabled: root.lensFlareEnabled
    property alias lensFlareGhostCountValue: root.lensFlareGhostCount
    property alias lensFlareGhostDispersalValue: root.lensFlareGhostDispersal
    property alias lensFlareHaloWidthValue: root.lensFlareHaloWidth
    property alias lensFlareBloomBiasValue: root.lensFlareBloomBias
    property alias lensFlareStretchValue: root.lensFlareStretchToAspect

    property alias internalDepthOfFieldEnabled: root.depthOfFieldEnabled
    property alias dofFocusDistance: root.depthOfFieldFocusDistance
    property alias dofFocusRange: root.depthOfFieldFocusRange
    property alias dofBlurAmount: root.depthOfFieldBlurAmount

    property alias internalVignetteEnabled: root.vignetteEnabled
    property alias internalVignetteStrength: root.vignetteStrength
    property alias vignetteRadiusValue: root.vignetteRadius

    colorAdjustmentsEnabled: effectsBoolDefault("colorAdjustmentsEnabled", "color_adjustments_enabled", true)

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

    function effectsBoolDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEffectsDefaults)
            return fallback
        var value = boolFromKeys(root.contextEffectsDefaults, primaryKey, secondaryKey)
        return value === undefined ? fallback : value
    }

    function effectsNumberDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEffectsDefaults)
            return fallback
        var value = numberFromKeys(root.contextEffectsDefaults, primaryKey, secondaryKey)
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

    function applyEffectsPayload(params) {
        if (!params)
            return

        function coerceNumber(value) {
            var numeric = Number(value)
            return isFinite(numeric) ? numeric : undefined
        }

        function coerceInt(value) {
            var numeric = coerceNumber(value)
            if (numeric === undefined)
                return undefined
            return Math.round(numeric)
        }

        function assignLensFlareGhostCount(value) {
            var ghostCount = coerceInt(value)
            if (ghostCount === undefined)
                return
            if (ghostCount < 0)
                ghostCount = 0
            try {
                lensFlareGhostCountValue = ghostCount
            } catch (error) {
                console.warn("⚠️ SceneEnvironmentController: lensFlareGhostCount assignment failed", error)
            }
        }

        var bloomSection = valueFromKeys(params, "bloom", "bloom")
        if (bloomSection && typeof bloomSection === "object") {
            var nestedBloomEnabled = boolFromKeys(bloomSection, "enabled", "enabled")
            if (nestedBloomEnabled !== undefined)
                bloomEnabled = !!nestedBloomEnabled

            var nestedBloomIntensity = numberFromKeys(bloomSection, "intensity", "intensity")
            if (nestedBloomIntensity !== undefined)
                bloomIntensity = nestedBloomIntensity

            var nestedBloomThreshold = numberFromKeys(bloomSection, "threshold", "threshold")
            if (nestedBloomThreshold !== undefined)
                bloomThreshold = nestedBloomThreshold

            var nestedBloomSpread = numberFromKeys(bloomSection, "spread", "spread")
            if (nestedBloomSpread !== undefined)
                bloomSpread = nestedBloomSpread

            var nestedGlowStrength = numberFromKeys(bloomSection, "glowStrength", "glow_strength")
            if (nestedGlowStrength !== undefined)
                bloomGlowStrength = nestedGlowStrength

            var nestedHdrMax = numberFromKeys(bloomSection, "hdrMax", "hdr_max")
            if (nestedHdrMax !== undefined)
                bloomHdrMaximum = nestedHdrMax

            var nestedHdrScale = numberFromKeys(bloomSection, "hdrScale", "hdr_scale")
            if (nestedHdrScale !== undefined)
                bloomHdrScale = nestedHdrScale

            var nestedQualityHigh = boolFromKeys(bloomSection, "qualityHigh", "quality_high")
            if (nestedQualityHigh !== undefined)
                bloomQualityHigh = !!nestedQualityHigh

            var nestedBicubic = boolFromKeys(bloomSection, "bicubicUpscale", "bicubic_upscale")
            if (nestedBicubic !== undefined)
                bloomUseBicubicUpscale = !!nestedBicubic
        }

        var bloomEnabledValue = boolFromKeys(params, "bloomEnabled", "bloom_enabled")
        if (bloomEnabledValue !== undefined)
            bloomEnabled = !!bloomEnabledValue

        var bloomIntensityValue = numberFromKeys(params, "bloomIntensity", "bloom_intensity")
        if (bloomIntensityValue !== undefined)
            bloomIntensity = bloomIntensityValue

        var bloomThresholdValue = numberFromKeys(params, "bloomThreshold", "bloom_threshold")
        if (bloomThresholdValue !== undefined)
            bloomThreshold = bloomThresholdValue

        var bloomSpreadValue = numberFromKeys(params, "bloomSpread", "bloom_spread")
        if (bloomSpreadValue !== undefined)
            bloomSpread = bloomSpreadValue

        var bloomGlowStrengthValue = numberFromKeys(params, "bloomGlowStrength", "bloom_glow_strength")
        if (bloomGlowStrengthValue !== undefined)
            bloomGlowStrength = bloomGlowStrengthValue

        var bloomHdrMaximumValue = numberFromKeys(params, "bloomHdrMaximum", "bloom_hdr_max")
        if (bloomHdrMaximumValue !== undefined)
            bloomHdrMaximum = bloomHdrMaximumValue

        var bloomHdrScaleValue = numberFromKeys(params, "bloomHdrScale", "bloom_hdr_scale")
        if (bloomHdrScaleValue !== undefined)
            bloomHdrScale = bloomHdrScaleValue

        var bloomQualityHighValue = boolFromKeys(params, "bloomQualityHigh", "bloom_quality_high")
        if (bloomQualityHighValue !== undefined)
            bloomQualityHigh = !!bloomQualityHighValue

        var bloomBicubicValue = boolFromKeys(params, "bloomUseBicubicUpscale", "bloom_bicubic_upscale")
        if (bloomBicubicValue !== undefined)
            bloomUseBicubicUpscale = !!bloomBicubicValue

        var depthOfFieldSection = valueFromKeys(params, "depthOfField", "depth_of_field")
        if (depthOfFieldSection && typeof depthOfFieldSection === "object") {
            var nestedDofEnabled = boolFromKeys(depthOfFieldSection, "enabled", "enabled")
            if (nestedDofEnabled !== undefined)
                internalDepthOfFieldEnabled = !!nestedDofEnabled

            var nestedDofFocus = numberFromKeys(depthOfFieldSection, "focusDistance", "focus_distance")
            if (nestedDofFocus !== undefined)
                dofFocusDistance = nestedDofFocus

            var nestedDofRange = numberFromKeys(depthOfFieldSection, "focusRange", "focus_range")
            if (nestedDofRange !== undefined)
                dofFocusRange = nestedDofRange

            var nestedDofBlur = numberFromKeys(depthOfFieldSection, "blurAmount", "blur")
            if (nestedDofBlur === undefined)
                nestedDofBlur = numberFromKeys(depthOfFieldSection, "blur", "blur")
            if (nestedDofBlur !== undefined)
                dofBlurAmount = nestedDofBlur

            var nestedDofAutoFocus = boolFromKeys(depthOfFieldSection, "autoFocus", "auto_focus")
            if (nestedDofAutoFocus !== undefined && ("depthOfFieldAutoFocus" in root))
                root.depthOfFieldAutoFocus = !!nestedDofAutoFocus
        }

        var dofEnabledValue = boolFromKeys(params, "depthOfFieldEnabled", "depth_of_field")
        if (dofEnabledValue !== undefined)
            internalDepthOfFieldEnabled = !!dofEnabledValue

        var dofFocusValue = numberFromKeys(params, "dofFocusDistance", "dof_focus_distance")
        if (dofFocusValue !== undefined)
            dofFocusDistance = dofFocusValue

        var dofRangeValue = numberFromKeys(params, "dofFocusRange", "dof_focus_range")
        if (dofRangeValue !== undefined)
            dofFocusRange = dofRangeValue

        var dofBlurValue = numberFromKeys(params, "dofBlurAmount", "dof_blur")
        if (dofBlurValue !== undefined)
            dofBlurAmount = dofBlurValue

        var dofAutoFocusValue = boolFromKeys(params, "dofAutoFocus", "dof_auto_focus")
        if (dofAutoFocusValue !== undefined && ("depthOfFieldAutoFocus" in root))
            root.depthOfFieldAutoFocus = !!dofAutoFocusValue

        var lensFlareSection = valueFromKeys(params, "lensFlare", "lens_flare")
        if (lensFlareSection && typeof lensFlareSection === "object") {
            var nestedLensEnabled = boolFromKeys(lensFlareSection, "enabled", "enabled")
            if (nestedLensEnabled !== undefined)
                internalLensFlareEnabled = !!nestedLensEnabled

            var nestedGhostCount = numberFromKeys(lensFlareSection, "ghostCount", "ghost_count")
            if (nestedGhostCount === undefined)
                nestedGhostCount = numberFromKeys(lensFlareSection, "ghosts", "ghosts")
            assignLensFlareGhostCount(nestedGhostCount)

            var nestedGhostDispersal = numberFromKeys(lensFlareSection, "ghostDispersal", "ghost_dispersal")
            if (nestedGhostDispersal !== undefined)
                lensFlareGhostDispersalValue = nestedGhostDispersal

            var nestedHaloWidth = numberFromKeys(lensFlareSection, "haloWidth", "halo_width")
            if (nestedHaloWidth !== undefined)
                lensFlareHaloWidthValue = nestedHaloWidth

            var nestedBloomBias = numberFromKeys(lensFlareSection, "bloomBias", "bloom_bias")
            if (nestedBloomBias !== undefined)
                lensFlareBloomBiasValue = nestedBloomBias

            var nestedStretch = boolFromKeys(lensFlareSection, "stretchToAspect", "stretch_to_aspect")
            if (nestedStretch !== undefined)
                lensFlareStretchValue = !!nestedStretch
        }

        var lensFlareEnabledValue = boolFromKeys(params, "lensFlareEnabled", "lens_flare")
        if (lensFlareEnabledValue !== undefined)
            internalLensFlareEnabled = !!lensFlareEnabledValue

        var lensFlareGhostCountRaw = numberFromKeys(params, "lensFlareGhostCount", "lens_flare_ghost_count")
        assignLensFlareGhostCount(lensFlareGhostCountRaw)

        var lensFlareGhostDispersalRaw = numberFromKeys(params, "lensFlareGhostDispersal", "lens_flare_ghost_dispersal")
        if (lensFlareGhostDispersalRaw !== undefined)
            lensFlareGhostDispersalValue = lensFlareGhostDispersalRaw

        var lensFlareHaloWidthRaw = numberFromKeys(params, "lensFlareHaloWidth", "lens_flare_halo_width")
        if (lensFlareHaloWidthRaw !== undefined)
            lensFlareHaloWidthValue = lensFlareHaloWidthRaw

        var lensFlareBloomBiasRaw = numberFromKeys(params, "lensFlareBloomBias", "lens_flare_bloom_bias")
        if (lensFlareBloomBiasRaw !== undefined)
            lensFlareBloomBiasValue = lensFlareBloomBiasRaw

        var lensFlareStretchValueRaw = boolFromKeys(params, "lensFlareStretchToAspect", "lens_flare_stretch_to_aspect")
        if (lensFlareStretchValueRaw !== undefined)
            lensFlareStretchValue = !!lensFlareStretchValueRaw

        var colorSection = valueFromKeys(params, "colorAdjustments", "color_adjustments")
        if (colorSection && typeof colorSection === "object") {
            var nestedEnabled = boolFromKeys(colorSection, "enabled", "enabled")
            if (nestedEnabled !== undefined)
                colorAdjustmentsEnabled = !!nestedEnabled

            var nestedBrightness = numberFromKeys(colorSection, "brightness", "brightness")
            if (nestedBrightness !== undefined)
                adjustmentBrightnessValue = nestedBrightness

            var nestedContrast = numberFromKeys(colorSection, "contrast", "contrast")
            if (nestedContrast !== undefined)
                adjustmentContrastValue = nestedContrast

            var nestedSaturation = numberFromKeys(colorSection, "saturation", "saturation")
            if (nestedSaturation !== undefined)
                adjustmentSaturationValue = nestedSaturation
        }

        var enabledValue = boolFromKeys(params, "colorAdjustmentsEnabled", "color_adjustments_enabled")
        if (enabledValue !== undefined)
            colorAdjustmentsEnabled = !!enabledValue

        var brightnessValue = numberFromKeys(params, "adjustmentBrightness", "adjustment_brightness")
        if (brightnessValue !== undefined)
            adjustmentBrightnessValue = brightnessValue

        var contrastValue = numberFromKeys(params, "adjustmentContrast", "adjustment_contrast")
        if (contrastValue !== undefined)
            adjustmentContrastValue = contrastValue

        var saturationValue = numberFromKeys(params, "adjustmentSaturation", "adjustment_saturation")
        if (saturationValue !== undefined)
            adjustmentSaturationValue = saturationValue

        var vignetteSection = params.vignette && typeof params.vignette === "object"
                ? params.vignette
                : null
        if (vignetteSection) {
            var nestedVignetteEnabled = boolFromKeys(vignetteSection, "enabled", "enabled")
            if (nestedVignetteEnabled !== undefined)
                vignetteEnabled = !!nestedVignetteEnabled
            var nestedVignetteStrength = numberFromKeys(vignetteSection, "strength", "strength")
            if (nestedVignetteStrength !== undefined)
                internalVignetteStrength = nestedVignetteStrength
            var nestedVignetteRadius = numberFromKeys(vignetteSection, "radius", "radius")
            if (nestedVignetteRadius !== undefined)
                vignetteRadiusValue = Math.max(0.0, nestedVignetteRadius)
        }

        var vignetteEnabledValue = boolFromKeys(params, "vignetteEnabled", "vignette_enabled")
        if (vignetteEnabledValue === undefined)
            vignetteEnabledValue = boolFromKeys(params, "vignette", "vignette")
        if (vignetteEnabledValue !== undefined)
            vignetteEnabled = !!vignetteEnabledValue

        var vignetteStrengthValue = numberFromKeys(params, "vignetteStrength", "vignette_strength")
        if (vignetteStrengthValue !== undefined)
            internalVignetteStrength = vignetteStrengthValue

        var vignetteRadiusValueRaw = numberFromKeys(params, "vignetteRadius", "vignette_radius")
        if (vignetteRadiusValueRaw !== undefined)
            vignetteRadiusValue = Math.max(0.0, vignetteRadiusValueRaw)
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
        var fogTransmitCurveNested = Number(fog.transmit_curve)
        if (isFinite(fogTransmitCurveNested))
            fogTransmitCurve = fogTransmitCurveNested
    }
}
// EOF: close ExtendedSceneEnvironment component
}
