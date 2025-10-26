import QtQuick 6.10
import QtQuick3D 6.10
import PneumoStabSim 1.0

SimulationRoot {
    id: root
    anchors.fill: parent
    sceneBridge: pythonSceneBridge
    Component.onCompleted: {
        if (typeof sceneBridge === "undefined" || sceneBridge === null) {
            console.error(
                "SimulationRoot ожидает pythonSceneBridge из контекста, но получил null."
            )
        }
    }
}
