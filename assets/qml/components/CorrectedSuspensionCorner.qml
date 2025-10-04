import QtQuick
import QtQuick3D

// FULLY CORRECTED 2-METER SUSPENSION COMPONENT
Node {
    id: suspensionCorner
    
    property vector3d j_arm
    property vector3d j_tail  
    property vector3d j_rod
    property real leverAngle
    property real leverLength: 315
    
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