import QtQuick
import QtQuick3D

/*
 * Frame Component - U-shaped frame (3 beams)
 * Extracted from main.qml for modular QML architecture
 *
 * Constructs a U-frame with:
 * - Bottom horizontal beam (along Z axis)
 * - Front vertical beam (at front end)
 * - Rear vertical beam (at rear end)
 */
Node {
    id: frame

    // ===============================================================
    // REQUIRED PROPERTIES
    // ===============================================================

    required property Node worldRoot
    required property real beamSizeM // m - cross-section size
    required property real frameHeightM // m - height of vertical beams
    required property real frameLengthM // m - length along Z axis
    required property var frameMaterial

    // ===============================================================
    // FRAME GEOMETRY (3 beams forming U-shape)
    // Центрируем U-раму относительно нуля координат по оси Z.
    // Нижняя балка проходит от -L/2 до +L/2, стойки на концах.
    // ===============================================================

    // 1. BOTTOM BEAM (horizontal, along Z axis) — центр по Z в 0
    Model {
        parent: worldRoot
        source: "#Cube"
        position: Qt.vector3d(0, beamSizeM /2,0)
        scale: Qt.vector3d(beamSizeM, beamSizeM, frameLengthM)
        materials: [frameMaterial]
    }

    // 2. FRONT VERTICAL BEAM (at Z = -frameLength/2 + beamSize/2)
    Model {
        parent: worldRoot
        source: "#Cube"
        position: Qt.vector3d(0, beamSizeM + frameHeightM /2, -frameLengthM /2 + beamSizeM /2)
        scale: Qt.vector3d(beamSizeM, frameHeightM, beamSizeM)
        materials: [frameMaterial]
    }

    // 3. REAR VERTICAL BEAM (at Z = +frameLength/2 - beamSize/2)
    Model {
        parent: worldRoot
        source: "#Cube"
        position: Qt.vector3d(0, beamSizeM + frameHeightM /2, frameLengthM /2 - beamSizeM /2)
        scale: Qt.vector3d(beamSizeM, frameHeightM, beamSizeM)
        materials: [frameMaterial]
    }

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    Component.onCompleted: {
        console.log("🏗️ Frame initialized (centered): " + beamSizeM.toFixed(3) + " × " + frameHeightM.toFixed(3) + " × " + frameLengthM.toFixed(3) + " m")
    }
}
