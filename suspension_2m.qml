
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    // Animation properties
    property real animationTime: 0.0
    property real animationSpeed: 0.8

    // 2-meter suspension system coordinates
    property real beamSize: 120
    property real frameHeight: 650
    property real frameLength: 2000

    // ANIMATED lever angles (small oscillations for testing)
    property real fl_angle: 8 * Math.sin(animationTime)
    property real fr_angle: 8 * Math.sin(animationTime + Math.PI/4)
    property real rl_angle: 8 * Math.sin(animationTime + Math.PI/2)
    property real rr_angle: 8 * Math.sin(animationTime + 3*Math.PI/4)

    // Base joint positions (FIXED frame attachments)
    property vector3d fl_j_arm: Qt.vector3d(-150, 60, -1000)
    property vector3d fr_j_arm: Qt.vector3d(150, 60, -1000)
    property vector3d rl_j_arm: Qt.vector3d(-150, 60, 1000)
    property vector3d rr_j_arm: Qt.vector3d(150, 60, 1000)

    property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)
    property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)
    property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)
    property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)

    // ANIMATED rod positions (move with lever rotation) - CORRECTED DIRECTIONS
    property real leverLength: 315  // Distance from pivot to rod attachment
    
    // FL/RL: Base angle 180deg (pointing LEFT) + oscillation
    property vector3d fl_j_rod: Qt.vector3d(
        fl_j_arm.x + leverLength * Math.cos((180 + fl_angle) * Math.PI / 180),
        fl_j_arm.y + leverLength * Math.sin((180 + fl_angle) * Math.PI / 180),
        fl_j_arm.z
    )
    property vector3d rl_j_rod: Qt.vector3d(
        rl_j_arm.x + leverLength * Math.cos((180 + rl_angle) * Math.PI / 180),
        rl_j_arm.y + leverLength * Math.sin((180 + rl_angle) * Math.PI / 180),
        rl_j_arm.z
    )
    
    // FR/RR: Base angle 0deg (pointing RIGHT) + oscillation  
    property vector3d fr_j_rod: Qt.vector3d(
        fr_j_arm.x + leverLength * Math.cos((0 + fr_angle) * Math.PI / 180),
        fr_j_arm.y + leverLength * Math.sin((0 + fr_angle) * Math.PI / 180),
        fr_j_arm.z
    )
    property vector3d rr_j_rod: Qt.vector3d(
        rr_j_arm.x + leverLength * Math.cos((0 + rr_angle) * Math.PI / 180),
        rr_j_arm.y + leverLength * Math.sin((0 + rr_angle) * Math.PI / 180),
        rr_j_arm.z
    )

    // Camera
    property real cameraDistance: 3500
    property real cameraPitch: -25
    property real cameraYaw: 35

    // Animation timer
    Timer {
        running: true
        interval: 33  // 30 FPS
        repeat: true
        onTriggered: {
            animationTime += animationSpeed * 0.033
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
        
        // CORRECTED LEVER (proper positioning and rotation around pivot with correct base angles)
        Model {
            source: "#Cube"
            // Position lever CENTERED on pivot point j_arm with correct base direction
            property real baseAngle: (j_arm.x < 0) ? 180 : 0  // Left side: 180deg, Right side: 0deg
            property real totalAngle: baseAngle + leverAngle
            
            position: Qt.vector3d(j_arm.x + (leverLength/2) * Math.cos(totalAngle * Math.PI / 180), 
                                 j_arm.y + (leverLength/2) * Math.sin(totalAngle * Math.PI / 180), 
                                 j_arm.z)
            scale: Qt.vector3d(leverLength/100, 0.8, 0.8)
            eulerRotation: Qt.vector3d(0, 0, totalAngle)  // Rotate with base + oscillation
            materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
        }
        
        // FIXED CYLINDER - STARTS FROM END OF TAIL ROD (not from j_tail joint)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: 250  // CONSTANT cylinder working length
            property real lTailRod: 100  // Tail rod length
            
            // Cylinder starts FROM END OF TAIL ROD (not from j_tail)
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),  // End of tail rod
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            property vector3d cylStart: tailRodEnd  // Cylinder starts where tail rod ends
            property vector3d cylEnd: Qt.vector3d(
                cylStart.x + cylDirection.x * (lBody / cylDirectionLength),
                cylStart.y + cylDirection.y * (lBody / cylDirectionLength),
                cylStart.z
            )
            
            position: Qt.vector3d((cylStart.x + cylEnd.x)/2, (cylStart.y + cylEnd.y)/2, cylStart.z)
            scale: Qt.vector3d(1.2, lBody/100, 1.2)  // Working cylinder length only
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylEnd.y - cylStart.y, cylEnd.x - cylStart.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.12; alphaMode: PrincipledMaterial.Blend }
        }
        
        // MOVING PISTON (animated inside cylinder that starts from tail rod end) - CORRECT DIMENSIONS
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: 250
            property real lTailRod: 100
            property real pistonRatio: Math.max(0.0, Math.min(1.0, (leverAngle + 8) / 16))  // Scale -8deg..+8deg to 0..1
            
            // Cylinder starts FROM END OF TAIL ROD
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            property vector3d cylStart: tailRodEnd
            
            // PISTON MOVES inside cylinder based on LEVER ANGLE
            property vector3d pistonPos: Qt.vector3d(
                cylStart.x + cylDirection.x * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.y + cylDirection.y * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.z
            )
            
            position: pistonPos
            // CORRECT DIMENSIONS: 20mm thick, 90% of cylinder diameter (1.2 * 0.9 = 1.08)
            scale: Qt.vector3d(1.08, 0.2, 1.08)  // Diameter 90% of cylinder, thickness 20mm
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ff0066"; metalness: 0.9; roughness: 0.1 }  // BRIGHT MAGENTA
            
            Component.onCompleted: {
                console.log("PISTON DEBUG - Angle:", leverAngle, "Ratio:", pistonRatio)
            }
        }
        
        // METAL ROD (from piston to j_rod) - NORMAL THICKNESS
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: 250
            property real lTailRod: 100
            property real pistonRatio: Math.max(0.0, Math.min(1.0, (leverAngle + 8) / 16))  // SAME as piston
            
            // Cylinder starts FROM END OF TAIL ROD (same as piston calculation)
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            property vector3d cylStart: tailRodEnd
            
            // Rod starts from PISTON position (same calculation as piston)
            property vector3d rodStart: Qt.vector3d(
                cylStart.x + cylDirection.x * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.y + cylDirection.y * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.z
            )
            
            position: Qt.vector3d((rodStart.x + j_rod.x)/2, (rodStart.y + j_rod.y)/2, j_rod.z)
            scale: Qt.vector3d(0.5, Math.hypot(j_rod.x - rodStart.x, j_rod.y - rodStart.y, 0)/100, 0.5)  // Normal rod thickness
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - rodStart.y, j_rod.x - rodStart.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }  // STEEL
        }
        
        // TAIL ROD (100mm extension from j_tail toward j_rod)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lTailRod: 100  // Fixed 100mm tail rod length
            
            // Tail rod goes 100mm from j_tail toward j_rod direction
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            
            position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
            scale: Qt.vector3d(0.5, lTailRod/100, 0.5)  // SAME diameter as main rod, 100mm length
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(tailRodEnd.y - j_tail.y, tailRodEnd.x - j_tail.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }  // STEEL
        }
        
        // CORRECTED CYLINDRICAL JOINTS (PROPERLY ROUND AND Z-ORIENTED)
        
        // Tail joint - TRULY ROUND along Z-axis (correct scale after rotation)
        Model {
            source: "#Cylinder"
            position: j_tail
            scale: Qt.vector3d(1.2, 2.4, 1.2)  // After 90deg rotation: X=diameter, Y=length, Z=diameter
            eulerRotation: Qt.vector3d(90, 0, 0)  // Rotate 90deg around X to orient along Z-axis
            materials: PrincipledMaterial { baseColor: "#0088ff"; metalness: 0.8; roughness: 0.2 }
        }
        
        // Arm joint - TRULY ROUND along Z-axis (correct scale after rotation)
        Model {
            source: "#Cylinder"
            position: j_arm
            scale: Qt.vector3d(1.0, 2.0, 1.0)  // After 90deg rotation: X=diameter, Y=length, Z=diameter
            eulerRotation: Qt.vector3d(90, 0, 0)  // Rotate 90deg around X to orient along Z-axis
            materials: PrincipledMaterial { baseColor: "#ff8800"; metalness: 0.8; roughness: 0.2 }
        }
        
        // Rod joint - TRULY ROUND along Z-axis (correct scale after rotation)
        Model {
            source: "#Cylinder" 
            position: j_rod
            scale: Qt.vector3d(0.8, 1.6, 0.8)  // After 90deg rotation: X=diameter, Y=length, Z=diameter
            eulerRotation: Qt.vector3d(90, 0, 0)  // Rotate 90deg around X to orient along Z-axis
            materials: PrincipledMaterial { baseColor: "#00ff44"; metalness: 0.7; roughness: 0.3 }
        }
    }

    // Four suspension corners with ALL ISSUES FIXED
    CorrectedSuspensionCorner { j_arm: fl_j_arm; j_tail: fl_j_tail; j_rod: fl_j_rod; leverAngle: fl_angle }
    CorrectedSuspensionCorner { j_arm: fr_j_arm; j_tail: fr_j_tail; j_rod: fr_j_rod; leverAngle: fr_angle }
    CorrectedSuspensionCorner { j_arm: rl_j_arm; j_tail: rl_j_tail; j_rod: rl_j_rod; leverAngle: rl_angle }
    CorrectedSuspensionCorner { j_arm: rr_j_arm; j_tail: rr_j_tail; j_rod: rr_j_rod; leverAngle: rr_angle }

    // Small reference markers
    Model { source: "#Sphere"; position: fl_j_arm; scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_arm; scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_arm; scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_arm; scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }

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
        console.log("=== FULLY CORRECTED 2-METER SUSPENSION ===")
        console.log("FIXES APPLIED:")
        console.log("Round joints: scale(X=Y, Z=length)")
        console.log("Moving pistons: animated with rod extension")
        console.log("Steel rods: metalness=0.95 (not rubber)")
        console.log("Correct lever angles: from animation (not static 180deg)")
        console.log("Complete functional code")
        console.log("=== DEBUG VALUES ===")
        console.log("FL angle:", fl_angle)
        console.log("FR angle:", fr_angle)
        console.log("FL j_rod pos:", fl_j_rod.x, fl_j_rod.y, fl_j_rod.z)
        console.log("FR j_rod pos:", fr_j_rod.x, fl_j_rod.y, fl_j_rod.z)
        console.log("Animation time:", animationTime)
        console.log("Lever length:", leverLength)
        view3d.forceActiveFocus()
    }
}
