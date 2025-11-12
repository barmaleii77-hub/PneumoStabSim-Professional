import QtQuick 6.10
import QtQuick3D 6.10
import QtQuick3D.Helpers 6.10
import QtQuick3D.Particles3D 6.10
import "../../components/GeometryCompat.js" as GeometryCompat
import "../../components/MaterialCompat.js" as MaterialCompat

pragma ComponentBehavior: Bound

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
    property real glowPhase: 0.0
    property bool particlesEnabled: true   // включение системы частиц

    readonly property real _intensityCeiling: Math.max(1e-6, Math.abs(maxIntensity))
    readonly property real normalizedIntensity: Math.min(Math.abs(flowIntensity) / _intensityCeiling, 1.0)
    readonly property real _directionSign: flowDirection === "exhaust" ? -1.0 : 1.0
    readonly property bool active: valveOpen && normalizedIntensity > 0.01
    readonly property color _activeColor: valveOpen ? (flowDirection === "exhaust" ? exhaustColor : intakeColor) : inactiveColor
    readonly property real _opacity: valveOpen ? (0.25 + normalizedIntensity * 0.65) : 0.18
    readonly property real _emissive: valveOpen ? (normalizedIntensity * 2.5) : 0.0
    readonly property real _glowStrength: valveOpen ? (0.4 + normalizedIntensity * 0.4) : 0.0
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

    NumberAnimation on glowPhase {
        id: glowAnimation
        from: 0
        to: 1
        duration: Math.max(400, 1500 - Math.min(0.98, root.animationSpeedFactor) * 900)
        loops: Animation.Infinite
        running: root.active
        easing.type: Easing.InOutQuad
    }

    onNormalizedIntensityChanged: {
        flowAnimation.duration = Math.max(250, 1400 - Math.min(0.98, animationSpeedFactor) * 900)
        glowAnimation.duration = Math.max(400, 1500 - Math.min(0.98, animationSpeedFactor) * 900)
        // реактивное обновление эмиссии
        MaterialCompat.applyEmissive(shaftMat, _activeColor, _emissive)
        MaterialCompat.applyEmissive(arrowHaloMat, _activeColor, _glowStrength * 2.0)
        if (particleMat)
            MaterialCompat.applyEmissive(particleMat, _activeColor, normalizedIntensity * 3.0)
        for (var i = 0; i < pulseRepeater.count; ++i) {
            var obj = pulseRepeater.itemAt(i)
            if (obj && obj.pulseMaterial) {
                MaterialCompat.applyEmissive(obj.pulseMaterial, _activeColor, normalizedIntensity * 1.2)
            }
        }
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

    // --- СИСТЕМА ЧАСТИЦ (вернута) ---
    ParticleSystem3D {
        id: flowParticles
        running: root.active && root.particlesEnabled
        // базовый материал частиц
        ModelParticle3D {
            id: particleDelegate
            maxAmount: 400
            delegate: Model {
                source: "#Sphere"
                scale: Qt.vector3d(0.05, 0.05, 0.05) * root.sceneScale
                materials: PrincipledMaterial {
                    id: particleMat
                    baseColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                    opacity: Math.min(0.9, 0.25 + root.normalizedIntensity * 0.5)
                    alphaMode: PrincipledMaterial.Blend
                    roughness: 0.4
                    metalness: 0.0
                    Component.onCompleted: MaterialCompat.applyEmissive(particleMat, root._activeColor, root.normalizedIntensity * 3.0)
                }
            }
        }
        // REPLACED: Emitter3D -> ParticleEmitter3D for Qt 6.10 compatibility
        ParticleEmitter3D {
            id: mainEmitter
            particle: particleDelegate
            enabled: root.active && root.particlesEnabled
            emitRate: 40 + root.normalizedIntensity * 160
            lifeSpan: 650
            lifeSpanVariation: 150
            velocity: VectorDirection3D { direction: Qt.vector3d(0, 0, root._directionSign * 1.0) }
            shape: ParticleShape3D {
                type: ParticleShape3D.Cylinder
                extents: Qt.vector3d(root.radiusM * root.sceneScale * 0.4, (root.bodyLengthM * root.sceneScale) / 2, root.radiusM * root.sceneScale * 0.4)
            }
        }
    }

    Node {
        id: arrowContent
        position: Qt.vector3d(0, 0, 0)

        Model {
            id: shaft
            source: "#Cylinder"
            Component.onCompleted: GeometryCompat.applyCylinderMesh(shaft, 32, 8)
            eulerRotation.x: 90
            scale: Qt.vector3d(
                root.radiusM * root.sceneScale,
                (root.bodyLengthM * root.sceneScale) / 2,
                root.radiusM * root.sceneScale
            )
            materials: PrincipledMaterial {
                id: shaftMat
                baseColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                opacity: root._opacity
                alphaMode: PrincipledMaterial.Blend
                roughness: 0.35
                metalness: 0.05
                Component.onCompleted: MaterialCompat.applyEmissive(shaftMat, root._activeColor, root._emissive)
            }
        }

        Model {
            id: arrowHalo
            source: "#Cylinder"
            Component.onCompleted: GeometryCompat.applyCylinderMesh(arrowHalo, 48, 8)
            eulerRotation.x: 90
            visible: root.active
            scale: Qt.vector3d(
                root.radiusM * root.sceneScale * 1.8,
                (root.bodyLengthM * root.sceneScale) / 2.1,
                root.radiusM * root.sceneScale * 1.8
            )
            materials: PrincipledMaterial {
                id: arrowHaloMat
                baseColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                opacity: root._glowStrength * 0.25
                alphaMode: PrincipledMaterial.Blend
                roughness: 1.0
                metalness: 0.0
                Component.onCompleted: MaterialCompat.applyEmissive(arrowHaloMat, root._activeColor, root._glowStrength * 2.0)
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
                    source: "#Cone"
                    Component.onCompleted: GeometryCompat.applyConeMesh(pulseModel, 24, 8)
                    position: Qt.vector3d(
                        0,
                        0,
                        root._directionSign * ((progress - 0.5) * root.travelDistanceM * root.sceneScale)
                    )
                    scale: Qt.vector3d(
                        root.radiusM * root.sceneScale * (0.55 + root.normalizedIntensity * 0.25),
                        root.headLengthM * root.sceneScale * 0.65,
                        root.radiusM * root.sceneScale * (0.55 + root.normalizedIntensity * 0.25)
                    )
                    eulerRotation.x: 90
                    eulerRotation.z: root._directionSign < 0 ? 180 : 0
                    materials: PrincipledMaterial {
                        id: pulseMaterial
                        baseColor: Qt.rgba(root._activeColor.r, root._activeColor.g, root._activeColor.b, 1)
                        opacity: Math.max(0.12, root.normalizedIntensity * 0.8)
                        alphaMode: PrincipledMaterial.Blend
                        roughness: 0.3
                        metalness: 0.0
                        Component.onCompleted: MaterialCompat.applyEmissive(pulseMaterial, root._activeColor, root.normalizedIntensity * 1.2)
                    }
                }
            }
        }

        Model {
            id: head
            source: "#Cone"
            Component.onCompleted: GeometryCompat.applyConeMesh(head, 32, 8)
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
                alphaMode: PrincipledMaterial.Blend
                roughness: 0.35
                metalness: 0.05
            }
        }
    }
}
