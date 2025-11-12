import QtQuick 6.10
import QtQuick3D 6.10
pragma ComponentBehavior: Bound
import "../../components/GeometryCompat.js" as GeometryCompat
import "../../components/MaterialCompat.js" as MaterialCompat

Node {
    id: root

    property bool active: false
    property real intensity: 0.0
    property real sceneScale: 1.0
    property real radiusM: 0.08
    property real columnHeightM: 0.16
    property color activeColor: "#ffd166"
    property color inactiveColor: "#3b4252"
    property string flowDirection: "exhaust"
    property real glowPhase: 0.0

    readonly property real _clampedIntensity: Math.min(Math.max(intensity, 0.0), 1.0)
    readonly property color _accentColor: flowDirection === "intake"
        ? Qt.rgba(0.35, 0.65, 1.0, 1.0)
        : Qt.rgba(1.0, 0.45, 0.2, 1.0)
    readonly property color _currentColor: active ? _blendColor(activeColor, _accentColor, 0.35 + _clampedIntensity * 0.45) : inactiveColor
    readonly property real _opacity: active ? (0.3 + _clampedIntensity * 0.6) : 0.18
    readonly property real _emissive: active ? (0.35 + _clampedIntensity * 1.8 + 0.3 * Math.sin(glowPhase * Math.PI * 2)) : 0.0

    function _blendColor(baseColor, overlayColor, factor) {
        factor = Math.max(0.0, Math.min(1.0, Number(factor)))
        var base = Qt.rgba(baseColor.r, baseColor.g, baseColor.b, 1)
        var overlay = Qt.rgba(overlayColor.r, overlayColor.g, overlayColor.b, 1)
        return Qt.rgba(
            base.r + (overlay.r - base.r) * factor,
            base.g + (overlay.g - base.g) * factor,
            base.b + (overlay.b - base.b) * factor,
            1
        )
    }

    NumberAnimation on glowPhase {
        id: glowAnimation
        from: 0
        to: 1
        duration: Math.max(500, 1800 - root._clampedIntensity * 800)
        loops: Animation.Infinite
        running: root.active
        easing.type: Easing.InOutSine
    }

    onGlowPhaseChanged: {
        MaterialCompat.applyEmissive(valveBodyMat, _currentColor, _emissive)
    }

    Model {
        id: valveBody
        source: "#Sphere"
        Component.onCompleted: GeometryCompat.applySphereMesh(valveBody, 24, 36)
        scale: Qt.vector3d(
            root.radiusM * root.sceneScale,
            root.radiusM * root.sceneScale,
            root.radiusM * root.sceneScale
        )
        materials: PrincipledMaterial {
            id: valveBodyMat
            baseColor: Qt.rgba(root._currentColor.r, root._currentColor.g, root._currentColor.b, 1)
            opacity: root._opacity
            alphaMode: PrincipledMaterial.Blend
            roughness: 0.4
            metalness: 0.0
            Component.onCompleted: MaterialCompat.applyEmissive(valveBodyMat, root._currentColor, root._emissive)
        }
    }

    Model {
        id: valveHalo
        source: "#Torus"
        visible: root.active
        scale: Qt.vector3d(
            root.radiusM * root.sceneScale * 1.05,
            root.radiusM * root.sceneScale * 1.05,
            root.radiusM * root.sceneScale * 1.05
        )
        materials: PrincipledMaterial {
            baseColor: Qt.rgba(root._currentColor.r, root._currentColor.g, root._currentColor.b, 1)
            opacity: 0.08 + root._clampedIntensity * 0.22
            alphaMode: PrincipledMaterial.Blend
            roughness: 0.9
            metalness: 0.0
        }
    }

    Model {
        id: gaugeColumn
        source: "#Cylinder"
        Component.onCompleted: GeometryCompat.applyCylinderMesh(gaugeColumn, 32, 1)
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
            alphaMode: PrincipledMaterial.Blend
            roughness: 0.3
            metalness: 0.0
        }
    }
}
