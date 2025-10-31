import QtQuick 6.10
import QtQuick.Controls 6.10
import PneumoStabSim 1.0
import "./"

Item {
    id: root
    anchors.fill: parent

    signal batchUpdatesApplied(var summary)
    signal animationToggled(bool running)

    readonly property bool hasSceneBridge: typeof pythonSceneBridge !== "undefined" && pythonSceneBridge !== null

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
