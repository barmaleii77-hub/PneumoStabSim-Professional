import QtQuick 6.10
import QtQuick3D 6.10

Node {
    id: root

    property real flowValue: 0.0
    property real flowIntensity: Math.abs(flowValue)
    property real maxFlow: 0.05
    property real maxIntensity: maxFlow
    property string flowDirection: flowValue >= 0 ? "intake" : "exhaust"
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

    readonly property real _intensityCeiling: Math.max(1e-6, Math.abs(maxIntensity))
    readonly property real normalizedIntensity: Math.min(Math.abs(flowIntensity) / _intensityCeiling, 1.0)
    readonly property real _directionSign: flowDirection === "exhaust" ? -1.0 : 1.0
    readonly property bool active: valveOpen && normalizedIntensity > 0.01
    readonly property color _activeColor: valveOpen ? (flowDirection === "exhaust" ? exhaustColor : intakeColor) : inactiveColor
    readonly property real _opacity: valveOpen ? (0.25 + normalizedIntensity * 0.65) : 0.18
    readonly property real _emissive: valveOpen ? (normalizedIntensity * 2.5) : 0.0
    property real animationSpeedFactor: normalizedIntensity
    property int pulseCount: active ? Math.max(3, Math.round(6 * normalizedIntensity + 2)) : 0

    eulerRotation: Qt.vector3d(orientationEuler.x, orientationEuler.y, orientationEuler.z)
    visible: normalizedIntensity > 0.001 || valveOpen

    NumberAnimation on flowPhase {
        id: flowAnimation
        from: 0
        to: 1
        duration: Math.max(250, 1400 - Math.min(0.98, root.animationSpeedFactor) * 900)
        loops: Animation.Infinite
        running: root.active
        easing.type: Easing.Linear
    }

    onNormalizedIntensityChanged: {
        flowAnimation.duration = Math.max(250, 1400 - Math.min(0.98, animationSpeedFactor) * 900)
    }

    onActiveChanged: {
        if (!active)
            flowPhase = 0.0
    }

    onAnimationSpeedFactorChanged: {
        flowAnimation.duration = Math.max(250, 1400 - Math.min(0.98, animationSpeedFactor) * 900)
    }

    onFlowPhaseChanged: {
        var offset = (flowPhase - 0.5) * travelDistanceM * sceneScale
        arrowContent.position = Qt.vector3d(0, 0, _directionSign * offset)
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

        Node {
            id: pulseContainer
            visible: root.active && root.pulseCount > 0

            Repeater {
                id: pulseRepeater
                model: root.pulseCount
                delegate: Model {
                    id: pulseModel
                    readonly property real progress: ((root.flowPhase + index / Math.max(1, root.pulseCount)) % 1)
                    mesh: SphereMesh {}
                    position: Qt.vector3d(
                        0,
                        0,
                        root._directionSign * ((progress - 0.5) * root.travelDistanceM * root.sceneScale)
                    )
                    scale: Qt.vector3d(
                        root.radiusM * root.sceneScale * 0.6,
                        root.radiusM * root.sceneScale * 0.6,
                        root.radiusM * root.sceneScale * 0.6
                    )
                    materials: PrincipledMaterial {
                        baseColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                        opacity: Math.max(0.15, root.normalizedIntensity * 0.85)
                        alphaMode: PrincipledMaterial.AlphaBlend
                        roughness: 0.25
                        metalness: 0.0
                        emissiveColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                        emissiveFactor: 0.6 + root.normalizedIntensity * 1.8
                    }
                }
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
