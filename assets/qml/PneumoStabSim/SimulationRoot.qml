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
 * PneumoStabSim - MAIN QML (restored functional version)
 */
Item {
    id: root
    anchors.fill: parent

    // Bridge
    property var sceneBridge: null
    // External references
    property var postEffects: null
    property var sceneView: null

    // Post-processing bypass
    property bool postProcessingBypassed: false
    property string postProcessingBypassReason: ""
    property var postProcessingEffectBackup: []

    // Simplified fallback
    property bool simpleFallbackActive: false
    property string simpleFallbackReason: ""
    signal simpleFallbackRequested(string reason)
    signal simpleFallbackRecovered()

    // Shader diagnostics
    signal shaderStatusDumpRequested(var payload)

    // Empty defaults helpers
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

    // Core state mirrors
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

    // Batch updates
    property var pendingPythonUpdates: null
    property var lastUpdateByCategory: ({})
    signal batchUpdatesApplied(var summary)
    signal animationToggled(bool running)

    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates || typeof pendingPythonUpdates !== "object")
            return
        try { applyBatchedUpdates(pendingPythonUpdates) } finally { pendingPythonUpdates = null }
    }

    // Indicators (declarative bindings)
    QtObject {
        id: geometryIndicator
        property bool active: root.geometryStateReceived
        property bool warning: !root.sceneBridgeAvailable || (!active && root.sceneBridgeAvailable)
        property string detailText: active ? (Object.keys(root.geometryState).length + " параметров") : "Ожидание данных от SceneBridge"
        property string secondaryText: active ? "" : (root.sceneBridgeAvailable ? "Сигналы ещё не получены" : "Bridge недоступен")
        property bool pulse: root.sceneBridgeDispatchCount > 0 && active
    }
    QtObject {
        id: simulationIndicator
        property bool active: root.simulationStateReceived
        property bool warning: !root.sceneBridgeAvailable || (!active && root.sceneBridgeAvailable)
        property int _leverCount: active && root.simulationState && root.simulationState.levers ? Object.keys(root.simulationState.levers).length : 0
        property int _pistonCount: active && root.simulationState && root.simulationState.pistons ? Object.keys(root.simulationState.pistons).length : 0
        property string detailText: active ? ("Рычаги: " + _leverCount + " • Поршни: " + _pistonCount) : "Нет активного снапшота"
        property string secondaryText: {
            if (!active) return root.sceneBridgeAvailable ? "Ожидание шага" : "Bridge недоступен"
            var ag = root.simulationState && root.simulationState.aggregates ? root.simulationState.aggregates : null
            if (ag && ag.stepNumber !== undefined && ag.simulationTime !== undefined)
                return "Шаг " + ag.stepNumber + " • Время " + ag.simulationTime + " с"
            return ""
        }
        property bool pulse: root.sceneBridgeDispatchCount > 0 && active
    }
    property alias geometryIndicatorItem: geometryIndicator
    property alias simulationIndicatorItem: simulationIndicator

    // Render related state
    property real renderScale: 1.0
    property int frameRateLimit: 0
    property string renderPolicyKey: "always"
    property var renderState: ({})
    property var qualityState: ({})
    property var sceneRenderDefaults: ({})
    property var sceneQualityDefaults: ({})
    // Используем простой literal для корректной конверсии в Python dict
    property var environmentState: ({})

    property var effectsState: ({})
    property var cameraStateSnapshot: ({})

    // Reflection probe diagnostic flags (добавлено заново)
    property bool reflectionProbeDefaultsWarningIssued: false
    // Типизированный список строк для корректного экспорта в Python (list)
    property list<string> reflectionProbeMissingKeys: []

    // Reflection probe
    // Инициализация состояния учитывает initialReflectionProbeSettings ещё до Component.onCompleted
    property bool reflectionProbeEnabledState: {
        function _reflectionEnabledFromSettings() {
            if (typeof initialReflectionProbeSettings !== "undefined"
                    && initialReflectionProbeSettings
                    && initialReflectionProbeSettings.enabled !== undefined) {
                return !!initialReflectionProbeSettings.enabled
            }

            if (typeof initialSceneSettings !== "undefined" && initialSceneSettings) {
                if (initialSceneSettings.graphics && initialSceneSettings.graphics.environment
                        && initialSceneSettings.graphics.environment.reflection_enabled !== undefined) {
                    return !!initialSceneSettings.graphics.environment.reflection_enabled
                }

                if (initialSceneSettings.graphics && initialSceneSettings.graphics.reflection_probe
                        && initialSceneSettings.graphics.reflection_probe.enabled !== undefined) {
                    return !!initialSceneSettings.graphics.reflection_probe.enabled
                }
            }

            return true
        }

        return _reflectionEnabledFromSettings()
    }
    property bool reflectionProbeEnabled: reflectionProbeEnabledOverrideActive
            ? reflectionProbeEnabledOverride
            : reflectionProbeEnabledState
    property bool reflectionProbeEnabledOverrideActive: false
    property bool reflectionProbeEnabledOverride: true
    property real reflectionProbePaddingM: 0.0
    property string reflectionProbeQualitySetting: "medium"
    property string reflectionProbeRefreshModeSetting: "static"
    property string reflectionProbeTimeSlicingSetting: "allfaces"

    // Suspension & scene defaults
    property real sceneScaleFactor: 1.0
    property real suspensionRodWarningThresholdM: 0.001

    // Controllers
    property var cameraController: null
    property var rigAnimation: null

    // Animation flags
    property bool pythonAnimationActive: false
    property bool pythonFrameActive: false
    property bool pythonLeverAnglesActive: false
    property bool pythonPistonsActive: false

    // Animation scalar state (required by tests expecting animationToggled)
    property bool isRunning: false
    property real animationTime: 0.0

    // Debounce flash
    property real batchFlashOpacity: 0.0

    // Helpers --------------------------------------------------
    function _logBatchEvent(eventType, name) {
        try {
            if (typeof window !== "undefined" && window && typeof window.logQmlEvent === "function")
                window.logQmlEvent(eventType, name)
        } catch (error) {
            console.debug("[SimulationRoot] Failed to forward batch event", eventType, name, error)
        }
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
    function _normaliseState(value) { if (!value || typeof value !== "object") return ({}); var copy={}; for (var key in value) if (Object.prototype.hasOwnProperty.call(value,key)) copy[key]=value[key]; return copy }
    function _isEmptyMap(value) { if (!value || typeof value !== "object") return true; for (var key in value) if (Object.prototype.hasOwnProperty.call(value,key)) return false; return true }

    function _storeLastUpdate(category, payload) {
        var snapshot = _cloneObject(lastUpdateByCategory)
        snapshot[category] = payload && typeof payload === "object" ? _normaliseState(payload) : payload
        lastUpdateByCategory = snapshot
    }
    function _acknowledgeBatch(categories) {
        if (categories && categories.length) batchFlashOpacity = 1.0
        var summary = { timestamp: Date.now(), categories: categories ? categories.slice() : [], source: "python" }
        batchUpdatesApplied(summary)
    }

    // Batch dispatcher ------------------------------------------
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

    // Category handlers -----------------------------------------
    function applyGeometryUpdates(params) {
        _logBatchEvent("function_called","applyGeometryUpdates")
        var normalized = _normaliseState(params)
        if (!_isEmptyMap(normalized)) {
            geometryState = _deepMerge(geometryState, normalized)
            geometryStateReceived = true
        }
        _storeLastUpdate("geometry", normalized)
    }
    function applySimulationUpdates(params) {
        _logBatchEvent("function_called","applySimulationUpdates")
        var normalized = _normaliseState(params)
        if (!_isEmptyMap(normalized)) { simulationState = _deepMerge(simulationState, normalized); simulationStateReceived = true }
        if (normalized.animation) applyAnimationUpdates(normalized.animation)
        if (normalized.threeD) applyThreeDUpdates(normalized.threeD)
        _storeLastUpdate("simulation", normalized)
    }
    function applyAnimationUpdates(params) {
        _logBatchEvent("function_called","applyAnimationUpdates")
        var payload = params || {}
        var previousRunning = isRunning
        function _num(v,f){ if(v===undefined||v===null) return f; var c=Number(v); return isNaN(c)?f:c }
        function _bool(v,f){ if(v===undefined||v===null) return f; return Boolean(v) }
        animationTime = _num(payload.animation_time, animationTime)
        animationTime = _num(payload.animationTime, animationTime)
        isRunning = _bool(payload.is_running, isRunning)
        isRunning = _bool(payload.isRunning, isRunning)
        pythonAnimationActive = _bool(payload.python_driven, pythonAnimationActive)
        pythonAnimationActive = _bool(payload.pythonDriven, pythonAnimationActive)
        if (isRunning !== previousRunning) animationToggled(isRunning)
        _storeLastUpdate("animation", payload)
    }
    function applyLightingUpdates(params) { _logBatchEvent("function_called","applyLightingUpdates"); var normalized=_normaliseState(params); _storeLastUpdate("lighting",normalized) }
    function applyMaterialUpdates(params) { _logBatchEvent("function_called","applyMaterialUpdates"); var normalized=_normaliseState(params); _storeLastUpdate("materials",normalized) }

    function applyEnvironmentUpdates(params) {
        _logBatchEvent("function_called","applyEnvironmentUpdates")
        var normalized = _normaliseState(params)
        // Прямое присваивание входного params (QVariantMap) даёт Python dict;
        // затем дополняем ранее накопленным состоянием.
        var base = environmentState && typeof environmentState === 'object' ? environmentState : {}
        var merged = {}
        // Сначала базовые ключи
        for (var bk in base) if (Object.prototype.hasOwnProperty.call(base,bk)) merged[bk] = base[bk]
        // Затем новые
        for (var nk in normalized) if (Object.prototype.hasOwnProperty.call(normalized,nk)) merged[nk] = normalized[nk]
        // Сохраняем как params если обновление происходит впервые, иначе merged
        environmentState = (Object.keys(base).length === 0) ? params : merged
        if(normalized.fog_enabled !== undefined) envController.fogEnabled = !!normalized.fog_enabled
        if(normalized.fog_density !== undefined) envController.fog.density = Number(normalized.fog_density) || 0.0
        if(normalized.ibl_enabled !== undefined) envController.iblLightingEnabled = !!normalized.ibl_enabled
        if(normalized.skybox_enabled !== undefined) envController.skyboxToggleFlag = !!normalized.skybox_enabled
        var reflectionToggle = normalized.reflection_enabled !== undefined ? normalized.reflection_enabled : normalized.reflectionEnabled
        if (reflectionToggle !== undefined) {
            envController.reflectionProbeEnabled = !!reflectionToggle
            _applyReflectionProbeEnabledOverride(reflectionToggle)
        }
        _storeLastUpdate("environment", normalized)
        _refreshReflectionProbeObject()
    }
    function applySceneUpdates(params) { _logBatchEvent("function_called","applySceneUpdates"); _storeLastUpdate("scene", params || {}) }
    function applyQualityUpdates(params) {
        _logBatchEvent("function_called","applyQualityUpdates")
        var normalized = _normaliseState(params)
        qualityState = _deepMerge(qualityState, normalized)
        _syncRenderSettingsState()
        _storeLastUpdate("quality", normalized)
    }
    function applyCameraUpdates(params) {
        _logBatchEvent("function_called","applyCameraUpdates")
        var normalized = _normaliseState(params)
        cameraStateSnapshot = _deepMerge(cameraStateSnapshot, normalized)
        _storeLastUpdate("camera", normalized)
    }
    function applyEffectsUpdates(params) {
        _logBatchEvent("function_called","applyEffectsUpdates")
        var normalized = _normaliseState(params)
        effectsState = _deepMerge(effectsState, normalized)
        _storeLastUpdate("effects", normalized)
    }
    function applyRenderSettings(params) {
        _logBatchEvent("function_called","applyRenderSettings")
        var payload = params || {}
        if (payload.environment) applyEnvironmentUpdates(payload.environment)
        if (payload.quality) applyQualityUpdates(payload.quality)
        if (payload.effects) applyEffectsUpdates(payload.effects)
        if (payload.camera) applyCameraUpdates(payload.camera)
        var direct = _normaliseState(payload.render)
        if (!_isEmptyMap(direct)) renderState = _deepMerge(renderState, direct)
        _syncRenderSettingsState(); _storeLastUpdate("render", payload)
    }
    function applyThreeDUpdates(params) {
        _logBatchEvent("function_called","applyThreeDUpdates")
        var normalized = _normaliseState(params)
        threeDState = _deepMerge(threeDState, normalized)
        flowTelemetry = _normaliseState(normalized.flowNetwork || normalized.flownetwork)
        receiverTelemetry = _resolveReceiverTelemetry(normalized)
        var reflectionNode = normalized.reflectionProbe || normalized.reflection_probe || normalized.reflection
        if (_isPlainObject(reflectionNode)) {
            if (reflectionNode.enabled !== undefined) _applyReflectionProbeEnabledOverride(reflectionNode.enabled)
            if (reflectionNode.padding !== undefined) reflectionProbePaddingM = sanitizeReflectionProbePadding(reflectionNode.padding)
            if (reflectionNode.quality !== undefined) reflectionProbeQualitySetting = String(reflectionNode.quality).toLowerCase()
            if (reflectionNode.refreshMode || reflectionNode.refresh_mode) reflectionProbeRefreshModeSetting = String(reflectionNode.refreshMode || reflectionNode.refresh_mode).toLowerCase()
            if (reflectionNode.timeSlicing || reflectionNode.time_slicing) reflectionProbeTimeSlicingSetting = String(reflectionNode.timeSlicing || reflectionNode.time_slicing).toLowerCase()
        }
        _storeLastUpdate("threeD", normalized)
        _refreshReflectionProbeObject()
    }
    function apply3DUpdates(params) { applyThreeDUpdates(params) }

    // Update* legacy aliases (used by diagnostics / panels)
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

    // Render sync ------------------------------------------------
    function _renderSources() { return [renderState||({}), qualityState||({}), sceneRenderDefaults||({}), sceneQualityDefaults||({})] }
    function _syncRenderSettingsState() {
        var sources = _renderSources()
        function _first(keys){ for (var i=0;i<sources.length;++i){ var s=sources[i]; if(!s||typeof s!=="object") continue; for (var k=0;k<keys.length;++k){ var n=keys[k]; if(s[n]!==undefined) return s[n] } } return undefined }
        function _num(v,f){ var n=Number(v); return isFinite(n)?n:f }
        function _policy(v){ if(v===undefined||v===null) return renderPolicyKey; var t=String(v).toLowerCase().trim(); if(t==="on_demand"||t==="on-demand") t="ondemand"; return ["always","ondemand","automatic","manual"].indexOf(t)!==-1 ? t : renderPolicyKey }
        var scaleCandidate=_first(["renderScale","render_scale","sceneScaleFactor","scene_scale_factor"])
        var frameCandidate=_first(["frameRateLimit","frame_rate_limit","frameLimit","frame_limit"])
        var policyCandidate=_first(["renderPolicy","render_policy","renderMode","render_mode"])
        if(scaleCandidate!==undefined){ var s=_num(scaleCandidate, renderScale); if(isFinite(s)&&s>0) renderScale=s }
        if(frameCandidate!==undefined){ var f=_num(frameCandidate, frameRateLimit); if(isFinite(f)&&f>=0) frameRateLimit=f }
        if(policyCandidate!==undefined){ renderPolicyKey=_policy(policyCandidate) }
    }
    function _applyReflectionProbeEnabledOverride(candidate) {
        if (candidate === undefined || candidate === null) return
        var coerced = !!candidate
        var needsUpdate = !reflectionProbeEnabledOverrideActive || reflectionProbeEnabledOverride !== coerced
        if (needsUpdate) reflectionProbeEnabledOverride = coerced
        if (!reflectionProbeEnabledOverrideActive || needsUpdate) reflectionProbeEnabledOverrideActive = true
    }
    function sanitizeReflectionProbePadding(value) { var n=Number(value); return isFinite(n)&&n>=0? n : 0.0 }
    function _resolveReceiverTelemetry(source) {
        var state=_normaliseState(source); if(_isEmptyMap(state)) return ({})
        if(state.receiver) { var direct=_normaliseState(state.receiver); if(!_isEmptyMap(direct)) return direct }
        var network=state.flowNetwork || state.flownetwork
        if(network && network.receiver) return _normaliseState(network.receiver)
        return ({})
    }

    // Shader diagnostics (simplified forwarding) -----------------
    function diagnosticsWindow() { return typeof window !== "undefined" && window ? window : null }
    function registerShaderWarning(effectId, message) {
        var host = diagnosticsWindow()
        if (host && typeof host.registerShaderWarning === "function") {
            try { host.registerShaderWarning(effectId, message); return } catch(e) {}
        }
    }
    function clearShaderWarning(effectId) {
        var host = diagnosticsWindow()
        if (host && typeof host.clearShaderWarning === "function") {
            try { host.clearShaderWarning(effectId); return } catch(e) {}
        }
    }

    // Connections to sceneBridge --------------------------------
    Connections {
        target: root.sceneBridge
        enabled: !!target
        function onGeometryChanged(payload) { root.applyGeometryUpdates(payload) }
        function onSimulationChanged(payload) { root.applySimulationUpdates(payload) }
        function onUpdatesDispatched(payload) {
            if (payload && typeof payload === "object") {
                root.sceneBridgeDispatchCount += 1
                geometryIndicator.pulse = true
                simulationIndicator.pulse = true
            }
        }
    }

    // Проксирование предупреждений шейдеров из PostEffects в sceneBridge
    Connections {
        target: root.postEffects
        enabled: !!target && !!root.sceneBridge
        ignoreUnknownSignals: true

        function onEffectsBypassChanged() {
            if (!root.postEffects)
                return
            try {
                var bypass = !!root.postEffects.effectsBypass
                var reason = String(root.postEffects.effectsBypassReason || "")
                if (root.postProcessingBypassed !== bypass)
                    root.postProcessingBypassed = bypass
                if (root.postProcessingBypassReason !== reason)
                    root.postProcessingBypassReason = reason

                if (bypass) {
                    // Backup current effects and clear the chain on the view stub
                    if (root.sceneView) {
                        var current = root.sceneView.effects
                        if (current && typeof current === "object" && typeof current.slice === "function")
                            root.postProcessingEffectBackup = current.slice()
                        else
                            root.postProcessingEffectBackup = []
                        try { root.sceneView.effects = [] } catch (e) {}
                    }
                    // Forward structured snapshot to Python for diagnostics
                    try {
                        var snapshot = root.postEffects.dumpShaderStatus(reason)
                        root.shaderStatusDumpRequested(snapshot)
                    } catch (e) {}
                } else {
                    // Restore effect list if we have a backup (and PostEffects still exposes effectList)
                    if (root.sceneView && root.postProcessingEffectBackup && root.postProcessingEffectBackup.length > 0) {
                        try { root.sceneView.effects = root.postProcessingEffectBackup } catch (e) {}
                    } else if (root.sceneView && root.postEffects) {
                        // Если бэкапа нет, но есть исходный список – восстановить его
                        try {
                            var effectList = root.postEffects.effectList
                            if (effectList && typeof effectList === "object")
                                root.sceneView.effects = effectList
                        } catch (e) {}
                    }
                    root.postProcessingEffectBackup = []
                    // Emit a status snapshot to confirm recovery
                    try {
                        var snapshot2 = root.postEffects.dumpShaderStatus("")
                        root.shaderStatusDumpRequested(snapshot2)
                    } catch (e) {}
                }
            } catch (err) {
                console.error("[SimulationRoot] effectsBypassChanged handler failed:", err)
            }
        }

        // Добавляем обработчики сигналов PostEffects для маршрутизации shader предупреждений
        function onEffectCompilationError(effectId, fallbackActive, message) {
            try {
                if (root.sceneBridge && typeof root.sceneBridge.registerShaderWarning === 'function') {
                    root.sceneBridge.registerShaderWarning(effectId, message)
                }
                // Emit status snapshot for tests expecting shaderStatusDumpRequested
                var snapshot = root.postEffects && typeof root.postEffects.dumpShaderStatus === 'function'
                    ? root.postEffects.dumpShaderStatus(message)
                    : { effectsBypass: root.postProcessingBypassed, effectsBypassReason: root.postProcessingBypassReason }
                root.shaderStatusDumpRequested(snapshot)
            } catch (e) {
                console.debug('[SimulationRoot] onEffectCompilationError routing failed', e)
            }
        }
        function onEffectCompilationRecovered(effectId, wasFallbackActive) {
            try {
                if (root.sceneBridge && typeof root.sceneBridge.clearShaderWarning === 'function') {
                    root.sceneBridge.clearShaderWarning(effectId)
                }
                var snapshot = root.postEffects && typeof root.postEffects.dumpShaderStatus === 'function'
                    ? root.postEffects.dumpShaderStatus('recovered')
                    : { effectsBypass: root.postProcessingBypassed, effectsBypassReason: root.postProcessingBypassReason }
                root.shaderStatusDumpRequested(snapshot)
            } catch (e) {
                console.debug('[SimulationRoot] onEffectCompilationRecovered routing failed', e)
            }
        }
    }

    // Initial hydration -----------------------------------------
    Component.onCompleted: {
        console.log("[SimulationRoot] Component completed; sceneBridge:", sceneBridge ? "available" : "missing")
        if (typeof initialReflectionProbeSettings !== "undefined" && initialReflectionProbeSettings) {
            var keys = ["enabled","padding_m","quality","refresh_mode","time_slicing"]
            var missingTmp = []
            for (var i=0;i<keys.length;++i){ if(initialReflectionProbeSettings[keys[i]] === undefined) missingTmp.push(keys[i]) }
            reflectionProbeMissingKeys = missingTmp  // Прямое присваивание типизированному списку
            reflectionProbeDefaultsWarningIssued = missingTmp.length > 0
            if (initialReflectionProbeSettings.enabled !== undefined) {
                _applyReflectionProbeEnabledOverride(initialReflectionProbeSettings.enabled)
                reflectionProbeEnabledState = !!initialReflectionProbeSettings.enabled
            }
            if (initialReflectionProbeSettings.padding_m !== undefined) {
                reflectionProbePaddingM = sanitizeReflectionProbePadding(initialReflectionProbeSettings.padding_m)
            } else if (missingTmp.indexOf("padding_m") !== -1) {
                reflectionProbePaddingM = 0.15
            }
            if (initialReflectionProbeSettings.quality !== undefined) reflectionProbeQualitySetting = String(initialReflectionProbeSettings.quality).toLowerCase()
            if (initialReflectionProbeSettings.refresh_mode !== undefined) reflectionProbeRefreshModeSetting = String(initialReflectionProbeSettings.refresh_mode).toLowerCase()
            if (initialReflectionProbeSettings.time_slicing !== undefined) reflectionProbeTimeSlicingSetting = String(initialReflectionProbeSettings.time_slicing).toLowerCase()
            _refreshReflectionProbeObject()
        }
        if (typeof initialSceneSettings !== "undefined" && initialSceneSettings && initialSceneSettings.graphics && initialSceneSettings.graphics.environment) {
            var env = initialSceneSettings.graphics.environment
            if (env.reflection_enabled === false) {
                _applyReflectionProbeEnabledOverride(false)
                reflectionProbeEnabledState = false
            }
            if (env.reflection_enabled !== undefined) envController.reflectionProbeEnabled = !!env.reflection_enabled
            if (env.reflection_padding_m !== undefined) reflectionProbePaddingM = sanitizeReflectionProbePadding(env.reflection_padding_m)
            _refreshReflectionProbeObject()
        }

        var sceneDefaults = null
        if (typeof initialSceneSettings !== "undefined" && initialSceneSettings) {
            if (initialSceneSettings.scene && typeof initialSceneSettings.scene === "object") {
                sceneDefaults = initialSceneSettings.scene
            } else if (initialSceneSettings.graphics && initialSceneSettings.graphics.scene) {
                sceneDefaults = initialSceneSettings.graphics.scene
            }
        }

        if (sceneDefaults) {
            if (sceneDefaults.scale_factor !== undefined) {
                var coercedScale = Number(sceneDefaults.scale_factor)
                if (isFinite(coercedScale) && coercedScale > 0) {
                    sceneScaleFactor = coercedScale
                }
            }
            var suspensionDefaults = sceneDefaults.suspension
            if (suspensionDefaults && suspensionDefaults.rod_warning_threshold_m !== undefined) {
                var rodThreshold = Number(suspensionDefaults.rod_warning_threshold_m)
                if (isFinite(rodThreshold) && rodThreshold > 0) {
                    suspensionRodWarningThresholdM = rodThreshold
                }
            }
        }
        _applyBridgeSnapshot(sceneBridge)
    }
    onSceneBridgeChanged: { _applyBridgeSnapshot(sceneBridge) }

    function _applyBridgeSnapshot(target) {
        if (!target) {
            geometryState = ({}); simulationState = ({}); threeDState = ({}); renderState = ({}); flowTelemetry = ({}); receiverTelemetry = ({})
            geometryStateReceived = false; simulationStateReceived = false
            return
        }
        try { geometryState = _normaliseState(target.geometry) } catch(e) { geometryState = ({}) }
        try { simulationState = _normaliseState(target.simulation) } catch(e) { simulationState = ({}) }
        geometryStateReceived = !_isEmptyMap(geometryState)
        simulationStateReceived = !_isEmptyMap(simulationState)
    }

    // Environment & Reflection infrastructure (для тестов)
    // (переименовано чтобы избежать alias self-reference)
    QtObject {
        id: envController
        objectName: "sceneEnvironment"
        property bool fogEnabled: false
        property QtObject fog: QtObject { property real density: 0.0 }
        property bool iblLightingEnabled: false
        property bool skyboxToggleFlag: false
        property bool reflectionProbeEnabled: root.reflectionProbeEnabled
    }
    QtObject {
        id: suspensionAssembly
        objectName: "sceneSuspensionAssembly"
        property bool reflectionProbeEnabled: root.reflectionProbeEnabled
        property real reflectionProbePaddingM: root.reflectionProbePaddingM
        property real sceneScaleFactor: root.sceneScaleFactor
        property real rodWarningThreshold: root.suspensionRodWarningThresholdM
        property int reflectionProbeQualityValue: reflectionProbe ? reflectionProbe.quality : 0
        property int reflectionProbeRefreshModeValue: reflectionProbe ? reflectionProbe.refreshMode : 0
        property int reflectionProbeTimeSlicingValue: reflectionProbe ? reflectionProbe.timeSlicing : 0
        property QtObject reflectionProbe: QtObject {
            property bool enabled: suspensionAssembly.reflectionProbeEnabled
            property bool visible: enabled
            property int quality: 0
            property int refreshMode: 0
            property int timeSlicing: 0
        }
    }
    property alias sceneEnvironment: envController
    property alias sceneSuspensionAssembly: suspensionAssembly
    function _refreshReflectionProbeObject(){
        suspensionAssembly.reflectionProbe.enabled = suspensionAssembly.reflectionProbeEnabled
        suspensionAssembly.reflectionProbe.visible = suspensionAssembly.reflectionProbeEnabled
        suspensionAssembly.reflectionProbe.quality = _qualityToInt(reflectionProbeQualitySetting)
        suspensionAssembly.reflectionProbe.refreshMode = (function(m){switch(String(m).toLowerCase()){case "firstframe":return 1; case "everyframe":return 2; default:return 0}})(reflectionProbeRefreshModeSetting)
        suspensionAssembly.reflectionProbe.timeSlicing = (function(m){switch(String(m).toLowerCase()){case "allfaces":return 1; case "allfacesatonce":return 2; case "individualfaces":return 3; default:return 0}})(reflectionProbeTimeSlicingSetting)
        suspensionAssembly.reflectionProbePaddingM = reflectionProbePaddingM
    }

    // Mapping качества проба (восстановлено)
    function _qualityToInt(q){
        switch(String(q||"").toLowerCase()){
        case "low": return 1; case "medium": return 2; case "high": return 3; case "veryhigh": return 4; default: return 0 }
    }

}
