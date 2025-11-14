#pragma ComponentBehavior: Bound

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
 * (Оригинал восстановлен; добавлен effectsDefaultNumber helper)
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
    readonly property var propertySuffixMap: ({
        texture_path: "TexturePath",
        normal_strength: "NormalStrength",
        occlusion_amount: "OcclusionAmount",
        thickness: "Thickness",
        alpha_mode: "AlphaMode",
        alpha_cutoff: "AlphaCutoff"
    })
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
        try { applyBatchedUpdates(pendingPythonUpdates) } finally { pendingPythonUpdates = null }
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
            for (var key in base) if (Object.prototype.hasOwnProperty.call(base, key)) result[key] = base[key]
        }
        if (payload && typeof payload === "object") {
            for (var updateKey in payload) if (Object.prototype.hasOwnProperty.call(payload, updateKey)) result[updateKey] = payload[updateKey]
        }
        return result
    }
    function _isPlainObject(value) { return value && typeof value === "object" && !Array.isArray(value) }
    function _cloneObject(value) {
        if (!_isPlainObject(value)) return ({})
        var clone = {}
        for (var key in value) if (Object.prototype.hasOwnProperty.call(value, key)) clone[key] = _isPlainObject(value[key]) ? _cloneObject(value[key]) : value[key]
        return clone
    }
    function _deepMerge(base, payload) {
        var result = _cloneObject(base)
        if (_isPlainObject(payload)) for (var key in payload) if (Object.prototype.hasOwnProperty.call(payload,key)) result[key] = _isPlainObject(payload[key]) ? _deepMerge(result[key], payload[key]) : payload[key]
        return result
    }
    function _normaliseKeyList(names) {
        var list = []
        function add(name) { if (name && list.indexOf(name) === -1) list.push(name) }
        function pushVariants(raw) {
            if (raw === undefined || raw === null) return
            var text = String(raw)
            if (!text.length) return
            add(text)
            add(text.toLowerCase())
            add(text.replace(/([A-Z])/g, function(m){ return "_" + m.toLowerCase() }))
            add(text.replace(/_([a-zA-Z0-9])/g, function(_,c){ return c.toUpperCase() }))
        }
        if (Array.isArray(names)) for (var i=0;i<names.length;++i) pushVariants(names[i]); else pushVariants(names)
        return list
    }
    function _resolveMapEntry(source, nameOptions) {
        if (!_isPlainObject(source)) return undefined
        var names = _normaliseKeyList(nameOptions)
        for (var i=0;i<names.length;++i) if (names[i] && Object.prototype.hasOwnProperty.call(source, names[i])) return source[names[i]]
        return undefined
    }
    function _valueFromSubsection(sources, sectionNames, keyNames) {
        var sectionList = []
        if (Array.isArray(sectionNames)) sectionList = sectionNames
        else if (sectionNames !== undefined && sectionNames !== null) sectionList = [sectionNames]
        var keys = _normaliseKeyList(keyNames)
        for (var i=0;i<sources.length;++i) {
            var current = sources[i]; var valid = true
            for (var j=0;j<sectionList.length;++j) { current = _resolveMapEntry(current, sectionList[j]); if (!_isPlainObject(current)) { valid=false; break } }
            if (!valid) continue
            for (var k=0;k<keys.length;++k) { var candidate = current[keys[k]]; if (candidate !== undefined) return candidate }
        }
        return undefined
    }
    function _valueFromSources(sources, keyNames) { return _valueFromSubsection(sources, [], keyNames) }
    function _valueFromGroupOrPrefixes(sources, groupName, keyNames) {
        var groupedValue = _valueFromSubsection(sources, groupName, keyNames)
        if (groupedValue !== undefined) return groupedValue
        var groupVariants = _normaliseKeyList(groupName)
        var keyVariants = _normaliseKeyList(keyNames)
        var combined = []
        function appendKey(c) { if (c && c.length && combined.indexOf(c) === -1) combined.push(c) }
        for (var gi=0;gi<groupVariants.length;++gi) {
            var gv = groupVariants[gi]; if (!gv || !gv.length) continue
            for (var ki=0;ki<keyVariants.length;++ki) {
                var kv = keyVariants[ki]; if (!kv || !kv.length) continue
                appendKey(gv + "_" + kv)
                appendKey(gv + kv.charAt(0).toUpperCase() + kv.slice(1))
            }
        }
        if (!combined.length) return undefined
        return _valueFromSources(sources, combined)
    }
    function _coerceNumber(value, fallback) { var n = Number(value); return isFinite(n) ? n : fallback }
    function _coerceBool(value, fallback) {
        if (value === undefined || value === null) return fallback
        if (typeof value === "string") {
            var lowered = value.toLowerCase()
            if (["true","yes","1"].indexOf(lowered) !== -1) return true
            if (["false","no","0"].indexOf(lowered) !== -1) return false
        }
        return !!value
    }
    function _coerceColor(value, fallback) { if (value===undefined||value===null) return fallback; var t=String(value); return t.length?t:fallback }
    function _coerceString(value, fallback) { if (value===undefined||value===null) return fallback; var t=String(value); return t.length?t:fallback }
    function environmentDefaultsMapFor(source) {
        if (!_isPlainObject(source)) return ({})
        var direct = _resolveMapEntry(source, "environment")
        if (_isPlainObject(direct)) return _cloneObject(direct)
        var graphics = _resolveMapEntry(source, "graphics")
        if (_isPlainObject(graphics)) {
            var nested = _resolveMapEntry(graphics, "environment")
            if (_isPlainObject(nested)) return _cloneObject(nested)
        }
        return ({})
    }
    function environmentDefaultString(map, keys, fallback) {
        var value = _valueFromSources([map || ({})], keys)
        if (value === undefined || value === null) return fallback
        var text = String(value); return text.length ? text : fallback
    }
    function environmentDefaultNumber(map, keys, fallback) { return _coerceNumber(_valueFromSources([map||({})], keys), fallback) }
    function environmentDefaultBool(map, keys, fallback) { var value = _valueFromSources([map||({})], keys); return value === undefined ? fallback : _coerceBool(value, fallback) }
    function _normalizeRenderPolicy(value, fallback) {
        var defaultKey = fallback !== undefined && fallback !== null ? String(fallback) : "always"
        var text = _coerceString(value, defaultKey).toLowerCase()
        if (text === "on_demand" || text === "on-demand") text = "ondemand"
        if (["always","ondemand","automatic","manual"].indexOf(text) !== -1) return text
        return defaultKey.toLowerCase()
    }
    function _renderSources() { return [renderState||({}), qualityState||({}), sceneRenderDefaults||({}), sceneQualityDefaults||({})] }
    function _syncRenderSettingsState() {
        var sources = _renderSources()
        var scaleFallback = renderScale > 0 ? renderScale : 1.0
        var scaleValue = _coerceNumber(_valueFromSources(sources,["renderScale","render_scale","sceneScaleFactor","scene_scale_factor"]), scaleFallback)
        if (!isFinite(scaleValue) || scaleValue <= 0) scaleValue = 1.0
        if (scaleValue !== renderScale) renderScale = scaleValue
        var frameFallback = frameRateLimit >= 0 ? frameRateLimit : 0
        var frameValue = _coerceNumber(_valueFromSources(sources,["frameRateLimit","frame_rate_limit","frameLimit","frame_limit"]), frameFallback)
        if (!isFinite(frameValue) || frameValue < 0) frameValue = 0
        if (frameValue !== frameRateLimit) frameRateLimit = frameValue
        var policyValue = _valueFromSources(sources,["renderPolicy","render_policy","renderMode","render_mode"])
        var normalizedPolicy = _normalizeRenderPolicy(policyValue, renderPolicyKey)
        if (normalizedPolicy !== renderPolicyKey) renderPolicyKey = normalizedPolicy
    }
    function normalizeHdrSource(value) {
        if (value === undefined || value === null) return ""
        var text = String(value).trim()
        if (!text.length) return ""
        if (text.startsWith("qrc:/") || text.indexOf("://") > 0 || text.startsWith("data:")) return text
        return Qt.resolvedUrl(text)
    }
    function _storeLastUpdate(category, payload) {
        var snapshot = _mergeObjects(lastUpdateByCategory, {})
        var stored = payload && typeof payload === "object" ? _normaliseState(payload) : payload
        snapshot[category] = stored
        lastUpdateByCategory = snapshot
    }
    function _acknowledgeBatch(categories) {
        if (categories && categories.length) batchFlashOpacity = 1.0
        var summary = { timestamp: Date.now(), categories: categories && categories.length ? categories.slice() : [], source: "python" }
        batchUpdatesApplied(summary)
    }
    function applyBatchedUpdates(updates) {
        if (!updates || typeof updates !== "object") return
        _logBatchEvent("signal_received","applyBatchedUpdates")
        var categories = []
        if (updates.geometry !== undefined) { categories.push("geometry"); applyGeometryUpdates(updates.geometry) }
        if (updates.animation !== undefined) { categories.push("animation"); applyAnimationUpdates(updates.animation) }
        if (updates.lighting !== undefined) { categories.push("lighting"); applyLightingUpdates(updates.lighting) }
        if (updates.materials !== undefined) { categories.push("materials"); applyMaterialUpdates(updates.materials) }
        if (updates.environment !== undefined) { categories.push("environment"); applyEnvironmentUpdates(updates.environment) }
        if (updates.scene !== undefined) { categories.push("scene"); applySceneUpdates(updates.scene) }
        if (updates.quality !== undefined) { categories.push("quality"); applyQualityUpdates(updates.quality) }
        if (updates.camera !== undefined) { categories.push("camera"); applyCameraUpdates(updates.camera) }
        if (updates.effects !== undefined) { categories.push("effects"); applyEffectsUpdates(updates.effects) }
        if (updates.render !== undefined) { categories.push("render"); applyRenderSettings(updates.render) }
        if (updates.simulation !== undefined) { categories.push("simulation"); applySimulationUpdates(updates.simulation) }
        if (updates.threeD !== undefined) { categories.push("threeD"); applyThreeDUpdates(updates.threeD) }
        _acknowledgeBatch(categories)
    }
    function applyGeometryUpdates(params) {
        _logBatchEvent("function_called","applyGeometryUpdates")
        var normalized = _normaliseState(params)
        if (!_isEmptyMap(normalized)) {
            geometryState = _deepMerge(geometryState, normalized)
            geometryStateReceived = true
            if (cameraController && typeof cameraController.updateGeometry === "function") {
                try { cameraController.updateGeometry(normalized) } catch (e) { console.debug("[SimulationRoot] cameraController.updateGeometry failed", e) }
            }
        }
        _storeLastUpdate("geometry", normalized)
    }
    function applySimulationUpdates(params) {
        _logBatchEvent("function_called","applySimulationUpdates")
        var normalized = _normaliseState(params)
        if (!_isEmptyMap(normalized)) { simulationState = _mergeObjects(simulationState, normalized); simulationStateReceived = true }
        if (normalized.animation) applyAnimationUpdates(normalized.animation)
        if (normalized.threeD) applyThreeDUpdates(normalized.threeD)
        _storeLastUpdate("simulation", normalized)
    }
    function applyAnimationUpdates(params) {
        _logBatchEvent("function_called","applyAnimationUpdates")
        var payload = params || {}
        var previousRunning = isRunning
        function _normalizeNumber(v,f){ if(v===undefined||v===null) return f; var c=Number(v); return isNaN(c)?f:c }
        animationTime = _normalizeNumber(payload.animation_time, animationTime)
        animationTime = _normalizeNumber(payload.animationTime, animationTime)
        function _normalizeBool(v,f){ if(v===undefined||v===null) return f; return Boolean(v) }
        isRunning = _normalizeBool(payload.is_running, isRunning)
        isRunning = _normalizeBool(payload.running, isRunning)
        pythonAnimationActive = _normalizeBool(payload.python_driven, pythonAnimationActive)
        pythonAnimationActive = _normalizeBool(payload.pythonDriven, pythonAnimationActive)
        var frameSource = _resolveMapEntry(payload,"frame")
        if (_isPlainObject(frameSource) && rigAnimation && typeof rigAnimation.applyFrameMotion === "function") {
            pythonFrameActive = true
            try { rigAnimation.applyFrameMotion(frameSource,{ immediate: !pythonAnimationActive }) } catch (e) { console.debug("[SimulationRoot] rigAnimation.applyFrameMotion failed", e) }
        }
        var leverAnglesSource = _resolveMapEntry(payload,["leverAngles","lever_angles"])
        if (_isPlainObject(leverAnglesSource) && rigAnimation && typeof rigAnimation.applyLeverAnglesRadians === "function") {
            pythonLeverAnglesActive = true
            try { rigAnimation.applyLeverAnglesRadians(leverAnglesSource,{ immediate: !pythonAnimationActive }) } catch (e) { console.debug("[SimulationRoot] rigAnimation.applyLeverAnglesRadians failed", e) }
        }
        var pistonSource = _resolveMapEntry(payload,["pistonPositions","piston_positions"])
        if (_isPlainObject(pistonSource) && rigAnimation && typeof rigAnimation.applyPistonPositions === "function") {
            pythonPistonsActive = true
            try { rigAnimation.applyPistonPositions(pistonSource,{ immediate: !pythonAnimationActive }) } catch (e) { console.debug("[SimulationRoot] rigAnimation.applyPistonPositions failed", e) }
        }
        _storeLastUpdate("animation", payload)
        if (isRunning !== previousRunning) animationToggled(isRunning)
    }
    function applyLightingUpdates(params) { _logBatchEvent("function_called","applyLightingUpdates"); var normalized=_normaliseState(params); lightingState=_deepMerge(lightingState,normalized); _storeLastUpdate("lighting",normalized) }
    function applyMaterialUpdates(params) { _logBatchEvent("function_called","applyMaterialUpdates"); var normalized=_normaliseState(params); materialsState=_deepMerge(materialsState,normalized); _storeLastUpdate("materials",normalized) }
    function applyEnvironmentUpdates(params) {
        _logBatchEvent("function_called","applyEnvironmentUpdates")
        var normalized = _normaliseState(params)
        environmentState = _deepMerge(environmentState, normalized)
        var reflectionToggle = _valueFromSources([normalized],["reflection_enabled","reflectionEnabled"])
        if (reflectionToggle !== undefined) _applyReflectionProbeEnabledOverride(reflectionToggle)
        if (sceneEnvironment && typeof sceneEnvironment.applyEnvironmentPayload === "function") {
            try { sceneEnvironment.applyEnvironmentPayload(normalized) } catch (e) { console.debug("[SimulationRoot] sceneEnvironment.applyEnvironmentPayload failed", e) }
        }
        var scaleCandidate = _valueFromSources([normalized],["sceneScaleFactor","scene_scale_factor","render_scale"])
        var numericScale = _coerceNumber(scaleCandidate, sceneScaleFactor)
        if (isFinite(numericScale) && numericScale > 0 && numericScale !== sceneScaleFactor) sceneScaleFactor = numericScale
        _storeLastUpdate("environment", normalized)
    }
    function applySceneUpdates(params) { _logBatchEvent("function_called","applySceneUpdates"); _storeLastUpdate("scene", params || {}) }
    function applyQualityUpdates(params) {
        _logBatchEvent("function_called","applyQualityUpdates")
        var normalized = _normaliseState(params)
        qualityState = _deepMerge(qualityState, normalized)
        if (sceneEnvironment && typeof sceneEnvironment.applyQualityPayload === "function") {
            try { sceneEnvironment.applyQualityPayload(normalized) } catch (e) { console.debug("[SimulationRoot] sceneEnvironment.applyQualityPayload failed", e) }
        }
        if (_isPlainObject(normalized) || !_isEmptyMap(qualityState)) _syncRenderSettingsState()
        _storeLastUpdate("quality", normalized)
    }
    function applyCameraUpdates(params) {
        _logBatchEvent("function_called","applyCameraUpdates")
        var normalized = _normaliseState(params)
        cameraStateSnapshot = _deepMerge(cameraStateSnapshot, normalized)
        if (cameraController && typeof cameraController.applyCameraUpdates === "function") {
            try { cameraController.applyCameraUpdates(normalized) } catch (e) { console.debug("[SimulationRoot] cameraController.applyCameraUpdates failed", e) }
        }
        _storeLastUpdate("camera", normalized)
    }
    function applyEffectsUpdates(params) {
        _logBatchEvent("function_called","applyEffectsUpdates")
        var normalized = _normaliseState(params)
        effectsState = _deepMerge(effectsState, normalized)
        if (sceneEnvironment && typeof sceneEnvironment.applyEffectsPayload === "function") {
            try { sceneEnvironment.applyEffectsPayload(normalized) } catch (e) { console.debug("[SimulationRoot] sceneEnvironment.applyEffectsPayload failed", e) }
        }
        if (postEffects && typeof postEffects.applyPayload === "function") {
            try { postEffects.applyPayload(normalized, sceneEnvironment) } catch (e) { console.debug("[SimulationRoot] postEffects.applyPayload failed", e) }
        }
        _storeLastUpdate("effects", normalized)
    }
    function applyRenderSettings(params) {
        _logBatchEvent("function_called","applyRenderSettings")
        var payload = params || {}
        if (payload.environment) applyEnvironmentUpdates(payload.environment)
        if (payload.quality) applyQualityUpdates(payload.quality)
        if (payload.effects) applyEffectsUpdates(payload.effects)
        if (payload.camera) applyCameraUpdates(payload.camera)
        var renderPayload = payload.render !== undefined ? _normaliseState(payload.render) : null
        if (_isPlainObject(renderPayload)) renderState = _deepMerge(renderState, renderPayload)
        var directOverrides = {}
        var scaleOverride = _valueFromSources([payload],["renderScale","render_scale","sceneScaleFactor","scene_scale_factor"])
        var numericScale = _coerceNumber(scaleOverride, renderScale)
        if (scaleOverride !== undefined && isFinite(numericScale) && numericScale > 0) directOverrides.renderScale = numericScale
        var frameOverride = _valueFromSources([payload],["frameRateLimit","frame_rate_limit","frameLimit","frame_limit"])
        var numericFrame = _coerceNumber(frameOverride, frameRateLimit)
        if (frameOverride !== undefined && isFinite(numericFrame) && numericFrame >= 0) directOverrides.frameRateLimit = numericFrame
        var policyOverride = _valueFromSources([payload],["renderPolicy","render_policy","renderMode","render_mode"])
        if (policyOverride !== undefined && policyOverride !== null) directOverrides.renderPolicy = _normalizeRenderPolicy(policyOverride, renderPolicyKey)
        if (!_isEmptyMap(directOverrides)) renderState = _deepMerge(renderState, directOverrides)
        _syncRenderSettingsState(); _storeLastUpdate("render", payload)
    }
    function _applyReflectionProbeEnabledOverride(candidate) {
        if (candidate === undefined || candidate === null) return
        var normalized = _coerceBool(candidate, reflectionProbeEnabledState)
        var coerced = !!normalized
        var needsUpdate = !reflectionProbeEnabledOverrideActive || reflectionProbeEnabledOverride !== coerced
        if (needsUpdate) reflectionProbeEnabledOverride = coerced
        if (!reflectionProbeEnabledOverrideActive || needsUpdate) reflectionProbeEnabledOverrideActive = true
    }
    function applyThreeDUpdates(params) {
        _logBatchEvent("function_called","applyThreeDUpdates")
        var normalized = _normaliseState(params)
        threeDState = _deepMerge(threeDState, normalized)
        var networkSource = null
        if (normalized && typeof normalized === "object") networkSource = normalized.flowNetwork !== undefined ? normalized.flowNetwork : normalized.flownetwork
        flowTelemetry = _normaliseState(networkSource)
        receiverTelemetry = _resolveReceiverTelemetry(normalized)
        var frameNode = _resolveMapEntry(normalized,"frame")
        if (_isPlainObject(frameNode) && rigAnimation && typeof rigAnimation.applyFrameMotion === "function") {
            pythonFrameActive = true
            try { rigAnimation.applyFrameMotion(frameNode,{ immediate: !pythonAnimationActive }) } catch (e) { console.debug("[SimulationRoot] rigAnimation.applyFrameMotion (threeD) failed", e) }
        }
        var leverNode = _resolveMapEntry(normalized,["leverAngles","lever_angles"])
        if (_isPlainObject(leverNode) && rigAnimation && typeof rigAnimation.applyLeverAnglesRadians === "function") {
            pythonLeverAnglesActive = true
            try { rigAnimation.applyLeverAnglesRadians(leverNode,{ immediate: !pythonAnimationActive }) } catch (e) { console.debug("[SimulationRoot] rigAnimation.applyLeverAnglesRadians (threeD) failed", e) }
        }
        var pistonNode = _resolveMapEntry(normalized,["pistonPositions","piston_positions"])
        if (_isPlainObject(pistonNode) && rigAnimation && typeof rigAnimation.applyPistonPositions === "function") {
            pythonPistonsActive = true
            try { rigAnimation.applyPistonPositions(pistonNode,{ immediate: !pythonAnimationActive }) } catch (e) { console.debug("[SimulationRoot] rigAnimation.applyPistonPositions (threeD) failed", e) }
        }
        var reflectionNode = _resolveMapEntry(normalized,["reflectionProbe","reflection_probe","reflection"])
        if (_isPlainObject(reflectionNode)) {
            if (reflectionNode.enabled !== undefined) _applyReflectionProbeEnabledOverride(reflectionNode.enabled)
            if (reflectionNode.padding !== undefined) reflectionProbePaddingM = sanitizeReflectionProbePadding(reflectionNode.padding)
            if (reflectionNode.quality !== undefined) { var qualityText=_coerceString(reflectionNode.quality, reflectionProbeQualitySetting); reflectionProbeQualitySetting=qualityText.toLowerCase() }
            if (reflectionNode.refreshMode !== undefined || reflectionNode.refresh_mode !== undefined) { var refreshCandidate = reflectionNode.refreshMode !== undefined ? reflectionNode.refreshMode : reflectionNode.refresh_mode; var refreshText=_coerceString(refreshCandidate, reflectionProbeRefreshModeSetting); reflectionProbeRefreshModeSetting=refreshText.toLowerCase() }
            if (reflectionNode.timeSlicing !== undefined || reflectionNode.time_slicing !== undefined) { var slicingCandidate = reflectionNode.timeSlicing !== undefined ? reflectionNode.timeSlicing : reflectionNode.time_slicing; var slicingText=_coerceString(slicingCandidate, reflectionProbeTimeSlicingSetting); reflectionProbeTimeSlicingSetting=slicingText.toLowerCase() }
        }
        var suspensionNode = _resolveMapEntry(normalized,["suspension"])
        if (_isPlainObject(suspensionNode)) {
            var thresholdCandidate = _valueFromSources([suspensionNode],["rod_warning_threshold_m","rodWarningThresholdM","rodWarningThreshold"])
            var thresholdNumeric = _coerceNumber(thresholdCandidate, suspensionRodWarningThresholdM)
            if (isFinite(thresholdNumeric)) { var clamped = Math.abs(thresholdNumeric); if (clamped !== suspensionRodWarningThresholdM) suspensionRodWarningThresholdM = clamped }
        }
        _storeLastUpdate("threeD", normalized)
    }
    function apply3DUpdates(params) { applyThreeDUpdates(params) }
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

    readonly property bool attachThreeD: typeof window !== "undefined" && !!window

    Component.onCompleted: {
        _refreshSceneDefaults()
        const hasBridge = sceneBridge !== null && sceneBridge !== undefined
        const hasWindow = typeof window !== "undefined" && window
        const windowIdentifier = hasWindow && typeof window.objectName === "string" && window.objectName.length > 0 ? window.objectName : "<anonymous>"
        const windowWarningAPI = hasWindow && typeof window.registerShaderWarning === "function"
        console.log("[SimulationRoot] Component completed; sceneBridge:", hasBridge ? "available" : "missing")
        console.log("[SimulationRoot] Window context:", hasWindow ? windowIdentifier : "<missing>")
        console.log("[SimulationRoot] Window.registerShaderWarning available:", windowWarningAPI)
        if (!hasWindow) console.warn("[SimulationRoot] Window context missing; shader warnings will stay local")
        _applyBridgeSnapshot(sceneBridge)
        if (sceneView) initializeRenderSettings()

        // Подхватываем начальные графические обновления из Python (env → SceneBridge)
        try {
            if (sceneBridge && sceneBridge.initialGraphicsUpdates) {
                var initBatch = sceneBridge.initialGraphicsUpdates
                if (initBatch && typeof initBatch === "object" && Object.keys(initBatch).length) {
                    try {
                        if (!applyBatchedUpdates(initBatch)) {
                            pendingPythonUpdates = initBatch
                        }
                    } catch (err) {
                        pendingPythonUpdates = initBatch
                    }
                }
            }
        } catch (e) {
            console.debug("[SimulationRoot] Failed to apply initial graphics updates", e)
        }
    }
    onSceneDefaultsChanged: _refreshSceneDefaults()
    onReflectionProbeDefaultsChanged: _refreshReflectionProbeDefaults()
    onEnvironmentDefaultsMapChanged: _refreshReflectionProbeDefaults()
    onSceneBridgeChanged: { _applyBridgeSnapshot(sceneBridge) }
    onSceneViewChanged: { if (sceneView) initializeRenderSettings() }

    function diagnosticsWindow() { return typeof window !== "undefined" && window ? window : null }
    function forwardShaderDiagnostics(eventType, effectId, message) {
        if (!Diagnostics || typeof Diagnostics.forward !== "function") return
        var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
        var normalizedMessage = message !== undefined && message !== null ? String(message) : ""
        var label = normalizedMessage.length ? normalizedId + ": " + normalizedMessage : normalizedId
        try { Diagnostics.forward(eventType, label, diagnosticsWindow(), "SimulationRoot") } catch (error) { console.warn("[SimulationRoot] Diagnostics forwarding failed", error) }
    }
    function registerShaderWarning(effectId, message) {
        var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
        var normalizedMessage = message !== undefined && message !== null ? String(message) : ""
        forwardShaderDiagnostics("shader_warning", normalizedId, normalizedMessage)
        var bridgeId = effectId !== undefined && effectId !== null ? effectId : normalizedId
        var bridgeMessage = message !== undefined && message !== null ? message : normalizedMessage
        var hostWindow = diagnosticsWindow()
        if (hostWindow && typeof hostWindow.registerShaderWarning === "function") {
            try { hostWindow.registerShaderWarning(bridgeId, bridgeMessage); return } catch (error) { console.debug("[SimulationRoot] window.registerShaderWarning failed", error) }
        }
        if (!sceneBridge) return
        try { if (typeof sceneBridge.registerShaderWarning === "function") sceneBridge.registerShaderWarning(bridgeId, bridgeMessage) } catch (error) { console.debug("[SimulationRoot] sceneBridge.registerShaderWarning.failed", error) }
    }
    function clearShaderWarning(effectId) {
        var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
        forwardShaderDiagnostics("shader_warning_cleared", normalizedId, "")
        var bridgeId = effectId !== undefined && effectId !== null ? effectId : normalizedId
        var hostWindow = diagnosticsWindow()
        if (hostWindow && typeof hostWindow.clearShaderWarning === "function") {
            try { hostWindow.clearShaderWarning(bridgeId); return } catch (error) { console.debug("[SimulationRoot] window.clearShaderWarning failed", error) }
        }
        if (!sceneBridge) return
        try { if (typeof sceneBridge.clearShaderWarning === "function") sceneBridge.clearShaderWarning(bridgeId) } catch (error) { console.debug("[SimulationRoot] sceneBridge.clearShaderWarning failed", error) }
    }
    function emitShaderStatusDump(reason) {
        if (!postEffects) return
        var snapshot = null
        try {
            if (typeof postEffects.dumpShaderStatus === "function") snapshot = postEffects.dumpShaderStatus(reason)
            else if (typeof postEffects.shaderStatusSnapshot === "function") snapshot = postEffects.shaderStatusSnapshot(reason)
        } catch (error) { console.debug("[SimulationRoot] dumpShaderStatus failed", error); snapshot = null }
        if (!snapshot || typeof snapshot !== "object") return
        if (reason && (!snapshot.effectsBypassReason || !snapshot.effectsBypassReason.length)) snapshot.effectsBypassReason = String(reason)
        try { shaderStatusDumpRequested(snapshot) } catch (error) { console.debug("[SimulationRoot] shaderStatusDumpRequested emit failed", error) }
    }
    function cloneEffectList(value) {
        if (!value) return []
        if (Array.isArray(value)) return value.slice()
        var copy = []; var length = 0
        try { length = value.length } catch (error) { length = 0 }
        for (var i=0;i<length;++i) { try { copy.push(value[i]) } catch (error) {} }
        return copy
    }
    function _normaliseState(value) { if (!value || typeof value !== "object") return ({}); var copy={}; for (var key in value) if (Object.prototype.hasOwnProperty.call(value,key)) copy[key]=value[key]; return copy }
    function _isEmptyMap(value) { if (!value || typeof value !== "object") return true; for (var key in value) if (Object.prototype.hasOwnProperty.call(value,key)) return false; return true }
    function _resetBridgeState() {
        geometryState = ({}); simulationState = ({}); threeDState = ({}); renderState = ({}); flowTelemetry = ({}); receiverTelemetry = ({})
        geometryStateReceived = false; simulationStateReceived = false; sceneBridgeDispatchCount = 0; _syncRenderSettingsState()
    }
    function _applyBridgeSnapshot(target) {
        if (!target) { _resetBridgeState(); return }
        try { geometryState = _normaliseState(target.geometry) } catch (error) { geometryState = ({}) }
        try { simulationState = _normaliseState(target.simulation) } catch (error) { simulationState = ({}) }
        try { threeDState = _normaliseState(target.threeD) } catch (error) { threeDState = ({}) }
        try { renderState = _normaliseState(target.render) } catch (error) { renderState = ({}) }
        var snapshotFlow = ({})
        try { if (threeDState && typeof threeDState === "object") snapshotFlow = _normaliseState(threeDState.flowNetwork || threeDState.flownetwork) } catch (error) { snapshotFlow = ({}) }
        flowTelemetry = snapshotFlow
        receiverTelemetry = _resolveReceiverTelemetry(threeDState)
        geometryStateReceived = !_isEmptyMap(geometryState)
        simulationStateReceived = !_isEmptyMap(simulationState)
        _syncRenderSettingsState()
    }
    function _resolveReceiverTelemetry(source) {
        var state = _normaliseState(source)
        if (_isEmptyMap(state)) return ({})
        var direct = null
        if (state.receiver !== undefined) direct = _normaliseState(state.receiver)
        if (!_isEmptyMap(direct)) return direct
        var network = null
        if (state.flowNetwork !== undefined) network = _normaliseState(state.flowNetwork)
        else if (state.flownetwork !== undefined) network = _normaliseState(state.flownetwork)
        if (network && !_isEmptyMap(network.receiver)) return _normaliseState(network.receiver)
        return ({})
    }
    function applyPostProcessingBypass(active, reason) {
        var normalizedReason = reason !== undefined && reason !== null ? String(reason) : ""
        var previousActive = postProcessingBypassed
        var previousReason = postProcessingBypassReason
        postProcessingBypassed = !!active
        postProcessingBypassReason = postProcessingBypassed ? normalizedReason : ""
        updateSimpleFallbackState(postProcessingBypassed, postProcessingBypassReason)
        if (postProcessingBypassed && !previousActive) emitShaderStatusDump(normalizedReason)
        else if (postProcessingBypassed && normalizedReason !== previousReason) emitShaderStatusDump(normalizedReason)
        if (!sceneView) {
            console.warn("[SimulationRoot] Unable to toggle post-processing bypass; sceneView is not set", active, normalizedReason)
            return
        }
        if (postProcessingBypassed) {
            console.warn("[SimulationRoot] Post-processing bypass activated", normalizedReason)
            try { var currentEffects = sceneView.effects; postProcessingEffectBackup = cloneEffectList(currentEffects) } catch (error) { postProcessingEffectBackup = []; console.debug("[SimulationRoot] Failed to cache View3D effects before bypass", error) }
            try { sceneView.effects = [] } catch (error) { console.warn("[SimulationRoot] Failed to clear View3D effects during bypass", error) }
        } else {
            if (previousActive) console.log("[SimulationRoot] Post-processing bypass cleared")
            try {
                var restoreEffects = []
                if (postProcessingEffectBackup && postProcessingEffectBackup.length) restoreEffects = postProcessingEffectBackup
                else if (postEffects && postEffects.effectList) restoreEffects = postEffects.effectList
                sceneView.effects = restoreEffects
                postProcessingEffectBackup = []
            } catch (error) { console.warn("[SimulationRoot] Failed to restore View3D effects after bypass", error) }
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
        function onEffectCompilationRecovered(effectId) { root.clearShaderWarning(effectId) }
        function onEffectsBypassChanged(active) {
            var reason = ""
            try { reason = target && typeof target.effectsBypassReason === "string" ? target.effectsBypassReason : "" } catch (error) {}
            root.applyPostProcessingBypass(active, reason)
        }
        function onEffectsBypassReasonChanged(reason) {
            if (!target || !target.effectsBypass) return
            root.applyPostProcessingBypass(true, reason)
        }
        function onSimplifiedRenderingRequested(reason) { root.updateSimpleFallbackState(true, reason) }
        function onSimplifiedRenderingRecovered() { root.updateSimpleFallbackState(false, "") }
    }

    Connections {
        target: root.sceneBridge
        enabled: !!target
        function onGeometryChanged(payload) { root.applyGeometryUpdates(payload) }
        function onSimulationChanged(payload) { root.applySimulationUpdates(payload) }
        function onUpdatesDispatched(payload) { if (payload && typeof payload === "object") root.sceneBridgeDispatchCount += 1 }
    }

    // --- Рендер настройки и состояния (добавлены для целостности) ---
    property real renderScale: 1.0
    property int frameRateLimit: 0
    property string renderPolicyKey: "always"
    property var renderState: ({})
    property var qualityState: ({})
    property var sceneRenderDefaults: ({})
    property var sceneQualityDefaults: ({})
    property var environmentState: ({})
    property var effectsState: ({})
    property var cameraStateSnapshot: ({})
    property bool reflectionProbeEnabledState: true
    property bool reflectionProbeEnabledOverrideActive: false
    property bool reflectionProbeEnabledOverride: true
    property real reflectionProbePaddingM: 0.0
    property string reflectionProbeQualitySetting: "medium"
    property string reflectionProbeRefreshModeSetting: "static"
    property string reflectionProbeTimeSlicingSetting: "allfaces"
    property real suspensionRodWarningThresholdM: 0.0
    property var cameraController: null
    property var rigAnimation: null
    property bool pythonAnimationActive: false
    property bool pythonFrameActive: false
    property bool pythonLeverAnglesActive: false
    property bool pythonPistonsActive: false
    property bool pythonFrameActive: false

    // Восстановлен Binding эффектов
    Binding {
        id: viewEffectsBinding
        target: root.sceneView
        property: "effects"
        value: root.postProcessingBypassed ? [] : (root.postEffects && root.postEffects.effectList ? root.postEffects.effectList : [])
        when: !!root.sceneView
    }

    function initializeRenderSettings() {
        var sources = [renderState||({}), qualityState||({}), sceneRenderDefaults||({}), sceneQualityDefaults||({})]
        function _firstDefined(keys){ for (var i=0;i<sources.length;++i){ var s=sources[i]; if (!s||typeof s!=='object') continue; for (var k=0;k<keys.length;++k){ var name=keys[k]; if (s[name]!==undefined) return s[name] } } return undefined }
        var scaleCandidate = _firstDefined(["renderScale","render_scale","sceneScaleFactor","scene_scale_factor"])
        var frameCandidate = _firstDefined(["frameRateLimit","frame_rate_limit","frameLimit","frame_limit"])
        var policyCandidate = _firstDefined(["renderPolicy","render_policy","renderMode","render_mode"])
        function _coerceNumber(v,f){ var n=Number(v); return isFinite(n)?n:f }
        function _normalizePolicy(v){ if(v===undefined||v===null) return renderPolicyKey; var t=String(v).toLowerCase().trim(); if(t==="on_demand"||t==="on-demand") t="ondemand"; if(["always","ondemand","automatic","manual"].indexOf(t)!==-1) return t; console.warn("[SimulationRoot] Invalid renderPolicy", v, "-> using", renderPolicyKey); return renderPolicyKey }
        if (scaleCandidate!==undefined) { var s=_coerceNumber(scaleCandidate, renderScale); if (!isFinite(s)||s<=0){ console.warn("[SimulationRoot] Invalid renderScale", scaleCandidate); } else renderScale=s }
        if (frameCandidate!==undefined) { var f=_coerceNumber(frameCandidate, frameRateLimit); if(!isFinite(f)||f<0){ console.warn("[SimulationRoot] Invalid frameRateLimit", frameCandidate) } else frameRateLimit=f }
        if (policyCandidate!==undefined) { renderPolicyKey=_normalizePolicy(policyCandidate) }
    }

}
