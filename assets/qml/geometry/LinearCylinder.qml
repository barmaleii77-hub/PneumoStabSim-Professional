import QtQuick 6.10
import QtQuick3D 6.10
import "../components/GeometryCompat.js" as GeometryCompat
import CustomGeometry 1.0

/*
 * LinearCylinder - reusable helper for cylinders stretched between two points
 * Assumes geometry primarily lies in the X/Y plane (Z offsets are supported but
 * only used for midpoint calculation). Rotation is resolved around the Z axis,
 * which matches the planar lever/tail layout in the suspension assembly.
 */
Node {
    id: root

    // --- Required endpoints (scene units, metres in our simulation) ---
    required property vector3d startPoint
    required property vector3d endPoint

    // --- Appearance ---
    property real radius: 0.05
    property var material: null
    property list<Material> materialOverrides

    // --- Quality ---
    property int segments: 24
    property int rings: 1

    // --- Behaviour ---
    property real minimumLength: 1e-6
    property bool warnOnTinyLength: true

    readonly property vector3d _delta: Qt.vector3d(
        endPoint.x - startPoint.x,
        endPoint.y - startPoint.y,
        endPoint.z - startPoint.z
    )

    readonly property real _rawLength: Math.sqrt(
        _delta.x * _delta.x +
        _delta.y * _delta.y +
        _delta.z * _delta.z
    )

    readonly property real length: Math.max(_rawLength, minimumLength)
    readonly property vector3d midpoint: Qt.vector3d(
        (startPoint.x + endPoint.x) / 2,
        (startPoint.y + endPoint.y) / 2,
        (startPoint.z + endPoint.z) / 2
    )

    readonly property real safeRadius: Math.max(radius, 1e-5)

    readonly property real rotationDeg: Math.atan2(_delta.y, _delta.x) * 180 / Math.PI + 90

    Component.onCompleted: {
        if (warnOnTinyLength && _rawLength < minimumLength * 2)
            console.warn("LinearCylinder: endpoints nearly overlapping", startPoint, endPoint)
        // Применяем исходные параметры к процедурной геометрии
        proceduralGeometry.segments = segments
        proceduralGeometry.rings = rings
        proceduralGeometry.radius = safeRadius
        proceduralGeometry.length = length
    }

    onSegmentsChanged: proceduralGeometry.segments = segments
    onRingsChanged: proceduralGeometry.rings = rings
    onRadiusChanged: proceduralGeometry.radius = safeRadius
    onLengthChanged: proceduralGeometry.length = length
    onStartPointChanged: proceduralGeometry.length = length
    onEndPointChanged: proceduralGeometry.length = length

    ProceduralCylinderGeometry {
        id: proceduralGeometry
        objectName: "proceduralGeometry"
    }

    Model {
        id: cylinderModel
        objectName: "cylinderModel"
        position: root.midpoint
        eulerRotation: Qt.vector3d(0, 0, root.rotationDeg)
        // Базовый примитив: #Cylinder; затем пытаемся апгрейдить до CylinderMesh при наличии плагина
        source: "#Cylinder"
        // Используем процедурную геометрию, если доступна; иначе апгрейд через Helpers.
        geometry: proceduralGeometry
        Component.onCompleted: {
            // Попытка апгрейда только если proceduralGeometry не создан (fallback сценарий)
            if (!proceduralGeometry) {
                GeometryCompat.applyCylinderMesh(cylinderModel, root.segments, root.rings)
            }
        }
        scale: Qt.vector3d(root.safeRadius, root.length / 2, root.safeRadius)
        materials: root.material ? [root.material] : root.materialOverrides
    }
}
