import QtQml 6.10
import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import QtQuick3D 6.10
import QtQuick3D.Helpers 6.10
import "../camera"
import "../components"
import "../effects"
import "../geometry"
import "../lighting"
import scene 1.0 as Scene
import "../animation"
import "../diagnostics/LogBridge.js" as Diagnostics

/*
 * PneumoStabSim - MAIN QML (v4.9.x)
 *
 * View3D + ExtendedSceneEnvironment (HDR/IBL), IBL Probe Loader,
 * ReflectionProbe для локальных отражений.
 * Полноценная анимированная схема (рама, рычаги, шарниры, цилиндры,
 * штоки, хвостовики, поршни). Без кнопок на канве.
 * Обновления приходят из панелей через apply*Updates и batched updates.
 */
 Item {
 id: root
 anchors.fill: parent

    property var sceneBridge: null
    property var postEffects: null
    property var sceneView: null
    property bool postProcessingBypassed: false
    property string postProcessingBypassReason: ""
    property var postProcessingEffectBackup: []
    property bool simpleFallbackActive: false
    property string simpleFallbackReason: ""
    signal simpleFallbackRequested(string reason)
    signal simpleFallbackRecovered()
    signal shaderStatusDumpRequested(var payload)
    readonly property var emptyDefaultsObject: Object.freeze({})
    readonly property var emptyGeometryDefaults: emptyDefaultsObject
    readonly property var emptyMaterialsDefaults: emptyDefaultsObject
    property var geometryState: ({})
    property var simulationState: ({})
    property var threeDState: ({})
    property var flowTelemetry: ({})
    property var receiverTelemetry: ({})
    property bool geometryStateReceived: false
    property bool simulationStateReceived: false
    property int sceneBridgeDispatchCount: 0
    readonly property bool sceneBridgeAvailable: sceneBridge !== null && sceneBridge !== undefined
    readonly property bool geometryStateReady: !_isEmptyMap(geometryState)
    readonly property bool simulationStateReady: !_isEmptyMap(simulationState)

 // ---------------------------------------------
 // Свойства и сигнал для батч-обновлений из Python
 // ---------------------------------------------
    property var pendingPythonUpdates: null
    property var lastUpdateByCategory: ({})
signal batchUpdatesApplied(var summary)
signal animationToggled(bool running)

    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates || typeof pendingPythonUpdates !== "object")
            return
        try {
            applyBatchedUpdates(pendingPythonUpdates)
        } finally {
            pendingPythonUpdates = null
        }
    }

    function _logBatchEvent(eventType, name) {
        try {
            if (typeof window !== "undefined" && window && typeof window.logQmlEvent === "function")
                window.logQmlEvent(eventType, name)
        } catch (error) {
            console.debug("[SimulationRoot] Failed to forward batch event", eventType, name, error)
        }
    }

    function _mergeObjects(base, payload) {
        var result = {}
        if (base && typeof base === "object") {
            for (var key in base) {
                if (Object.prototype.hasOwnProperty.call(base, key))
                    result[key] = base[key]
            }
        }
        if (payload && typeof payload === "object") {
            for (var updateKey in payload) {
                if (Object.prototype.hasOwnProperty.call(payload, updateKey))
                    result[updateKey] = payload[updateKey]
            }
        }
        return result
    }

    function _isPlainObject(value) {
        return value && typeof value === "object" && !Array.isArray(value)
    }

    function _cloneObject(value) {
        if (!_isPlainObject(value))
            return ({})
        var clone = {}
        for (var key in value) {
            if (!Object.prototype.hasOwnProperty.call(value, key))
                continue
            var entry = value[key]
            clone[key] = _isPlainObject(entry) ? _cloneObject(entry) : entry
        }
        return clone
    }

    function _deepMerge(base, payload) {
        var result = _cloneObject(base)
        if (_isPlainObject(payload)) {
            for (var key in payload) {
                if (!Object.prototype.hasOwnProperty.call(payload, key))
                    continue
                var value = payload[key]
                if (_isPlainObject(value))
                    result[key] = _deepMerge(result[key], value)
                else
                    result[key] = value
            }
        }
        return result
    }

    function _normaliseKeyList(names) {
        var list = []
        function add(name) {
            if (name && list.indexOf(name) === -1)
                list.push(name)
        }
        function pushVariants(raw) {
            if (raw === undefined || raw === null)
                return
            var text = String(raw)
            if (!text.length)
                return
            add(text)
            add(text.toLowerCase())
            add(text.replace(/([A-Z])/g, function(match) { return "_" + match.toLowerCase() }))
            add(text.replace(/_([a-zA-Z0-9])/g, function(_, chr) { return chr.toUpperCase() }))
        }
        if (Array.isArray(names)) {
            for (var i = 0; i < names.length; ++i)
                pushVariants(names[i])
        } else {
            pushVariants(names)
        }
        return list
    }

    function _resolveMapEntry(source, nameOptions) {
        if (!_isPlainObject(source))
            return undefined
        var names = _normaliseKeyList(nameOptions)
        for (var i = 0; i < names.length; ++i) {
            var candidateName = names[i]
            if (candidateName && Object.prototype.hasOwnProperty.call(source, candidateName))
                return source[candidateName]
        }
        return undefined
    }

    function _valueFromSubsection(sources, sectionNames, keyNames) {
        var sectionList = []
        if (Array.isArray(sectionNames))
            sectionList = sectionNames
        else if (sectionNames !== undefined && sectionNames !== null)
            sectionList = [sectionNames]
        var keys = _normaliseKeyList(keyNames)
        for (var i = 0; i < sources.length; ++i) {
            var current = sources[i]
            var valid = true
            for (var j = 0; j < sectionList.length; ++j) {
                current = _resolveMapEntry(current, sectionList[j])
                if (!_isPlainObject(current)) {
                    valid = false
                    break
                }
            }
            if (!valid)
                continue
            for (var k = 0; k < keys.length; ++k) {
                var candidate = current[keys[k]]
                if (candidate !== undefined)
                    return candidate
            }
        }
        return undefined
    }

    function _valueFromSources(sources, keyNames) {
        return _valueFromSubsection(sources, [], keyNames)
    }

    function _coerceNumber(value, fallback) {
        var numeric = Number(value)
        return isFinite(numeric) ? numeric : fallback
    }

    function _coerceBool(value, fallback) {
        if (value === undefined || value === null)
            return fallback
        if (typeof value === "string") {
            var lowered = value.toLowerCase()
            if (lowered === "true" || lowered === "yes" || lowered === "1")
                return true
            if (lowered === "false" || lowered === "no" || lowered === "0")
                return false
        }
        return !!value
    }

    function _coerceColor(value, fallback) {
        if (value === undefined || value === null)
            return fallback
        var text = String(value)
        return text.length ? text : fallback
    }

    function _coerceString(value, fallback) {
        if (value === undefined || value === null)
            return fallback
        var text = String(value)
        return text.length ? text : fallback
    }

    function environmentDefaultsMapFor(source) {
        if (!_isPlainObject(source))
            return ({})
        var direct = _resolveMapEntry(source, "environment")
        if (_isPlainObject(direct))
            return _cloneObject(direct)
        var graphics = _resolveMapEntry(source, "graphics")
        if (_isPlainObject(graphics)) {
            var nested = _resolveMapEntry(graphics, "environment")
            if (_isPlainObject(nested))
                return _cloneObject(nested)
        }
        return ({})
    }

    function environmentDefaultString(map, keys, fallback) {
        var value = _valueFromSources([map || ({})], keys)
        if (value === undefined || value === null)
            return fallback
        var text = String(value)
        return text.length ? text : fallback
    }

    function environmentDefaultNumber(map, keys, fallback) {
        return _coerceNumber(_valueFromSources([map || ({})], keys), fallback)
    }

    function environmentDefaultBool(map, keys, fallback) {
        var value = _valueFromSources([map || ({})], keys)
        return value === undefined ? fallback : _coerceBool(value, fallback)
    }

    function _normalizeRenderPolicy(value, fallback) {
        var defaultKey = fallback !== undefined && fallback !== null ? String(fallback) : "always"
        var text = _coerceString(value, defaultKey)
        var normalized = text.toLowerCase()
        if (normalized === "on_demand" || normalized === "on-demand")
            normalized = "ondemand"
        if (normalized === "always" || normalized === "ondemand" || normalized === "automatic" || normalized === "manual")
            return normalized
        return defaultKey.toLowerCase()
    }

    function _renderSources() {
        return [renderState || ({}), qualityState || ({}), sceneRenderDefaults || ({}), sceneQualityDefaults || ({})]
    }

    function _syncRenderSettingsState() {
        var sources = _renderSources()
        var scaleFallback = renderScale > 0 ? renderScale : 1.0
        var scaleValue = _coerceNumber(_valueFromSources(sources, ["renderScale", "render_scale", "sceneScaleFactor", "scene_scale_factor"]), scaleFallback)
        if (!isFinite(scaleValue) || scaleValue <= 0)
            scaleValue = 1.0
        if (scaleValue !== renderScale)
            renderScale = scaleValue

        var frameFallback = frameRateLimit >= 0 ? frameRateLimit : 0
        var frameValue = _coerceNumber(_valueFromSources(sources, ["frameRateLimit", "frame_rate_limit", "frameLimit", "frame_limit"]), frameFallback)
        if (!isFinite(frameValue) || frameValue < 0)
            frameValue = 0
        if (frameValue !== frameRateLimit)
            frameRateLimit = frameValue

        var policyValue = _valueFromSources(sources, ["renderPolicy", "render_policy", "renderMode", "render_mode"])
        var normalizedPolicy = _normalizeRenderPolicy(policyValue, renderPolicyKey)
        if (normalizedPolicy !== renderPolicyKey)
            renderPolicyKey = normalizedPolicy
    }

    function normalizeHdrSource(value) {
        if (value === undefined || value === null)
            return ""
        var text = String(value).trim()
        if (!text.length)
            return ""
        if (text.startsWith("qrc:/") || text.indexOf("://") > 0 || text.startsWith("data:"))
            return text
        return Qt.resolvedUrl(text)
    }

    function _storeLastUpdate(category, payload) {
        var snapshot = _mergeObjects(lastUpdateByCategory, {})
        var stored = payload
        if (payload && typeof payload === "object")
            stored = _normaliseState(payload)
        snapshot[category] = stored
        lastUpdateByCategory = snapshot
    }

    function _acknowledgeBatch(categories) {
        if (categories && categories.length)
            batchFlashOpacity = 1.0
        var summary = {
            timestamp: Date.now(),
            categories: categories && categories.length ? categories.slice() : [],
            source: "python"
        }
        batchUpdatesApplied(summary)
    }

    function applyBatchedUpdates(updates) {
        if (!updates || typeof updates !== "object")
            return

        _logBatchEvent("signal_received", "applyBatchedUpdates")

        var categories = []

        if (updates.geometry !== undefined) {
            categories.push("geometry")
            applyGeometryUpdates(updates.geometry)
        }
        if (updates.animation !== undefined) {
            categories.push("animation")
            applyAnimationUpdates(updates.animation)
        }
        if (updates.lighting !== undefined) {
            categories.push("lighting")
            applyLightingUpdates(updates.lighting)
        }
        if (updates.materials !== undefined) {
            categories.push("materials")
            applyMaterialUpdates(updates.materials)
        }
        if (updates.environment !== undefined) {
            categories.push("environment")
            applyEnvironmentUpdates(updates.environment)
        }
        if (updates.scene !== undefined) {
            categories.push("scene")
            applySceneUpdates(updates.scene)
        }
        if (updates.quality !== undefined) {
            categories.push("quality")
            applyQualityUpdates(updates.quality)
        }
        if (updates.camera !== undefined) {
            categories.push("camera")
            applyCameraUpdates(updates.camera)
        }
        if (updates.effects !== undefined) {
            categories.push("effects")
            applyEffectsUpdates(updates.effects)
        }
        if (updates.render !== undefined) {
            categories.push("render")
            applyRenderSettings(updates.render)
        }
        if (updates.simulation !== undefined) {
            categories.push("simulation")
            applySimulationUpdates(updates.simulation)
        }
        if (updates.threeD !== undefined) {
            categories.push("threeD")
            applyThreeDUpdates(updates.threeD)
        }

        _acknowledgeBatch(categories)
    }

    function applyGeometryUpdates(params) {
        _logBatchEvent("function_called", "applyGeometryUpdates")
        var normalized = _normaliseState(params)
        if (!_isEmptyMap(normalized)) {
            geometryState = _deepMerge(geometryState, normalized)
            geometryStateReceived = true
            if (cameraController && typeof cameraController.updateGeometry === "function") {
                try {
                    cameraController.updateGeometry(normalized)
                } catch (error) {
                    console.debug("[SimulationRoot] cameraController.updateGeometry failed", error)
                }
            }
        }
        _storeLastUpdate("geometry", normalized)
    }

    function applySimulationUpdates(params) {
        _logBatchEvent("function_called", "applySimulationUpdates")
        var normalized = _normaliseState(params)
        if (!_isEmptyMap(normalized)) {
            simulationState = _mergeObjects(simulationState, normalized)
            simulationStateReceived = true
        }
        if (normalized.animation)
            applyAnimationUpdates(normalized.animation)
        if (normalized.threeD)
            applyThreeDUpdates(normalized.threeD)
        _storeLastUpdate("simulation", normalized)
    }

    function applyAnimationUpdates(params) {
        _logBatchEvent("function_called", "applyAnimationUpdates")
        var payload = params || {}
        var previousRunning = isRunning

        function _normalizeNumber(value, fallback) {
            if (value === undefined || value === null)
                return fallback
            var converted = Number(value)
            return isNaN(converted) ? fallback : converted
        }

        animationTime = _normalizeNumber(payload.animation_time, animationTime)
        animationTime = _normalizeNumber(payload.animationTime, animationTime)

        function _normalizeBool(value, fallback) {
            if (value === undefined || value === null)
                return fallback
            return Boolean(value)
        }

        isRunning = _normalizeBool(payload.is_running, isRunning)
        isRunning = _normalizeBool(payload.running, isRunning)
        pythonAnimationActive = _normalizeBool(payload.python_driven, pythonAnimationActive)
        pythonAnimationActive = _normalizeBool(payload.pythonDriven, pythonAnimationActive)

        var frameSource = _resolveMapEntry(payload, "frame")
        if (_isPlainObject(frameSource) && rigAnimation && typeof rigAnimation.applyFrameMotion === "function") {
            pythonFrameActive = true
            try {
                rigAnimation.applyFrameMotion(frameSource, { immediate: !pythonAnimationActive })
            } catch (error) {
                console.debug("[SimulationRoot] rigAnimation.applyFrameMotion failed", error)
            }
        }

        var leverAnglesSource = _resolveMapEntry(payload, ["leverAngles", "lever_angles"])
        if (_isPlainObject(leverAnglesSource) && rigAnimation && typeof rigAnimation.applyLeverAnglesRadians === "function") {
            pythonLeverAnglesActive = true
            try {
                rigAnimation.applyLeverAnglesRadians(leverAnglesSource, { immediate: !pythonAnimationActive })
            } catch (error) {
                console.debug("[SimulationRoot] rigAnimation.applyLeverAnglesRadians failed", error)
            }
        }

        var pistonSource = _resolveMapEntry(payload, ["pistonPositions", "piston_positions"])
        if (_isPlainObject(pistonSource) && rigAnimation && typeof rigAnimation.applyPistonPositions === "function") {
            pythonPistonsActive = true
            try {
                rigAnimation.applyPistonPositions(pistonSource, { immediate: !pythonAnimationActive })
            } catch (error) {
                console.debug("[SimulationRoot] rigAnimation.applyPistonPositions failed", error)
            }
        }

        _storeLastUpdate("animation", payload)
        if (isRunning !== previousRunning)
            animationToggled(isRunning)
    }

    function applyLightingUpdates(params) {
        _logBatchEvent("function_called", "applyLightingUpdates")
        var normalized = _normaliseState(params)
        lightingState = _deepMerge(lightingState, normalized)
        _storeLastUpdate("lighting", normalized)
    }

    function applyMaterialUpdates(params) {
        _logBatchEvent("function_called", "applyMaterialUpdates")
        var normalized = _normaliseState(params)
        materialsState = _deepMerge(materialsState, normalized)
        _storeLastUpdate("materials", normalized)
    }

    function applyEnvironmentUpdates(params) {
        _logBatchEvent("function_called", "applyEnvironmentUpdates")
        var normalized = _normaliseState(params)
        environmentState = _deepMerge(environmentState, normalized)
        var reflectionToggle = _valueFromSources(
            [normalized],
            ["reflection_enabled", "reflectionEnabled"],
        )
        if (reflectionToggle !== undefined)
            _applyReflectionProbeEnabledOverride(reflectionToggle)
        if (sceneEnvironment && typeof sceneEnvironment.applyEnvironmentPayload === "function") {
            try {
                sceneEnvironment.applyEnvironmentPayload(normalized)
            } catch (error) {
                console.debug("[SimulationRoot] sceneEnvironment.applyEnvironmentPayload failed", error)
            }
        }
        var scaleCandidate = _valueFromSources([normalized], ["sceneScaleFactor", "scene_scale_factor", "render_scale"])
        var numericScale = _coerceNumber(scaleCandidate, sceneScaleFactor)
        if (isFinite(numericScale) && numericScale > 0 && numericScale !== sceneScaleFactor)
            sceneScaleFactor = numericScale
        _storeLastUpdate("environment", normalized)
    }

    function applySceneUpdates(params) {
        _logBatchEvent("function_called", "applySceneUpdates")
        _storeLastUpdate("scene", params || {})
    }

    function applyQualityUpdates(params) {
        _logBatchEvent("function_called", "applyQualityUpdates")
        var normalized = _normaliseState(params)
        qualityState = _deepMerge(qualityState, normalized)
        if (sceneEnvironment && typeof sceneEnvironment.applyQualityPayload === "function") {
            try {
                sceneEnvironment.applyQualityPayload(normalized)
            } catch (error) {
                console.debug("[SimulationRoot] sceneEnvironment.applyQualityPayload failed", error)
            }
        }
        if (_isPlainObject(normalized) || !_isEmptyMap(qualityState))
            _syncRenderSettingsState()
        _storeLastUpdate("quality", normalized)
    }

    function applyCameraUpdates(params) {
        _logBatchEvent("function_called", "applyCameraUpdates")
        var normalized = _normaliseState(params)
        cameraStateSnapshot = _deepMerge(cameraStateSnapshot, normalized)
        if (cameraController && typeof cameraController.applyCameraUpdates === "function") {
            try {
                cameraController.applyCameraUpdates(normalized)
            } catch (error) {
                console.debug("[SimulationRoot] cameraController.applyCameraUpdates failed", error)
            }
        }
        _storeLastUpdate("camera", normalized)
    }

    function applyEffectsUpdates(params) {
        _logBatchEvent("function_called", "applyEffectsUpdates")
        var normalized = _normaliseState(params)
        effectsState = _deepMerge(effectsState, normalized)
        if (sceneEnvironment && typeof sceneEnvironment.applyEffectsPayload === "function") {
            try {
                sceneEnvironment.applyEffectsPayload(normalized)
            } catch (error) {
                console.debug("[SimulationRoot] sceneEnvironment.applyEffectsPayload failed", error)
            }
        }
        if (postEffects && typeof postEffects.applyPayload === "function") {
            try {
                postEffects.applyPayload(normalized, sceneEnvironment)
            } catch (error) {
                console.debug("[SimulationRoot] postEffects.applyPayload failed", error)
            }
        }
        _storeLastUpdate("effects", normalized)
    }

    function applyRenderSettings(params) {
        _logBatchEvent("function_called", "applyRenderSettings")
        var payload = params || {}
        if (payload.environment)
            applyEnvironmentUpdates(payload.environment)
        if (payload.quality)
            applyQualityUpdates(payload.quality)
        if (payload.effects)
            applyEffectsUpdates(payload.effects)
        if (payload.camera)
            applyCameraUpdates(payload.camera)
        var renderPayload = null
        if (payload.render !== undefined)
            renderPayload = _normaliseState(payload.render)
        if (_isPlainObject(renderPayload))
            renderState = _deepMerge(renderState, renderPayload)
        var directOverrides = {}
        var scaleOverride = _valueFromSources([payload], ["renderScale", "render_scale", "sceneScaleFactor", "scene_scale_factor"])
        var numericScale = _coerceNumber(scaleOverride, renderScale)
        if (scaleOverride !== undefined && isFinite(numericScale) && numericScale > 0)
            directOverrides.renderScale = numericScale
        var frameOverride = _valueFromSources([payload], ["frameRateLimit", "frame_rate_limit", "frameLimit", "frame_limit"])
        var numericFrame = _coerceNumber(frameOverride, frameRateLimit)
        if (frameOverride !== undefined && isFinite(numericFrame) && numericFrame >= 0)
            directOverrides.frameRateLimit = numericFrame
        var policyOverride = _valueFromSources([payload], ["renderPolicy", "render_policy", "renderMode", "render_mode"])
        if (policyOverride !== undefined && policyOverride !== null)
            directOverrides.renderPolicy = _normalizeRenderPolicy(policyOverride, renderPolicyKey)
        if (!_isEmptyMap(directOverrides))
            renderState = _deepMerge(renderState, directOverrides)
        _syncRenderSettingsState()
        _storeLastUpdate("render", payload)
    }

    function _applyReflectionProbeEnabledOverride(candidate) {
        if (candidate === undefined || candidate === null)
            return
        var normalized = _coerceBool(candidate, reflectionProbeEnabledState)
        var coerced = !!normalized
        var needsUpdate = !reflectionProbeEnabledOverrideActive || reflectionProbeEnabledOverride !== coerced
        if (needsUpdate)
            reflectionProbeEnabledOverride = coerced
        if (!reflectionProbeEnabledOverrideActive || needsUpdate)
            reflectionProbeEnabledOverrideActive = true
    }

    function applyThreeDUpdates(params) {
        _logBatchEvent("function_called", "applyThreeDUpdates")
        var normalized = _normaliseState(params)
        threeDState = _deepMerge(threeDState, normalized)
        var networkSource = null
        if (normalized && typeof normalized === "object")
            networkSource = normalized.flowNetwork !== undefined ? normalized.flowNetwork : normalized.flownetwork
        flowTelemetry = _normaliseState(networkSource)
        receiverTelemetry = _resolveReceiverTelemetry(normalized)
        var frameNode = _resolveMapEntry(normalized, "frame")
        if (_isPlainObject(frameNode) && rigAnimation && typeof rigAnimation.applyFrameMotion === "function") {
            pythonFrameActive = true
            try {
                rigAnimation.applyFrameMotion(frameNode, { immediate: !pythonAnimationActive })
            } catch (error) {
                console.debug("[SimulationRoot] rigAnimation.applyFrameMotion (threeD) failed", error)
            }
        }
        var leverNode = _resolveMapEntry(normalized, ["leverAngles", "lever_angles"])
        if (_isPlainObject(leverNode) && rigAnimation && typeof rigAnimation.applyLeverAnglesRadians === "function") {
            pythonLeverAnglesActive = true
            try {
                rigAnimation.applyLeverAnglesRadians(leverNode, { immediate: !pythonAnimationActive })
            } catch (error) {
                console.debug("[SimulationRoot] rigAnimation.applyLeverAnglesRadians (threeD) failed", error)
            }
        }
        var pistonNode = _resolveMapEntry(normalized, ["pistonPositions", "piston_positions"])
        if (_isPlainObject(pistonNode) && rigAnimation && typeof rigAnimation.applyPistonPositions === "function") {
            pythonPistonsActive = true
            try {
                rigAnimation.applyPistonPositions(pistonNode, { immediate: !pythonAnimationActive })
            } catch (error) {
                console.debug("[SimulationRoot] rigAnimation.applyPistonPositions (threeD) failed", error)
            }
        }
        var reflectionNode = _resolveMapEntry(normalized, ["reflectionProbe", "reflection_probe", "reflection"])
        if (_isPlainObject(reflectionNode)) {
            if (reflectionNode.enabled !== undefined)
                _applyReflectionProbeEnabledOverride(reflectionNode.enabled)
            if (reflectionNode.padding !== undefined)
                reflectionProbePaddingM = sanitizeReflectionProbePadding(reflectionNode.padding)
            if (reflectionNode.quality !== undefined) {
                var qualityText = _coerceString(reflectionNode.quality, reflectionProbeQualitySetting)
                reflectionProbeQualitySetting = qualityText.toLowerCase()
            }
            if (reflectionNode.refreshMode !== undefined || reflectionNode.refresh_mode !== undefined) {
                var refreshCandidate = reflectionNode.refreshMode !== undefined ? reflectionNode.refreshMode : reflectionNode.refresh_mode
                var refreshText = _coerceString(refreshCandidate, reflectionProbeRefreshModeSetting)
                reflectionProbeRefreshModeSetting = refreshText.toLowerCase()
            }
            if (reflectionNode.timeSlicing !== undefined || reflectionNode.time_slicing !== undefined) {
                var slicingCandidate = reflectionNode.timeSlicing !== undefined ? reflectionNode.timeSlicing : reflectionNode.time_slicing
                var slicingText = _coerceString(slicingCandidate, reflectionProbeTimeSlicingSetting)
                reflectionProbeTimeSlicingSetting = slicingText.toLowerCase()
            }
        }
        var suspensionNode = _resolveMapEntry(normalized, ["suspension"])
        if (_isPlainObject(suspensionNode)) {
            var thresholdCandidate = _valueFromSources(
                [suspensionNode],
                ["rod_warning_threshold_m", "rodWarningThresholdM", "rodWarningThreshold"],
            )
            var thresholdNumeric = _coerceNumber(
                thresholdCandidate,
                suspensionRodWarningThresholdM,
            )
            if (isFinite(thresholdNumeric)) {
                var clampedThreshold = Math.abs(thresholdNumeric)
                if (clampedThreshold !== suspensionRodWarningThresholdM)
                    suspensionRodWarningThresholdM = clampedThreshold
            }
        }
        _storeLastUpdate("threeD", normalized)
    }

    function apply3DUpdates(params) {
        applyThreeDUpdates(params)
    }

    function updateGeometry(params) { applyGeometryUpdates(params) }
    function updateAnimation(params) { applyAnimationUpdates(params) }
    function updateLighting(params) { applyLightingUpdates(params) }
    function updateMaterials(params) { applyMaterialUpdates(params) }
    function updateEnvironment(params) { applyEnvironmentUpdates(params) }
    function updateScene(params) { applySceneUpdates(params) }
    function updateQuality(params) { applyQualityUpdates(params) }
    function updateCamera(params) { applyCameraUpdates(params) }
    function updateEffects(params) { applyEffectsUpdates(params) }
    function updateRender(params) { applyRenderSettings(params) }
    function updateThreeD(params) { applyThreeDUpdates(params) }

    Component.onCompleted: {
        _refreshSceneDefaults()
        const hasBridge = sceneBridge !== null && sceneBridge !== undefined
        const hasWindow = typeof window !== "undefined" && window
        const windowIdentifier = hasWindow && typeof window.objectName === "string" && window.objectName.length > 0
                ? window.objectName
                : "<anonymous>"
        const windowWarningAPI = hasWindow && typeof window.registerShaderWarning === "function"
        console.log("[SimulationRoot] Component completed; sceneBridge:", hasBridge ? "available" : "missing")
        console.log("[SimulationRoot] Window context:", hasWindow ? windowIdentifier : "<missing>")
        console.log("[SimulationRoot] Window.registerShaderWarning available:", windowWarningAPI)
        if (!hasWindow)
            console.warn("[SimulationRoot] Window context missing; shader warnings will stay local")
        _applyBridgeSnapshot(sceneBridge)
        initializeRenderSettings()
    }

    onSceneDefaultsChanged: _refreshSceneDefaults()
    onReflectionProbeDefaultsChanged: _refreshReflectionProbeDefaults()
    onEnvironmentDefaultsMapChanged: _refreshReflectionProbeDefaults()

    onSceneBridgeChanged: {
        _applyBridgeSnapshot(sceneBridge)
    }

    onSceneViewChanged: {
        if (sceneView)
            initializeRenderSettings()
    }

    function diagnosticsWindow() {
        return typeof window !== "undefined" && window ? window : null
    }

    function forwardShaderDiagnostics(eventType, effectId, message) {
        if (!Diagnostics || typeof Diagnostics.forward !== "function")
            return

        var normalizedId = effectId !== undefined && effectId !== null
                ? String(effectId)
                : "unknown"
        var normalizedMessage = message !== undefined && message !== null
                ? String(message)
                : ""

        var label = normalizedId
        if (normalizedMessage.length)
            label = normalizedId + ": " + normalizedMessage

        try {
            Diagnostics.forward(eventType, label, diagnosticsWindow(), "SimulationRoot")
        } catch (error) {
            console.warn("[SimulationRoot] Diagnostics forwarding failed", error)
        }
    }

    function registerShaderWarning(effectId, message) {
        var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
        var normalizedMessage = message !== undefined && message !== null ? String(message) : ""

        forwardShaderDiagnostics("shader_warning", normalizedId, normalizedMessage)

        var bridgeId = effectId !== undefined && effectId !== null ? effectId : normalizedId
        var bridgeMessage = message !== undefined && message !== null ? message : normalizedMessage

        var hostWindow = diagnosticsWindow()
        if (hostWindow && typeof hostWindow.registerShaderWarning === "function") {
            try {
                hostWindow.registerShaderWarning(bridgeId, bridgeMessage)
                return
            } catch (error) {
                console.debug("[SimulationRoot] window.registerShaderWarning failed", error)
            }
        }

        if (!sceneBridge)
            return

        try {
            if (typeof sceneBridge.registerShaderWarning === "function")
                sceneBridge.registerShaderWarning(bridgeId, bridgeMessage)
        } catch (error) {
            console.debug("[SimulationRoot] sceneBridge.registerShaderWarning failed", error)
        }
    }

    function clearShaderWarning(effectId) {
        var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"

        forwardShaderDiagnostics("shader_warning_cleared", normalizedId, "")

        var bridgeId = effectId !== undefined && effectId !== null ? effectId : normalizedId

        var hostWindow = diagnosticsWindow()
        if (hostWindow && typeof hostWindow.clearShaderWarning === "function") {
            try {
                hostWindow.clearShaderWarning(bridgeId)
                return
            } catch (error) {
                console.debug("[SimulationRoot] window.clearShaderWarning failed", error)
            }
        }

        if (!sceneBridge)
            return

        try {
            if (typeof sceneBridge.clearShaderWarning === "function")
                sceneBridge.clearShaderWarning(bridgeId)
        } catch (error) {
            console.debug("[SimulationRoot] sceneBridge.clearShaderWarning failed", error)
        }
    }

    function emitShaderStatusDump(reason) {
        if (!postEffects)
            return
        var snapshot = null
        try {
            if (typeof postEffects.dumpShaderStatus === "function")
                snapshot = postEffects.dumpShaderStatus(reason)
            else if (typeof postEffects.shaderStatusSnapshot === "function")
                snapshot = postEffects.shaderStatusSnapshot(reason)
        } catch (error) {
            console.debug("[SimulationRoot] dumpShaderStatus failed", error)
            snapshot = null
        }
        if (!snapshot || typeof snapshot !== "object")
            return
        if (reason && (!snapshot.effectsBypassReason || !snapshot.effectsBypassReason.length))
            snapshot.effectsBypassReason = String(reason)
        try {
            shaderStatusDumpRequested(snapshot)
        } catch (error) {
            console.debug("[SimulationRoot] shaderStatusDumpRequested emit failed", error)
        }
    }

    function cloneEffectList(value) {
        if (!value)
            return []
        if (Array.isArray(value))
            return value.slice()
        var copy = []
        var length = 0
        try {
            length = value.length
        } catch (error) {
            length = 0
        }
        for (var i = 0; i < length; ++i) {
            try {
                copy.push(value[i])
            } catch (error) {
            }
        }
        return copy
    }

    function _normaliseState(value) {
        if (!value || typeof value !== "object")
            return ({})
        var copy = {}
        for (var key in value) {
            if (Object.prototype.hasOwnProperty.call(value, key))
                copy[key] = value[key]
        }
        return copy
    }

    function _isEmptyMap(value) {
        if (!value || typeof value !== "object")
            return true
        for (var key in value) {
            if (Object.prototype.hasOwnProperty.call(value, key))
                return false
        }
        return true
    }

    function _resetBridgeState() {
        geometryState = ({})
        simulationState = ({})
        threeDState = ({})
        renderState = ({})
        flowTelemetry = ({})
        receiverTelemetry = ({})
        geometryStateReceived = false
        simulationStateReceived = false
        sceneBridgeDispatchCount = 0
        _syncRenderSettingsState()
    }

    function _applyBridgeSnapshot(target) {
        if (!target) {
            _resetBridgeState()
            return
        }
        try {
            geometryState = _normaliseState(target.geometry)
        } catch (error) {
            geometryState = ({})
        }
        try {
            simulationState = _normaliseState(target.simulation)
        } catch (error) {
            simulationState = ({})
        }
        try {
            threeDState = _normaliseState(target.threeD)
        } catch (error) {
            threeDState = ({})
        }
        try {
            renderState = _normaliseState(target.render)
        } catch (error) {
            renderState = ({})
        }
        var snapshotFlow = ({})
        try {
            if (threeDState && typeof threeDState === "object")
                snapshotFlow = _normaliseState(threeDState.flowNetwork || threeDState.flownetwork)
        } catch (error) {
            snapshotFlow = ({})
        }
        flowTelemetry = snapshotFlow
        receiverTelemetry = _resolveReceiverTelemetry(threeDState)
        geometryStateReceived = !_isEmptyMap(geometryState)
        simulationStateReceived = !_isEmptyMap(simulationState)
        _syncRenderSettingsState()
    }

    function _resolveReceiverTelemetry(source) {
        var state = _normaliseState(source)
        if (_isEmptyMap(state))
            return ({})
        var direct = null
        if (state.receiver !== undefined)
            direct = _normaliseState(state.receiver)
        if (!_isEmptyMap(direct))
            return direct
        var network = null
        if (state.flowNetwork !== undefined)
            network = _normaliseState(state.flowNetwork)
        else if (state.flownetwork !== undefined)
            network = _normaliseState(state.flownetwork)
        if (network && !_isEmptyMap(network.receiver))
            return _normaliseState(network.receiver)
        return ({})
    }

    function applyPostProcessingBypass(active, reason) {
        var normalizedReason = reason !== undefined && reason !== null ? String(reason) : ""
        var previousActive = postProcessingBypassed
        var previousReason = postProcessingBypassReason
        postProcessingBypassed = !!active
        postProcessingBypassReason = postProcessingBypassed ? normalizedReason : ""
        updateSimpleFallbackState(postProcessingBypassed, postProcessingBypassReason)

        if (postProcessingBypassed && !previousActive)
            emitShaderStatusDump(normalizedReason)
        else if (postProcessingBypassed && normalizedReason !== previousReason)
            emitShaderStatusDump(normalizedReason)

        if (!sceneView) {
            console.warn("[SimulationRoot] Unable to toggle post-processing bypass; sceneView is not set", active, normalizedReason)
            return
        }

        if (postProcessingBypassed) {
            console.warn("[SimulationRoot] Post-processing bypass activated", normalizedReason)
            try {
                var currentEffects = sceneView.effects
                postProcessingEffectBackup = cloneEffectList(currentEffects)
            } catch (error) {
                postProcessingEffectBackup = []
                console.debug("[SimulationRoot] Failed to cache View3D effects before bypass", error)
            }
            try {
                sceneView.effects = []
            } catch (error) {
                console.warn("[SimulationRoot] Failed to clear View3D effects during bypass", error)
            }
        } else {
            if (previousActive) {
                console.log("[SimulationRoot] Post-processing bypass cleared")
            }
            try {
                var restoreEffects = []
                if (postProcessingEffectBackup && postProcessingEffectBackup.length)
                    restoreEffects = postProcessingEffectBackup
                else if (postEffects && postEffects.effectList)
                    restoreEffects = postEffects.effectList
                sceneView.effects = restoreEffects
                postProcessingEffectBackup = []
            } catch (error) {
                console.warn("[SimulationRoot] Failed to restore View3D effects after bypass", error)
            }
        }
    }

    function updateSimpleFallbackState(active, reason) {
        var normalizedReason = reason && reason.length ? reason : qsTr("Rendering pipeline failure")
        if (active) {
            var reasonChanged = simpleFallbackReason !== normalizedReason
            if (!simpleFallbackActive) {
                simpleFallbackActive = true
                simpleFallbackReason = normalizedReason
                console.warn("[SimulationRoot] Simplified rendering requested ->", normalizedReason)
                simpleFallbackRequested(normalizedReason)
            } else if (reasonChanged) {
                simpleFallbackReason = normalizedReason
                console.warn("[SimulationRoot] Simplified rendering reason updated ->", normalizedReason)
                simpleFallbackRequested(normalizedReason)
            }
        } else {
            if (simpleFallbackActive) {
                simpleFallbackActive = false
                simpleFallbackReason = ""
                console.log("[SimulationRoot] Simplified rendering fallback cleared")
                simpleFallbackRecovered()
            } else if (simpleFallbackReason.length) {
                simpleFallbackReason = ""
            }
        }
    }

    Connections {
        id: postEffectsSignals
        target: root.postEffects
        enabled: !!target
        ignoreUnknownSignals: true

        function onEffectCompilationError(effectId, message) {
            var resolvedMessage = message

            if (resolvedMessage === undefined || resolvedMessage === null || resolvedMessage === "")
                resolvedMessage = qsTr("%1: compilation failed").arg(effectId)

            root.registerShaderWarning(effectId, resolvedMessage)
        }

        function onEffectCompilationRecovered(effectId) {
            root.clearShaderWarning(effectId)
        }

        function onEffectsBypassChanged(active) {
            var reason = ""
            try {
                reason = target && typeof target.effectsBypassReason === "string"
                        ? target.effectsBypassReason
                        : ""
            } catch (error) {
            }
            root.applyPostProcessingBypass(active, reason)
        }

        function onEffectsBypassReasonChanged(reason) {
            if (!target || !target.effectsBypass)
                return
            root.applyPostProcessingBypass(true, reason)
        }

        function onSimplifiedRenderingRequested(reason) {
            root.updateSimpleFallbackState(true, reason)
        }

        function onSimplifiedRenderingRecovered() {
            root.updateSimpleFallbackState(false, "")
        }
    }

    Connections {
        target: root.sceneBridge
        enabled: !!target

        function onGeometryChanged(payload) {
            root.geometryState = _normaliseState(payload)
            root.geometryStateReceived = !_isEmptyMap(root.geometryState)
        }

        function onSimulationChanged(payload) {
            root.simulationState = _normaliseState(payload)
            root.simulationStateReceived = !_isEmptyMap(root.simulationState)
        }

        function onUpdatesDispatched(payload) {
            if (payload && typeof payload === "object")
                root.sceneBridgeDispatchCount += 1
        }
    }

    Binding {
        id: viewEffectsBinding
        target: root.sceneView
        property: "effects"
        value: root.postEffects ? root.postEffects.effectList : []
        when: root.sceneView && root.postEffects && !root.postProcessingBypassed
    }

 // Состояние симуляции, управляется из Python (MainWindow)
 property bool isRunning: animationDefaults && animationDefaults.is_running !== undefined ? Boolean(animationDefaults.is_running) : false
 property var animationDefaults: typeof initialAnimationSettings !== "undefined" ? initialAnimationSettings : null
 property var sceneDefaults: typeof initialSceneSettings !== "undefined" ? initialSceneSettings : null
 property var geometryDefaults: typeof initialGeometrySettings !== "undefined" && initialGeometrySettings ? initialGeometrySettings : emptyGeometryDefaults
 property var diagnosticsDefaults: typeof initialDiagnosticsSettings !== "undefined" ? initialDiagnosticsSettings : null
    property var sceneMaterialsDefaults: ({})
    property var sceneLightingDefaults: ({})
    property var sceneEnvironmentDefaults: ({})
    property var sceneQualityDefaults: ({})
    property var sceneRenderDefaults: ({})
    property var sceneEffectsDefaults: ({})
    property var sceneSuspensionDefaults: ({})
    property var reflectionProbeDefaults: typeof initialReflectionProbeSettings !== "undefined" ? initialReflectionProbeSettings : null
    property var reflectionProbeDefaultsMap: ({})
    property var reflectionProbeMissingKeys: []
    property bool reflectionProbeDefaultsWarningIssued: false
    readonly property var reflectionProbeFallbackDefaults: ({
        "enabled": true,
        "padding_m": 0.15,
        "quality": "veryhigh",
        "refresh_mode": "everyframe",
        "time_slicing": "individualfaces"
    })
 property var lightingState: ({})
 property var materialsState: ({})
 property var environmentState: ({})
 property var qualityState: ({})
 property var renderState: ({})
 property var effectsState: ({})
 property var cameraStateSnapshot: ({})
 property var cameraHudSettings: ({})
 property bool cameraHudEnabled: false
 property real renderScale: 1.0
 property real frameRateLimit: 0.0
 property string renderPolicyKey: "always"
 property var sceneRenderSettings: null
 property bool renderSettingsSupported: false
    property real sceneScaleFactor: 1.0
    property real suspensionRodWarningThresholdM: 0.001
 property bool feedbackReady: false
 property real animationTime: animationDefaults && animationDefaults.animation_time !== undefined ? Number(animationDefaults.animation_time) :0.0 // сек, накапливается Python-таймером
 property bool pythonAnimationActive: false
 property bool pythonLeverAnglesActive: false
 property bool pythonPistonsActive: false
 property bool pythonFrameActive: false
 property bool pythonPressureActive: false
 property bool diagnosticsLoggingEnabled: false
 property bool fallbackEnabled: isRunning && !pythonAnimationActive
 property real fallbackPhase: 0.0
 property real lastFallbackPhase: 0.0
 property real fallbackBaseTime: animationTime
 readonly property real fallbackCycleSeconds: Math.max(0.2, 1.0 / Math.max(userFrequency, 0.01))
 property real batchFlashOpacity: 0.0

    function _sceneDefaultsSection(sectionName) {
        var base = sceneDefaults
        var direct = _resolveMapEntry(base, sectionName)
        if (_isPlainObject(direct))
            return _cloneObject(direct)
        var graphics = _resolveMapEntry(base, "graphics")
        if (_isPlainObject(graphics)) {
            var nested = _resolveMapEntry(graphics, sectionName)
            if (_isPlainObject(nested))
                return _cloneObject(nested)
        }
        return ({})
    }

    function _refreshSceneDefaults() {
        sceneMaterialsDefaults = _sceneDefaultsSection("materials")
        sceneLightingDefaults = _sceneDefaultsSection("lighting")
        sceneEnvironmentDefaults = _sceneDefaultsSection("environment")
        sceneQualityDefaults = _sceneDefaultsSection("quality")
        sceneRenderDefaults = _sceneDefaultsSection("render")
        sceneEffectsDefaults = _sceneDefaultsSection("effects")
        sceneSuspensionDefaults = _sceneDefaultsSection("suspension")
        environmentDefaultsMap = environmentDefaultsMapFor(sceneDefaults)
        _refreshReflectionProbeDefaults()
        _syncSuspensionDefaults()
        _syncRenderSettingsState()
    }

    function _refreshReflectionProbeDefaults() {
        var normalized = _normalizeReflectionProbePayload(reflectionProbeDefaults)
        if (_isEmptyMap(normalized))
            normalized = _normalizeReflectionProbePayload(
                _resolveMapEntry(sceneDefaults, ["graphics", "reflection_probe"])
            )
        if (_isEmptyMap(normalized))
            normalized = _normalizeReflectionProbePayload(
                _resolveMapEntry(sceneDefaults, "reflection_probe")
            )

        var requiredKeys = [
            "enabled",
            "padding_m",
            "quality",
            "refresh_mode",
            "time_slicing",
        ]
        var missing = []
        for (var i = 0; i < requiredKeys.length; ++i) {
            var key = requiredKeys[i]
            if (normalized[key] === undefined)
                missing.push(key)
        }

        if (missing.length) {
            reflectionProbeDefaultsWarningIssued = true
            reflectionProbeMissingKeys = missing.slice()
            console.warn(
                "[SimulationRoot] Reflection probe defaults missing keys:",
                missing.join(", ")
            )
        } else {
            reflectionProbeDefaultsWarningIssued = false
            reflectionProbeMissingKeys = []
        }

        reflectionProbeDefaultsMap = normalized
    }

    function materialsSources() {
        return [materialsState || ({}), sceneMaterialsDefaults || ({}), emptyMaterialsDefaults || ({})]
    }

    function lightingSources() {
        return [lightingState || ({}), sceneLightingDefaults || ({})]
    }

    function qualitySources() {
        return [qualityState || ({}), sceneQualityDefaults || ({})]
    }

    function environmentSources() {
        return [environmentState || ({}), sceneEnvironmentDefaults || ({})]
    }

    function _syncSuspensionDefaults() {
        var sources = []
        if (_isPlainObject(sceneSuspensionDefaults))
            sources.push(sceneSuspensionDefaults)
        if (!sources.length)
            sources.push({})

        var candidate = _valueFromSources(
            sources,
            ["rod_warning_threshold_m", "rodWarningThresholdM", "rodWarningThreshold"],
        )
        var numeric = _coerceNumber(candidate, suspensionRodWarningThresholdM)
        if (!isFinite(numeric))
            numeric = suspensionRodWarningThresholdM
        if (numeric < 0)
            numeric = Math.abs(numeric)
        if (numeric !== suspensionRodWarningThresholdM)
            suspensionRodWarningThresholdM = numeric
    }

    function geometrySources() {
        return [geometryState || ({}), geometryDefaults || ({}), emptyGeometryDefaults || ({})]
    }

    function geometryNumber(keys, fallback) {
        return _coerceNumber(_valueFromSources(geometrySources(), keys), fallback)
    }

    function environmentNumber(keys, fallback) {
        return _coerceNumber(_valueFromSources(environmentSources(), keys), fallback)
    }

    function environmentBool(keys, fallback) {
        var value = _valueFromSources(environmentSources(), keys)
        return value === undefined ? fallback : _coerceBool(value, fallback)
    }

    function _normalizeReflectionProbePayload(source) {
        if (!_isPlainObject(source))
            return ({})
        var normalized = ({})
        if (source.enabled !== undefined)
            normalized.enabled = _coerceBool(source.enabled, true)
        var paddingCandidate = _valueFromSources([source], ["padding_m", "padding"])
        if (paddingCandidate !== undefined) {
            var numericPadding = _coerceNumber(paddingCandidate, Number.NaN)
            if (isFinite(numericPadding))
                normalized.padding_m = numericPadding
        }
        var qualityCandidate = _valueFromSources([source], ["quality"])
        if (qualityCandidate !== undefined) {
            var qualityText = _coerceString(qualityCandidate, "")
            if (qualityText.length)
                normalized.quality = qualityText.toLowerCase()
        }
        var refreshCandidate = _valueFromSources([source], ["refresh_mode", "refreshMode"])
        if (refreshCandidate !== undefined) {
            var refreshText = _coerceString(refreshCandidate, "")
            if (refreshText.length)
                normalized.refresh_mode = refreshText.toLowerCase()
        }
        var slicingCandidate = _valueFromSources([source], ["time_slicing", "timeSlicing"])
        if (slicingCandidate !== undefined) {
            var slicingText = _coerceString(slicingCandidate, "")
            if (slicingText.length)
                normalized.time_slicing = slicingText.toLowerCase()
        }
        if (normalized.padding_m !== undefined)
            normalized.padding = normalized.padding_m
        return normalized
    }

    function _reflectionProbeSourceFromEnvironment(environmentMap) {
        if (!_isPlainObject(environmentMap))
            return ({})
        var legacy = ({
            enabled: _valueFromSources([environmentMap], ["reflection_enabled", "reflectionEnabled"]),
            padding_m: _valueFromSources([environmentMap], ["reflection_padding_m", "reflectionPaddingM"]),
            quality: _valueFromSources([environmentMap], ["reflection_quality", "reflectionQuality"]),
            refresh_mode: _valueFromSources([environmentMap], ["reflection_refresh_mode", "reflectionRefreshMode"]),
            time_slicing: _valueFromSources([environmentMap], ["reflection_time_slicing", "reflectionTimeSlicing"]),
        })
        return _normalizeReflectionProbePayload(legacy)
    }

    function reflectionProbeSources() {
        var sources = []
        var explicit = _normalizeReflectionProbePayload(reflectionProbeDefaultsMap)
        if (!_isEmptyMap(explicit))
            sources.push(explicit)
        var sceneDirect = _normalizeReflectionProbePayload(_resolveMapEntry(sceneDefaults, "reflection_probe"))
        if (!_isEmptyMap(sceneDirect))
            sources.push(sceneDirect)
        var sceneGraphics = _normalizeReflectionProbePayload(
            _resolveMapEntry(sceneDefaults, ["graphics", "reflection_probe"])
        )
        if (!_isEmptyMap(sceneGraphics))
            sources.push(sceneGraphics)
        var legacyEnvironment = _reflectionProbeSourceFromEnvironment(environmentDefaultsMap)
        if (!_isEmptyMap(legacyEnvironment))
            sources.push(legacyEnvironment)
        var fallback = _normalizeReflectionProbePayload(reflectionProbeFallbackDefaults)
        if (!_isEmptyMap(fallback))
            sources.push(fallback)
        return sources
    }

    function reflectionProbeDefaultBool(keys, fallback) {
        var value = _valueFromSources(reflectionProbeSources(), keys)
        return value === undefined ? fallback : _coerceBool(value, fallback)
    }

    function reflectionProbeDefaultNumber(keys, fallback) {
        return _coerceNumber(_valueFromSources(reflectionProbeSources(), keys), fallback)
    }

    function reflectionProbeDefaultString(keys, fallback) {
        var value = _valueFromSources(reflectionProbeSources(), keys)
        if (value === undefined || value === null)
            return fallback
        var text = String(value)
        return text.length ? text : fallback
    }

    function lightingNumber(group, keys, fallback) {
        return _coerceNumber(_valueFromSubsection(lightingSources(), group, keys), fallback)
    }

    function lightingBool(group, keys, fallback) {
        var value = _valueFromSubsection(lightingSources(), group, keys)
        return value === undefined ? fallback : _coerceBool(value, fallback)
    }

    function lightingColor(group, keys, fallback) {
        return _coerceColor(_valueFromSubsection(lightingSources(), group, keys), fallback)
    }

    function qualityShadowBool(keys, fallback) {
        var value = _valueFromSubsection(qualitySources(), [["shadowSettings", "shadows"]], keys)
        return value === undefined ? fallback : _coerceBool(value, fallback)
    }

    function qualityShadowNumber(keys, fallback) {
        return _coerceNumber(_valueFromSubsection(qualitySources(), [["shadowSettings", "shadows"]], keys), fallback)
    }

    function effectsSources() {
        return [effectsState || ({}), sceneEffectsDefaults || ({})]
    }

 function initializeRenderSettings() {
  if (sceneRenderSettings) {
   sceneRenderSettings.destroy();
   sceneRenderSettings = null;
  }

  var propertyExists = sceneView && typeof sceneView.renderSettings !== "undefined";
  if (typeof RenderSettings === "undefined" || !propertyExists) {
   renderSettingsSupported = false;
   console.warn("[SimulationRoot] RenderSettings type unavailable; using default View3D settings");
   return;
  }

  var qmlSource = "import QtQuick 6.10\n" +
                  "import QtQuick3D 6.10\n" +
                  "RenderSettings {\n" +
                  "    renderScale: Math.max(0.1, root.renderScale)\n" +
                  "    maximumFrameRate: root.frameRateLimit > 0 ? root.frameRateLimit : 0\n" +
                  "    renderPolicy: {\n" +
                  "        var key = root.renderPolicyKey || \\\"always\\\";\n" +
                  "        if (key === \\\"ondemand\\\")\n" +
                  "            return RenderSettings.OnDemand;\n" +
                  "        if (key === \\\"automatic\\\" && RenderSettings.Automatic !== undefined)\n" +
                  "            return RenderSettings.Automatic;\n" +
                  "        if (key === \\\"manual\\\" && RenderSettings.Manual !== undefined)\n" +
                  "            return RenderSettings.Manual;\n" +
                  "        return RenderSettings.Always;\n" +
                  "    }\n" +
                  "}\n";

  try {
   var created = Qt.createQmlObject(qmlSource, sceneView, "DynamicRenderSettings");
   if (created) {
    var depthPrepared = false;
    if (typeof DepthTextureActivator !== "undefined"
            && DepthTextureActivator
            && typeof DepthTextureActivator.prepareRenderSettings === "function") {
     depthPrepared = DepthTextureActivator.prepareRenderSettings(sceneView, created);
    } else {
     try {
      if ("depthPrePassEnabled" in created) {
       created.depthPrePassEnabled = true;
       depthPrepared = true;
      }
     } catch (error) {
      console.debug("[SimulationRoot] depthPrePassEnabled preconfigure failed", error);
     }
     try {
      if (typeof created.enableDepthBuffer === "function") {
       created.enableDepthBuffer();
       depthPrepared = true;
      }
     } catch (error) {
      console.debug("[SimulationRoot] enableDepthBuffer preconfigure failed", error);
     }
    }
    if (depthPrepared) {
     console.log("[SimulationRoot] RenderSettings depth pre-pass configured before assignment");
    }
    sceneView.renderSettings = created;
    sceneRenderSettings = created;
    renderSettingsSupported = true;
   } else {
    renderSettingsSupported = false;
    console.warn("[SimulationRoot] Failed to instantiate RenderSettings; defaults will be used");
   }
  } catch (error) {
   renderSettingsSupported = false;
   sceneRenderSettings = null;
   console.error("[SimulationRoot] initializeRenderSettings failed", error);
  }
 }

