import QtQuick 6.10
import QtQuick3D 6.10

Node {
    id: root

    property real flowValue: 0.0
    property real maxFlow: 0.05
    property bool valveOpen: true
    property color intakeColor: "#3fc1ff"
    property color exhaustColor: "#ff6b6b"
    property color inactiveColor: "#455066"
    property real sceneScale: 1.0
    property real bodyLengthM: 0.18
    property real headLengthM: 0.1
    property real radiusM: 0.045
    property real travelDistanceM: 0.24
    property vector3d orientationEuler: Qt.vector3d(0, 0, 0)
    property string lineLabel: ""
    property real flowPhase: 0.0

    readonly property real _maxMagnitude: Math.max(1e-6, Math.abs(maxFlow))
    readonly property real normalizedIntensity: Math.min(Math.abs(flowValue) / _maxMagnitude, 1.0)
    readonly property bool active: valveOpen && normalizedIntensity > 0.01
    readonly property color _activeColor: valveOpen ? (flowValue >= 0 ? intakeColor : exhaustColor) : inactiveColor
    readonly property real _opacity: valveOpen ? (0.25 + normalizedIntensity * 0.65) : 0.18
    readonly property real _emissive: valveOpen ? (normalizedIntensity * 2.5) : 0.0

    eulerRotation: Qt.vector3d(orientationEuler.x, orientationEuler.y, orientationEuler.z)
    visible: normalizedIntensity > 0.001 || valveOpen

    NumberAnimation on flowPhase {
        id: flowAnimation
        from: 0
        to: 1
        duration: Math.max(250, 1400 - root.normalizedIntensity * 900)
        loops: Animation.Infinite
        running: root.active
        easing.type: Easing.Linear
    }

    onNormalizedIntensityChanged: {
        flowAnimation.duration = Math.max(250, 1400 - normalizedIntensity * 900)
    }

    onActiveChanged: {
        if (!active)
            flowPhase = 0.0
    }

    onFlowPhaseChanged: {
        var direction = flowValue >= 0 ? 1 : -1
        var offset = (flowPhase - 0.5) * travelDistanceM * sceneScale
        arrowContent.position = Qt.vector3d(0, 0, direction * offset)
    }

    Node {
        id: arrowContent
        position: Qt.vector3d(0, 0, 0)

        Model {
            id: shaft
            mesh: CylinderMesh {}
            eulerRotation.x: 90
            scale: Qt.vector3d(
                root.radiusM * root.sceneScale,
                (root.bodyLengthM * root.sceneScale) / 2,
                root.radiusM * root.sceneScale
            )
            materials: PrincipledMaterial {
                baseColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                opacity: root._opacity
                alphaMode: PrincipledMaterial.AlphaBlend
                roughness: 0.35
                metalness: 0.05
                emissiveColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                emissiveFactor: root._emissive
            }
        }

        Model {
            id: head
            mesh: ConeMesh {}
            eulerRotation.x: 90
            position: Qt.vector3d(0, 0, (root.bodyLengthM * root.sceneScale) / 2)
            scale: Qt.vector3d(
                root.radiusM * root.sceneScale * 1.6,
                root.headLengthM * root.sceneScale,
                root.radiusM * root.sceneScale * 1.6
            )
            materials: PrincipledMaterial {
                baseColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                opacity: root._opacity
                alphaMode: PrincipledMaterial.AlphaBlend
                roughness: 0.35
                metalness: 0.05
                emissiveColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                emissiveFactor: root._emissive
            }
        }
    }
}
