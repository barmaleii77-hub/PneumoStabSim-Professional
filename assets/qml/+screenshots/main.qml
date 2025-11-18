import QtQuick 6.10
import "./Panels" as Panels

Item {
    id: root
    width: 640
    height: 360

    signal batchUpdatesApplied(var summary)
    signal animationToggled(bool running)

    property var pendingPythonUpdates: ({})

    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates || typeof pendingPythonUpdates !== "object")
            return
        if (Object.keys(pendingPythonUpdates).length === 0)
            return
        applyBatchedUpdates(pendingPythonUpdates)
        pendingPythonUpdates = null
    }

    function applyBatchedUpdates(payload) {
        if (!payload || typeof payload !== "object")
            return false
        if (Object.keys(payload).length === 0)
            return false
        var categories = []
        if (payload.animation) {
            categories.push("animation")
            applyAnimationUpdates(payload.animation)
        }
        if (payload.simulation) {
            categories.push("simulation")
            applySimulationUpdates(payload.simulation)
        }
        if (payload.effects) {
            categories.push("effects")
        }
        if (categories.length)
            batchUpdatesApplied({ categories: categories })
        return true
    }

    function applyAnimationUpdates(payload) {
        simulationPanel.applyAnimationSettings(payload)
    }

    function applySimulationUpdates(payload) {
        simulationPanel.applySimulationSettings(payload)
    }

    Rectangle {
        anchors.fill: parent
        color: "#141821"
    }

    Panels.SimulationPanel {
        id: simulationPanel
        anchors.centerIn: root
    }
}
