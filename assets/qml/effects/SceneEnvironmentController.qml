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
    property var diagnosticsTrace: sceneBridge && sceneBridge.signalTrace ? sceneBridge.signalTrace : null
    property var _settingsWarningCache: ({})

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
    property bool tonemapActive: effectsBoolDefault("tonemapActive", "tonemap_enabled", false)
    property string tonemapModeName: effectsStringDefault("tonemapModeName", "tonemap_mode", "filmic")
    property bool _tonemapModeGuard: false

    onTonemapActiveChanged: {
        var value = !!tonemapActive
        try {
            if (root.setProperty) {
                if (!root.property || root.property("tonemapActive") !== value)
                    root.setProperty("tonemapActive", value)
                if (!root.property || root.property("tonemapEnabled") !== value)
                    root.setProperty("tonemapEnabled", value)
            }
        } catch (error) {
            console.debug("SceneEnvironmentController: unable to sync tonemapEnabled", error)
        }
        try {
            mirrorHostProperty("tonemapActive", value)
        } catch (error) {
            console.debug("SceneEnvironmentController: mirror tonemapActive failed", error)
        }
    }

    onTonemapModeNameChanged: {
        if (_tonemapModeGuard)
            return
        var canonical = canonicalTonemapModeName(tonemapModeName)
        if (canonical !== tonemapModeName) {
            _tonemapModeGuard = true
            tonemapModeName = canonical
            _tonemapModeGuard = false
            return
        }
        _syncTonemapModeFromName(canonical)
        try {
            mirrorHostProperty("tonemapModeName", canonical)
        } catch (error) {
            console.debug("SceneEnvironmentController: mirror tonemapModeName failed", error)
        }
    }

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
    property real dofFocusDistanceMeters: effectsNumberDefault(
        "dofFocusDistance",
        "dof_focus_distance",
        2.5
    )
    property real dofFocusRangeMeters: effectsNumberDefault(
        "dofFocusRange",
        "dof_focus_range",
        0.9
    )
    property alias dofFocusDistance: root.dofFocusDistanceMeters
    property alias dofFocusRange: root.dofFocusRangeMeters
    property alias dofBlurAmount: root.depthOfFieldBlurAmount

    property alias internalVignetteEnabled: root.vignetteEnabled
    property alias internalVignetteStrength: root.vignetteStrength
    property alias vignetteRadiusValue: root.vignetteRadius

    // Fog (SceneEnvironment::fog) -------------------------------------------------
    property bool fogEnabled: environmentBoolDefault("fogEnabled", "fog_enabled", true)
    property color fogColor: environmentColorDefault("fogColor", "fog_color", "#aab9cf")
    property real fogDensity: environmentNumberDefault("fogDensity", "fog_density", 0.06)
    property bool fogDepthEnabled: environmentBoolDefault("fogDepthEnabled", "fog_depth_enabled", true)
    property real fogDepthCurve: environmentNumberDefault("fogDepthCurve", "fog_depth_curve", 1.0)
    property real fogDepthNear: environmentNumberDefault("fogDepthNear", "fog_depth_near", 2.0)
    property real fogDepthFar: environmentNumberDefault("fogDepthFar", "fog_depth_far", 20.0)
    property bool fogHeightEnabled: environmentBoolDefault("fogHeightEnabled", "fog_height_enabled", false)
    property real fogLeastIntenseY: environmentNumberDefault("fogLeastIntenseY", "fog_least_intense_y", 0.0)
    property real fogMostIntenseY: environmentNumberDefault("fogMostIntenseY", "fog_most_intense_y", 3.0)
    property real fogHeightCurve: environmentNumberDefault("fogHeightCurve", "fog_height_curve", 1.0)
    property bool fogTransmitEnabled: environmentBoolDefault("fogTransmitEnabled", "fog_transmit_enabled", true)
    property real fogTransmitCurve: environmentNumberDefault("fogTransmitCurve", "fog_transmit_curve", 1.0)
    property bool _fogSupportWarningShown: false

    Loader {
        id: fogLoader
        active: root.fogHelpersSupported
        sourceComponent: Fog {
            enabled: root.fogEnabled
            color: root.fogColor
            density: root.fogDensity
            depthEnabled: root.fogDepthEnabled && root.fogEnabled
            depthCurve: root.fogDepthCurve
            depthNear: root.toSceneLength(root.fogDepthNear)
            depthFar: root.toSceneLength(root.fogDepthFar)
            heightEnabled: root.fogHeightEnabled
            leastIntenseY: root.toSceneLength(root.fogLeastIntenseY)
            mostIntenseY: root.toSceneLength(root.fogMostIntenseY)
            heightCurve: root.fogHeightCurve
            transmitEnabled: root.fogTransmitEnabled
            transmitCurve: root.fogTransmitCurve
        }
        onStatusChanged: {
            if (status === Loader.Error) {
                root._emitFogSupportWarning(
                    qsTr("Fog helpers disabled: %1").arg(errorString() || qsTr("loader error"))
                )
            } else if (status === Loader.Ready) {
                console.log("🌫️ SceneEnvironmentController: fog helpers active (Qt", root.qtRuntimeVersionString || "unknown", ")")
            }
        }
    }

    fog: fogLoader.item

    depthOfFieldFocusDistance: root.toSceneLength(root.dofFocusDistanceMeters)
    depthOfFieldFocusRange: root.toSceneLength(root.dofFocusRangeMeters)

    property bool colorAdjustmentsEnabled: effectsBoolDefault(
        "colorAdjustmentsEnabled",
        "color_adjustments_enabled",
        true
    )
    property bool colorAdjustmentsActive: colorAdjustmentsEnabled
    property real adjustmentBrightness: effectsNumberDefault(
        "adjustmentBrightness",
        "adjustment_brightness",
        0.0
    )
    property real adjustmentContrast: effectsNumberDefault(
        "adjustmentContrast",
        "adjustment_contrast",
        0.0
    )
    property real adjustmentSaturation: effectsNumberDefault(
        "adjustmentSaturation",
        "adjustment_saturation",
        0.0
    )
    readonly property bool colorAdjustmentsHasOverrides: (Math.abs(adjustmentBrightness) > 0.0001)
            || (Math.abs(adjustmentContrast) > 0.0001)
            || (Math.abs(adjustmentSaturation) > 0.0001)

    function _syncColorAdjustmentFlags() {
        mirrorHostProperty("colorAdjustmentsHasOverrides", colorAdjustmentsHasOverrides)
        mirrorHostProperty("colorAdjustmentsActive", colorAdjustmentsActive)
    }

    onColorAdjustmentsEnabledChanged: {
        if (colorAdjustmentsActive !== colorAdjustmentsEnabled)
            colorAdjustmentsActive = colorAdjustmentsEnabled
        _syncColorAdjustmentFlags()
    }
    onColorAdjustmentsActiveChanged: {
        if (colorAdjustmentsEnabled !== colorAdjustmentsActive)
            colorAdjustmentsEnabled = colorAdjustmentsActive
        _syncColorAdjustmentFlags()
    }
    onAdjustmentBrightnessChanged: {
        mirrorHostProperty("adjustmentBrightness", adjustmentBrightness)
        _syncColorAdjustmentFlags()
    }
    onAdjustmentContrastChanged: {
        mirrorHostProperty("adjustmentContrast", adjustmentContrast)
        _syncColorAdjustmentFlags()
    }
    onAdjustmentSaturationChanged: {
        mirrorHostProperty("adjustmentSaturation", adjustmentSaturation)
        _syncColorAdjustmentFlags()
    }

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

 property string aaPrimaryMode: qualityStringDefault("aaPrimaryMode", "aa_primary_mode", "ssaa")
 property string aaQualityLevel: qualityStringDefault("aaQualityLevel", "aa_quality_level", "high")
 property string aaPostMode: qualityStringDefault("aaPostMode", "aa_post_mode", "taa")
 property bool taaEnabled: qualityBoolDefault("taaEnabled", "taa_enabled", true)
 property real taaStrength: qualityNumberDefault("taaStrength", "taa_strength", 0.4)
 property bool taaMotionAdaptive: qualityBoolDefault("taaMotionAdaptive", "taa_motion_adaptive", true)
 property bool fxaaEnabled: qualityBoolDefault("fxaaEnabled", "fxaa_enabled", false)
 property bool specularAAEnabled: qualityBoolDefault("specularAAEnabled", "specular_aa", false)
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

    property bool ditheringEnabled: qualityBoolDefault("ditheringEnabled", "dithering", true)
    property bool canUseDithering: false
    property real sceneScaleFactor:1.0

    readonly property string qtRuntimeVersionString: {
        if (typeof qtRuntimeVersion === "string" && qtRuntimeVersion.length > 0)
            return qtRuntimeVersion
        if (typeof Qt !== "undefined") {
            if (Qt.application && typeof Qt.application.qtVersion === "function") {
                try {
                    var fromApp = Qt.application.qtVersion()
                    if (fromApp)
                        return String(fromApp)
                } catch (qtVersionError) {
                    console.debug("SceneEnvironmentController: unable to query Qt.application.qtVersion", qtVersionError)
                }
            }
            if (typeof Qt.qVersion === "function") {
                try {
                    var direct = Qt.qVersion()
                    if (direct)
                        return String(direct)
                } catch (qVersionError) {
                    console.debug("SceneEnvironmentController: unable to query Qt.qVersion", qVersionError)
                }
            }
        }
        if (typeof Qt !== "undefined" && Qt.application && Qt.application.version !== undefined)
            return String(Qt.application.version)
        return ""
    }
    readonly property bool fogHelpersSupported: qtVersionAtLeast(6, 10) && typeof Fog !== "undefined"

    // Camera parameters required by custom fog shaders
    property real cameraClipNear: 0.1
    property real cameraClipFar: 10000.0
    property real cameraFieldOfView: 60.0
    property real cameraAspectRatio: 1.0

    function qtVersionAtLeast(requiredMajor, requiredMinor) {
        var versionString = root.qtRuntimeVersionString || "";
        if (!versionString)
            return false;
        var match = versionString.match(/(\d+)\.(\d+)/);
        if (!match)
            return false;
        var major = Number(match[1]);
        var minor = Number(match[2]);
        if (!isFinite(major) || !isFinite(minor))
            return false;
        if (major > requiredMajor)
            return true;
        if (major < requiredMajor)
            return false;
        return minor >= requiredMinor;
    }

    function _emitFogSupportWarning(reason) {
        if (root._fogSupportWarningShown)
            return
        root._fogSupportWarningShown = true
        var versionLabel = root.qtRuntimeVersionString || "unknown"
        console.warn("⚠️ SceneEnvironmentController:", reason, "(Qt", versionLabel + ")")
    }

    onFogHelpersSupportedChanged: {
        if (!fogHelpersSupported)
            root._emitFogSupportWarning(qsTr("Fog helpers require Qt 6.10 or newer"))
    }

    Component.onCompleted: {
        if (!root.fogHelpersSupported)
            root._emitFogSupportWarning(qsTr("Fog helpers require Qt 6.10 or newer"))
        Qt.callLater(_updateBufferRequirements)
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

    function hostHasProperty(host, name) {
        if (!host)
            return false
        try {
            if (host.hasOwnProperty && host.hasOwnProperty(name))
                return true
        } catch (error) {
            // ignore and fall back to `in` operator
        }
        return name in host
    }

    function mirrorHostProperty(propertyName, value) {
        var host = root.parent
        if (!hostHasProperty(host, propertyName))
            return
        if (host[propertyName] === value)
            return
        host[propertyName] = value
    }

    function _settingKey(primaryKey, secondaryKey) {
        if (primaryKey && String(primaryKey).length)
            return String(primaryKey)
        if (secondaryKey && String(secondaryKey).length)
            return String(secondaryKey)
        return "unknown"
    }

    function _recordSettingWarning(section, primaryKey, secondaryKey, reason, fallback) {
        var keyName = _settingKey(primaryKey, secondaryKey)
        var token = section + ":" + keyName + ":" + reason
        if (_settingsWarningCache[token])
            return
        _settingsWarningCache[token] = true

        var message = "Missing graphics." + section + "." + keyName + " (" + reason + "); fallback=" + fallback
        console.warn("SceneEnvironmentController:", message)

        logStructured("settings_fallback", {
            section: section,
            key: keyName,
            reason: reason,
            fallback: fallback
        })

        if (root.sceneBridge && typeof root.sceneBridge.logQmlEvent === "function") {
            try {
                root.sceneBridge.logQmlEvent("warning", "SceneEnvironmentController." + section + "." + keyName)
            } catch (error) {
                console.debug("SceneEnvironmentController: logQmlEvent failed", error)
            }
        }

        var overlay = diagnosticsTrace
        if (!overlay || typeof overlay.recordObservation !== "function")
            return
        try {
            overlay.recordObservation(
                "settings.graphicsFallback",
                {
                    section: section,
                    key: keyName,
                    reason: reason,
                    fallback: fallback
                },
                "qml",
                "SceneEnvironmentController"
            )
        } catch (error) {
            console.debug("SceneEnvironmentController: overlay record failed", error)
        }
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
        if (!root.contextEnvironmentDefaults) {
            _recordSettingWarning("environment", primaryKey, secondaryKey, "missing_context", fallback)
            return fallback
        }
        var value = boolFromKeys(root.contextEnvironmentDefaults, primaryKey, secondaryKey)
        if (value === undefined) {
            _recordSettingWarning("environment", primaryKey, secondaryKey, "missing", fallback)
            return fallback
        }
        return value
    }

    function environmentNumberDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEnvironmentDefaults) {
            _recordSettingWarning("environment", primaryKey, secondaryKey, "missing_context", fallback)
            return fallback
        }
        var value = numberFromKeys(root.contextEnvironmentDefaults, primaryKey, secondaryKey)
        if (value === undefined) {
            _recordSettingWarning("environment", primaryKey, secondaryKey, "missing", fallback)
            return fallback
        }
        return value
    }

    function environmentStringDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEnvironmentDefaults) {
            _recordSettingWarning("environment", primaryKey, secondaryKey, "missing_context", fallback)
            return fallback
        }
        var value = stringFromKeys(root.contextEnvironmentDefaults, primaryKey, secondaryKey)
        if (value === undefined) {
            _recordSettingWarning("environment", primaryKey, secondaryKey, "missing", fallback)
            return fallback
        }
        return value
    }

    function environmentColorDefault(primaryKey, secondaryKey, fallback) {
        var colorString = environmentStringDefault(primaryKey, secondaryKey, fallback)
        try {
            return Qt.color(colorString)
        } catch (error) {
            _recordSettingWarning("environment", primaryKey, secondaryKey, "invalid_color", fallback)
        }
        return Qt.color(fallback)
    }

    function effectsBoolDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEffectsDefaults) {
            _recordSettingWarning("effects", primaryKey, secondaryKey, "missing_context", fallback)
            return fallback
        }
        var value = boolFromKeys(root.contextEffectsDefaults, primaryKey, secondaryKey)
        if (value === undefined) {
            _recordSettingWarning("effects", primaryKey, secondaryKey, "missing", fallback)
            return fallback
        }
        return value
    }

    function effectsNumberDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEffectsDefaults) {
            _recordSettingWarning("effects", primaryKey, secondaryKey, "missing_context", fallback)
            return fallback
        }
        var value = numberFromKeys(root.contextEffectsDefaults, primaryKey, secondaryKey)
        if (value === undefined) {
            _recordSettingWarning("effects", primaryKey, secondaryKey, "missing", fallback)
            return fallback
        }
        return value
    }

    function effectsStringDefault(primaryKey, secondaryKey, fallback) {
        if (!root.contextEffectsDefaults) {
            _recordSettingWarning("effects", primaryKey, secondaryKey, "missing_context", fallback)
            return fallback
        }
        var value = stringFromKeys(root.contextEffectsDefaults, primaryKey, secondaryKey)
        if (value === undefined) {
            _recordSettingWarning("effects", primaryKey, secondaryKey, "missing", fallback)
            return fallback
        }
        return value
    }

    function qualityBoolDefault(primaryKey, secondaryKey, fallback) {
        var defaults = _qualityContextPayload()
        if (!defaults) {
            _recordSettingWarning("quality", primaryKey, secondaryKey, "missing_context", fallback)
            return fallback
        }
        var value = boolFromKeys(defaults, primaryKey, secondaryKey)
        if (value === undefined) {
            _recordSettingWarning("quality", primaryKey, secondaryKey, "missing", fallback)
            return fallback
        }
        return value
    }

    function qualityNumberDefault(primaryKey, secondaryKey, fallback) {
        var defaults = _qualityContextPayload()
        if (!defaults) {
            _recordSettingWarning("quality", primaryKey, secondaryKey, "missing_context", fallback)
            return fallback
        }
        var value = numberFromKeys(defaults, primaryKey, secondaryKey)
        if (value === undefined) {
            _recordSettingWarning("quality", primaryKey, secondaryKey, "missing", fallback)
            return fallback
        }
        return value
    }

    function qualityStringDefault(primaryKey, secondaryKey, fallback) {
        var defaults = _qualityContextPayload()
        if (!defaults) {
            _recordSettingWarning("quality", primaryKey, secondaryKey, "missing_context", fallback)
            return fallback
        }
        var value = stringFromKeys(defaults, primaryKey, secondaryKey)
        if (value === undefined) {
            _recordSettingWarning("quality", primaryKey, secondaryKey, "missing", fallback)
            return fallback
        }
        return value
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

    function _hasEnvironmentProperty(propertyName) {
        if (!propertyName)
            return false
        try {
            if (root.hasOwnProperty && root.hasOwnProperty(propertyName))
                return root[propertyName] !== undefined
        } catch (error) {
            // fall back to generic lookup
        }
        try {
            return root[propertyName] !== undefined
        } catch (error) {
            return false
        }
    }

    function _updateBufferRequirements() {
        if (!root.sceneBridge)
            return
        var updater = root.sceneBridge.updateBufferRequirements
        if (typeof updater === "function") {
            try {
                updater(root.temporalAAEnabled)
            } catch (error) {
                console.debug("SceneEnvironmentController: buffer requirement sync failed", error)
            }
        }
    }

    function canonicalTonemapModeName(value) {
        if (value === undefined || value === null)
            value = "filmic"
        var normalized = String(value).trim().toLowerCase()
        if (!normalized.length)
            normalized = "filmic"
        if (normalized === "disabled" || normalized === "off")
            return "none"
        if (normalized === "aces_filmic" || normalized === "aces filmic")
            return "aces"
        switch (normalized) {
        case "filmic":
        case "aces":
        case "reinhard":
        case "gamma":
        case "linear":
        case "none":
            return normalized
        default:
            return "filmic"
        }
    }

    function tonemapModeEnumForName(name) {
        if (!SceneEnvironment)
            return undefined
        var normalized = canonicalTonemapModeName(name)
        switch (normalized) {
        case "filmic":
            return sceneEnvironmentEnum("TonemapModeFilmic")
        case "aces":
            var aces = sceneEnvironmentEnum("TonemapModeAces")
            if (aces !== undefined)
                return aces
            return sceneEnvironmentEnum("TonemapModeFilmic")
        case "reinhard":
            return sceneEnvironmentEnum("TonemapModeReinhard", "TonemapModeLinear")
        case "gamma":
            var gamma = sceneEnvironmentEnum("TonemapModeGamma")
            if (gamma !== undefined)
                return gamma
            return sceneEnvironmentEnum("TonemapModeLinear")
        case "linear":
            return sceneEnvironmentEnum("TonemapModeLinear")
        case "none":
            var noneValue = sceneEnvironmentEnum("TonemapModeNone")
            if (noneValue !== undefined)
                return noneValue
            return sceneEnvironmentEnum("TonemapModeLinear")
        }
        return sceneEnvironmentEnum("TonemapModeFilmic")
    }

    function _syncTonemapModeFromName(name) {
        var modeValue = tonemapModeEnumForName(name)
        if (modeValue === undefined)
            return
        try {
            if (root.tonemapMode !== undefined && root.tonemapMode !== modeValue)
                root.tonemapMode = modeValue
        } catch (error) {
            console.debug("SceneEnvironmentController: tonemapMode assignment failed", error)
        }
    }

    function assignTonemapModeProperty(value) {
        if (value === undefined || value === null)
            return
        var canonical = canonicalTonemapModeName(value)
        if (tonemapModeName !== canonical) {
            tonemapModeName = canonical
        } else {
            _syncTonemapModeFromName(canonical)
            try {
                mirrorHostProperty("tonemapModeName", canonical)
            } catch (error) {
                console.debug("SceneEnvironmentController: mirror tonemapModeName failed", error)
            }
        }
    }

    function setTonemapEnabledFlag(enabled) {
        var value = !!enabled
        if (tonemapActive !== value) {
            tonemapActive = value
            return
        }
        try {
            if (root.setProperty) {
                if (!root.property || root.property("tonemapEnabled") !== value)
                    root.setProperty("tonemapEnabled", value)
            }
        } catch (error) {
            console.debug("SceneEnvironmentController: unable to set tonemapEnabled", error)
        }
        try {
            mirrorHostProperty("tonemapActive", value)
        } catch (error) {
            console.debug("SceneEnvironmentController: mirror tonemapActive failed", error)
        }
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

    function _forwardToParent(methodName, payload) {
        var host = root.parent
        if (!host)
            return
        var handler = host[methodName]
        if (typeof handler !== "function")
            return
        try {
            handler.call(host, payload)
        } catch (error) {
            console.debug("SceneEnvironmentController:", methodName, "forward failed", error)
        }
    }

    function _applyEnvironmentPayload(payload) {
        root.applyEnvironmentPayload(payload)
        _forwardToParent("applyEnvironmentPayload", payload)
    }

    function _applyQualityPayload(payload) {
        root.applyQualityPayload(payload)
        _forwardToParent("applyQualityPayload", payload)
    }

    function _applyEffectsPayload(payload) {
        root.applyEffectsPayload(payload)
        _forwardToParent("applyEffectsPayload", payload)
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
        ignoreUnknownSignals: true

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

    function applyQualityPayload(params) {
        if (!params)
            return

        var nested = []
        if (params.antialiasing && typeof params.antialiasing === "object")
            nested.push(params.antialiasing)
        if (params.quality && typeof params.quality === "object")
            nested.push(params.quality)

        for (var i = 0; i < nested.length; ++i)
            applyQualityPayload(nested[i])

        var presetValue = stringFromKeys(params, "qualityPreset", "preset")
        if (presetValue !== undefined) {
            var canonical = String(presetValue)
            if (qualityProfiles && typeof qualityProfiles.canonicalKey === "function") {
                var normalized = qualityProfiles.canonicalKey(presetValue)
                if (normalized)
                    canonical = normalized
            }
            if (qualityPreset !== canonical)
                qualityPreset = canonical
            activeQualityPreset = canonical
        }

        var primaryMode = stringFromKeys(params, "aaPrimaryMode", "aa_primary_mode")
        if (primaryMode !== undefined)
            aaPrimaryMode = primaryMode

        var qualityLevel = stringFromKeys(params, "aaQualityLevel", "aa_quality_level")
        if (qualityLevel !== undefined)
            aaQualityLevel = qualityLevel

        var postMode = stringFromKeys(params, "aaPostMode", "aa_post_mode")
        if (postMode !== undefined)
            aaPostMode = postMode

        var taaFlag = boolFromKeys(params, "taaEnabled", "taa_enabled")
        if (taaFlag !== undefined)
            taaEnabled = taaFlag

        var taaStrengthValue = numberFromKeys(params, "taaStrength", "taa_strength")
        if (taaStrengthValue !== undefined)
            taaStrength = taaStrengthValue

        var taaAdaptiveFlag = boolFromKeys(params, "taaMotionAdaptive", "taa_motion_adaptive")
        if (taaAdaptiveFlag !== undefined)
            taaMotionAdaptive = taaAdaptiveFlag

        var fxaaFlag = boolFromKeys(params, "fxaaEnabled", "fxaa_enabled")
        if (fxaaFlag !== undefined)
            fxaaEnabled = fxaaFlag

        var specularFlag = boolFromKeys(params, "specularAAEnabled", "specular_aa")
        if (specularFlag !== undefined)
            specularAAEnabled = specularFlag

        var ditheringFlag = boolFromKeys(params, "ditheringEnabled", "dithering")
        if (ditheringFlag !== undefined)
            ditheringEnabled = ditheringFlag

        var scaleValue = numberFromKeys(params, "sceneScaleFactor", "render_scale")
        if (scaleValue !== undefined)
            sceneScaleFactor = scaleValue
    }

    function applyQualityPresetInternal(name) {
        var requested = name
        if (qualityProfiles && typeof qualityProfiles.canonicalKey === "function") {
            var canonical = qualityProfiles.canonicalKey(name)
            if (canonical)
                requested = canonical
        }

        if (!requested)
            requested = String(name || "").trim().toLowerCase()

        if (!requested)
            return false

        var preset = null
        if (qualityProfiles && typeof qualityProfiles.presetFor === "function")
            preset = qualityProfiles.presetFor(requested)

        if (!preset)
            return false

        _applyingQualityPreset = true
        try {
            if (qualityPreset !== requested)
                qualityPreset = requested
            activeQualityPreset = requested

            if (preset.antialiasing && typeof preset.antialiasing === "object")
                applyQualityPayload(preset.antialiasing)
            if (preset.environment && typeof preset.environment === "object")
                applyEnvironmentPayload(preset.environment)
            if (preset.effects && typeof preset.effects === "object")
                applyEffectsPayload(preset.effects)
        } finally {
            _applyingQualityPreset = false
        }
        return true
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

        function assignColorAdjustmentsEnabled(value) {
            if (value === undefined)
                return
            var enabled = !!value
            try {
                if (colorAdjustmentsEnabled !== enabled)
                    colorAdjustmentsEnabled = enabled
                else if (colorAdjustmentsActive !== enabled)
                    colorAdjustmentsActive = enabled
            } catch (error) {
                console.warn("⚠️ SceneEnvironmentController: colorAdjustmentsEnabled assignment failed", error)
            }
            try {
                _syncColorAdjustmentFlags()
            } catch (error) {
                console.warn("⚠️ SceneEnvironmentController: _syncColorAdjustmentFlags failed", error)
            }
        }

        function assignColorAdjustment(propertyName, value) {
            if (value === undefined)
                return
            var numeric = Number(value)
            if (!isFinite(numeric))
                return
            var assigned = numeric
            try {
                if (root[propertyName] !== numeric)
                    root[propertyName] = numeric
            } catch (error) {
                console.warn("⚠️ SceneEnvironmentController:", propertyName, "assignment failed", error)
                return
            }
            try {
                mirrorHostProperty(propertyName, assigned)
            } catch (error) {
                console.warn("⚠️ SceneEnvironmentController: mirror", propertyName, "failed", error)
            }
            try {
                _syncColorAdjustmentFlags()
            } catch (error) {
                console.warn("⚠️ SceneEnvironmentController: _syncColorAdjustmentFlags failed", error)
            }
        }

        function assignRootBool(propertyName, value) {
            if (value === undefined)
                return
            var normalized = !!value
            try {
                if (root[propertyName] !== normalized)
                    root[propertyName] = normalized
            } catch (error) {
                console.warn("⚠️ SceneEnvironmentController:", propertyName, "bool assignment failed", error)
            }
        }

        function assignRootNumber(propertyName, value, options) {
            if (value === undefined)
                return
            var numeric = coerceNumber(value)
            if (numeric === undefined)
                return
            var opts = options || {}
            var finalValue = numeric
            if (opts.min !== undefined && finalValue < opts.min)
                finalValue = opts.min
            if (opts.max !== undefined && finalValue > opts.max)
                finalValue = opts.max
            try {
                root[propertyName] = finalValue
            } catch (error) {
                console.warn("⚠️ SceneEnvironmentController:", propertyName, "numeric assignment failed", error)
            }
        }

        function payloadHas(source, key) {
            if (!source || typeof source !== "object")
                return false
            return Object.prototype.hasOwnProperty.call(source, key)
        }

        var bloomSection = valueFromKeys(params, "bloom", "bloom")
        if (bloomSection && typeof bloomSection === "object") {
            if (payloadHas(bloomSection, "enabled"))
                assignRootBool("bloomEnabled", bloomSection.enabled)
            else
                assignRootBool("bloomEnabled", boolFromKeys(bloomSection, "enabled", "enabled"))

            if (payloadHas(bloomSection, "intensity"))
                assignRootNumber("bloomIntensity", bloomSection.intensity)
            else
                assignRootNumber("bloomIntensity", numberFromKeys(bloomSection, "intensity", "intensity"))

            if (payloadHas(bloomSection, "threshold"))
                assignRootNumber("bloomThreshold", bloomSection.threshold)
            else
                assignRootNumber("bloomThreshold", numberFromKeys(bloomSection, "threshold", "threshold"))

            if (payloadHas(bloomSection, "spread"))
                assignRootNumber("bloomSpread", bloomSection.spread)
            else
                assignRootNumber("bloomSpread", numberFromKeys(bloomSection, "spread", "spread"))

            if (payloadHas(bloomSection, "glowStrength"))
                assignRootNumber("bloomGlowStrength", bloomSection.glowStrength)
            else
                assignRootNumber("bloomGlowStrength", numberFromKeys(bloomSection, "glowStrength", "glow_strength"))

            if (payloadHas(bloomSection, "hdrMax"))
                assignRootNumber("bloomHdrMaximum", bloomSection.hdrMax)
            else
                assignRootNumber("bloomHdrMaximum", numberFromKeys(bloomSection, "hdrMax", "hdr_max"))

            if (payloadHas(bloomSection, "hdrScale"))
                assignRootNumber("bloomHdrScale", bloomSection.hdrScale)
            else
                assignRootNumber("bloomHdrScale", numberFromKeys(bloomSection, "hdrScale", "hdr_scale"))

            if (payloadHas(bloomSection, "qualityHigh"))
                assignRootBool("bloomQualityHigh", bloomSection.qualityHigh)
            else
                assignRootBool("bloomQualityHigh", boolFromKeys(bloomSection, "qualityHigh", "quality_high"))

            if (payloadHas(bloomSection, "bicubicUpscale"))
                assignRootBool("bloomUseBicubicUpscale", bloomSection.bicubicUpscale)
            else
                assignRootBool("bloomUseBicubicUpscale", boolFromKeys(bloomSection, "bicubicUpscale", "bicubic_upscale"))
        }

        if (payloadHas(params, "bloomEnabled") || payloadHas(params, "bloom_enabled"))
            assignRootBool("bloomEnabled", boolFromKeys(params, "bloomEnabled", "bloom_enabled"))

        if (payloadHas(params, "bloomIntensity") || payloadHas(params, "bloom_intensity"))
            assignRootNumber("bloomIntensity", numberFromKeys(params, "bloomIntensity", "bloom_intensity"))

        if (payloadHas(params, "bloomThreshold") || payloadHas(params, "bloom_threshold"))
            assignRootNumber("bloomThreshold", numberFromKeys(params, "bloomThreshold", "bloom_threshold"))

        if (payloadHas(params, "bloomSpread") || payloadHas(params, "bloom_spread"))
            assignRootNumber("bloomSpread", numberFromKeys(params, "bloomSpread", "bloom_spread"))

        if (payloadHas(params, "bloomGlowStrength") || payloadHas(params, "bloom_glow_strength"))
            assignRootNumber("bloomGlowStrength", numberFromKeys(params, "bloomGlowStrength", "bloom_glow_strength"))

        if (payloadHas(params, "bloomHdrMaximum") || payloadHas(params, "bloom_hdr_max"))
            assignRootNumber("bloomHdrMaximum", numberFromKeys(params, "bloomHdrMaximum", "bloom_hdr_max"))

        if (payloadHas(params, "bloomHdrScale") || payloadHas(params, "bloom_hdr_scale"))
            assignRootNumber("bloomHdrScale", numberFromKeys(params, "bloomHdrScale", "bloom_hdr_scale"))

        if (payloadHas(params, "bloomQualityHigh") || payloadHas(params, "bloom_quality_high"))
            assignRootBool("bloomQualityHigh", boolFromKeys(params, "bloomQualityHigh", "bloom_quality_high"))

        if (payloadHas(params, "bloomUseBicubicUpscale") || payloadHas(params, "bloom_bicubic_upscale"))
            assignRootBool("bloomUseBicubicUpscale", boolFromKeys(params, "bloomUseBicubicUpscale", "bloom_bicubic_upscale"))

        var depthOfFieldSection = valueFromKeys(params, "depthOfField", "depth_of_field")
        if (depthOfFieldSection && typeof depthOfFieldSection === "object") {
            if (payloadHas(depthOfFieldSection, "enabled"))
                assignRootBool("internalDepthOfFieldEnabled", depthOfFieldSection.enabled)
            else
                assignRootBool("internalDepthOfFieldEnabled", boolFromKeys(depthOfFieldSection, "enabled", "enabled"))

            if (payloadHas(depthOfFieldSection, "focusDistance"))
                assignRootNumber("dofFocusDistance", depthOfFieldSection.focusDistance)
            else
                assignRootNumber("dofFocusDistance", numberFromKeys(depthOfFieldSection, "focusDistance", "focus_distance"))

            if (payloadHas(depthOfFieldSection, "focusRange"))
                assignRootNumber("dofFocusRange", depthOfFieldSection.focusRange)
            else
                assignRootNumber("dofFocusRange", numberFromKeys(depthOfFieldSection, "focusRange", "focus_range"))

            var nestedDofBlur = payloadHas(depthOfFieldSection, "blurAmount")
                    ? depthOfFieldSection.blurAmount
                    : numberFromKeys(depthOfFieldSection, "blurAmount", "blur")
            if (nestedDofBlur === undefined)
                nestedDofBlur = numberFromKeys(depthOfFieldSection, "blur", "blur")
            assignRootNumber("dofBlurAmount", nestedDofBlur)

            if (payloadHas(depthOfFieldSection, "autoFocus")) {
                if (("depthOfFieldAutoFocus" in root))
                    assignRootBool("depthOfFieldAutoFocus", depthOfFieldSection.autoFocus)
            } else if (("depthOfFieldAutoFocus" in root)) {
                assignRootBool("depthOfFieldAutoFocus", boolFromKeys(depthOfFieldSection, "autoFocus", "auto_focus"))
            }
        }

        if (payloadHas(params, "depthOfFieldEnabled") || payloadHas(params, "depth_of_field"))
            assignRootBool("internalDepthOfFieldEnabled", boolFromKeys(params, "depthOfFieldEnabled", "depth_of_field"))

        if (payloadHas(params, "dofFocusDistance") || payloadHas(params, "dof_focus_distance"))
            assignRootNumber("dofFocusDistance", numberFromKeys(params, "dofFocusDistance", "dof_focus_distance"))

        if (payloadHas(params, "dofFocusRange") || payloadHas(params, "dof_focus_range"))
            assignRootNumber("dofFocusRange", numberFromKeys(params, "dofFocusRange", "dof_focus_range"))

        if (payloadHas(params, "dofBlurAmount") || payloadHas(params, "dof_blur"))
            assignRootNumber("dofBlurAmount", numberFromKeys(params, "dofBlurAmount", "dof_blur"))

        if ((payloadHas(params, "dofAutoFocus") || payloadHas(params, "dof_auto_focus")) && ("depthOfFieldAutoFocus" in root))
            assignRootBool("depthOfFieldAutoFocus", boolFromKeys(params, "dofAutoFocus", "dof_auto_focus"))

        var lensFlareSection = valueFromKeys(params, "lensFlare", "lens_flare")
        if (lensFlareSection && typeof lensFlareSection === "object") {
            if (payloadHas(lensFlareSection, "enabled"))
                assignRootBool("internalLensFlareEnabled", lensFlareSection.enabled)
            else
                assignRootBool("internalLensFlareEnabled", boolFromKeys(lensFlareSection, "enabled", "enabled"))

            var nestedGhostCount = payloadHas(lensFlareSection, "ghostCount")
                    ? lensFlareSection.ghostCount
                    : numberFromKeys(lensFlareSection, "ghostCount", "ghost_count")
            if (nestedGhostCount === undefined)
                nestedGhostCount = numberFromKeys(lensFlareSection, "ghosts", "ghosts")
            assignLensFlareGhostCount(nestedGhostCount)

            if (payloadHas(lensFlareSection, "ghostDispersal"))
                assignRootNumber("lensFlareGhostDispersalValue", lensFlareSection.ghostDispersal)
            else
                assignRootNumber("lensFlareGhostDispersalValue", numberFromKeys(lensFlareSection, "ghostDispersal", "ghost_dispersal"))

            if (payloadHas(lensFlareSection, "haloWidth"))
                assignRootNumber("lensFlareHaloWidthValue", lensFlareSection.haloWidth)
            else
                assignRootNumber("lensFlareHaloWidthValue", numberFromKeys(lensFlareSection, "haloWidth", "halo_width"))

            if (payloadHas(lensFlareSection, "bloomBias"))
                assignRootNumber("lensFlareBloomBiasValue", lensFlareSection.bloomBias)
            else
                assignRootNumber("lensFlareBloomBiasValue", numberFromKeys(lensFlareSection, "bloomBias", "bloom_bias"))

            if (payloadHas(lensFlareSection, "stretchToAspect"))
                assignRootBool("lensFlareStretchValue", lensFlareSection.stretchToAspect)
            else
                assignRootBool("lensFlareStretchValue", boolFromKeys(lensFlareSection, "stretchToAspect", "stretch_to_aspect"))
        }

        if (payloadHas(params, "lensFlareEnabled") || payloadHas(params, "lens_flare"))
            assignRootBool("internalLensFlareEnabled", boolFromKeys(params, "lensFlareEnabled", "lens_flare"))

        if (payloadHas(params, "lensFlareGhostCount") || payloadHas(params, "lens_flare_ghost_count"))
            assignLensFlareGhostCount(numberFromKeys(params, "lensFlareGhostCount", "lens_flare_ghost_count"))

        if (payloadHas(params, "lensFlareGhostDispersal") || payloadHas(params, "lens_flare_ghost_dispersal"))
            assignRootNumber("lensFlareGhostDispersalValue", numberFromKeys(params, "lensFlareGhostDispersal", "lens_flare_ghost_dispersal"))

        if (payloadHas(params, "lensFlareHaloWidth") || payloadHas(params, "lens_flare_halo_width"))
            assignRootNumber("lensFlareHaloWidthValue", numberFromKeys(params, "lensFlareHaloWidth", "lens_flare_halo_width"))

        if (payloadHas(params, "lensFlareBloomBias") || payloadHas(params, "lens_flare_bloom_bias"))
            assignRootNumber("lensFlareBloomBiasValue", numberFromKeys(params, "lensFlareBloomBias", "lens_flare_bloom_bias"))

        if (payloadHas(params, "lensFlareStretchToAspect") || payloadHas(params, "lens_flare_stretch_to_aspect"))
            assignRootBool("lensFlareStretchValue", boolFromKeys(params, "lensFlareStretchToAspect", "lens_flare_stretch_to_aspect"))

        var colorSection = valueFromKeys(params, "colorAdjustments", "color_adjustments")
        if (colorSection && typeof colorSection === "object") {
            var nestedEnabled = boolFromKeys(colorSection, "enabled", "enabled")
            assignColorAdjustmentsEnabled(nestedEnabled)

            var nestedBrightness = numberFromKeys(colorSection, "brightness", "brightness")
            assignColorAdjustment("adjustmentBrightness", nestedBrightness)

            var nestedContrast = numberFromKeys(colorSection, "contrast", "contrast")
            assignColorAdjustment("adjustmentContrast", nestedContrast)

            var nestedSaturation = numberFromKeys(colorSection, "saturation", "saturation")
            assignColorAdjustment("adjustmentSaturation", nestedSaturation)
        }

        var activeValue = boolFromKeys(params, "colorAdjustmentsActive", "color_adjustments_active")
        assignColorAdjustmentsEnabled(activeValue)

        var enabledValue = boolFromKeys(params, "colorAdjustmentsEnabled", "color_adjustments_enabled")
        assignColorAdjustmentsEnabled(enabledValue)

        var brightnessValue = numberFromKeys(params, "adjustmentBrightness", "adjustment_brightness")
        assignColorAdjustment("adjustmentBrightness", brightnessValue)

        var contrastValue = numberFromKeys(params, "adjustmentContrast", "adjustment_contrast")
        assignColorAdjustment("adjustmentContrast", contrastValue)

        var saturationValue = numberFromKeys(params, "adjustmentSaturation", "adjustment_saturation")
        assignColorAdjustment("adjustmentSaturation", saturationValue)

        var vignetteSection = params.vignette && typeof params.vignette === "object"
                ? params.vignette
                : null
        if (vignetteSection) {
            if (payloadHas(vignetteSection, "enabled"))
                assignRootBool("vignetteEnabled", vignetteSection.enabled)
            else
                assignRootBool("vignetteEnabled", boolFromKeys(vignetteSection, "enabled", "enabled"))

            if (payloadHas(vignetteSection, "strength"))
                assignRootNumber("internalVignetteStrength", vignetteSection.strength)
            else
                assignRootNumber("internalVignetteStrength", numberFromKeys(vignetteSection, "strength", "strength"))

            if (payloadHas(vignetteSection, "radius"))
                assignRootNumber("vignetteRadiusValue", vignetteSection.radius, { min: 0.0 })
            else
                assignRootNumber("vignetteRadiusValue", numberFromKeys(vignetteSection, "radius", "radius"), { min: 0.0 })
        }

        var vignetteEnabledValue = undefined
        if (payloadHas(params, "vignetteEnabled") || payloadHas(params, "vignette_enabled"))
            vignetteEnabledValue = boolFromKeys(params, "vignetteEnabled", "vignette_enabled")
        else if (payloadHas(params, "vignette"))
            vignetteEnabledValue = boolFromKeys(params, "vignette", "vignette")
        if (vignetteEnabledValue !== undefined)
            assignRootBool("vignetteEnabled", vignetteEnabledValue)

        if (payloadHas(params, "vignetteStrength") || payloadHas(params, "vignette_strength"))
            assignRootNumber("internalVignetteStrength", numberFromKeys(params, "vignetteStrength", "vignette_strength"))

        if (payloadHas(params, "vignetteRadius") || payloadHas(params, "vignette_radius"))
            assignRootNumber("vignetteRadiusValue", numberFromKeys(params, "vignetteRadius", "vignette_radius"), { min: 0.0 })
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
        assignTonemapModeProperty(tonemapModeKey)
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
            assignTonemapModeProperty(tonemap.mode)
        if (tonemap.exposure !== undefined)
            tonemapExposure = Number(tonemap.exposure)
        if (tonemap.white_point !== undefined)
            tonemapWhitePoint = Number(tonemap.white_point)
    }

    var fogEnabledValue = boolFromKeys(params, "fogEnabled", "fog_enabled")
    if (fogEnabledValue !== undefined)
        fogEnabled = fogEnabledValue
    var fogDepthEnabledValue = boolFromKeys(params, "fogDepthEnabled", "fog_depth_enabled")
    if (fogDepthEnabledValue !== undefined)
        fogDepthEnabled = !!fogDepthEnabledValue
    var fogColorValue = valueFromKeys(params, "fogColor", "fog_color")
    if (fogColorValue !== undefined)
        fogColor = fogColorValue
    var fogDensityValue = numberFromKeys(params, "fogDensity", "fog_density")
    if (fogDensityValue !== undefined)
        fogDensity = fogDensityValue
    var fogDepthCurveValue = numberFromKeys(params, "fogDepthCurve", "fog_depth_curve")
    if (fogDepthCurveValue !== undefined && isFinite(fogDepthCurveValue))
        fogDepthCurve = fogDepthCurveValue
    var fogNearValue = numberFromKeys(params, "fogDepthNear", "fog_near")
    if (fogNearValue === undefined)
        fogNearValue = numberFromKeys(params, "fogNear", "fog_near")
    if (fogNearValue !== undefined && isFinite(fogNearValue))
        fogDepthNear = fogNearValue
    var fogFarValue = numberFromKeys(params, "fogDepthFar", "fog_far")
    if (fogFarValue === undefined)
        fogFarValue = numberFromKeys(params, "fogFar", "fog_far")
    if (fogFarValue !== undefined && isFinite(fogFarValue))
        fogDepthFar = fogFarValue
    var fogHeightFlag = boolFromKeys(params, "fogHeightEnabled", "fog_height_enabled")
    if (fogHeightFlag !== undefined)
        fogHeightEnabled = !!fogHeightFlag
    var fogLeastValue = numberFromKeys(params, "fogLeastIntenseY", "fog_least_intense_y")
    if (fogLeastValue !== undefined && isFinite(fogLeastValue))
        fogLeastIntenseY = fogLeastValue
    var fogMostValue = numberFromKeys(params, "fogMostIntenseY", "fog_most_intense_y")
    if (fogMostValue !== undefined && isFinite(fogMostValue))
        fogMostIntenseY = fogMostValue
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
        if (fog.depth_enabled !== undefined)
            fogDepthEnabled = !!fog.depth_enabled
        if (fog.color)
            fogColor = fog.color
        if (fog.near !== undefined) {
            var fogNestedNear = Number(fog.near)
            if (isFinite(fogNestedNear))
                fogDepthNear = fogNestedNear
        }
        if (fog.depth_near !== undefined) {
            var fogNestedDepthNear = Number(fog.depth_near)
            if (isFinite(fogNestedDepthNear))
                fogDepthNear = fogNestedDepthNear
        }
        if (fog.far !== undefined) {
            var fogNestedFar = Number(fog.far)
            if (isFinite(fogNestedFar))
                fogDepthFar = fogNestedFar
        }
        if (fog.depth_far !== undefined) {
            var fogNestedDepthFar = Number(fog.depth_far)
            if (isFinite(fogNestedDepthFar))
                fogDepthFar = fogNestedDepthFar
        }
        if (fog.density !== undefined)
            fogDensity = Number(fog.density)
        if (fog.depth_curve !== undefined) {
            var fogNestedDepthCurve = Number(fog.depth_curve)
            if (isFinite(fogNestedDepthCurve))
                fogDepthCurve = fogNestedDepthCurve
        }
        if (fog.height_enabled !== undefined)
            fogHeightEnabled = !!fog.height_enabled
        if (fog.least_intense_y !== undefined) {
            var fogLeastNested = Number(fog.least_intense_y)
            if (isFinite(fogLeastNested))
                fogLeastIntenseY = fogLeastNested
        }
        if (fog.most_intense_y !== undefined) {
            var fogMostNested = Number(fog.most_intense_y)
            if (isFinite(fogMostNested))
                fogMostIntenseY = fogMostNested
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
