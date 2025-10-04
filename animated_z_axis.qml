
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    // Animation properties
    property real animationTime: 0.0
    property real animationSpeed: 1.5

    // 2-meter suspension system coordinates
    property real beamSize: 120
    property real frameHeight: 650
    property real frameLength: 2000

    // Animated lever angles (sine waves with different phases)
    property real fl_angle: 10 * Math.sin(animationTime)
    property real fr_angle: 10 * Math.sin(animationTime + Math.PI/3)
    property real rl_angle: 10 * Math.sin(animationTime + 2*Math.PI/3)
    property real rr_angle: 10 * Math.sin(animationTime + Math.PI)

    // Base coordinates
    property vector3d fl_j_arm_base: Qt.vector3d(-150, 60, -1000)
    property vector3d fr_j_arm_base: Qt.vector3d(150, 60, -1000)
    property vector3d rl_j_arm_base: Qt.vector3d(-150, 60, 1000)
    property vector3d rr_j_arm_base: Qt.vector3d(150, 60, 1000)

    property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)
    property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)
    property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)
    property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)

    // Animated rod positions (70% along 450mm lever from pivot)
    property real leverLength: 450
    property real attachFrac: 0.7
    
    property vector3d fl_j_rod: Qt.vector3d(
        fl_j_arm_base.x + leverLength * attachFrac * Math.cos(fl_angle * Math.PI / 180),
        fl_j_arm_base.y + leverLength * attachFrac * Math.sin(fl_angle * Math.PI / 180),
        fl_j_arm_base.z
    )
    property vector3d fr_j_rod: Qt.vector3d(
        fr_j_arm_base.x + leverLength * attachFrac * Math.cos(fr_angle * Math.PI / 180),
        fr_j_arm_base.y + leverLength * attachFrac * Math.sin(fr_angle * Math.PI / 180),
        fr_j_arm_base.z
    )
    property vector3d rl_j_rod: Qt.vector3d(
        rl_j_arm_base.x + leverLength * attachFrac * Math.cos(rl_angle * Math.PI / 180),
        rl_j_arm_base.y + leverLength * attachFrac * Math.sin(rl_angle * Math.PI / 180),
        rl_j_arm_base.z
    )
    property vector3d rr_j_rod: Qt.vector3d(
        rr_j_arm_base.x + leverLength * attachFrac * Math.cos(rr_angle * Math.PI / 180),
        rr_j_arm_base.y + leverLength * attachFrac * Math.sin(rr_angle * Math.PI / 180),
        rr_j_arm_base.z
    )

    // Camera
    property real cameraDistance: 3500
    property real cameraPitch: -25
    property real cameraYaw: 35

    // Animation timer
    Timer {
        running: true
        interval: 16  // ~60 FPS
        repeat: true
        onTriggered: {
            animationTime += animationSpeed * 0.016  // 16ms timestep
        }
    }

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

    // ANIMATED SUSPENSION COMPONENT WITH Z-AXIS JOINTS
    component AnimatedSuspensionCorner: Node {
        property vector3d j_arm_base
        property vector3d j_tail  
        property vector3d j_rod
        property real leverAngle
        
        // Animated lever (rotates with angle)
        Model {
            source: "#Cube"
            position: Qt.vector3d((j_arm_base.x + j_rod.x)/2, (j_arm_base.y + j_rod.y)/2, j_arm_base.z)
            scale: Qt.vector3d(leverLength/100, 0.8, 0.8)
            eulerRotation: Qt.vector3d(0, 0, leverAngle)
            materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
        }
        
        // FIXED CYLINDER (250mm)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real fixedCylLength: 250
            property vector3d cylEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (fixedCylLength / cylDirectionLength),
                j_tail.y + cylDirection.y * (fixedCylLength / cylDirectionLength),
                j_tail.z
            )
            
            position: Qt.vector3d((j_tail.x + cylEnd.x)/2, (j_tail.y + cylEnd.y)/2, j_tail.z)
            scale: Qt.vector3d(1.2, fixedCylLength/100, 1.2)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylEnd.y - j_tail.y, cylEnd.x - j_tail.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.15; alphaMode: PrincipledMaterial.Blend }
        }
        
        // ANIMATED PISTON (moves with rod extension)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real fixedCylLength: 250
            property real rodExtension: cylDirectionLength - fixedCylLength
            property real pistonPositionRatio: Math.max(0.0, Math.min(1.0, rodExtension / 200.0))
            
            property vector3d pistonPos: Qt.vector3d(
                j_tail.x + cylDirection.x * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
                j_tail.y + cylDirection.y * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
                j_tail.z
            )
            
            position: pistonPos
            scale: Qt.vector3d(1.1, 1.2, 1.1)  // Thick visible disc
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ff3333"; metalness: 0.8; roughness: 0.2 }
        }
        
        // ANIMATED ROD (extends/retracts from piston)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real fixedCylLength: 250
            property real rodExtension: cylDirectionLength - fixedCylLength
            property real pistonPositionRatio: Math.max(0.0, Math.min(1.0, rodExtension / 200.0))
            
            property vector3d rodStart: Qt.vector3d(
                j_tail.x + cylDirection.x * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
                j_tail.y + cylDirection.y * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
                j_tail.z
            )
            
            position: Qt.vector3d((rodStart.x + j_rod.x)/2, (rodStart.y + j_rod.y)/2, j_rod.z)
            scale: Qt.vector3d(0.3, Math.hypot(j_rod.x - rodStart.x, j_rod.y - rodStart.y, 0)/100, 0.3)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - rodStart.y, j_rod.x - rodStart.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.9; roughness: 0.1 }
        }
        
        // Z-AXIS CYLINDRICAL JOINTS (CORRECTLY ORIENTED)
        
        // Tail joint - ANIMATED with slight oscillation
        Model {
            source: "#Cylinder"
            position: j_tail
            scale: Qt.vector3d(2.4, 2.4, 1.2)
            eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.1)  // Slight rotation with lever motion
            materials: PrincipledMaterial { baseColor: "#333333"; metalness: 0.9; roughness: 0.2 }
        }
        
        // Arm joint - ANIMATED rotation
        Model {
            source: "#Cylinder"
            position: j_arm_base
            scale: Qt.vector3d(2.0, 2.0, 1.0)
            eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.2)  // Follows lever rotation
            materials: PrincipledMaterial { baseColor: "#555555"; metalness: 0.9; roughness: 0.2 }
        }
        
        // Rod joint - ANIMATED with lever
        Model {
            source: "#Cylinder"
            position: j_rod
            scale: Qt.vector3d(1.6, 1.6, 0.8)
            eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.3)  // More rotation at rod end
            materials: PrincipledMaterial { baseColor: "#777777"; metalness: 0.8; roughness: 0.3 }
        }
    }

    // Four animated suspension corners
    AnimatedSuspensionCorner { j_arm_base: fl_j_arm_base; j_tail: fl_j_tail; j_rod: fl_j_rod; leverAngle: fl_angle }
    AnimatedSuspensionCorner { j_arm_base: fr_j_arm_base; j_tail: fr_j_tail; j_rod: fr_j_rod; leverAngle: fr_angle }
    AnimatedSuspensionCorner { j_arm_base: rl_j_arm_base; j_tail: rl_j_tail; j_rod: rl_j_rod; leverAngle: rl_angle }
    AnimatedSuspensionCorner { j_arm_base: rr_j_arm_base; j_tail: rr_j_tail; j_rod: rr_j_rod; leverAngle: rr_angle }

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
        console.log("=== ANIMATED Z-AXIS CYLINDRICAL JOINTS ===")
        console.log("? Levers rotate with sine wave animation")
        console.log("? Pistons move inside transparent cylinders")
        console.log("? Rods extend/retract correctly")
        console.log("? Joints oriented along Z-axis with eulerRotation(90,0,0)")
        console.log("? Joints animate slightly with lever motion")
        view3d.forceActiveFocus()
    }
}
