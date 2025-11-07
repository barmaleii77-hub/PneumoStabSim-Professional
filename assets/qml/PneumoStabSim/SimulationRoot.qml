import QtQml 6.10
import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import QtQuick.Timeline 1.0
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
            geometryState = _mergeObjects(geometryState, normalized)
            geometryStateReceived = true
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

        _storeLastUpdate("animation", payload)
        if (isRunning !== previousRunning)
            animationToggled(isRunning)
    }

    function applyLightingUpdates(params) {
        _logBatchEvent("function_called", "applyLightingUpdates")
        _storeLastUpdate("lighting", params || {})
    }

    function applyMaterialUpdates(params) {
        _logBatchEvent("function_called", "applyMaterialUpdates")
        _storeLastUpdate("materials", params || {})
    }

    function applyEnvironmentUpdates(params) {
        _logBatchEvent("function_called", "applyEnvironmentUpdates")
        _storeLastUpdate("environment", params || {})
    }

    function applySceneUpdates(params) {
        _logBatchEvent("function_called", "applySceneUpdates")
        _storeLastUpdate("scene", params || {})
    }

    function applyQualityUpdates(params) {
        _logBatchEvent("function_called", "applyQualityUpdates")
        _storeLastUpdate("quality", params || {})
    }

    function applyCameraUpdates(params) {
        _logBatchEvent("function_called", "applyCameraUpdates")
        _storeLastUpdate("camera", params || {})
    }

    function applyEffectsUpdates(params) {
        _logBatchEvent("function_called", "applyEffectsUpdates")
        _storeLastUpdate("effects", params || {})
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
        _storeLastUpdate("render", payload)
    }

    function applyThreeDUpdates(params) {
        _logBatchEvent("function_called", "applyThreeDUpdates")
        var normalized = _normaliseState(params)
        threeDState = normalized
        var networkSource = null
        if (normalized && typeof normalized === "object")
            networkSource = normalized.flowNetwork !== undefined ? normalized.flowNetwork : normalized.flownetwork
        flowTelemetry = _normaliseState(networkSource)
        receiverTelemetry = _resolveReceiverTelemetry(normalized)
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
    }

    onSceneBridgeChanged: {
        _applyBridgeSnapshot(sceneBridge)
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
        flowTelemetry = ({})
        receiverTelemetry = ({})
        geometryStateReceived = false
        simulationStateReceived = false
        sceneBridgeDispatchCount = 0
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
        postProcessingBypassed = !!active
        postProcessingBypassReason = postProcessingBypassed ? normalizedReason : ""
        updateSimpleFallbackState(postProcessingBypassed, postProcessingBypassReason)

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

            registerShaderWarning(effectId, resolvedMessage)
        }

        function onEffectCompilationRecovered(effectId) {
            clearShaderWarning(effectId)
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
 property var cameraHudSettings: ({})
 property bool cameraHudEnabled: false
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

readonly property var environmentDefaultsMap: environmentDefaultsMapFor(sceneDefaults)
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
}
