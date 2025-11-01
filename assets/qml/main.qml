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

    function applyGeometryUpdates(params) { return _invokeOnActiveRoot("applyGeometryUpdates", params) }
    function updateGeometry(params) { return _invokeOnActiveRoot("updateGeometry", params) }
    function applyAnimationUpdates(params) { return _invokeOnActiveRoot("applyAnimationUpdates", params) }
    function updateAnimation(params) { return _invokeOnActiveRoot("updateAnimation", params) }
    function applyLightingUpdates(params) { return _invokeOnActiveRoot("applyLightingUpdates", params) }
    function updateLighting(params) { return _invokeOnActiveRoot("updateLighting", params) }
    function applyMaterialUpdates(params) { return _invokeOnActiveRoot("applyMaterialUpdates", params) }
    function updateMaterials(params) { return _invokeOnActiveRoot("updateMaterials", params) }
    function applyEnvironmentUpdates(params) { return _invokeOnActiveRoot("applyEnvironmentUpdates", params) }
    function updateEnvironment(params) { return _invokeOnActiveRoot("updateEnvironment", params) }
    function applyQualityUpdates(params) { return _invokeOnActiveRoot("applyQualityUpdates", params) }
    function updateQuality(params) { return _invokeOnActiveRoot("updateQuality", params) }
    function applyCameraUpdates(params) { return _invokeOnActiveRoot("applyCameraUpdates", params) }
    function updateCamera(params) { return _invokeOnActiveRoot("updateCamera", params) }
    function applyEffectsUpdates(params) { return _invokeOnActiveRoot("applyEffectsUpdates", params) }
    function updateEffects(params) { return _invokeOnActiveRoot("updateEffects", params) }
    function applySimulationUpdates(params) { return _invokeOnActiveRoot("applySimulationUpdates", params) }
    function applyThreeDUpdates(params) { return _invokeOnActiveRoot("applyThreeDUpdates", params) }
    function apply3DUpdates(params) { return _invokeOnActiveRoot("apply3DUpdates", params) }
    function applyRenderSettings(params) { return _invokeOnActiveRoot("applyRenderSettings", params) }

    Component.onCompleted: _flushQueuedBatches()

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
            _flushQueuedBatches()
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
            _flushQueuedBatches()
        }
    }
}
