
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    // 2-meter suspension system coordinates - CORRECT ANGLES!
    property real beamSize: 120
    property real frameHeight: 650
    property real frameLength: 2000

    // Lever joints (300mm apart)
    property vector3d fl_j_arm: Qt.vector3d(-150, 60, -1000)
    property vector3d fr_j_arm: Qt.vector3d(150, 60, -1000)
    property vector3d rl_j_arm: Qt.vector3d(-150, 60, 1000)
    property vector3d rr_j_arm: Qt.vector3d(150, 60, 1000)

    // Cylinder tail joints (200mm apart)
    property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)
    property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)
    property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)
    property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)

    // Rod attachments (horizontal levers)
    property vector3d fl_j_rod: Qt.vector3d(-465, 60, -1000)
    property vector3d fr_j_rod: Qt.vector3d(465, 60, -1000)
    property vector3d rl_j_rod: Qt.vector3d(-465, 60, 1000)
    property vector3d rr_j_rod: Qt.vector3d(465, 60, 1000)

    // Camera
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

    // Origin marker
    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        scale: Qt.vector3d(3.0, 3.0, 3.0)
        materials: PrincipledMaterial { baseColor: "#ffff00"; lighting: PrincipledMaterial.NoLighting }
    }

    // U-Frame
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, 0)
        scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, -1000)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, 1000)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // FL Suspension - CORRECTED MECHANICS
    // LEVER - should be HORIZONTAL (0 degrees) in base position
    Model {
        source: "#Cube"
        position: Qt.vector3d((fl_j_arm.x + fl_j_rod.x)/2, (fl_j_arm.y + fl_j_rod.y)/2, fl_j_arm.z)
        scale: Qt.vector3d(Math.hypot(fl_j_rod.x - fl_j_arm.x, fl_j_rod.y - fl_j_arm.y, 0)/100, 0.8, 0.8)
        eulerRotation: Qt.vector3d(0, 0, 0)  // HORIZONTAL - no rotation needed for base position
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }
    
    // FIXED CYLINDER (250mm from tail toward rod)
    Model {
        source: "#Cylinder"
        property vector3d cylDirection: Qt.vector3d(fl_j_rod.x - fl_j_tail.x, fl_j_rod.y - fl_j_tail.y, 0)
        property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
        property real fixedCylLength: 250
        property vector3d cylEnd: Qt.vector3d(
            fl_j_tail.x + cylDirection.x * (fixedCylLength / cylDirectionLength),
            fl_j_tail.y + cylDirection.y * (fixedCylLength / cylDirectionLength),
            fl_j_tail.z
        )
        
        position: Qt.vector3d((fl_j_tail.x + cylEnd.x)/2, (fl_j_tail.y + cylEnd.y)/2, fl_j_tail.z)
        
        property real cylAngle: Math.atan2(cylEnd.y - fl_j_tail.y, cylEnd.x - fl_j_tail.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(1.2, fixedCylLength/100, 1.2)
        eulerRotation: Qt.vector3d(0, 0, cylAngle)
        materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.3; alphaMode: PrincipledMaterial.Blend }
    }
    
    // VISIBLE PISTON (INSIDE cylinder at fixed position for now)
    Model {
        source: "#Cylinder"
        property vector3d cylDirection: Qt.vector3d(fl_j_rod.x - fl_j_tail.x, fl_j_rod.y - fl_j_tail.y, 0)
        property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
        property real fixedCylLength: 250
        
        // Piston at 60% along cylinder axis from tail
        property vector3d pistonPos: Qt.vector3d(
            fl_j_tail.x + cylDirection.x * ((fixedCylLength * 0.6) / cylDirectionLength),
            fl_j_tail.y + cylDirection.y * ((fixedCylLength * 0.6) / cylDirectionLength),
            fl_j_tail.z
        )
        
        position: pistonPos
        
        property real pistonAngle: Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(1.0, 0.8, 1.0)  // Thick visible disc
        eulerRotation: Qt.vector3d(0, 0, pistonAngle)
        materials: PrincipledMaterial { baseColor: "#ff0000"; metalness: 0.8; roughness: 0.2 }  // BRIGHT RED
    }
    
    // ROD (from cylinder end to j_rod)
    Model {
        source: "#Cylinder"
        property vector3d cylDirection: Qt.vector3d(fl_j_rod.x - fl_j_tail.x, fl_j_rod.y - fl_j_tail.y, 0)
        property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
        property real fixedCylLength: 250
        property vector3d rodStart: Qt.vector3d(
            fl_j_tail.x + cylDirection.x * (fixedCylLength / cylDirectionLength),
            fl_j_tail.y + cylDirection.y * (fixedCylLength / cylDirectionLength),
            fl_j_tail.z
        )
        
        position: Qt.vector3d((rodStart.x + fl_j_rod.x)/2, (rodStart.y + fl_j_rod.y)/2, fl_j_rod.z)
        
        property real rodLength: Math.hypot(fl_j_rod.x - rodStart.x, fl_j_rod.y - rodStart.y, 0)
        property real rodAngle: Math.atan2(fl_j_rod.y - rodStart.y, fl_j_rod.x - rodStart.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(0.3, rodLength/100, 0.3)
        eulerRotation: Qt.vector3d(0, 0, rodAngle)
        materials: PrincipledMaterial { baseColor: "#bbbbbb"; metalness: 0.9; roughness: 0.1 }
    }
    
    // Attachments
    Model { source: "#Sphere"; position: fl_j_tail; scale: Qt.vector3d(1.8, 1.8, 1.8); materials: PrincipledMaterial { baseColor: "#666666"; metalness: 0.8; roughness: 0.3 } }
    Model { source: "#Sphere"; position: fl_j_arm; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#ffaa00"; metalness: 0.8; roughness: 0.3 } }

    // Markers for reference
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

    // Mouse control
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
        console.log("=== FIXED 2-METER SUSPENSION SYSTEM ===")
        console.log("Lever spacing:", Math.abs(fr_j_arm.x - fl_j_arm.x) + "mm")
        console.log("Tail spacing:", Math.abs(fr_j_tail.x - fl_j_tail.x) + "mm")
        console.log("Plane spacing:", Math.abs(rl_j_arm.z - fl_j_arm.z) + "mm")
        
        // ANGLE DEBUG
        var fl_angle = Math.atan2(fl_j_rod.y - fl_j_arm.y, fl_j_rod.x - fl_j_arm.x) * 180 / Math.PI
        console.log("FL angle should be 180deg (horizontal left):", fl_angle)
        
        var fr_angle = Math.atan2(fr_j_rod.y - fr_j_arm.y, fr_j_rod.x - fr_j_arm.x) * 180 / Math.PI
        console.log("FR angle should be 0deg (horizontal right):", fr_angle)
        
        console.log("PISTON should be BRIGHT RED and visible inside transparent cylinder!")
        
        view3d.forceActiveFocus()
    }
}
