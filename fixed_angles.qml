
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    property real beamSize: 120
    property real frameHeight: 650
    property real frameLength: 2000

    property vector3d fl_j_arm: Qt.vector3d(-150, 60, -1000)
    property vector3d fr_j_arm: Qt.vector3d(150, 60, -1000)
    property vector3d rl_j_arm: Qt.vector3d(-150, 60, 1000)
    property vector3d rr_j_arm: Qt.vector3d(150, 60, 1000)

    property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)
    property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)
    property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)
    property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)

    property vector3d fl_j_rod: Qt.vector3d(-465, 60, -1000)
    property vector3d fr_j_rod: Qt.vector3d(465, 60, -1000)
    property vector3d rl_j_rod: Qt.vector3d(-465, 60, 1000)
    property vector3d rr_j_rod: Qt.vector3d(465, 60, 1000)

    property real cameraDistance: 3000
    property real cameraPitch: -20
    property real cameraYaw: 30

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#f0f0f0"
        antialiasingMode: SceneEnvironment.MSAA
    }

    Node {
        id: rig
        position: Qt.vector3d(0, frameHeight/2, 0)
        eulerRotation: Qt.vector3d(cameraPitch, cameraYaw, 0)

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, cameraDistance)
            fieldOfView: 45
        }
    }

    DirectionalLight {
        eulerRotation.x: -30
        eulerRotation.y: -45
        brightness: 2.0
    }

    // Origin and Frame
    Model { source: "#Sphere"; position: Qt.vector3d(0, 0, 0); scale: Qt.vector3d(3.0, 3.0, 3.0); materials: PrincipledMaterial { baseColor: "#ffff00"; lighting: PrincipledMaterial.NoLighting } }
    
    Model { source: "#Cube"; position: Qt.vector3d(0, beamSize/2, 0); scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100); materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 } }
    Model { source: "#Cube"; position: Qt.vector3d(0, beamSize + frameHeight/2, -1000); scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100); materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 } }
    Model { source: "#Cube"; position: Qt.vector3d(0, beamSize + frameHeight/2, 1000); scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100); materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 } }

    // FL Suspension - SIMPLE CORRECT ORIENTATIONS
    Model {
        source: "#Cube"
        position: Qt.vector3d((fl_j_arm.x + fl_j_rod.x)/2, fl_j_arm.y, fl_j_arm.z)
        scale: Qt.vector3d(4.5, 0.8, 0.8)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }
    
    Model {
        id: flCylinder
        source: "#Cylinder"
        property vector3d start: Qt.vector3d(fl_j_tail.x, fl_j_tail.y - 100, fl_j_tail.z)
        property vector3d end: Qt.vector3d(fl_j_tail.x - 200, fl_j_tail.y - 200, fl_j_tail.z)
        position: Qt.vector3d((start.x + end.x)/2, (start.y + end.y)/2, start.z)
        
        property real len: Math.hypot(end.x - start.x, end.y - start.y, 0)
        property real angle: Math.atan2(end.y - start.y, end.x - start.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(1.0, len/100, 1.0)
        eulerRotation: Qt.vector3d(0, 0, angle)
        materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.6; alphaMode: PrincipledMaterial.Blend }
    }
    
    Model {
        source: "#Cylinder"
        property vector3d start: Qt.vector3d(fl_j_tail.x - 200, fl_j_tail.y - 200, fl_j_tail.z)
        property vector3d end: fl_j_rod
        position: Qt.vector3d((start.x + end.x)/2, (start.y + end.y)/2, start.z)
        
        property real len: Math.hypot(end.x - start.x, end.y - start.y, 0)
        property real angle: Math.atan2(end.y - start.y, end.x - start.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(0.4, len/100, 0.4)
        eulerRotation: Qt.vector3d(0, 0, angle)
        materials: PrincipledMaterial { baseColor: "#e6e6e6"; metalness: 1.0; roughness: 0.1 }
    }

    // FR Suspension - MIRROR
    Model {
        source: "#Cube"
        position: Qt.vector3d((fr_j_arm.x + fr_j_rod.x)/2, fr_j_arm.y, fr_j_arm.z)
        scale: Qt.vector3d(4.5, 0.8, 0.8)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }
    
    Model {
        source: "#Cylinder"
        property vector3d start: Qt.vector3d(fr_j_tail.x, fr_j_tail.y - 100, fr_j_tail.z)
        property vector3d end: Qt.vector3d(fr_j_tail.x + 200, fr_j_tail.y - 200, fr_j_tail.z)
        position: Qt.vector3d((start.x + end.x)/2, (start.y + end.y)/2, start.z)
        
        property real len: Math.hypot(end.x - start.x, end.y - start.y, 0)
        property real angle: Math.atan2(end.y - start.y, end.x - start.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(1.0, len/100, 1.0)
        eulerRotation: Qt.vector3d(0, 0, angle)
        materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.6; alphaMode: PrincipledMaterial.Blend }
    }
    
    Model {
        source: "#Cylinder"
        property vector3d start: Qt.vector3d(fr_j_tail.x + 200, fr_j_tail.y - 200, fr_j_tail.z)
        property vector3d end: fr_j_rod
        position: Qt.vector3d((start.x + end.x)/2, (start.y + end.y)/2, start.z)
        
        property real len: Math.hypot(end.x - start.x, end.y - start.y, 0)
        property real angle: Math.atan2(end.y - start.y, end.x - start.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(0.4, len/100, 0.4)
        eulerRotation: Qt.vector3d(0, 0, angle)
        materials: PrincipledMaterial { baseColor: "#e6e6e6"; metalness: 1.0; roughness: 0.1 }
    }

    // RL and RR similar...
    Model {
        source: "#Cube"
        position: Qt.vector3d((rl_j_arm.x + rl_j_rod.x)/2, rl_j_arm.y, rl_j_arm.z)
        scale: Qt.vector3d(4.5, 0.8, 0.8)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }

    Model {
        source: "#Cube"
        position: Qt.vector3d((rr_j_arm.x + rr_j_rod.x)/2, rr_j_arm.y, rr_j_arm.z)
        scale: Qt.vector3d(4.5, 0.8, 0.8)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }

    // Markers
    Model { source: "#Sphere"; position: fl_j_arm; scale: Qt.vector3d(2.0, 2.0, 2.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_arm; scale: Qt.vector3d(2.0, 2.0, 2.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_arm; scale: Qt.vector3d(2.0, 2.0, 2.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_arm; scale: Qt.vector3d(2.0, 2.0, 2.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    
    Model { source: "#Sphere"; position: fl_j_tail; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_tail; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_tail; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_tail; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    
    Model { source: "#Sphere"; position: fl_j_rod; scale: Qt.vector3d(1.2, 1.2, 1.2); materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_rod; scale: Qt.vector3d(1.2, 1.2, 1.2); materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_rod; scale: Qt.vector3d(1.2, 1.2, 1.2); materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_rod; scale: Qt.vector3d(1.2, 1.2, 1.2); materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting } }

    MouseArea {
        anchors.fill: parent
        property real lastX: 0; property real lastY: 0; property bool dragging: false
        onPressed: function(mouse) { lastX = mouse.x; lastY = mouse.y; dragging = true }
        onReleased: function(mouse) { dragging = false }
        onPositionChanged: function(mouse) {
            if (!dragging) return
            cameraYaw += (mouse.x - lastX) * 0.5
            cameraPitch -= (mouse.y - lastY) * 0.5
            cameraPitch = Math.max(-89, Math.min(89, cameraPitch))
            lastX = mouse.x; lastY = mouse.y
        }
        onWheel: function(wheel) {
            var factor = 1.0 + (wheel.angleDelta.y / 1200.0)
            cameraDistance *= factor
            cameraDistance = Math.max(500, Math.min(8000, cameraDistance))
        }
    }

    Component.onCompleted: {
        console.log("=== FIXED ANGLES TEST ===")
        console.log("FL cylinder angle should point from tail toward rod area")
        console.log("FR cylinder angle should mirror FL")
        view3d.forceActiveFocus()
    }
}
