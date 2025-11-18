pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick3D 6.10
import PneumoStabSim 1.0 as PSS
import "./"
import "./effects"          // Ensure local effect controllers (e.g., SceneEnvironmentController) are resolved
import "./Panels" as Panels
import "training" as Training
import components 1.0 as Components

Item {
    id: root
    anchors.fill: parent

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

    // qmllint disable unqualified
    readonly property var hostWindow: (typeof globalThis !== "undefined" && globalThis.window !== undefined) ? globalThis.window : null
    property var contextSceneBridge: (typeof globalThis !== "undefined" && globalThis.pythonSceneBridge !== undefined) ? globalThis.pythonSceneBridge : null
    property var contextTelemetryBridge: (typeof globalThis !== "undefined" && globalThis.pythonTelemetryBridge !== undefined) ? globalThis.pythonTelemetryBridge : null
    property var contextTrainingBridge: (typeof globalThis !== "undefined" && globalThis.trainingBridge !== undefined) ? globalThis.trainingBridge : null
    property var contextModesMetadata: (typeof globalThis !== "undefined" && globalThis.modesMetadata !== undefined) ? globalThis.modesMetadata : ({})
    property var contextInitialModesSettings: (typeof globalThis !== "undefined" && globalThis.initialModesSettings !== undefined) ? globalThis.initialModesSettings : undefined
    property var contextInitialAnimationSettings: (typeof globalThis !== "undefined" && globalThis.initialAnimationSettings !== undefined) ? globalThis.initialAnimationSettings : undefined
    property var contextInitialPneumaticSettings: (typeof globalThis !== "undefined" && globalThis.initialPneumaticSettings !== undefined) ? globalThis.initialPneumaticSettings : undefined
    property var contextInitialSimulationSettings: (typeof globalThis !== "undefined" && globalThis.initialSimulationSettings !== undefined) ? globalThis.initialSimulationSettings : undefined
    property var contextInitialCylinderSettings: (typeof globalThis !== "undefined" && globalThis.initialCylinderSettings !== undefined) ? globalThis.initialCylinderSettings : undefined
    // qmllint enable unqualified

    property var pendingPythonUpdates: ({})
    property var _queuedBatchedUpdates: []
    property var _pendingSimulationPanelCalls: []
    property bool showTrainingPresets: true
    property bool telemetryPanelVisible: true

    readonly property bool hasSceneBridge: contextSceneBridge !== null
    readonly property bool fogApiAvailable: environmentDefaults && environmentDefaults.fogHelpersSupported
    readonly property var simulationRootItem: simulationLoader.item
    readonly property var sceneSharedMaterials: simulationRootItem ? simulationRootItem.sceneSharedMaterials : null
    readonly property var sceneDirectionalLights: simulationRootItem ? simulationRootItem.sceneDirectionalLights : null
    readonly property var scenePointLights: simulationRootItem ? simulationRootItem.scenePointLights : null
    readonly property var sceneSuspensionAssembly: simulationRootItem ? simulationRootItem.sceneSuspensionAssembly : null
    readonly property var sceneFrameNode: sceneSuspensionAssembly ? sceneSuspensionAssembly.frameNode : null
    property bool simpleFallbackActive: false
    property string simpleFallbackReason: ""

    // ---------------------------------------------------------
    // Environment defaults mirrored from SceneEnvironmentController
    // ---------------------------------------------------------
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

    // SSAO properties
    property bool ssaoEnabled: true
    property real ssaoRadius: 0.008
    property real ssaoIntensity: 1.0
    property real ssaoSoftness: 20.0
    property real ssaoBias: 0.025
    property bool ssaoDither: true
    property int ssaoSampleRate: 4

    // Bloom and glow
    property bool bloomEnabled: true
    property real bloomIntensity: 0.5
    property real bloomThreshold: 1.0
    property real bloomSecondaryBloom: 0.65
    property real bloomStrength: 1.0
    property bool glowQualityHighEnabled: true
    property bool glowUseBicubic: true
    property real glowHdrMaximumValue: 8.0
    property real glowHdrScale: 2.0

    // Lens flare
    property bool lensFlareActive: false
    property int lensFlareGhosts: 4
    property real lensFlareGhostDispersalValue: 0.06
    property real lensFlareHaloWidthValue: 0.05
    property real lensFlareBloomBiasValue: 1.0
    property real lensFlareStretchValue: 0.0

    // Depth of field
    property bool depthOfFieldActive: false
    property bool depthOfFieldAutoFocus: true
    property real depthOfFieldFocusDistanceValue: 2.5
    property real depthOfFieldFocusRangeValue: 0.9
    property real depthOfFieldBlurAmountValue: 4.0

    // Fog
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

    // Vignette & adjustments
    property bool vignetteActive: false
    property real vignetteStrengthValue: 0.35
    property real vignetteRadiusValue: 0.5

    property bool colorAdjustmentsEnabled: true
    property bool colorAdjustmentsActive: true
    property bool colorAdjustmentsHasOverrides: false
    property real adjustmentBrightness: 0.0
    property real adjustmentContrast: 0.0
    property real adjustmentSaturation: 0.0

    SceneEnvironmentController {
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

         fog: Fog {
             id: environmentFog

             enabled: environmentDefaults.fogHelpersSupported && root.fogEnabled
             color: root.fogColor
             density: root.fogDensity

             Component.onCompleted: {
                 if (!("density" in environmentFog)) {
                     console.warn("[main.qml] Fog component is missing density property; disabling fog")
                     environmentFog.enabled = false
                 }
             }

             depthEnabled: environmentDefaults.fogHelpersSupported && root.fogDepthEnabled && root.fogEnabled
             depthCurve: root.fogDepthCurve
             depthNear: environmentDefaults.toSceneLength(root.fogDepthNear)
             depthFar: environmentDefaults.toSceneLength(root.fogDepthFar)
             heightEnabled: root.fogHeightEnabled
             leastIntenseY: environmentDefaults.toSceneLength(root.fogLeastIntenseY)
             mostIntenseY: environmentDefaults.toSceneLength(root.fogMostIntenseY)
             heightCurve: root.fogHeightCurve
             transmitEnabled: root.fogTransmitEnabled
             transmitCurve: root.fogTransmitCurve
         }

        vignetteEnabled: root.vignetteActive
        vignetteStrength: root.vignetteStrengthValue
        vignetteRadius: root.vignetteRadiusValue

        colorAdjustmentsEnabled: root.colorAdjustmentsEnabled
        colorAdjustmentsActive: root.colorAdjustmentsActive
        adjustmentBrightness: root.adjustmentBrightness
        adjustmentContrast: root.adjustmentContrast
        adjustmentSaturation: root.adjustmentSaturation
    }

    Connections {
        target: environmentDefaults
        ignoreUnknownSignals: true

        function onFogHelpersSupportedChanged() {
            if (environmentDefaults && !environmentDefaults.fogHelpersSupported) {
                console.warn("[main.qml] Fog helpers unavailable; fog settings downgraded to defaults")
                root.fogEnabled = false
                root.fogDepthEnabled = false
                root.fogHeightEnabled = false
                root.fogTransmitEnabled = false
            }
        }
    }

    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates || typeof pendingPythonUpdates !== "object") {
            return
        }
        if (Object.keys(pendingPythonUpdates).length === 0) {
            return
        }

        if (!_deliverBatchedUpdates(pendingPythonUpdates)) {
            _enqueueBatchedPayload(pendingPythonUpdates)
        }
    }

    function _enqueueBatchedPayload(payload) {
        if (!_queuedBatchedUpdates) {
            _queuedBatchedUpdates = []
        }
        _queuedBatchedUpdates = _queuedBatchedUpdates.concat([payload])
    }

    function _flushQueuedBatches() {
        if (!_queuedBatchedUpdates || _queuedBatchedUpdates.length === 0) {
            return
        }

        var remaining = []
        for (var i = 0; i < _queuedBatchedUpdates.length; ++i) {
            var payload = _queuedBatchedUpdates[i]
            if (!_deliverBatchedUpdates(payload)) {
                remaining.push(payload)
            }
        }

        _queuedBatchedUpdates = remaining
    }

    function _deliverBatchedUpdates(payload) {
        return _invokeOnActiveRoot("applyBatchedUpdates", payload)
    }

    function _invokeOnActiveRoot(methodName, payload) {
        var target = _activeSimulationRoot()
        if (!target) {
            console.warn("[main.qml] No active simulation root for", methodName)
            return false
        }

        var handler = target[methodName]
        if (typeof handler !== "function") {
            console.warn("[main.qml] Active simulation root is missing handler", methodName)
            return false
        }

        try {
            var result
            if (payload === undefined) {
                result = handler.call(target)
            } else {
                result = handler.call(target, payload)
            }
            return result === undefined ? true : Boolean(result)
        } catch (error) {
            console.error("[main.qml] Handler", methodName, "threw an error", error)
            return false
        }
    }

    function _activeSimulationRoot() {
        if (simulationLoader.active && simulationLoader.item) {
            return simulationLoader.item
        }
        if (fallbackLoader.active && fallbackLoader.item) {
            return fallbackLoader.item
        }
        if (simulationLoader.item) {
            return simulationLoader.item
        }
        if (fallbackLoader.item) {
            return fallbackLoader.item
        }
        return null
    }

    function registerShaderWarning(effectId, message) {
        var target = _activeSimulationRoot()
        if (target && typeof target.registerShaderWarning === "function") {
            try {
                target.registerShaderWarning(effectId, message)
                return
            } catch (error) {
                console.debug("[main.qml] registerShaderWarning forwarding failed", error)
            }
        }

        if (root.hostWindow && typeof root.hostWindow.registerShaderWarning === "function") {
            try {
                root.hostWindow.registerShaderWarning(effectId, message)
            } catch (error) {
                console.debug("[main.qml] window.registerShaderWarning failed", error)
            }
        }
    }

    function clearShaderWarning(effectId) {
        var target = _activeSimulationRoot()
        if (target && typeof target.clearShaderWarning === "function") {
            try {
                target.clearShaderWarning(effectId)
                return
            } catch (error) {
                console.debug("[main.qml] clearShaderWarning forwarding failed", error)
            }
        }

        if (root.hostWindow && typeof root.hostWindow.clearShaderWarning === "function") {
            try {
                root.hostWindow.clearShaderWarning(effectId)
            } catch (error) {
                console.debug("[main.qml] window.clearShaderWarning failed", error)
            }
        }
    }

    function applyBatchedUpdates(updates) {
        if (!updates || typeof updates !== "object") {
            return false
        }

        if (_deliverBatchedUpdates(updates)) {
            return true
        }

        _enqueueBatchedPayload(updates)
        return false
    }

    // `applyGeometryUpdates` is declared explicitly (see below) to avoid
    // dynamic property installation errors when the scene loader initialises.
    readonly property var _proxyMethodNames: [
        "updateGeometry",
        "applyGeometryUpdates",
        "applyAnimationUpdates",
        "updateAnimation",
        "applyLightingUpdates",
        "updateLighting",
        "applyMaterialUpdates",
        "updateMaterials",
        "applyEnvironmentUpdates",
        "updateEnvironment",
        "applySceneUpdates",
        "updateScene",
        "applyQualityUpdates",
        "updateQuality",
        "applyCameraUpdates",
        "updateCamera",
        "applyEffectsUpdates",
        "updateEffects",
        "applySimulationUpdates",
        "applyThreeDUpdates",
        "apply3DUpdates",
        "applyRenderSettings"
    ]

    function _createProxyMethod(methodName) {
        return function(params) {
            return _invokeOnActiveRoot(methodName, params)
        }
    }

    function _invokeSimulationPanel(methodName, payload) {
        if (simulationPanel && simulationPanel.isReady && typeof simulationPanel[methodName] === "function") {
            try {
                return simulationPanel[methodName](payload)
            } catch (error) {
                console.error("SimulationPanel call failed", methodName, error)
            }
        } else {
            _pendingSimulationPanelCalls.push({ name: methodName, payload: payload })
        }
        return false
    }

    function _flushSimulationPanelCalls() {
        if (!simulationPanel || !simulationPanel.isReady)
            return
        if (!_pendingSimulationPanelCalls || !_pendingSimulationPanelCalls.length)
            return
        const queue = _pendingSimulationPanelCalls.slice()
        _pendingSimulationPanelCalls = []
        for (let i = 0; i < queue.length; ++i) {
            const entry = queue[i]
            if (!entry || !entry.name)
                continue
            if (typeof simulationPanel[entry.name] !== "function")
                continue
            try {
                simulationPanel[entry.name](entry.payload)
            } catch (error) {
                console.error("Failed to flush simulation panel call", entry.name, error)
            }
        }
    }

    function _onSimulationPanelReady() {
        _flushSimulationPanelCalls()
    }

    function applyModesSettings(payload) {
        return _invokeSimulationPanel("applyModesSettings", payload)
    }

    function applyAnimationSettings(payload) {
        return _invokeSimulationPanel("applyAnimationSettings", payload)
    }

    function applyPneumaticSettings(payload) {
        return _invokeSimulationPanel("applyPneumaticSettings", payload)
    }

    function applySimulationSettings(payload) {
        return _invokeSimulationPanel("applySimulationSettings", payload)
    }

    function applyCylinderSettings(payload) {
        return _invokeSimulationPanel("applyCylinderSettings", payload)
    }

    function applyGeometryUpdates(payload) {
        return _invokeSimulationPanel("applyGeometryUpdates", payload)
    }

    function updateGeometry(payload) {
        return _invokeSimulationPanel("updateGeometry", payload)
    }

    Component.onCompleted: {
        for (var i = 0; i < _proxyMethodNames.length; ++i) {
            var methodName = _proxyMethodNames[i]
            // Skip if method already defined explicitly (like applyAnimationSettings)
            try {
                if (root.hasOwnProperty(methodName)) {
                    continue
                }
            } catch (error) {
                // Fallback for environments without hasOwnProperty
                if (typeof root[methodName] !== "undefined") {
                    continue
                }
            }
            root[methodName] = _createProxyMethod(methodName)
        }
        _flushSimulationPanelCalls()

        // Подхватываем начальные графические обновления из Python (env → SceneBridge)
        try {
          if (root.hasSceneBridge && root.contextSceneBridge) {
              var initBatch = root.contextSceneBridge.initialGraphicsUpdates
              if (initBatch && typeof initBatch === "object" && Object.keys(initBatch).length) {
                  if (!_deliverBatchedUpdates(initBatch)) {
                      _enqueueBatchedPayload(initBatch)
                  }
              }
            }
        } catch (e) {
            console.debug("[main.qml] Initial graphics updates apply failed", e)
        }
    }

    Loader {
        id: simulationLoader
          objectName: "simulationLoader"
          anchors.fill: parent
          active: true
          sourceComponent: PSS.SimulationRoot {
              id: simulationRoot
              sceneBridge: root.contextSceneBridge
              fogDepthCurve: root.fogDepthCurve
          }
          onStatusChanged: {
              if (status === Loader.Error) {
                  var loadError = simulationLoader.sourceComponent ? simulationLoader.sourceComponent.errorString() : ""
                  console.error("Failed to load SimulationRoot:", loadError)
                  var normalizedReason = loadError && loadError.length ? loadError : "SimulationRoot load failure"
                  root.simpleFallbackReason = normalizedReason
                  if (!root.simpleFallbackActive)
                      console.warn("[main.qml] Switching to simplified fallback after SimulationRoot load failure")
                  root.simpleFallbackActive = true
              }
              if (status === Loader.Ready) {
                  if (item)
                      item.visible = !root.simpleFallbackActive
                  root._flushQueuedBatches()
              }
          }
          // qmllint disable missing-property
          onLoaded: {
              if (item && item.batchUpdatesApplied) {
                  item.batchUpdatesApplied.connect(root.batchUpdatesApplied)
              }
              if (item && item.animationToggled) {
                  item.animationToggled.connect(root.animationToggled)
              }
              if (item)
                  item.visible = !root.simpleFallbackActive
          }
          // qmllint enable missing-property
      }

    Connections {
        target: simulationLoader.item
        ignoreUnknownSignals: true

        function onSimpleFallbackRequested(reason) {
            var normalized = reason && reason.length ? reason : "Rendering pipeline failure"
            if (!root.simpleFallbackActive) {
                console.warn("[main.qml] Simplified rendering fallback activated:", normalized)
            } else if (root.simpleFallbackReason !== normalized) {
                console.warn("[main.qml] Simplified rendering reason updated:", normalized)
            }
            root.simpleFallbackReason = normalized
            root.simpleFallbackActive = true
            if (simulationLoader.item)
                simulationLoader.item.visible = false
        }

        function onSimpleFallbackRecovered() {
            if (!root.simpleFallbackActive)
                return
            root.simpleFallbackActive = false
            root.simpleFallbackReason = ""
            if (simulationLoader.item)
                simulationLoader.item.visible = true
            console.log("[main.qml] Simplified rendering fallback cleared")
        }

        function onShaderStatusDumpRequested(payload) {
            root.shaderStatusDumpRequested(payload)
        }
    }

      Loader {
          id: fallbackLoader
          objectName: "fallbackLoader"
          anchors.fill: parent
          active: !root.hasSceneBridge || root.simpleFallbackActive
          sourceComponent: SimulationFallbackRoot {}
          onStatusChanged: {
              if (status === Loader.Ready) {
                  root._flushQueuedBatches()
              }
          }
          // qmllint disable missing-property
          onLoaded: {
              if (item && item.batchUpdatesApplied) {
                  item.batchUpdatesApplied.connect(root.batchUpdatesApplied)
              }
              if (item && item.animationToggled) {
                  item.animationToggled.connect(root.animationToggled)
              }
          }
          // qmllint enable missing-property
      }

      Panels.SimulationPanel {
        id: simulationPanel
        objectName: "simulationPanel"
        controller: root
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 16
        z: 9050
        visible: true
        property var _modesMetadataValue: ({})
        modesMetadata: _modesMetadataValue
        property var _initialModesValue: ({})
        initialModes: _initialModesValue
        property var _initialAnimationValue: ({})
        initialAnimation: _initialAnimationValue
        property var _initialPneumaticValue: ({})
        initialPneumatic: _initialPneumaticValue
        property var _initialSimulationValue: ({})
        initialSimulation: _initialSimulationValue
        property var _initialCylinderValue: ({})
        initialCylinder: _initialCylinderValue

          Component.onCompleted: {
              if (root.contextModesMetadata !== undefined) _modesMetadataValue = root.contextModesMetadata
              if (root.contextInitialModesSettings !== undefined) _initialModesValue = root.contextInitialModesSettings
              if (root.contextInitialAnimationSettings !== undefined) _initialAnimationValue = root.contextInitialAnimationSettings
              if (root.contextInitialPneumaticSettings !== undefined) _initialPneumaticValue = root.contextInitialPneumaticSettings
              if (root.contextInitialSimulationSettings !== undefined) _initialSimulationValue = root.contextInitialSimulationSettings
              if (root.contextInitialCylinderSettings !== undefined) _initialCylinderValue = root.contextInitialCylinderSettings
          }

        onSimulationControlRequested: function(command) { root.simulationControlRequested(command) }
        onModesPresetSelected: function(presetId) { root.modesPresetSelected(presetId) }
        onModesModeChanged: function(modeType, newMode) { root.modesModeChanged(modeType, newMode) }
        onModesPhysicsChanged: function(payload) { root.modesPhysicsChanged(payload) }
        onModesAnimationChanged: function(payload) { root.modesAnimationChanged(payload) }
        onPneumaticSettingsChanged: function(payload) { root.pneumaticSettingsChanged(payload) }
        onSimulationSettingsChanged: function(payload) { root.simulationSettingsChanged(payload) }
        onCylinderSettingsChanged: function(payload) { root.cylinderSettingsChanged(payload) }
        onAccordionPresetActivated: function(panelId, presetId) {
            root.accordionPresetActivated(panelId, presetId)
        }
        onAccordionFieldCommitted: function(panelId, field, value) {
            root.accordionFieldCommitted(panelId, field, value)
        }
        onAccordionValidationChanged: function(panelId, field, state, message) {
            root.accordionValidationChanged(panelId, field, state, message)
        }
    }

      Training.TrainingPanel {
          id: trainingPanel
          anchors.top: parent.top
          anchors.right: parent.right
          anchors.margins: 16
          visible: root.showTrainingPresets && root.contextTrainingBridge !== null
          z: 9000
          opacity: 0.96
          onPresetActivated: function(presetId) {
              console.log("Training preset selected", presetId)
          }
      }

      Components.TelemetryChartPanel {
          id: telemetryPanel
          anchors.left: root.parent ? root.parent.left : undefined
          anchors.bottom: root.parent ? root.parent.bottom : undefined
          anchors.margins: 16
          telemetryBridge: root.contextTelemetryBridge
          visible: root.telemetryPanelVisible && telemetryBridge !== null
      }
  }
