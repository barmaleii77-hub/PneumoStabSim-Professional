#pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick3D 6.10
import QtQml 6.10
import PneumoStabSim 1.0           // allow bare SimulationRoot usage for compatibility with tests
import PneumoStabSim 1.0 as PSS    // keep alias for explicit references if needed
import "./"
import "./effects" as Effects          // Ensure local effect controllers (e.g., SceneEnvironmentController) are resolved
import "./Panels" as Panels
import "./training" as Training
import "./components" as Components
import "./components/BatchDispatch.js" as Batch

// Полноценная сцена; селектор "+screenshots" может подключать упрощённый вариант.
Item {
    id: root
    objectName: "mainRoot"
    anchors.fill: parent

    // --- Сигналы интеграции
    signal batchUpdatesApplied(var summary)
    signal animationToggled(bool running)
    signal simulationControlRequested(string command)
    signal modesPresetSelected(string presetId)
    signal modesModeChanged(string modeType, string newMode)
    signal modesPhysicsChanged(var payload)
    signal modesAnimationChanged(var payload)
    signal pneumaticSettingsChanged(var payload)
    signal simulationSettingsChanged(var payload)
    signal cylinderSettingsChanged(var payload)
    signal shaderStatusDumpRequested(var payload)
    signal accordionPresetActivated(string panelId, string presetId)
    signal accordionFieldCommitted(string panelId, string field, var value)
    signal accordionValidationChanged(string panelId, string field, string state, string message)

    // --- Контекстные бриджи
    readonly property var hostWindow: (typeof globalThis !== "undefined" && globalThis.window !== undefined) ? globalThis.window : null
    readonly property var contextSceneBridge: (typeof globalThis !== "undefined" && globalThis.pythonSceneBridge !== undefined) ? globalThis.pythonSceneBridge : null
    readonly property var contextTelemetryBridge: (typeof globalThis !== "undefined" && globalThis.pythonTelemetryBridge !== undefined) ? globalThis.pythonTelemetryBridge : null
    readonly property var contextTrainingBridge: (typeof globalThis !== "undefined" && globalThis.trainingBridge !== undefined) ? globalThis.trainingBridge : null
    readonly property var contextModesMetadata: (typeof globalThis !== "undefined" && globalThis.modesMetadata !== undefined) ? globalThis.modesMetadata : ({})
    readonly property var contextInitialModesSettings: (typeof globalThis !== "undefined" && globalThis.initialModesSettings !== undefined) ? globalThis.initialModesSettings : undefined
    readonly property var contextInitialAnimationSettings: (typeof globalThis !== "undefined" && globalThis.initialAnimationSettings !== undefined) ? globalThis.initialAnimationSettings : undefined
    readonly property var contextInitialPneumaticSettings: (typeof globalThis !== "undefined" && globalThis.initialPneumaticSettings !== undefined) ? globalThis.initialPneumaticSettings : undefined
    readonly property var contextInitialSimulationSettings: (typeof globalThis !== "undefined" && globalThis.initialSimulationSettings !== undefined) ? globalThis.initialSimulationSettings : undefined
    readonly property var contextInitialCylinderSettings: (typeof globalThis !== "undefined" && globalThis.initialCylinderSettings !== undefined) ? globalThis.initialCylinderSettings : undefined

    // --- Состояние батчей
    property var pendingPythonUpdates: ({})
    property bool postProcessingBypassed: false
    property string postProcessingBypassReason: ""
    property var _queuedBatchedUpdates: []
    property var _pendingSimulationPanelCalls: []
    property bool showTrainingPresets: true
    property bool telemetryPanelVisible: true
    property int _appliedBatchCounter: 0
    property int _lastDeliveredBatchId: 0

    readonly property bool hasSceneBridge: contextSceneBridge !== null
    readonly property var simulationRootItem: simulationLoader.item
    readonly property var sceneSharedMaterials: simulationRootItem ? simulationRootItem.sceneSharedMaterials : null
    readonly property var sceneDirectionalLights: simulationRootItem ? simulationRootItem.sceneDirectionalLights : null
    readonly property var scenePointLights: simulationRootItem ? simulationRootItem.scenePointLights : null
    readonly property var sceneSuspensionAssembly: simulationRootItem ? simulationRootItem.sceneSuspensionAssembly : null
    readonly property var sceneFrameNode: sceneSuspensionAssembly ? sceneSuspensionAssembly.frameNode : null
    property bool simpleFallbackActive: false
    property string simpleFallbackReason: ""

    // --- Environment defaults (зеркало контроллера)
    property real environmentSceneScaleFactor: 1.0
    property color environmentBackgroundColor: "#1f242c"
    property string environmentBackgroundMode: "skybox"
    property bool environmentSkyboxEnabled: true
    property bool environmentIblMasterEnabled: true
    property bool environmentIblLightingEnabled: true
    property bool environmentIblBackgroundEnabled: true
    property bool environmentIblBindToCamera: false
    property real environmentIblIntensity: 1.3
    property real environmentSkyboxBrightness: 1.0
    property real environmentProbeHorizon: 0.0
    property real environmentIblRotationPitch: 0.0
    property real environmentIblRotationYaw: 0.0
    property real environmentIblRotationRoll: 0.0
    property real environmentSkyboxBlur: 0.08
    property string environmentAaPrimaryMode: "ssaa"
    property string environmentAaQualityLevel: "high"
    property string environmentAaPostMode: "taa"
    property bool environmentTaaEnabled: true
    property real environmentTaaStrength: 0.4
    property bool environmentTaaMotionAdaptive: true
    property bool environmentFxaaEnabled: false
    property bool environmentSpecularAaEnabled: true
    property bool environmentDitheringEnabled: true
    property bool environmentTonemapEnabled: false
    property string environmentTonemapMode: "filmic"
    property real environmentTonemapExposure: 1.0
    property real environmentTonemapWhitePoint: 1.0
    property bool ssaoEnabled: true
    property real ssaoRadius: 0.008
    property real ssaoIntensity: 1.0
    property real ssaoSoftness: 20.0
    property real ssaoBias: 0.025
    property bool ssaoDither: true
    property int ssaoSampleRate: 4
    property bool bloomEnabled: true
    property real bloomIntensity: 0.5
    property real bloomThreshold: 1.0
    property real bloomSecondaryBloom: 0.65
    property real bloomStrength: 1.0
    property bool glowQualityHighEnabled: true
    property bool glowUseBicubic: true
    property real glowHdrMaximumValue: 8.0
    property real glowHdrScale: 2.0
    property bool lensFlareActive: false
    property int lensFlareGhosts: 4
    property real lensFlareGhostDispersalValue: 0.06
    property real lensFlareHaloWidthValue: 0.05
    property real lensFlareBloomBiasValue: 1.0
    property real lensFlareStretchValue: 0.0
    property bool depthOfFieldActive: false
    property bool depthOfFieldAutoFocus: true
    property real depthOfFieldFocusDistanceValue: 2.5
    property real depthOfFieldFocusRangeValue: 0.9
    property real depthOfFieldBlurAmountValue: 4.0
    property bool fogEnabled: true
    property bool fogDepthEnabled: true
    property color fogColor: "#aab9cf"
    property real fogDensity: 0.06
    property real fogDepthNear: 2.0
    property real fogDepthFar: 20.0
    property real fogDepthCurve: 1.0
    property bool fogHeightEnabled: false
    property real fogLeastIntenseY: 0.0
    property real fogMostIntenseY: 3.0
    property real fogHeightCurve: 1.0
    property bool fogTransmitEnabled: true
    property real fogTransmitCurve: 1.0
    property bool vignetteActive: false
    property real vignetteStrengthValue: 0.35
    property real vignetteRadiusValue: 0.5
    property bool colorAdjustmentsEnabled: true
    property bool colorAdjustmentsActive: true
    property bool colorAdjustmentsHasOverrides: false
    property real adjustmentBrightness: 0.0
    property real adjustmentContrast: 0.0
    property real adjustmentSaturation: 0.0

    Effects.SceneEnvironmentController {
        id: environmentDefaults
        objectName: "environmentDefaults"
        sceneScaleFactor: root.environmentSceneScaleFactor
        qtRuntimeVersionData: "6.10.0"
        backgroundColor: root.environmentBackgroundColor
        backgroundModeKey: root.environmentBackgroundMode
        skyboxToggleFlag: root.environmentSkyboxEnabled
        iblMasterEnabled: root.environmentIblMasterEnabled
        iblLightingEnabled: root.environmentIblLightingEnabled
        iblBackgroundEnabled: root.environmentIblBackgroundEnabled
        iblBindToCamera: root.environmentIblBindToCamera
        iblIntensity: root.environmentIblIntensity
        skyboxBrightnessValue: root.environmentSkyboxBrightness
        probeHorizonValue: root.environmentProbeHorizon
        iblRotationPitchDeg: root.environmentIblRotationPitch
        iblRotationDeg: root.environmentIblRotationYaw
        iblRotationRollDeg: root.environmentIblRotationRoll
        skyboxBlurValue: root.environmentSkyboxBlur
        aaPrimaryMode: root.environmentAaPrimaryMode
        aaQualityLevel: root.environmentAaQualityLevel
        aaPostMode: root.environmentAaPostMode
        taaEnabled: root.environmentTaaEnabled
        taaStrength: root.environmentTaaStrength
        taaMotionAdaptive: root.environmentTaaMotionAdaptive
        fxaaEnabled: root.environmentFxaaEnabled
        specularAAEnabled: root.environmentSpecularAaEnabled
        ditheringEnabled: root.environmentDitheringEnabled
        tonemapActive: root.environmentTonemapEnabled
        tonemapModeName: root.environmentTonemapMode
        tonemapExposureValue: root.environmentTonemapExposure
        tonemapWhitePointValue: root.environmentTonemapWhitePoint
        ssaoEnabled: root.ssaoEnabled
        aoEnabled: root.ssaoEnabled
        ssaoRadius: root.ssaoRadius
        ssaoIntensity: root.ssaoIntensity
        ssaoSoftness: root.ssaoSoftness
        ssaoBias: root.ssaoBias
        ssaoDither: root.ssaoDither
        ssaoSampleRate: root.ssaoSampleRate
        bloomEnabled: root.bloomEnabled
        bloomIntensity: root.bloomIntensity
        bloomThreshold: root.bloomThreshold
        bloomSpread: root.bloomSecondaryBloom
        bloomGlowStrength: root.bloomStrength
        bloomQualityHigh: root.glowQualityHighEnabled
        bloomUseBicubicUpscale: root.glowUseBicubic
        bloomHdrMaximum: root.glowHdrMaximumValue
        bloomHdrScale: root.glowHdrScale
        lensFlareEnabled: root.lensFlareActive
        lensFlareGhostCount: root.lensFlareGhosts
        lensFlareGhostDispersal: root.lensFlareGhostDispersalValue
        lensFlareHaloWidth: root.lensFlareHaloWidthValue
        lensFlareBloomBias: root.lensFlareBloomBiasValue
        lensFlareStretchToAspect: root.lensFlareStretchValue
        depthOfFieldEnabled: root.depthOfFieldActive
        depthOfFieldAutoFocus: root.depthOfFieldAutoFocus
        depthOfFieldFocusDistance: root.depthOfFieldFocusDistanceValue
        depthOfFieldFocusRange: root.depthOfFieldFocusRangeValue
        depthOfFieldBlurAmount: root.depthOfFieldBlurAmountValue
        fogEnabled: root.fogEnabled
        fogColor: root.fogColor
        fogDensity: root.fogDensity
        fogDepthEnabled: root.fogDepthEnabled
        fogDepthCurve: root.fogDepthCurve
        fogDepthNear: root.fogDepthNear
        fogDepthFar: root.fogDepthFar
        fogHeightEnabled: root.fogHeightEnabled
        fogLeastIntenseY: root.fogLeastIntenseY
        fogMostIntenseY: root.fogMostIntenseY
        fogHeightCurve: root.fogHeightCurve
        fogTransmitEnabled: root.fogTransmitEnabled
        fogTransmitCurve: root.fogTransmitCurve
        vignetteEnabled: root.vignetteActive
        vignetteStrength: root.vignetteStrengthValue
        vignetteRadius: root.vignetteRadiusValue
        colorAdjustmentsEnabled: root.colorAdjustmentsEnabled
        colorAdjustmentsActive: root.colorAdjustmentsActive
        adjustmentBrightness: root.adjustmentBrightness
        adjustmentContrast: root.adjustmentContrast
        adjustmentSaturation: root.adjustmentSaturation
        onFogHelpersSupportedChanged: {
            if (!fogHelpersSupported) {
                console.warn("[main.qml] Fog helpers unavailable; disabling advanced fog")
                root.fogDepthEnabled = false
                root.fogHeightEnabled = false
                root.fogTransmitEnabled = false
            }
        }
    }

    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates || typeof pendingPythonUpdates !== "object") return
        if (Object.keys(pendingPythonUpdates).length === 0) return
        if (!_deliverBatchedUpdates(pendingPythonUpdates)) _enqueueBatchedPayload(pendingPythonUpdates)
    }

    function _enqueueBatchedPayload(payload) {
        if (!payload || typeof payload !== "object") return
        if (!_queuedBatchedUpdates) _queuedBatchedUpdates = []
        _queuedBatchedUpdates.push(payload)
    }
    function _flushQueuedBatches() {
        if (!_queuedBatchedUpdates || !_queuedBatchedUpdates.length) return
        var remaining = []
        for (var i = 0; i < _queuedBatchedUpdates.length; ++i) {
            var payload = _queuedBatchedUpdates[i]
            if (!_deliverBatchedUpdates(payload)) remaining.push(payload)
        }
        _queuedBatchedUpdates = remaining
    }

    function _syncPostProcessingState() {
        var target = _activeSimulationRoot()
        var bypass = false
        var reason = ""
        if (target) {
            try {
                bypass = !!target.postProcessingBypassed
                if (target.postProcessingBypassReason !== undefined && target.postProcessingBypassReason !== null)
                    reason = String(target.postProcessingBypassReason)
            } catch(e) { console.debug("[main.qml] post-processing state read failed", e) }
        }
        if (postProcessingBypassed !== bypass) postProcessingBypassed = bypass
        if (postProcessingBypassReason !== reason) postProcessingBypassReason = reason
    }

    function _deliverBatchedUpdates(payload) {
        if (payload && typeof payload === "object" && payload.effects) {
            var ep = payload.effects
            if (ep.effects_bypass !== undefined) postProcessingBypassed = !!ep.effects_bypass
            if (ep.effects_bypass_reason !== undefined) postProcessingBypassReason = String(ep.effects_bypass_reason || "")
        }
        // Фильтр по монотонику batch_id (если присутствует)
        var batchId = -1
        if (payload && typeof payload.batch_id === "number") batchId = payload.batch_id
        if (batchId !== -1 && batchId <= _lastDeliveredBatchId) {
            console.debug("[main.qml] Skipping stale batch", batchId, "<=", _lastDeliveredBatchId)
            return true // считаем доставленным чтобы не зацикливать очередь
        }
        var delivered = _invokeOnActiveRoot("applyBatchedUpdates", payload)
        if (delivered) {
            _lastDeliveredBatchId = batchId !== -1 ? batchId : (_lastDeliveredBatchId + 1)
            _appliedBatchCounter += 1
        }
        _syncPostProcessingState()
        return delivered
    }

    function _invokeOnActiveRoot(methodName, payload) {
        var target = _activeSimulationRoot()
        if (!target) { console.warn("[main.qml] No active simulation root for", methodName); return false }
        var handler = target[methodName]
        if (typeof handler !== "function") { console.warn("[main.qml] Root missing handler", methodName); return false }
        try { return payload === undefined ? (handler.call(target) === undefined ? true : !!handler.call(target)) : (handler.call(target, payload) === undefined ? true : !!handler.call(target, payload)) }
        catch (error) { console.error("[main.qml] Handler", methodName, "error", error); return false }
    }
    function _activeSimulationRoot() {
        if (simulationLoader.active && simulationLoader.item) return simulationLoader.item
        if (fallbackLoader.active && fallbackLoader.item) return fallbackLoader.item
        if (simulationLoader.item) return simulationLoader.item
        if (fallbackLoader.item) return fallbackLoader.item
        return null
    }

    function registerShaderWarning(effectId, message) {
        var target = _activeSimulationRoot()
        if (target && typeof target.registerShaderWarning === "function") { try { target.registerShaderWarning(effectId, message); return } catch(e){ console.debug("[main.qml] forward registerShaderWarning failed", e) } }
        if (hostWindow && typeof hostWindow.registerShaderWarning === "function") { try { hostWindow.registerShaderWarning(effectId, message) } catch(e){ console.debug("[main.qml] host registerShaderWarning failed", e) } }
    }
    function clearShaderWarning(effectId) {
        var target = _activeSimulationRoot()
        if (target && typeof target.clearShaderWarning === "function") { try { target.clearShaderWarning(effectId); return } catch(e){ console.debug("[main.qml] forward clearShaderWarning failed", e) } }
        if (hostWindow && typeof hostWindow.clearShaderWarning === "function") { try { hostWindow.clearShaderWarning(effectId) } catch(e){ console.debug("[main.qml] host clearShaderWarning failed", e) } }
    }

    function applyBatchedUpdates(updates) {
        if (!updates || typeof updates !== "object") return false
        if (_deliverBatchedUpdates(updates)) return true
        _enqueueBatchedPayload(updates)
        return false
    }

    readonly property var _proxyMethodNames: ["updateGeometry","applyGeometryUpdates","applyAnimationUpdates","updateAnimation","applyLightingUpdates","updateLighting","applyMaterialUpdates","updateMaterials","applyEnvironmentUpdates","updateEnvironment","applySceneUpdates","updateScene","applyQualityUpdates","updateQuality","applyCameraUpdates","updateCamera","applyEffectsUpdates","updateEffects","applySimulationUpdates","applyThreeDUpdates","apply3DUpdates","applyRenderSettings"]

    function _createProxyMethod(methodName) { return function(params){ return _invokeOnActiveRoot(methodName, params) } }
    function _installProxyMethodStubs() {
        for (var i=0;i<_proxyMethodNames.length;++i){ var m=_proxyMethodNames[i]; try{ if (root.hasOwnProperty && root.hasOwnProperty(m)) continue } catch(e){ if (typeof root[m] !== "undefined") continue } root[m]=_createProxyMethod(m) }
    }
    function _invokeSimulationPanel(methodName, payload) {
        if (simulationPanel && simulationPanel.isReady && typeof simulationPanel[methodName] === "function") {
            try { return simulationPanel[methodName](payload) } catch(e){ console.error("SimulationPanel call failed", methodName, e) }
        } else { _pendingSimulationPanelCalls.push({name:methodName,payload:payload}) }
        return false
    }
    function _flushSimulationPanelCalls(){ if(!simulationPanel||!simulationPanel.isReady) return; if(!_pendingSimulationPanelCalls||!_pendingSimulationPanelCalls.length) return; const q=_pendingSimulationPanelCalls.slice(); _pendingSimulationPanelCalls=[]; for(let i=0;i<q.length;++i){ const e=q[i]; if(!e||!e.name) continue; if(typeof simulationPanel[e.name] !== "function") continue; try{ simulationPanel[e.name](e.payload) } catch(err){ console.error("Failed to flush simulation panel call", e.name, err) } } }
    function _onSimulationPanelReady(){ _flushSimulationPanelCalls() }
    function applyModesSettings(p){ return _invokeSimulationPanel("applyModesSettings",p) }
    function applyAnimationSettings(p){ return _invokeSimulationPanel("applyAnimationSettings",p) }
    function applyPneumaticSettings(p){ return _invokeSimulationPanel("applyPneumaticSettings",p) }
    function applySimulationSettings(p){ return _invokeSimulationPanel("applySimulationSettings",p) }
    function applyCylinderSettings(p){ return _invokeSimulationPanel("applyCylinderSettings",p) }
    function applyGeometryUpdates(p){ return _invokeSimulationPanel("applyGeometryUpdates",p) }
    function updateGeometry(p){ return _invokeSimulationPanel("updateGeometry",p) }

    function _applyInitialGraphicsUpdatesFromBridge(){ if(!hasSceneBridge||!contextSceneBridge) return; try{ var initBatch=contextSceneBridge.initialGraphicsUpdates; if(!initBatch||typeof initBatch!=="object"||!Object.keys(initBatch).length) return; if(!_deliverBatchedUpdates(initBatch)) _enqueueBatchedPayload(initBatch) } catch(e){ console.debug("[main.qml] Initial graphics updates apply failed", e) } }

    function _summarize_captured_payloads() { return { applied: _appliedBatchCounter, lastId: _lastDeliveredBatchId } }

    Component.onCompleted: { postProcessingBypassed=false; postProcessingBypassReason=""; _syncPostProcessingState(); _installProxyMethodStubs(); _flushSimulationPanelCalls(); _applyInitialGraphicsUpdatesFromBridge() }

    Loader { id: simulationLoader; objectName: "simulationLoader"; anchors.fill: parent; active: true; sourceComponent: SimulationRoot { id: simulationRoot; sceneBridge: contextSceneBridge } onStatusChanged: { if (status===Loader.Error){ var loadError=simulationLoader.sourceComponent ? simulationLoader.sourceComponent.errorString() : ""; console.error("Failed to load SimulationRoot:", loadError); var reason= loadError && loadError.length ? loadError : "SimulationRoot load failure"; simpleFallbackReason=reason; if(!simpleFallbackActive) console.warn("[main.qml] Switching to simplified fallback after SimulationRoot load failure"); simpleFallbackActive=true } if(status===Loader.Ready){ if(item) item.visible=!simpleFallbackActive; _syncPostProcessingState(); _flushQueuedBatches() } } onLoaded: { if(item&&item.batchUpdatesApplied) item.batchUpdatesApplied.connect(root.batchUpdatesApplied); if(item&&item.animationToggled) item.animationToggled.connect(root.animationToggled); if(item) item.visible=!simpleFallbackActive } }

    Connections { target: simulationLoader.item; ignoreUnknownSignals: true; function onSimpleFallbackRequested(reason){ var normalized=reason&&reason.length?reason:"Rendering pipeline failure"; if(!simpleFallbackActive) console.warn("[main.qml] Simplified rendering fallback activated:", normalized); else if(simpleFallbackReason!==normalized) console.warn("[main.qml] Simplified rendering reason обновлена:", normalized); simpleFallbackReason=normalized; simpleFallbackActive=true; if(simulationLoader.item) simulationLoader.item.visible=false } function onSimpleFallbackRecovered(){ if(!simpleFallbackActive) return; simpleFallbackActive=false; simpleFallbackReason=""; if(simulationLoader.item) simulationLoader.item.visible=true; console.log("[main.qml] Simplified rendering fallback cleared") } function onShaderStatusDumpRequested(payload){ shaderStatusDumpRequested(payload) } }

    Loader { id: fallbackLoader; objectName: "fallbackLoader"; anchors.fill: parent; active: !hasSceneBridge || simpleFallbackActive; sourceComponent: SimulationFallbackRoot {} onStatusChanged: { if(status===Loader.Ready){ _syncPostProcessingState(); _flushQueuedBatches() } } onLoaded: { if(item&&item.batchUpdatesApplied) item.batchUpdatesApplied.connect(root.batchUpdatesApplied); if(item&&item.animationToggled) item.animationToggled.connect(root.animationToggled) } }

    Connections { target: simulationLoader.item; enabled: !!target; ignoreUnknownSignals: true; function onPostProcessingBypassedChanged(){ _syncPostProcessingState() } function onPostProcessingBypassReasonChanged(){ _syncPostProcessingState() } }
    Connections { target: fallbackLoader.item; enabled: !!target; ignoreUnknownSignals: true; function onPostProcessingBypassedChanged(){ _syncPostProcessingState() } function onPostProcessingBypassReasonChanged(){ _syncPostProcessingState() } }

    Panels.SimulationPanel { id: simulationPanel; objectName: "simulationPanel"; controller: root; anchors.top: parent.top; anchors.left: parent.left; anchors.margins: 16; z: 9050; visible: true; property var _modesMetadataValue: ({}); modesMetadata: _modesMetadataValue; property var _initialModesValue: ({}); initialModes: _initialModesValue; property var _initialAnimationValue: ({}); initialAnimation: _initialAnimationValue; property var _initialPneumaticValue: ({}); initialPneumatic: _initialPneumaticValue; property var _initialSimulationValue: ({}); initialSimulation: _initialSimulationValue; property var _initialCylinderValue: ({}); initialCylinder: _initialCylinderValue; Component.onCompleted: { if(contextModesMetadata!==undefined) _modesMetadataValue=contextModesMetadata; if(contextInitialModesSettings!==undefined) _initialModesValue=contextInitialModesSettings; if(contextInitialAnimationSettings!==undefined) _initialAnimationValue=contextInitialAnimationSettings; if(contextInitialPneumaticSettings!==undefined) _initialPneumaticValue=contextInitialPneumaticSettings; if(contextInitialSimulationSettings!==undefined) _initialSimulationValue=contextInitialSimulationSettings; if(contextInitialCylinderSettings!==undefined) _initialCylinderValue=contextInitialCylinderSettings; _onSimulationPanelReady() } onSimulationControlRequested: function(command){ simulationControlRequested(command) } onModesPresetSelected: function(presetId){ modesPresetSelected(presetId) } onModesModeChanged: function(modeType,newMode){ modesModeChanged(modeType,newMode) } onModesPhysicsChanged: function(payload){ modesPhysicsChanged(payload) } onModesAnimationChanged: function(payload){ modesAnimationChanged(payload) } onPneumaticSettingsChanged: function(payload){ pneumaticSettingsChanged(payload) } onSimulationSettingsChanged: function(payload){ simulationSettingsChanged(payload) } onCylinderSettingsChanged: function(payload){ cylinderSettingsChanged(payload) } onAccordionPresetActivated: function(panelId,presetId){ accordionPresetActivated(panelId,presetId) } onAccordionFieldCommitted: function(panelId,field,value){ accordionFieldCommitted(panelId,field,value) } onAccordionValidationChanged: function(panelId,field,state,message){ accordionValidationChanged(panelId,field,state,message) } }

    Rectangle { id: postEffectsBypassBadge; objectName: "postEffectsBypassBadge"; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 12; color: "#CC1f2933"; radius: 8; visible: postProcessingBypassed; border.color: "#b3ffffff"; border.width: 1; opacity: 0.92; implicitWidth: badgeRow.implicitWidth + 20; implicitHeight: badgeRow.implicitHeight + 20; Row { id: badgeRow; spacing: 8; anchors.fill: parent; anchors.margins: 10; Rectangle { width: 10; height: 10; radius: 5; color: "#ffcc66" } Column { spacing: 2; Text { text: qsTr("Post-effects bypassed"); font.pixelSize: 14; color: "#ffffff"; font.bold: true } Text { text: postProcessingBypassReason && postProcessingBypassReason.length ? postProcessingBypassReason : qsTr("Fallback rendering active"); font.pixelSize: 12; color: "#e6ffffff"; elide: Text.ElideRight; width: 220 } } } }

    Training.TrainingPanel { id: trainingPanel; anchors.top: parent.top; anchors.right: parent.right; anchors.margins: 16; visible: showTrainingPresets && contextTrainingBridge !== null; z: 9000; opacity: 0.96; onPresetActivated: function(presetId){ console.log("Training preset selected", presetId) } }

    Components.TelemetryChartPanel { id: telemetryPanel; anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: 16; telemetryBridge: contextTelemetryBridge; visible: telemetryPanelVisible && telemetryBridge !== null }
}
