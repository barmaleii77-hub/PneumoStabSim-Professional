import QtQuick 6.10
import QtQuick.Controls 6.10
import PneumoStabSim 1.0
import "./"

Item {
    id: root
    anchors.fill: parent

    signal batchUpdatesApplied(var summary)
    signal animationToggled(bool running)

    property var pendingPythonUpdates: ({})
    property var _queuedBatchedUpdates: []

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

    property bool environmentSsaoEnabled: true
    property real environmentSsaoRadius: 0.008
    property real environmentSsaoIntensity: 1.0
    property real environmentSsaoSoftness: 20.0
    property bool environmentSsaoDither: true
    property int environmentSsaoSampleRate: 4

    property bool environmentBloomEnabled: true
    property real environmentBloomIntensity: 0.5
    property real environmentBloomThreshold: 1.0
    property real environmentBloomSpread: 0.65
    property real environmentBloomGlowStrength: 1.0
    property bool environmentBloomQualityHigh: true
    property bool environmentBloomUseBicubic: true
    property real environmentBloomHdrMaximum: 8.0
    property real environmentBloomHdrScale: 2.0

    property bool environmentLensFlareEnabled: false
    property int environmentLensFlareGhostCount: 4
    property real environmentLensFlareGhostDispersal: 0.06
    property real environmentLensFlareHaloWidth: 0.05
    property real environmentLensFlareBloomBias: 1.0
    property real environmentLensFlareStretch: 0.0

    property bool environmentDepthOfFieldEnabled: false
    property bool environmentDofAutoFocus: true
    property real environmentDofFocusDistance: 2.5
    property real environmentDofFocusRange: 0.9
    property real environmentDofBlurAmount: 4.0

    property bool environmentFogEnabled: true
    property color environmentFogColor: "#aab9cf"
    property real environmentFogDensity: 0.06
    property real environmentFogNear: 2.0
    property real environmentFogFar: 20.0
    property bool environmentFogHeightEnabled: false
    property real environmentFogLeastIntenseY: 0.0
    property real environmentFogMostIntenseY: 3.0
    property real environmentFogHeightCurve: 1.0
    property bool environmentFogTransmitEnabled: true
    property real environmentFogTransmitCurve: 1.0

    property bool environmentVignetteEnabled: false
    property real environmentVignetteStrength: 0.35
    property real environmentVignetteRadius: 0.5

    property real environmentAdjustmentBrightness: 0.0
    property real environmentAdjustmentContrast: 0.0
    property real environmentAdjustmentSaturation: 0.0

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

        ssaoEnabled: root.environmentSsaoEnabled
        ssaoRadius: root.environmentSsaoRadius
        ssaoIntensity: root.environmentSsaoIntensity
        ssaoSoftness: root.environmentSsaoSoftness
        ssaoDither: root.environmentSsaoDither
        ssaoSampleRate: root.environmentSsaoSampleRate

        bloomEnabled: root.environmentBloomEnabled
        bloomIntensity: root.environmentBloomIntensity
        bloomThreshold: root.environmentBloomThreshold
        bloomSpread: root.environmentBloomSpread
        bloomGlowStrength: root.environmentBloomGlowStrength
        bloomQualityHigh: root.environmentBloomQualityHigh
        bloomUseBicubicUpscale: root.environmentBloomUseBicubic
        bloomHdrMaximum: root.environmentBloomHdrMaximum
        bloomHdrScale: root.environmentBloomHdrScale

        internalLensFlareEnabled: root.environmentLensFlareEnabled
        lensFlareGhostCountValue: root.environmentLensFlareGhostCount
        lensFlareGhostDispersalValue: root.environmentLensFlareGhostDispersal
        lensFlareHaloWidthValue: root.environmentLensFlareHaloWidth
        lensFlareBloomBiasValue: root.environmentLensFlareBloomBias
        lensFlareStretchValue: root.environmentLensFlareStretch

        internalDepthOfFieldEnabled: root.environmentDepthOfFieldEnabled
        depthOfFieldAutoFocus: root.environmentDofAutoFocus
        dofFocusDistance: root.environmentDofFocusDistance
        dofFocusRange: root.environmentDofFocusRange
        dofBlurAmount: root.environmentDofBlurAmount

        fogEnabled: root.environmentFogEnabled
        fogColor: root.environmentFogColor
        fogDensity: root.environmentFogDensity
        fogNear: root.environmentFogNear
        fogFar: root.environmentFogFar
        fogHeightEnabled: root.environmentFogHeightEnabled
        fogLeastIntenseY: root.environmentFogLeastIntenseY
        fogMostIntenseY: root.environmentFogMostIntenseY
        fogHeightCurve: root.environmentFogHeightCurve
        fogTransmitEnabled: root.environmentFogTransmitEnabled
        fogTransmitCurve: root.environmentFogTransmitCurve

        internalVignetteEnabled: root.environmentVignetteEnabled
        internalVignetteStrength: root.environmentVignetteStrength
        vignetteRadiusValue: root.environmentVignetteRadius

        adjustmentBrightnessValue: root.environmentAdjustmentBrightness
        adjustmentContrastValue: root.environmentAdjustmentContrast
        adjustmentSaturationValue: root.environmentAdjustmentSaturation
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
        active: root.hasSceneBridge
        sourceComponent: SimulationRoot {
            id: simulationRoot
            sceneBridge: pythonSceneBridge
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
}
