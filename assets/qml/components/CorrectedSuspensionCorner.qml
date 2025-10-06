import QtQuick
import QtQuick3D

// FULLY CORRECTED 2-METER SUSPENSION COMPONENT
// INITIAL STATE: V_head = V_rod, lever HORIZONTAL
Node {
    id: suspensionCorner
    
    property vector3d j_arm
    property vector3d j_tail  
    property vector3d j_rod
    property real leverAngle
    property real leverLength: 315
    
    // CORRECTED: Piston at EQUAL VOLUMES position
    // V_head = V_rod when piston at 105mm (42% of 250mm body)
    property real pistonPositionMm: 105.0  // mm from cylinder start (CALCULATED!)
    property real pistonRatio: 0.42        // 0.42 = 105/250 (FIXED VALUE!)
    
    // Rod length CALCULATED from initial geometry
    property real pistonRodLength: 200.0  // mm - will be updated from geometry
    
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
    
    // PISTON ROD (CONSTANT LENGTH FROM UI!)
    // Length is SET BY USER, NOT calculated from geometry!
    // Goes from piston in direction toward j_rod
    Model {
        source: "#Cylinder"
        
        // Direction from piston toward j_rod
        property real rodDirX: j_rod.x - pistonCenter.x
        property real rodDirY: j_rod.y - pistonCenter.y
        property real rodDirLen: Math.hypot(rodDirX, rodDirY)
        
        // Normalized direction
        property real rodDirNormX: rodDirX / rodDirLen
        property real rodDirNormY: rodDirY / rodDirLen
        
        // Rod end position (piston + pistonRodLength in direction of j_rod)
        property vector3d rodEnd: Qt.vector3d(
            pistonCenter.x + rodDirNormX * pistonRodLength,
            pistonCenter.y + rodDirNormY * pistonRodLength,
            pistonCenter.z
        )
        
        // Center of rod (midpoint from piston to rodEnd)
        position: Qt.vector3d((pistonCenter.x + rodEnd.x)/2, (pistonCenter.y + rodEnd.y)/2, pistonCenter.z)
        
        // Scale: CONSTANT length from UI (pistonRodLength)
        scale: Qt.vector3d(0.5, pistonRodLength/100, 0.5)
        
        // Rotation to align piston ? rod end
        eulerRotation: Qt.vector3d(0, 0, Math.atan2(rodEnd.y - pistonCenter.y, rodEnd.x - pistonCenter.x) * 180 / Math.PI + 90)
        
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