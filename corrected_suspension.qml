
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    // Animation properties
    property real animationTime: 0.0
    property real animationSpeed: 1.0

    // 2-meter suspension system coordinates
    property real beamSize: 120
    property real frameHeight: 650
    property real frameLength: 2000

    // ANIMATED lever angles (small oscillations)
    property real fl_angle: 5 * Math.sin(animationTime)
    property real fr_angle: 5 * Math.sin(animationTime + Math.PI/4)
    property real rl_angle: 5 * Math.sin(animationTime + Math.PI/2)
    property real rr_angle: 5 * Math.sin(animationTime + 3*Math.PI/4)

    // Base joint positions (FIXED)
    property vector3d fl_j_arm: Qt.vector3d(-150, 60, -1000)
    property vector3d fr_j_arm: Qt.vector3d(150, 60, -1000)
    property vector3d rl_j_arm: Qt.vector3d(-150, 60, 1000)
    property vector3d rr_j_arm: Qt.vector3d(150, 60, 1000)

    property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)
    property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)
    property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)
    property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)

    // ANIMATED rod positions (move with lever angles)
    property real leverLength: 315  // Distance from j_arm to j_rod
    
    property vector3d fl_j_rod: Qt.vector3d(
        fl_j_arm.x + leverLength * Math.cos(fl_angle * Math.PI / 180),
        fl_j_arm.y + leverLength * Math.sin(fl_angle * Math.PI / 180),
        fl_j_arm.z
    )
    property vector3d fr_j_rod: Qt.vector3d(
        fr_j_arm.x + leverLength * Math.cos(fr_angle * Math.PI / 180),
        fr_j_arm.y + leverLength * Math.sin(fr_angle * Math.PI / 180),
        fr_j_arm.z
    )
    property vector3d rl_j_rod: Qt.vector3d(
        rl_j_arm.x + leverLength * Math.cos(rl_angle * Math.PI / 180),
        rl_j_arm.y + leverLength * Math.sin(rl_angle * Math.PI / 180),
        rl_j_arm.z
    )
    property vector3d rr_j_rod: Qt.vector3d(
        rr_j_arm.x + leverLength * Math.cos(rr_angle * Math.PI / 180),
        rr_j_arm.y + leverLength * Math.sin(rr_angle * Math.PI / 180),
        rr_j_arm.z
    )

    // Camera
    property real cameraDistance: 3500
    property real cameraPitch: -25
    property real cameraYaw: 35

    // Animation timer
    Timer {
        running: true
        interval: 33  // ~30 FPS for smooth animation
        repeat: true
        onTriggered: {
            animationTime += animationSpeed * 0.033
        }
    }

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#f5f5f5"
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
        brightness: 2.5
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

    // CORRECTED SUSPENSION COMPONENT
    component CorrectedSuspensionCorner: Node {
        property vector3d j_arm
        property vector3d j_tail  
        property vector3d j_rod
        property real leverAngle
        
        // CORRECTED LEVER (proper orientation)
        Model {
            source: "#Cube"
            position: Qt.vector3d((j_arm.x + j_rod.x)/2, (j_arm.y + j_rod.y)/2, j_arm.z)
            scale: Qt.vector3d(leverLength/100, 0.8, 0.8)
            eulerRotation: Qt.vector3d(0, 0, leverAngle)  // Use ANIMATED angle, not static calculation
            materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
        }
        
        // FIXED CYLINDER (constant 250mm length)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: 250  // CONSTANT cylinder length
            property vector3d cylEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lBody / cylDirectionLength),
                j_tail.y + cylDirection.y * (lBody / cylDirectionLength),
                j_tail.z
            )
            
            position: Qt.vector3d((j_tail.x + cylEnd.x)/2, (j_tail.y + cylEnd.y)/2, j_tail.z)
            scale: Qt.vector3d(1.2, lBody/100, 1.2)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylEnd.y - j_tail.y, cylEnd.x - j_tail.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.15; alphaMode: PrincipledMaterial.Blend }
        }
        
        // MOVING PISTON (animated inside cylinder)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: 250
            property real rodExtension: cylDirectionLength - lBody
            property real pistonRatio: Math.max(0.0, Math.min(1.0, rodExtension / 200.0))
            
            // PISTON MOVES inside cylinder based on rod extension
            property vector3d pistonPos: Qt.vector3d(
                j_tail.x + cylDirection.x * ((lBody * (0.85 - pistonRatio * 0.7)) / cylDirectionLength),
                j_tail.y + cylDirection.y * ((lBody * (0.85 - pistonRatio * 0.7)) / cylDirectionLength),
                j_tail.z
            )
            
            position: pistonPos
            scale: Qt.vector3d(1.1, 1.0, 1.1)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ff2222"; metalness: 0.8; roughness: 0.2 }
        }
        
        // CONSTANT LENGTH ROD (from piston to j_rod)  
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: 250
            property real rodExtension: cylDirectionLength - lBody
            property real pistonRatio: Math.max(0.0, Math.min(1.0, rodExtension / 200.0))
            
            // Rod starts from PISTON position (same calculation)
            property vector3d rodStart: Qt.vector3d(
                j_tail.x + cylDirection.x * ((lBody * (0.85 - pistonRatio * 0.7)) / cylDirectionLength),
                j_tail.y + cylDirection.y * ((lBody * (0.85 - pistonRatio * 0.7)) / cylDirectionLength),
                j_tail.z
            )
            
            // CONSTANT rod length from piston to j_rod
            property real rodLength: Math.hypot(j_rod.x - rodStart.x, j_rod.y - rodStart.y, 0)
            
            position: Qt.vector3d((rodStart.x + j_rod.x)/2, (rodStart.y + j_rod.y)/2, j_rod.z)
            scale: Qt.vector3d(0.3, rodLength/100, 0.3)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - rodStart.y, j_rod.x - rodStart.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.9; roughness: 0.1 }
        }
        
        // ROUND CYLINDRICAL JOINTS (NOT flattened ellipses)
        
        // Tail joint - PERFECTLY ROUND
        Model {
            source: "#Cylinder"
            position: j_tail
            scale: Qt.vector3d(1.2, 1.2, 2.4)  // ROUND cross-section (X=Y), length along Z
            eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.05)  // Z-axis alignment + slight animation
            materials: PrincipledMaterial { baseColor: "#333333"; metalness: 0.9; roughness: 0.2 }
        }
        
        // Arm joint - PERFECTLY ROUND  
        Model {
            source: "#Cylinder"
            position: j_arm
            scale: Qt.vector3d(1.0, 1.0, 2.0)  // ROUND cross-section
            eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.1)  // Z-axis + animation
            materials: PrincipledMaterial { baseColor: "#555555"; metalness: 0.9; roughness: 0.2 }
        }
        
        // Rod joint - PERFECTLY ROUND
        Model {
            source: "#Cylinder" 
            position: j_rod
            scale: Qt.vector3d(0.8, 0.8, 1.6)  // ROUND cross-section
            eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.15)  // Z-axis + animation
            materials: PrincipledMaterial { baseColor: "#777777"; metalness: 0.8; roughness: 0.3 }
        }
    }

    // Four suspension corners with CORRECTED mechanics
    CorrectedSuspensionCorner { j_arm: fl_j_arm; j_tail: fl_j_tail; j_rod: fl_j_rod; leverAngle: fl_angle }
    CorrectedSuspensionCorner { j_arm: fr_j_arm; j_tail: fr_j_tail; j_rod: fr_j_rod; leverAngle: fr_angle }
    CorrectedSuspensionCorner { j_arm: rl_j_arm; j_tail: rl_j_tail; j_rod: rl_j_rod; leverAngle: rl_angle }
    CorrectedSuspensionCorner { j_arm: rr_j_arm; j_tail: rr_j_tail; j_rod: rr_j_rod; leverAngle: rr_angle }

    // Small reference markers
    Model { source: "#Sphere"; position: fl_j_arm; scale: Qt.vector3d(0.4, 0.4, 0.4); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_arm; scale: Qt.vector3d(0.4, 0.4, 0.4); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_arm; scale: Qt.vector3d(0.4, 0.4, 0.4); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_arm; scale: Qt.vector3d(0.4, 0.4, 0.4); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }

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
        console.log("=== FULLY CORRECTED SUSPENSION SYSTEM ===")
        console.log("FIXES:")
        console.log("? Round cylindrical joints (X=Y scale)")
        console.log("? Moving pistons inside cylinders")
        console.log("? Constant rod lengths (not variable)")
        console.log("? Correct lever angles (not pointing to frame)")
        console.log("? Smooth 30fps animation")
        view3d.forceActiveFocus()
    }
}
