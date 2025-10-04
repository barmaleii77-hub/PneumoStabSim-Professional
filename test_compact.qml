
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    // COMPACT coordinates centered at origin
    property real beamSize: 120
    property real frameHeight: 650
    property real frameLength: 1500

    // NEW PLANAR coordinates - all points in proper XY planes
    property vector3d fl_j_arm: Qt.vector3d(-80, 60, -150)    // ON BEAM AXIS (Y=60)
    property vector3d fr_j_arm: Qt.vector3d(80, 60, -150)     // ON BEAM AXIS (Y=60)
    property vector3d rl_j_arm: Qt.vector3d(-80, 60, 150)     // ON BEAM AXIS (Y=60)
    property vector3d rr_j_arm: Qt.vector3d(80, 60, 150)      // ON BEAM AXIS (Y=60)

    // Cylinder tail joints (where cylinders attach to frame) - CORRECTED HEIGHT
    property vector3d fl_j_tail: Qt.vector3d(-16, 710, -150)  // At horn height minus half beam section
    property vector3d fr_j_tail: Qt.vector3d(16, 710, -150)   // At horn height minus half beam section
    property vector3d rl_j_tail: Qt.vector3d(-16, 710, 150)   // At horn height minus half beam section
    property vector3d rr_j_tail: Qt.vector3d(16, 710, 150)    // At horn height minus half beam section

    // Camera
    property real cameraDistance: 800
    property real cameraPitch: -20
    property real cameraYaw: 30

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#f0f0f0"
        antialiasingMode: SceneEnvironment.MSAA
    }

    // Camera rig
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

    // Origin marker (0,0,0) - YELLOW
    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        scale: Qt.vector3d(3.0, 3.0, 3.0)
        materials: PrincipledMaterial {
            baseColor: "#ffff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }

    // U-FRAME with horns in SAME PLANES as suspension
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, 0)  // Bottom beam centered
        scale: Qt.vector3d(beamSize/100, beamSize/100, 300/100)  // Compact 300mm length
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // Front horn at Z = -150 (SAME as front suspension)
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, -150)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // Rear horn at Z = 150 (SAME as rear suspension)
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, 150)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // Lever joints (GREEN) - where levers attach to frame
    Model {
        source: "#Sphere"
        position: fl_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: fr_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rl_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rr_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
    }

    // Cylinder tail joints (BLUE) - where cylinders attach to frame
    Model {
        source: "#Sphere"
        position: fl_j_tail
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: fr_j_tail
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rl_j_tail
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rr_j_tail
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
    }

    // Mouse control
    MouseArea {
        anchors.fill: parent
        property real lastX: 0
        property real lastY: 0
        property bool dragging: false
        
        onPressed: function(mouse) {
            lastX = mouse.x; lastY = mouse.y; dragging = true
        }
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
            cameraDistance = Math.max(200, Math.min(3000, cameraDistance))
        }
    }

    Component.onCompleted: {
        console.log("=== COMPACT COORDINATES TEST ===")
        console.log("Origin (0,0,0) = YELLOW sphere")
        console.log("Frame centered at origin")
        console.log("Lever joints (GREEN):")
        console.log("  FL j_arm:", fl_j_arm)
        console.log("  FR j_arm:", fr_j_arm)
        console.log("Cylinder tail joints (BLUE):")
        console.log("  FL j_tail:", fl_j_tail)
        console.log("  FR j_tail:", fr_j_tail)
        
        var distance_arm = Math.hypot(fl_j_arm.x, fl_j_arm.y, fl_j_arm.z)
        var distance_tail = Math.hypot(fl_j_tail.x, fl_j_tail.y, fl_j_tail.z)
        
        console.log("Distances from origin:")
        console.log("  Lever joint:", distance_arm.toFixed(1) + "mm")
        console.log("  Cylinder tail:", distance_tail.toFixed(1) + "mm")
        
        if (distance_arm < 250 && distance_tail < 250) {
            console.log("? ALL COORDINATES ARE COMPACT!")
        } else {
            console.log("? SOME COORDINATES STILL TOO FAR!")
        }
        
        // Check planar alignment
        console.log("Planar alignment check:")
        console.log("  Front plane (Z=-150): FL_arm.z=" + fl_j_arm.z + ", FL_tail.z=" + fl_j_tail.z)
        console.log("  Rear plane (Z=150): RL_arm.z=" + rl_j_arm.z + ", RL_tail.z=" + rl_j_tail.z)
        
        view3d.forceActiveFocus()
    }
}
