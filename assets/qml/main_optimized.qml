import QtQuick 6.10
import QtQuick3D 6.10
import PneumoStabSim 1.0

// Optimised entry point that mirrors the primary SimulationRoot but allows
// Python to request this file explicitly when forcing the optimised layout.
SimulationRoot {
    id: root
    anchors.fill: parent
    sceneBridge: pythonSceneBridge
}
