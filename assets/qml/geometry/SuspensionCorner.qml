import QtQuick
import QtQuick3D

/*
 * Suspension Corner Component - Complete suspension assembly
 * Extracted from main.qml for modular QML architecture
 *
 * Includes:
 * - Lever (arm)
 * - Tail rod
 * - Cylinder body (transparent)
 * - Piston (animated)
 * - Piston rod (from piston to j_rod)
 * - 3 Cylindrical joints (tail, arm, rod)
 */
Node {
    id: suspensionCorner

    // ===============================================================
    // REQUIRED PROPERTIES - Joint positions and geometry
    // ===============================================================

    required property vector3d j_arm      // Arm pivot point
    required property vector3d j_tail     // Tail attachment point
    required property real leverAngle     // Lever rotation angle (degrees)
    required property real pistonPositionFromPython  // Piston position from simulation (mm)

    // ===============================================================
    // GEOMETRY PARAMETERS (from root or defaults)
    // ===============================================================

    property real leverLength: 800        // мм
    property real rodPosition: 0.6        // Fraction (0.0 - 1.0)
    property real cylinderLength: 500     // мм
    property real boreHead: 80            // мм
    property real rodDiameter: 35         // мм
    property real pistonThickness: 25     // мм
    property real pistonRodLength: 200    // мм
    property int cylinderSegments: 64
    property int cylinderRings: 8
    // Новый параметр длины хвостовика цилиндра (отрезок от j_tail до начала цилиндра)
    property real tailRodLength: 100      // мм

    // Масштабы шарниров (радиус/высота) как множители базовых значений
    property real jointTailScale: 1.0
    property real jointArmScale: 1.0
    property real jointRodScale: 1.0

    // ===============================================================
    // MATERIAL PROPERTIES (required from parent)
    // ===============================================================

    required property var leverMaterial
    required property var tailRodMaterial
    required property var cylinderMaterial
    required property var pistonBodyMaterial
    required property var pistonRodMaterial
    required property var jointTailMaterial
    required property var jointArmMaterial
    required property var jointRodMaterial

    // ===============================================================
    // CALCULATED PROPERTIES - Geometry calculations
    // ===============================================================

    readonly property real baseAngle: (j_arm.x < 0) ? 180 : 0  // Left: 180°, Right: 0°
    readonly property real totalAngle: baseAngle + leverAngle

    // Calculate j_rod position (rod attachment point on lever)
    readonly property vector3d j_rod: Qt.vector3d(
        j_arm.x + (leverLength * rodPosition) * Math.cos(totalAngle * Math.PI / 180),
        j_arm.y + (leverLength * rodPosition) * Math.sin(totalAngle * Math.PI / 180),
        j_arm.z
    )

    // Cylinder axis direction
    readonly property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
    readonly property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y)
    readonly property vector3d cylDirectionNorm: Qt.vector3d(
        cylDirection.x / cylDirectionLength,
        cylDirection.y / cylDirectionLength,
        0
    )

    // Tail rod end position (cylinder starts here)
    readonly property vector3d tailRodEnd: Qt.vector3d(
        j_tail.x + cylDirectionNorm.x * tailRodLength,
        j_tail.y + cylDirectionNorm.y * tailRodLength,
        j_tail.z
    )
    readonly property vector3d cylStart: tailRodEnd

    // Cylinder end position
    readonly property vector3d cylEnd: Qt.vector3d(
        cylStart.x + cylDirectionNorm.x * cylinderLength,
        cylStart.y + cylDirectionNorm.y * cylinderLength,
        cylStart.z
    )

    // Piston center position (from Python simulation)
    readonly property vector3d pistonCenter: Qt.vector3d(
        cylStart.x + cylDirectionNorm.x * pistonPositionFromPython,
        cylStart.y + cylDirectionNorm.y * pistonPositionFromPython,
        cylStart.z
    )

    // ===============================================================
    // ERROR CHECKING - Rod length consistency
    // ===============================================================

    readonly property real rodLengthError: {
        const dx = j_rod.x - pistonCenter.x
        const dy = j_rod.y - pistonCenter.y
        const actualLength = Math.hypot(dx, dy)
        return Math.abs(actualLength - pistonRodLength)
    }

    // ===============================================================
    // VISUAL COMPONENTS
    // ===============================================================

    // 1. LEVER (rotating arm)
    Model {
        source: "#Cube"
        position: Qt.vector3d(
            j_arm.x + (leverLength/2) * Math.cos(totalAngle * Math.PI / 180),
            j_arm.y + (leverLength/2) * Math.sin(totalAngle * Math.PI / 180),
            j_arm.z
        )
        scale: Qt.vector3d(leverLength/100, 0.8, 0.8)
        eulerRotation: Qt.vector3d(0, 0, totalAngle)
        materials: [leverMaterial]
    }

    // 2. TAIL ROD (from j_tail to cylinder start)
    Model {
        source: "#Cylinder"
        position: Qt.vector3d(
            (j_tail.x + tailRodEnd.x)/2,
            (j_tail.y + tailRodEnd.y)/2,
            j_tail.z
        )
        scale: Qt.vector3d(0.5, tailRodLength/100, 0.5)
        eulerRotation: Qt.vector3d(0, 0, Math.atan2(tailRodEnd.y - j_tail.y, tailRodEnd.x - j_tail.x) * 180 / Math.PI + 90)
        materials: [tailRodMaterial]
    }

    // 3. CYLINDER BODY (transparent, fixed)
    Model {
        source: "#Cylinder"
        position: Qt.vector3d(
            (cylStart.x + cylEnd.x)/2,
            (cylStart.y + cylEnd.y)/2,
            cylStart.z
        )
        scale: Qt.vector3d(boreHead/100 * 1.2, cylinderLength/100, boreHead/100 * 1.2)
        eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylEnd.y - cylStart.y, cylEnd.x - cylStart.x) * 180 / Math.PI + 90)
        materials: [cylinderMaterial]
    }

    // 4. PISTON (moving, position from Python)
    Model {
        source: "#Cylinder"
        position: pistonCenter
        // ✅ ЕДИНОЕ масштабирование /100 для согласованности
        scale: Qt.vector3d(boreHead/100 * 1.08, pistonThickness/100, boreHead/100 * 1.08)
        eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
        materials: [pistonBodyMaterial]
    }

    // 5. PISTON ROD (from piston to j_rod, CONSTANT length)
    Model {
        source: "#Cylinder"

        // Direction from piston to j_rod
        property real rodDirX: j_rod.x - pistonCenter.x
        property real rodDirY: j_rod.y - pistonCenter.y
        property real rodDirLen: Math.hypot(rodDirX, rodDirY)

        // Normalized direction
        property real rodDirNormX: rodDirX / rodDirLen
        property real rodDirNormY: rodDirY / rodDirLen

        // Rod end position (piston + rodLength in direction of j_rod)
        property vector3d rodEnd: Qt.vector3d(
            pistonCenter.x + rodDirNormX * pistonRodLength,
            pistonCenter.y + rodDirNormY * pistonRodLength,
            pistonCenter.z
        )

        position: Qt.vector3d(
            (pistonCenter.x + rodEnd.x)/2,
            (pistonCenter.y + rodEnd.y)/2,
            pistonCenter.z
        )
        // ✅ ЕДИНОЕ масштабирование /100 для согласованности
        scale: Qt.vector3d(rodDiameter/100 * 0.5, pistonRodLength/100, rodDiameter/100 * 0.5)
        eulerRotation: Qt.vector3d(0, 0, Math.atan2(rodEnd.y - pistonCenter.y, rodEnd.x - pistonCenter.x) * 180 / Math.PI + 90)
        materials: [pistonRodMaterial]
    }

    // ===============================================================
    // JOINTS (cylindrical, Z-axis oriented)
    // ===============================================================

    // 6. TAIL JOINT (blue, at j_tail)
    Model {
        source: "#Cylinder"
        position: j_tail
        // Масштабируем базовые значения через множитель jointTailScale
        scale: Qt.vector3d(1.2 * jointTailScale, 2.4 * jointTailScale, 1.2 * jointTailScale)
        eulerRotation: Qt.vector3d(90, 0, 0)
        materials: [jointTailMaterial]
    }

    // 7. ARM JOINT (orange, at j_arm)
    Model {
        source: "#Cylinder"
        position: j_arm
        scale: Qt.vector3d(1.0 * jointArmScale, 2.0 * jointArmScale, 1.0 * jointArmScale)
        eulerRotation: Qt.vector3d(90, 0, 0)
        materials: [jointArmMaterial]
    }

    // 8. ROD JOINT (green, at j_rod)
    Model {
        source: "#Cylinder"
        position: j_rod
        scale: Qt.vector3d(0.8 * jointRodScale, 1.6 * jointRodScale, 0.8 * jointRodScale)
        eulerRotation: Qt.vector3d(90, 0, 0)
        materials: [jointRodMaterial]
    }

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    Component.onCompleted: {
        console.log("🔧 SuspensionCorner initialized:")
        console.log("   j_arm:", j_arm.x, j_arm.y, j_arm.z)
        console.log("   j_tail:", j_tail.x, j_tail.y, j_tail.z)
        console.log("   j_rod:", j_rod.x, j_rod.y, j_rod.z)
        console.log("   leverAngle:", leverAngle, "deg")
        console.log("   pistonPosition:", pistonPositionFromPython, "mm")
        console.log("   rodLengthError:", rodLengthError.toFixed(2), "mm")
    }
}
