import QtQuick6.10
import QtQuick.Controls6.10
import PneumoStabSim1.0
import "./"

Item {
 id: root
 anchors.fill: parent

 readonly property bool hasSceneBridge: typeof pythonSceneBridge !== "undefined" && pythonSceneBridge !== null

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
 console.error("Failed to load SimulationRoot:", errorString())
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
}
