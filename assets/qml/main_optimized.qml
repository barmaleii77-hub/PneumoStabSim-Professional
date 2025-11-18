import QtQuick 6.10
import QtQuick3D 6.10
import QtQuick.Controls 6.10
import PneumoStabSim 1.0
import "./"
import "./components"

Item {
    id: root
    anchors.fill: parent

    readonly property bool hasSceneBridge: typeof pythonSceneBridge !== "undefined" && pythonSceneBridge !== null

    // Lightweight IBL probe wiring for diagnostics and compatibility checks
    readonly property bool iblTextureReady: iblProbeLoader && iblProbeLoader.probe
    readonly property alias lightProbe: iblProbeLoader.probe

    Loader {
        id: simulationLoader
        anchors.fill: parent
        active: root.hasSceneBridge
        sourceComponent: SimulationRoot {
            id: simulationRoot
            sceneBridge: pythonSceneBridge
        }

        onStatusChanged: {
            if (status === Loader.Error) {
                console.error("Failed to load SimulationRoot (optimized):", errorString())
                fallbackLoader.active = true
            }
        }
    }

    Loader {
        id: fallbackLoader
        anchors.fill: parent
        active: !root.hasSceneBridge
        sourceComponent: SimulationFallbackRoot {}
    }

    Loader {
        id: iblLoaderHost
        active: false
        sourceComponent: IblProbeLoader {
            id: iblProbeLoader
            primarySource: ""
        }
    }
}
