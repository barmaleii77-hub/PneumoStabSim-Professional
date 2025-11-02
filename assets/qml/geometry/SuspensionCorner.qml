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

    // Значения заполняются родительской сборкой. Здесь используются нули, чтобы
    // избежать неявных жёстко заданных параметров.
    property real leverLengthM: 0.0
    property real rodPosition: 0.0        // Fraction (0.0 - 1.0)
    property real cylinderLength: 0.0
    property real boreHead: 0.0
    property real rodDiameter: 0.0
    property real pistonThickness: 0.0
    property real pistonRodLength: 0.0
    property int cylinderSegments: 0
    property int cylinderRings: 0
    // Новый параметр длины хвостовика цилиндра (отрезок от j_tail до начала цилиндра)
    property real tailRodLength: 0.0

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
    readonly property real pistonRadius: Math.max(cylinderRadius * 0.92, 0.001)
    readonly property real pistonHalfThickness: Math.max(pistonThickness, 1e-4) / 2
    readonly property real pistonRodRadius: Math.max(rodDiameter / 2, 0.001)
    readonly property real tailRodRadius: Math.max(pistonRodRadius * 0.8, 0.001)
    readonly property real leverThickness: Math.max(pistonRodRadius * 1.2, 0.008)
    readonly property real jointBaseRadius: Math.max(cylinderRadius * 0.6, 0.01)
    readonly property real jointBaseHalfHeight: Math.max(cylinderRadius * 0.6, 0.01)
    readonly property real jointTailRadius: jointBaseRadius * jointTailScale
    readonly property real jointArmRadius: jointBaseRadius * jointArmScale
    readonly property real jointRodRadius: Math.max(pistonRodRadius * 1.1, 0.005) * jointRodScale
    readonly property real jointTailHalfHeight: jointBaseHalfHeight * jointTailScale
    readonly property real jointArmHalfHeight: jointBaseHalfHeight * jointArmScale
    readonly property real jointRodHalfHeight: Math.max(pistonRodRadius, 0.005) * jointRodScale

    // Pre-computed rod direction to keep rendering logic clean
    readonly property vector3d pistonRodDirection: {
        const dx = j_rod.x - pistonCenter.x
        const dy = j_rod.y - pistonCenter.y
        const length = Math.hypot(dx, dy)
        if (length < 1e-6)
            return Qt.vector3d(0, 1, 0)
        return Qt.vector3d(dx / length, dy / length, 0)
    }

    readonly property vector3d pistonRodEnd: Qt.vector3d(
        pistonCenter.x + pistonRodDirection.x * pistonRodLength,
        pistonCenter.y + pistonRodDirection.y * pistonRodLength,
        pistonCenter.z
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
    LinearCylinder {
        startPoint: j_tail
        endPoint: tailRodEnd
        radius: tailRodRadius
        material: tailRodMaterial
        minimumLength: 1e-5
    }

    // 3. CYLINDER BODY (transparent, fixed)
    LinearCylinder {
        startPoint: cylStart
        endPoint: cylEnd
        radius: cylinderRadius * 1.05
        material: cylinderMaterial
        warnOnTinyLength: false
        segments: cylinderSegments
        rings: cylinderRings
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
    LinearCylinder {
        startPoint: pistonCenter
        endPoint: pistonRodEnd
        radius: pistonRodRadius
        material: pistonRodMaterial
        minimumLength: 1e-5
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
