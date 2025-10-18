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
    required property real beamSize       // mm - cross-section size
    required property real frameHeight    // mm - height of vertical beams
    required property real frameLength    // mm - length along Z axis
    required property var frameMaterial
    
    // ===============================================================
    // FRAME GEOMETRY (3 beams forming U-shape)
    // ===============================================================
    
    // 1. BOTTOM BEAM (horizontal, along Z axis)
    Model {
        parent: worldRoot
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, frameLength/2)
        scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100)
        materials: [frameMaterial]
    }
    
    // 2. FRONT VERTICAL BEAM (at Z = beamSize/2)
    Model {
        parent: worldRoot
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, beamSize/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: [frameMaterial]
    }
    
    // 3. REAR VERTICAL BEAM (at Z = frameLength - beamSize/2)
    Model {
        parent: worldRoot
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, frameLength - beamSize/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: [frameMaterial]
    }
    
    // ===============================================================
    // INITIALIZATION
    // ===============================================================
    
    Component.onCompleted: {
        console.log("🏗️ Frame initialized: " + beamSize + " × " + frameHeight + " × " + frameLength + " mm")
    }
}
