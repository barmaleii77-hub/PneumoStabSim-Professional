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
    required property real pistonPositionM // Piston position from simulation (m)

    // ===============================================================
    // GEOMETRY PARAMETERS (from root or defaults)
    // ===============================================================

    property real leverLengthM:0.8        // м
    property real rodPosition: 0.6        // Fraction (0.0 - 1.0)
    property real cylinderLength: 500E-3  // м
    property real boreHead: 80E-3         // м
    property real rodDiameter: 35E-3      // м
    property real pistonThickness: 25E-3  // м
    property real pistonRodLength: 200E-3 // м
    property int cylinderSegments: 64
    property int cylinderRings: 8
    // Новый параметр длины хвостовика цилиндра (отрезок от j_tail до начала цилиндра)
    property real tailRodLength: 100E-3   // м

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

    readonly property real baseAngleDeg: j_arm.x < 0 ? 180 : 0  // Left: 180°, Right: 0°
    readonly property real totalAngleDeg: baseAngleDeg + leverAngle
    readonly property real totalAngleRad: totalAngleDeg * Math.PI / 180
    readonly property real leverOffset: leverLengthM * rodPosition

    // Calculate j_rod position (rod attachment point on lever)
    readonly property vector3d j_rod: Qt.vector3d(
        j_arm.x + leverOffset * Math.cos(totalAngleRad),
        j_arm.y + leverOffset * Math.sin(totalAngleRad),
        j_arm.z
    )

    // Cylinder axis direction
    readonly property vector3d cylDirection: Qt.vector3d(
        j_rod.x - j_tail.x,
        j_rod.y - j_tail.y,
        0
    )
    readonly property real cylDirectionLength: Math.max(
        Math.hypot(cylDirection.x, cylDirection.y),
        1e-6
    )
    readonly property vector3d cylDirectionNorm: Qt.vector3d(
        cylDirection.x / cylDirectionLength,
        cylDirection.y / cylDirectionLength,
        0
    )
    readonly property real cylinderAngleDeg: Math.atan2(
        cylDirection.y,
        cylDirection.x
    ) * 180 / Math.PI

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
        cylStart.x + cylDirectionNorm.x * pistonPositionM,
        cylStart.y + cylDirectionNorm.y * pistonPositionM,
        cylStart.z
    )

    // Derived radii and half-lengths (metres)
    readonly property real cylinderRadius: Math.max(boreHead / 2, 0.001)
    readonly property real cylinderHalfLength: Math.max(cylinderLength, 1e-4) / 2
    readonly property real pistonRadius: Math.max(cylinderRadius * 0.92, 0.001)
    readonly property real pistonHalfThickness: Math.max(pistonThickness, 1e-4) / 2
    readonly property real pistonRodRadius: Math.max(rodDiameter / 2, 0.001)
    readonly property real pistonRodHalfLength: Math.max(pistonRodLength, 1e-4) / 2
    readonly property real tailRodRadius: Math.max(pistonRodRadius * 0.8, 0.001)
    readonly property real tailRodHalfLength: Math.max(tailRodLength, 1e-4) / 2
    readonly property real leverThickness: Math.max(pistonRodRadius * 1.2, 0.008)
    readonly property real jointBaseRadius: Math.max(cylinderRadius * 0.6, 0.01)
    readonly property real jointBaseHalfHeight: Math.max(cylinderRadius * 0.6, 0.01)
    readonly property real jointTailRadius: jointBaseRadius * jointTailScale
    readonly property real jointArmRadius: jointBaseRadius * jointArmScale
    readonly property real jointRodRadius: Math.max(pistonRodRadius * 1.1, 0.005) * jointRodScale
    readonly property real jointTailHalfHeight: jointBaseHalfHeight * jointTailScale
    readonly property real jointArmHalfHeight: jointBaseHalfHeight * jointArmScale
    readonly property real jointRodHalfHeight: Math.max(pistonRodRadius, 0.005) * jointRodScale

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

    Model {
        source: "#Cube"
        position: Qt.vector3d(
            j_arm.x + (leverLengthM / 2) * Math.cos(totalAngleRad),
            j_arm.y + (leverLengthM / 2) * Math.sin(totalAngleRad),
            j_arm.z
        )
        scale: Qt.vector3d(leverLengthM, leverThickness, leverThickness)
        eulerRotation: Qt.vector3d(0, 0, totalAngleDeg)
        materials: [leverMaterial]
    }

    // 2. TAIL ROD (from j_tail to cylinder start)
    Model {
        source: "#Cylinder"
        position: Qt.vector3d(
            (j_tail.x + tailRodEnd.x) / 2,
            (j_tail.y + tailRodEnd.y) / 2,
            j_tail.z
        )
        scale: Qt.vector3d(tailRodRadius, tailRodHalfLength, tailRodRadius)
        eulerRotation: Qt.vector3d(0, 0, cylinderAngleDeg + 90)
        materials: [tailRodMaterial]
    }

    // 3. CYLINDER BODY (transparent, fixed)
    Model {
        source: "#Cylinder"
        position: Qt.vector3d(
            (cylStart.x + cylEnd.x) / 2,
            (cylStart.y + cylEnd.y) / 2,
            cylStart.z
        )
        scale: Qt.vector3d(cylinderRadius * 1.05, cylinderHalfLength, cylinderRadius * 1.05)
        eulerRotation: Qt.vector3d(0, 0, cylinderAngleDeg + 90)
        materials: [cylinderMaterial]
    }

    // 4. PISTON (moving, position from Python)
    Model {
        source: "#Cylinder"
        position: pistonCenter
        scale: Qt.vector3d(pistonRadius, pistonHalfThickness, pistonRadius)
        eulerRotation: Qt.vector3d(0, 0, cylinderAngleDeg + 90)
        materials: [pistonBodyMaterial]
    }

    // 5. PISTON ROD (from piston to j_rod, CONSTANT length)
    Model {
        source: "#Cylinder"

        // Direction from piston to j_rod
        property real rodDirX: j_rod.x - pistonCenter.x
        property real rodDirY: j_rod.y - pistonCenter.y
        property real rodDirLen: Math.hypot(rodDirX, rodDirY)
        property real rodDirSafe: Math.max(rodDirLen, 1e-6)

        // Normalized direction
        property real rodDirNormX: rodDirX / rodDirSafe
        property real rodDirNormY: rodDirY / rodDirSafe

        // Rod end position (piston + rodLength in direction of j_rod)
        property vector3d rodEnd: Qt.vector3d(
            pistonCenter.x + rodDirNormX * pistonRodLength,
            pistonCenter.y + rodDirNormY * pistonRodLength,
            pistonCenter.z
        )

        position: Qt.vector3d(
            (pistonCenter.x + rodEnd.x) / 2,
            (pistonCenter.y + rodEnd.y) / 2,
            pistonCenter.z
        )
        scale: Qt.vector3d(pistonRodRadius, pistonRodHalfLength, pistonRodRadius)
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
        scale: Qt.vector3d(jointTailRadius, jointTailHalfHeight, jointTailRadius)
        eulerRotation: Qt.vector3d(90, 0, 0)
        materials: [jointTailMaterial]
    }

    // 7. ARM JOINT (orange, at j_arm)
    Model {
        source: "#Cylinder"
        position: j_arm
        scale: Qt.vector3d(jointArmRadius, jointArmHalfHeight, jointArmRadius)
        eulerRotation: Qt.vector3d(90, 0, 0)
        materials: [jointArmMaterial]
    }

    // 8. ROD JOINT (green, at j_rod)
    Model {
        source: "#Cylinder"
        position: j_rod
        scale: Qt.vector3d(jointRodRadius, jointRodHalfHeight, jointRodRadius)
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
        console.log("   pistonPosition:", pistonPositionM, "m")
        console.log("   rodLengthError:", rodLengthError.toFixed(4), "m")
    }
}
