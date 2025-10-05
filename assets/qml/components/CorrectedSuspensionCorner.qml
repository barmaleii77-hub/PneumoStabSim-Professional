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
    
    // NEW: Piston position from Python (GeometryBridge)
    property real pistonPositionMm: 125.0  // Default to center
    property real pistonRatio: 0.5         // Default to center (0..1)
    
    // CALCULATE CYLINDER GEOMETRY
    property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
    property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
    property vector3d cylDirectionNorm: Qt.vector3d(
        cylDirection.x / cylDirectionLength,
        cylDirection.y / cylDirectionLength,
        0
    )
    
    property real lBody: 250  // CONSTANT cylinder working length
    property real lTailRod: 100  // Tail rod length
    
    // Cylinder starts FROM END OF TAIL ROD
    property vector3d tailRodEnd: Qt.vector3d(
        j_tail.x + cylDirectionNorm.x * lTailRod,
        j_tail.y + cylDirectionNorm.y * lTailRod,
        j_tail.z
    )
    property vector3d cylStart: tailRodEnd
    
    // Cylinder end (where rod exits)
    property vector3d cylEnd: Qt.vector3d(
        cylStart.x + cylDirectionNorm.x * lBody,
        cylStart.y + cylDirectionNorm.y * lBody,
        cylStart.z
    )
    
    // Current piston position (from Python)
    property vector3d pistonCenter: Qt.vector3d(
        cylStart.x + cylDirectionNorm.x * pistonPositionMm,
        cylStart.y + cylDirectionNorm.y * pistonPositionMm,
        cylStart.z
    )
    
    // FULL PISTON ROD LENGTH (CONSTANT!)
    // Calculate from CENTER position to j_rod as baseline
    property real centerPistonPos: lBody / 2
    property vector3d centerPistonCenter: Qt.vector3d(
        cylStart.x + cylDirectionNorm.x * centerPistonPos,
        cylStart.y + cylDirectionNorm.y * centerPistonPos,
        cylStart.z
    )
    property real fullRodLength: Math.hypot(j_rod.x - centerPistonCenter.x, j_rod.y - centerPistonCenter.y)
    
    // CORRECTED LEVER
    Model {
        source: "#Cube"
        property real baseAngle: (j_arm.x < 0) ? 180 : 0
        property real totalAngle: baseAngle + leverAngle
        
        position: Qt.vector3d(j_arm.x + (leverLength/2) * Math.cos(totalAngle * Math.PI / 180), 
                             j_arm.y + (leverLength/2) * Math.sin(totalAngle * Math.PI / 180), 
                             j_arm.z)
        scale: Qt.vector3d(leverLength/100, 0.8, 0.8)
        eulerRotation: Qt.vector3d(0, 0, totalAngle)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }
    
    // FIXED CYLINDER BODY (transparent)
    Model {
        source: "#Cylinder"
        
        position: Qt.vector3d((cylStart.x + cylEnd.x)/2, (cylStart.y + cylEnd.y)/2, cylStart.z)
        scale: Qt.vector3d(1.2, lBody/100, 1.2)
        eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylEnd.y - cylStart.y, cylEnd.x - cylStart.x) * 180 / Math.PI + 90)
        materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.12; alphaMode: PrincipledMaterial.Blend }
    }
    
    // MOVING PISTON
    Model {
        source: "#Cylinder"
        
        position: pistonCenter
        scale: Qt.vector3d(1.08, 0.2, 1.08)
        eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
        materials: PrincipledMaterial { baseColor: "#ff0066"; metalness: 0.9; roughness: 0.1 }
    }
    
    // FULL PISTON ROD (CONSTANT LENGTH!)
    // Goes from piston TO j_rod with FIXED length
    // Entire rod is visible (part inside cylinder, part outside)
    Model {
        source: "#Cylinder"
        
        // Center of full rod (midpoint from piston to j_rod)
        position: Qt.vector3d((pistonCenter.x + j_rod.x)/2, (pistonCenter.y + j_rod.y)/2, pistonCenter.z)
        
        // Scale: CONSTANT length (fullRodLength)
        scale: Qt.vector3d(0.5, fullRodLength/100, 0.5)
        
        // Rotation to align piston ? j_rod
        eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - pistonCenter.y, j_rod.x - pistonCenter.x) * 180 / Math.PI + 90)
        
        materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }
    }
    
    // TAIL ROD
    Model {
        source: "#Cylinder"
        
        position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
        scale: Qt.vector3d(0.5, lTailRod/100, 0.5)
        eulerRotation: Qt.vector3d(0, 0, Math.atan2(tailRodEnd.y - j_tail.y, tailRodEnd.x - j_tail.x) * 180 / Math.PI + 90)
        materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }
    }
    
    // CYLINDRICAL JOINTS
    
    Model {
        source: "#Cylinder"
        position: j_tail
        scale: Qt.vector3d(1.2, 2.4, 1.2)
        eulerRotation: Qt.vector3d(90, 0, 0)
        materials: PrincipledMaterial { baseColor: "#0088ff"; metalness: 0.8; roughness: 0.2 }
    }
    
    Model {
        source: "#Cylinder"
        position: j_arm
        scale: Qt.vector3d(1.0, 2.0, 1.0)
        eulerRotation: Qt.vector3d(90, 0, 0)
        materials: PrincipledMaterial { baseColor: "#ff8800"; metalness: 0.8; roughness: 0.2 }
    }
    
    Model {
        source: "#Cylinder" 
        position: j_rod
        scale: Qt.vector3d(0.8, 1.6, 0.8)
        eulerRotation: Qt.vector3d(90, 0, 0)
        materials: PrincipledMaterial { baseColor: "#00ff44"; metalness: 0.7; roughness: 0.3 }
    }
}