readonly property real defaultDofFocusDistanceM: effectsDefaultNumber(["dof_focus_distance"], 2.5)

property var environmentDefaultsMap: ({})
readonly property var activeMaterialsDefaults: _deepMerge(sceneMaterialsDefaults, materialsState)
readonly property var activeLightingDefaults: _deepMerge(sceneLightingDefaults, lightingState)
property bool reflectionProbeEnabledDefault: reflectionProbeDefaultBool(
    ["enabled", "reflection_enabled", "reflectionEnabled"],
    environmentDefaultBool(environmentDefaultsMap, ["reflection_enabled", "reflectionEnabled"], true)
)
property bool reflectionProbeEnabledOverrideActive: false
property bool reflectionProbeEnabledOverride: reflectionProbeEnabledDefault
readonly property bool reflectionProbeEnabledState: reflectionProbeEnabledOverrideActive
        ? reflectionProbeEnabledOverride
        : reflectionProbeEnabledDefault

onReflectionProbeEnabledDefaultChanged: {
    if (!reflectionProbeEnabledOverrideActive)
        reflectionProbeEnabledOverride = reflectionProbeEnabledDefault
}
property string reflectionProbeQualitySetting: (function() {
    var fallback = environmentDefaultString(
        environmentDefaultsMap,
        ["reflection_quality", "reflectionQuality"],
        "veryhigh"
    )
    var value = reflectionProbeDefaultString(
        ["quality", "reflection_quality", "reflectionQuality"],
        fallback
    )
    return value.toLowerCase()
})()
property string reflectionProbeRefreshModeSetting: (function() {
    var fallback = environmentDefaultString(
        environmentDefaultsMap,
        ["reflection_refresh_mode", "reflectionRefreshMode"],
        "everyframe"
    )
    var value = reflectionProbeDefaultString(
        ["refresh_mode", "refreshMode", "reflection_refresh_mode", "reflectionRefreshMode"],
        fallback
    )
    return value.toLowerCase()
})()
property string reflectionProbeTimeSlicingSetting: (function() {
    var fallback = environmentDefaultString(
        environmentDefaultsMap,
        ["reflection_time_slicing", "reflectionTimeSlicing"],
        "individualfaces"
    )
    var value = reflectionProbeDefaultString(
        ["time_slicing", "timeSlicing", "reflection_time_slicing", "reflectionTimeSlicing"],
        fallback
    )
    return value.toLowerCase()
})()
property real reflectionProbePaddingM: reflectionProbeDefaultNumber(
    ["padding_m", "padding"],
    environmentNumber(["reflection_padding_m", "reflection_probe_padding", "reflectionProbePadding"], 0.15)
)
readonly property int reflectionProbeQualityValue: reflectionProbeQualityFrom(reflectionProbeQualitySetting)
readonly property int reflectionProbeRefreshModeValue: reflectionProbeRefreshModeFrom(reflectionProbeRefreshModeSetting)
readonly property int reflectionProbeTimeSlicingValue: reflectionProbeTimeSlicingFrom(reflectionProbeTimeSlicingSetting)
property color environmentBackgroundColorDefault: environmentDefaultString(environmentDefaultsMap, ["background_color", "backgroundColor"], "#1f242c")
property string environmentBackgroundModeDefault: environmentDefaultString(environmentDefaultsMap, ["background_mode", "backgroundMode"], "skybox")
property bool environmentSkyboxEnabledDefault: environmentDefaultBool(environmentDefaultsMap, ["skybox_enabled", "skyboxEnabled"], true)
property bool environmentIblBackgroundEnabledDefault: environmentDefaultBool(environmentDefaultsMap, ["ibl_background_enabled", "iblBackgroundEnabled", "skybox_enabled", "skyboxEnabled"], true)
property bool environmentIblLightingEnabledDefault: environmentDefaultBool(environmentDefaultsMap, ["ibl_lighting_enabled", "iblLightingEnabled", "ibl_enabled", "iblEnabled"], true)
property bool environmentIblMasterEnabledDefault: environmentDefaultBool(environmentDefaultsMap, ["ibl_master_enabled", "iblMasterEnabled"], environmentIblLightingEnabledDefault || environmentIblBackgroundEnabledDefault)
property bool environmentIblBindToCameraDefault: environmentDefaultBool(environmentDefaultsMap, ["ibl_bind_to_camera", "iblBindToCamera"], false)
property real environmentIblIntensityDefault: environmentDefaultNumber(environmentDefaultsMap, ["ibl_intensity", "iblIntensity"], 1.3)
property real environmentSkyboxBrightnessDefault: environmentDefaultNumber(environmentDefaultsMap, ["skybox_brightness", "probe_brightness", "skyboxBrightness", "probeBrightness"], 1.0)
property real environmentProbeHorizonDefault: environmentDefaultNumber(environmentDefaultsMap, ["probe_horizon", "probeHorizon"], 0.0)
property real environmentIblRotationPitchDefault: environmentDefaultNumber(environmentDefaultsMap, ["ibl_offset_x", "iblRotationPitchDeg"], 0.0)
property real environmentIblRotationYawDefault: environmentDefaultNumber(environmentDefaultsMap, ["ibl_rotation", "iblRotationDeg"], 0.0)
property real environmentIblRotationRollDefault: environmentDefaultNumber(environmentDefaultsMap, ["ibl_offset_y", "iblRotationRollDeg"], 0.0)
property real environmentSkyboxBlurDefault: environmentDefaultNumber(environmentDefaultsMap, ["skybox_blur", "skyboxBlur"], 0.08)
property url environmentHdrSourceDefault: normalizeHdrSource(environmentDefaultString(environmentDefaultsMap, ["ibl_source", "hdr_source", "iblPrimary"], ""))

    function parseReflectionProbeEnum(value, mapping, fallback) {
        if (value === undefined || value === null)
            return fallback
        var original = String(value).trim().toLowerCase()
        if (!original.length)
            return fallback
        if (Object.prototype.hasOwnProperty.call(mapping, original))
            return mapping[original]
        var normalized = original.replace(/[^a-z0-9]/g, "")
        if (Object.prototype.hasOwnProperty.call(mapping, normalized))
            return mapping[normalized]
        return fallback
    }

    function reflectionProbeQualityFrom(value) {
        return parseReflectionProbeEnum(value, {
            low: ReflectionProbe.Low,
            medium: ReflectionProbe.Medium,
            high: ReflectionProbe.High,
            veryhigh: ReflectionProbe.VeryHigh,
            very_high: ReflectionProbe.VeryHigh,
            ultra: ReflectionProbe.VeryHigh
        }, ReflectionProbe.VeryHigh)
    }

    function reflectionProbeRefreshModeFrom(value) {
        return parseReflectionProbeEnum(value, {
            everyframe: ReflectionProbe.EveryFrame,
            always: ReflectionProbe.EveryFrame,
            firstframe: ReflectionProbe.FirstFrame,
            first_frame: ReflectionProbe.FirstFrame,
            first: ReflectionProbe.FirstFrame,
            never: ReflectionProbe.FirstFrame,
            disabled: ReflectionProbe.FirstFrame,
            off: ReflectionProbe.FirstFrame
        }, ReflectionProbe.EveryFrame)
    }

    function reflectionProbeTimeSlicingFrom(value) {
        return parseReflectionProbeEnum(value, {
            notimeslicing: ReflectionProbe.NoTimeSlicing,
            none: ReflectionProbe.NoTimeSlicing,
            allfacesatonce: ReflectionProbe.AllFacesAtOnce,
            allfaces: ReflectionProbe.AllFacesAtOnce,
            together: ReflectionProbe.AllFacesAtOnce,
            individualfaces: ReflectionProbe.IndividualFaces,
            perface: ReflectionProbe.IndividualFaces
        }, ReflectionProbe.IndividualFaces);
    }

    function sanitizeReflectionProbePadding(value) {
        if (value === undefined || value === null)
            return reflectionProbePaddingM;
        var numeric = Number(value);
        if (!isFinite(numeric))
            return reflectionProbePaddingM;
        return Math.max(0, numeric);
    }


    PostEffects {
        id: postEffectsComponent
        visible: false
        enabled: false
        diagnosticsLoggingEnabled: root.diagnosticsLoggingEnabled
        onSimplifiedRenderingRequested: root.updateSimpleFallbackState(true, reason)
        onSimplifiedRenderingRecovered: root.updateSimpleFallbackState(false, "")
    }

    Binding {
        target: root
        property: "postEffects"
        value: postEffectsComponent
    }

    SceneEnvironmentController {
        id: sceneEnvironment
        objectName: "sceneEnvironment"
        sceneBridge: root.sceneBridge
        diagnosticsLoggingEnabled: root.diagnosticsLoggingEnabled
        materialsDefaultsOverride: root.activeMaterialsDefaults
        lightingContextOverride: root.activeLightingDefaults
        onSimplifiedRenderingRequested: root.updateSimpleFallbackState(true, reason)
        onSimplifiedRenderingRecovered: root.updateSimpleFallbackState(false, "")
    }

    Animation.RigAnimationController {
        id: rigAnimation
        smoothingEnabled: true
        smoothingDurationMs: 160.0
        angleSnapThresholdDeg: 5.0
        pistonSnapThresholdM: 0.01
    }

    Scene.SharedMaterials {
        id: sharedMaterials
        initialSharedMaterials: sceneMaterialsDefaults
        materialsDefaults: root.activeMaterialsDefaults
    }

    View3D {
        id: sceneView
        objectName: "simulationView"
        anchors.fill: parent
        visible: !root.simpleFallbackActive
        camera: cameraController.camera
        environment: sceneEnvironment

        Node {
            id: worldRoot
            objectName: "worldRoot"
            position: Qt.vector3d(0, rigAnimation.frameHeave * root.sceneScaleFactor, 0)
            eulerRotation: Qt.vector3d(rigAnimation.framePitchDeg, 0, rigAnimation.frameRollDeg)
        }

        Scene.SuspensionAssembly {
            id: suspensionAssembly
            worldRoot: worldRoot
            geometryState: root.geometryState
            geometryDefaults: root.geometryDefaults
            emptyGeometryDefaults: root.emptyGeometryDefaults
            sharedMaterials: sharedMaterials
            materialsDefaults: root.activeMaterialsDefaults
            leverAngles: rigAnimation.leverAnglesDeg
            pistonPositions: rigAnimation.pistonPositions
            sceneScaleFactor: root.sceneScaleFactor
            flowTelemetry: root.flowTelemetry
            receiverTelemetry: root.receiverTelemetry
            reflectionProbeEnabled: root.reflectionProbeEnabledState
            reflectionProbePaddingM: sanitizeReflectionProbePadding(root.reflectionProbePaddingM)
            reflectionProbeQualityValue: root.reflectionProbeQualityValue
            reflectionProbeRefreshModeValue: root.reflectionProbeRefreshModeValue
            reflectionProbeTimeSlicingValue: root.reflectionProbeTimeSlicingValue
            rodWarningThreshold: root.suspensionRodWarningThresholdM
        }

        DirectionalLights {
            id: directionalLights
            worldRoot: worldRoot
            cameraRig: cameraController.rig
            shadowsEnabled: qualityShadowBool(["enabled"], true)
            shadowResolution: qualityShadowNumber(["resolution", "shadowResolution"], 4096)
            shadowFilterSamples: qualityShadowNumber(["filterSamples", "filter", "samples"], 32)
            shadowBias: qualityShadowNumber(["bias", "shadowBias"], 8.0)
            shadowFactor: qualityShadowNumber(["factor", "darkness", "shadowFactor"], 80.0)

            keyLightBrightness: lightingNumber("key", ["brightness", "intensity"], 1.0)
            keyLightColor: lightingColor("key", "color", "#ffffff")
            keyLightAngleX: lightingNumber("key", ["angle_x", "angleX"], 25.0)
            keyLightAngleY: lightingNumber("key", ["angle_y", "angleY"], 23.5)
            keyLightAngleZ: lightingNumber("key", ["angle_z", "angleZ"], 0.0)
            keyLightCastsShadow: lightingBool("key", ["cast_shadow", "castsShadow"], true)
            keyLightBindToCamera: lightingBool("key", ["bind_to_camera", "bindToCamera"], false)
            keyLightPosX: lightingNumber("key", ["position_x", "pos_x", "x"], 0.0)
            keyLightPosY: lightingNumber("key", ["position_y", "pos_y", "y"], 0.0)
            keyLightPosZ: lightingNumber("key", ["position_z", "pos_z", "z"], 0.0)

            fillLightBrightness: lightingNumber("fill", ["brightness", "intensity"], 1.0)
            fillLightColor: lightingColor("fill", "color", "#f1f4ff")
            fillLightAngleX: lightingNumber("fill", ["angle_x", "angleX"], 0.0)
            fillLightAngleY: lightingNumber("fill", ["angle_y", "angleY"], -45.0)
            fillLightAngleZ: lightingNumber("fill", ["angle_z", "angleZ"], 0.0)
            fillLightCastsShadow: lightingBool("fill", ["cast_shadow", "castsShadow"], false)
            fillLightBindToCamera: lightingBool("fill", ["bind_to_camera", "bindToCamera"], false)
            fillLightPosX: lightingNumber("fill", ["position_x", "pos_x", "x"], 0.0)
            fillLightPosY: lightingNumber("fill", ["position_y", "pos_y", "y"], 0.0)
            fillLightPosZ: lightingNumber("fill", ["position_z", "pos_z", "z"], 0.0)

            rimLightBrightness: lightingNumber("rim", ["brightness", "intensity"], 1.1)
            rimLightColor: lightingColor("rim", "color", "#ffe1bd")
            rimLightAngleX: lightingNumber("rim", ["angle_x", "angleX"], 30.0)
            rimLightAngleY: lightingNumber("rim", ["angle_y", "angleY"], -135.0)
            rimLightAngleZ: lightingNumber("rim", ["angle_z", "angleZ"], 0.0)
            rimLightCastsShadow: lightingBool("rim", ["cast_shadow", "castsShadow"], false)
            rimLightBindToCamera: lightingBool("rim", ["bind_to_camera", "bindToCamera"], false)
            rimLightPosX: lightingNumber("rim", ["position_x", "pos_x", "x"], 0.0)
            rimLightPosY: lightingNumber("rim", ["position_y", "pos_y", "y"], 0.0)
            rimLightPosZ: lightingNumber("rim", ["position_z", "pos_z", "z"], 0.0)
        }

        PointLights {
            id: pointLights
            worldRoot: worldRoot
            cameraRig: cameraController.rig
            pointLightBrightness: lightingNumber("point", ["brightness", "intensity"], 50.0)
            pointLightColor: lightingColor("point", "color", "#fff7e0")
            pointLightX: lightingNumber("point", ["position_x", "pos_x", "x"], 0.0)
            pointLightY: lightingNumber("point", ["position_y", "pos_y", "y"], 2.6)
            pointLightZ: lightingNumber("point", ["position_z", "pos_z", "z"], 1.5)
            pointLightRange: lightingNumber("point", "range", 3.6)
            constantFade: lightingNumber("point", ["constant_fade", "constantFade"], 1.0)
            linearFade: lightingNumber("point", ["linear_fade", "linearFade"], 0.01)
            quadraticFade: lightingNumber("point", ["quadratic_fade", "quadraticFade"], 1.0)
            pointLightCastsShadow: lightingBool("point", ["cast_shadow", "castsShadow"], false)
            pointLightBindToCamera: lightingBool("point", ["bind_to_camera", "bindToCamera"], false)
        }
    }

    Binding {
        target: root
        property: "sceneView"
        value: sceneView
    }

    CameraController {
        id: cameraController
        anchors.fill: parent
        worldRoot: worldRoot
        view3d: sceneView
        sceneBridge: root.sceneBridge
        taaMotionAdaptive: environmentBool(["taa_motion_adaptive", "taaMotionAdaptive"], false)
        hudVisible: root.cameraHudEnabled
        hudSettings: root.cameraHudSettings
        sceneScaleFactor: root.sceneScaleFactor
        visible: !root.simpleFallbackActive
        z: 5000
        onHudToggleRequested: root.cameraHudEnabled = !root.cameraHudEnabled
    }

    BridgeIndicatorsPanel {
        id: bridgeIndicatorsPanel
        objectName: "bridgeIndicators"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 18
        geometryState: root.geometryState
        simulationState: root.simulationState
        sceneBridgeConnected: root.sceneBridgeAvailable
        sceneBridgeHasUpdates: root.sceneBridgeDispatchCount > 0
        visible: true
        z: 9500
    }

    readonly property alias bridgeIndicators: bridgeIndicatorsPanel
    readonly property alias geometryIndicatorItem: bridgeIndicatorsPanel.geometryIndicatorItem
    readonly property alias simulationIndicatorItem: bridgeIndicatorsPanel.simulationIndicatorItem
    readonly property alias sceneSharedMaterials: sharedMaterials
    readonly property alias sceneDirectionalLights: directionalLights
    readonly property alias scenePointLights: pointLights
    readonly property alias sceneSuspensionAssembly: suspensionAssembly
}
