import QtQuick 6.10
import QtQuick.Controls 6.10
import PneumoStabSim 1.0
import "./"
import "training" as Training
import components 1.0 as Components

Item {
    id: root
    anchors.fill: parent

    signal batchUpdatesApplied(var summary)
    signal animationToggled(bool running)

    property var pendingPythonUpdates: ({})
    property var _queuedBatchedUpdates: []
    property bool showTrainingPresets: true
    property bool telemetryPanelVisible: true

    readonly property bool hasSceneBridge: typeof pythonSceneBridge !== "undefined" && pythonSceneBridge !== null

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
    property string environmentOitMode: "weighted"

    property bool environmentTonemapEnabled: false
    property string environmentTonemapMode: "filmic"
    property real environmentTonemapExposure: 1.0
    property real environmentTonemapWhitePoint: 1.0

    // SSAO properties
    property bool ssaoEnabled: true
    property real ssaoRadius: 0.008
    property real ssaoIntensity: 1.0
    property real ssaoSoftness: 20.0
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
    property color fogColor: "#aab9cf"
    property real fogDensity: 0.06
    property real fogDepthNear: 2.0
    property real fogDepthFar: 20.0
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

    property real adjustmentBrightnessValue: 0.0
    property real adjustmentContrastValue: 0.0
    property real adjustmentSaturationValue: 0.0

    SceneEnvironmentController {
        id: environmentDefaults
        objectName: "environmentDefaults"

        sceneScaleFactor: root.environmentSceneScaleFactor

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
        oitMode: root.environmentOitMode

        tonemapActive: root.environmentTonemapEnabled
        tonemapModeName: root.environmentTonemapMode
        tonemapExposure: root.environmentTonemapExposure
        tonemapWhitePoint: root.environmentTonemapWhitePoint

        ssaoEnabled: root.ssaoEnabled
        ssaoRadius: root.ssaoRadius
        ssaoIntensity: root.ssaoIntensity
        ssaoSoftness: root.ssaoSoftness
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
        fogNear: root.fogDepthNear
        fogFar: root.fogDepthFar
        fogHeightEnabled: root.fogHeightEnabled
        fogLeastIntenseY: root.fogLeastIntenseY
        fogMostIntenseY: root.fogMostIntenseY
        fogHeightCurve: root.fogHeightCurve
        fogTransmitEnabled: root.fogTransmitEnabled
        fogTransmitCurve: root.fogTransmitCurve

        vignetteEnabled: root.vignetteActive
        vignetteStrength: root.vignetteStrengthValue
        vignetteRadius: root.vignetteRadiusValue

        colorAdjustmentsEnabled: true
        adjustmentBrightness: root.adjustmentBrightnessValue
        adjustmentContrast: root.adjustmentContrastValue
        adjustmentSaturation: root.adjustmentSaturationValue
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

    readonly property var _proxyMethodNames: [
        "applyGeometryUpdates",
        "updateGeometry",
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

    Component.onCompleted: {
        for (var i = 0; i < _proxyMethodNames.length; ++i) {
            var methodName = _proxyMethodNames[i]
            if (typeof root[methodName] !== "function") {
                root[methodName] = _createProxyMethod(methodName)
            }
        }
    }

    Loader {
        id: simulationLoader
        objectName: "simulationLoader"
        anchors.fill: parent
        active: true
        sourceComponent: SimulationRoot {
            id: simulationRoot
            sceneBridge: root.hasSceneBridge ? pythonSceneBridge : null
        }
        onStatusChanged: {
            if (status === Loader.Error) {
                console.error("Failed to load SimulationRoot:", errorString())
                fallbackLoader.active = true
            }
            if (status === Loader.Ready) {
                _flushQueuedBatches()
            }
        }
        onLoaded: {
            if (item && item.batchUpdatesApplied) {
                item.batchUpdatesApplied.connect(root.batchUpdatesApplied)
            }
            if (item && item.animationToggled) {
                item.animationToggled.connect(root.animationToggled)
            }
        }
    }

    Loader {
        id: fallbackLoader
        objectName: "fallbackLoader"
        anchors.fill: parent
        active: !root.hasSceneBridge
        sourceComponent: SimulationFallbackRoot {}
        onStatusChanged: {
            if (status === Loader.Ready) {
                _flushQueuedBatches()
            }
        }
        onLoaded: {
            if (item && item.batchUpdatesApplied) {
                item.batchUpdatesApplied.connect(root.batchUpdatesApplied)
            }
            if (item && item.animationToggled) {
                item.animationToggled.connect(root.animationToggled)
            }
        }
    }

    Training.TrainingPanel {
        id: trainingPanel
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 16
        visible: root.showTrainingPresets && typeof trainingBridge !== "undefined" && trainingBridge !== null
        z: 9000
        opacity: 0.96
        onPresetActivated: function(presetId) {
            console.log("Training preset selected", presetId)
        }
    }

    Components.TelemetryChartPanel {
        id: telemetryPanel
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 16
        telemetryBridge: typeof pythonTelemetryBridge !== "undefined" ? pythonTelemetryBridge : null
        visible: root.telemetryPanelVisible
            && telemetryBridge !== null
    }
}
