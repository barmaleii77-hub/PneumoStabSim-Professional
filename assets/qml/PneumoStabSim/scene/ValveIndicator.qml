import QtQuick 6.10
import QtQuick3D 6.10

Node {
    id: root

    property bool active: false
    property real intensity: 0.0
    property real sceneScale: 1.0
    property real radiusM: 0.08
    property real columnHeightM: 0.16
    property color activeColor: "#ffd166"
    property color inactiveColor: "#3b4252"

    readonly property real _clampedIntensity: Math.min(Math.max(intensity, 0.0), 1.0)
    readonly property color _currentColor: active ? activeColor : inactiveColor
    readonly property real _opacity: active ? (0.35 + _clampedIntensity * 0.55) : 0.2
    readonly property real _emissive: active ? (0.4 + _clampedIntensity * 1.6) : 0.0

    Model {
        id: valveBody
        mesh: SphereMesh {}
        scale: Qt.vector3d(
            root.radiusM * root.sceneScale,
            root.radiusM * root.sceneScale,
            root.radiusM * root.sceneScale
        )
        materials: PrincipledMaterial {
            baseColor: Qt.rgba(root._currentColor.r, root._currentColor.g, root._currentColor.b, 1)
            opacity: root._opacity
            alphaMode: PrincipledMaterial.AlphaBlend
            roughness: 0.4
            metalness: 0.0
            emissiveColor: Qt.rgba(root._currentColor.r, root._currentColor.g, root._currentColor.b, 1)
            emissiveFactor: root._emissive
        }
    }

    Model {
        id: gaugeColumn
        mesh: CylinderMesh {}
        visible: root.active && root._clampedIntensity > 0.01
        position: Qt.vector3d(
            0,
            -(root.radiusM + Math.max(0.0, root.columnHeightM * root._clampedIntensity / 2)) * root.sceneScale,
            0
        )
        scale: Qt.vector3d(
            root.radiusM * root.sceneScale * 0.4,
            Math.max(0.01, root.columnHeightM * root.sceneScale * root._clampedIntensity / 2),
            root.radiusM * root.sceneScale * 0.4
        )
        materials: PrincipledMaterial {
            baseColor: Qt.rgba(root.activeColor.r, root.activeColor.g, root.activeColor.b, 1)
            opacity: 0.3 + root._clampedIntensity * 0.6
            alphaMode: PrincipledMaterial.AlphaBlend
            roughness: 0.3
            metalness: 0.0
            emissiveColor: Qt.rgba(root.activeColor.r, root.activeColor.g, root.activeColor.b, 1)
            emissiveFactor: 0.5 + root._clampedIntensity * 1.8
        }
    }
}
