import QtQuick 6.10
import QtQuick3D 6.10

import "../components"
// qmllint disable import
import "../geometry"
import "."

/*
 * SuspensionAssembly - encapsulates the full pneumatic suspension rig
 * including the structural frame, four suspension corners and the
 * reflection probe used for physically based rendering. Geometry
 * calculations are centralised in the embedded `kinematics` helper to
 * keep SimulationRoot.qml free from repetitive trigonometry.
 */
Node {
    id: assembly

    // ------------------------------------------------------------------
    // Required context
    // ------------------------------------------------------------------
    required property Node worldRoot
    required property var geometryState
    required property SharedMaterials sharedMaterials

    // ------------------------------------------------------------------
    // Animation inputs (degrees for lever angles, metres for pistons)
    // ------------------------------------------------------------------
    property var leverAngles: ({ fl: 0.0, fr: 0.0, rl: 0.0, rr: 0.0 })
    property var pistonPositions: ({ fl: 0.0, fr: 0.0, rl: 0.0, rr: 0.0 })

    // ------------------------------------------------------------------
    // Scene scale & diagnostics
    // ------------------------------------------------------------------
    property real sceneScaleFactor: 1.0
    property real rodWarningThreshold: 0.001

    // ------------------------------------------------------------------
    // Reflection probe configuration
    // ------------------------------------------------------------------
    property bool reflectionProbeEnabled: true
    property real reflectionProbePadding: 0.15
    property int reflectionProbeQualityValue: ReflectionProbe.VeryHigh
    property int reflectionProbeRefreshModeValue: ReflectionProbe.EveryFrame
    property int reflectionProbeTimeSlicingValue: ReflectionProbe.IndividualFaces

    // ------------------------------------------------------------------
    // Convenience aliases
    // ------------------------------------------------------------------
    readonly property alias frontLeftCorner: flCorner
    readonly property alias frontRightCorner: frCorner
    readonly property alias rearLeftCorner: rlCorner
    readonly property alias rearRightCorner: rrCorner
    readonly property alias reflectionProbe: mainReflectionProbe

    // ------------------------------------------------------------------
    // Geometry helper centralising coordinate math
    // ------------------------------------------------------------------
    QtObject {
        id: kinematics

        function _normalisedSide(side) {
            return String(side).toLowerCase()
        }

        function isRear(side) {
            return _normalisedSide(side).charAt(0) === "r"
        }

        function isLeft(side) {
            return _normalisedSide(side).charAt(1) === "l"
        }

        function geometryValue(key, fallback) {
            const state = assembly.geometryState || {}
            if (state[key] !== undefined)
                return state[key]
            return fallback
        }

        function armZ(side) {
            const frameLength = geometryValue("frameLength", 3.4)
            const pivot = geometryValue("frameToPivot", 0.42)
            return isRear(side) ? frameLength - pivot : pivot
        }

        function armPosition(side) {
            const trackWidth = geometryValue("trackWidth", 2.34)
            const beamSize = geometryValue("beamSize", 0.12)
            const x = (isLeft(side) ? -1 : 1) * trackWidth / 2
            return Qt.vector3d(x, beamSize, armZ(side))
        }

        function tailPosition(side) {
            const arm = armPosition(side)
            const beamSize = geometryValue("beamSize", 0.12)
            const frameHeight = geometryValue("frameHeight", 0.65)
            return Qt.vector3d(arm.x, beamSize + frameHeight, arm.z)
        }

        function leverAngle(side) {
            const key = _normalisedSide(side)
            const angles = assembly.leverAngles || {}
            const raw = Number(angles[key])
            return isFinite(raw) ? raw : 0.0
        }

        function pistonPosition(side) {
            const key = _normalisedSide(side)
            const store = assembly.pistonPositions || {}
            const raw = Number(store[key])
            return isFinite(raw) ? raw : 0.0
        }
    }

    // Expose helper functions for consumers (SimulationRoot compatibility)
    function geometryValue(key, fallback) { return kinematics.geometryValue(key, fallback) }
    function cornerArmPosition(side) { return kinematics.armPosition(side) }
    function cornerTailPosition(side) { return kinematics.tailPosition(side) }
    function leverAngleFor(side) { return kinematics.leverAngle(side) }
    function pistonPositionFor(side) { return kinematics.pistonPosition(side) }

    function toSceneLength(meters) {
        const numeric = Number(meters)
        if (!isFinite(numeric))
            return 0.0
        return numeric * sceneScaleFactor
    }

    // Anchor the assembly node to the external world root so that any
    // transforms (frame heave/pitch/roll) apply uniformly to all children.
    parent: worldRoot

    Frame {
        id: frame
        worldRoot: assembly
        beamSizeM: assembly.geometryValue("beamSize", 0.12)
        frameHeightM: assembly.geometryValue("frameHeight", 0.65)
        frameLengthM: assembly.geometryValue("frameLength", 3.4)
        frameMaterial: assembly.sharedMaterials.frameMaterial
    }

    ReflectionProbe {
        id: mainReflectionProbe
        parent: assembly
        visible: assembly.reflectionProbeEnabled
        parallaxCorrection: true
        quality: assembly.reflectionProbeQualityValue
        refreshMode: assembly.reflectionProbeRefreshModeValue
        timeSlicing: assembly.reflectionProbeTimeSlicingValue
        position: {
            const beam = Math.max(assembly.geometryValue("beamSize", 0.0), 0)
            const frameHeight = Math.max(assembly.geometryValue("frameHeight", 0.0), 0)
            return Qt.vector3d(0, assembly.toSceneLength((beam / 2) + (frameHeight / 2)), 0)
        }
        boxSize: {
            const track = Math.max(assembly.geometryValue("trackWidth", 0.0), 0)
            const frameHeight = Math.max(assembly.geometryValue("frameHeight", 0.0), 0)
            const beam = Math.max(assembly.geometryValue("beamSize", 0.0), 0)
            const frameLength = Math.max(assembly.geometryValue("frameLength", 0.0), 0)
            const padding = Math.max(0, assembly.reflectionProbePadding) * 2
            return Qt.vector3d(
                        Math.max(1.0, assembly.toSceneLength(track + padding)),
                        Math.max(1.0, assembly.toSceneLength(frameHeight + beam + padding)),
                        Math.max(1.0, assembly.toSceneLength(frameLength + padding)))
        }
    }

    SuspensionCorner {
        id: flCorner
        j_arm: assembly.cornerArmPosition("fl")
        j_tail: assembly.cornerTailPosition("fl")
        leverAngle: assembly.leverAngleFor("fl")
        pistonPositionM: assembly.pistonPositionFor("fl")
        leverLengthM: assembly.geometryValue("leverLength", 0.75)
        rodPosition: assembly.geometryValue("rodPosition", 0.34)
        cylinderLength: assembly.geometryValue("cylinderLength", 0.46)
        boreHead: assembly.geometryValue("boreHead", 0.11)
        rodDiameter: assembly.geometryValue("rodDiameter", 0.035)
        pistonThickness: assembly.geometryValue("pistonThickness", 0.025)
        pistonRodLength: assembly.geometryValue("pistonRodLength", 0.32)
        tailRodLength: assembly.geometryValue("tailRodLength", 0.18)
        cylinderSegments: assembly.geometryValue("cylinderSegments", 64)
        cylinderRings: assembly.geometryValue("cylinderRings", 8)
        leverMaterial: assembly.sharedMaterials.leverMaterial
        tailRodMaterial: assembly.sharedMaterials.tailRodMaterial
        cylinderMaterial: assembly.sharedMaterials.cylinderMaterial
        pistonBodyMaterial: assembly.sharedMaterials.pistonBodyMaterial
        pistonRodMaterial: assembly.sharedMaterials.pistonRodMaterial
        jointTailMaterial: assembly.sharedMaterials.jointTailMaterial
        jointArmMaterial: assembly.sharedMaterials.jointArmMaterial
        jointRodMaterial: AnimatedRodMaterial {
            okColor: assembly.sharedMaterials.jointRodOkColor
            warningColor: assembly.sharedMaterials.jointRodErrorColor
            warning: flCorner.rodLengthError > assembly.rodWarningThreshold
        }
    }

    SuspensionCorner {
        id: frCorner
        j_arm: assembly.cornerArmPosition("fr")
        j_tail: assembly.cornerTailPosition("fr")
        leverAngle: assembly.leverAngleFor("fr")
        pistonPositionM: assembly.pistonPositionFor("fr")
        leverLengthM: assembly.geometryValue("leverLength", 0.75)
        rodPosition: assembly.geometryValue("rodPosition", 0.34)
        cylinderLength: assembly.geometryValue("cylinderLength", 0.46)
        boreHead: assembly.geometryValue("boreHead", 0.11)
        rodDiameter: assembly.geometryValue("rodDiameter", 0.035)
        pistonThickness: assembly.geometryValue("pistonThickness", 0.025)
        pistonRodLength: assembly.geometryValue("pistonRodLength", 0.32)
        tailRodLength: assembly.geometryValue("tailRodLength", 0.18)
        cylinderSegments: assembly.geometryValue("cylinderSegments", 64)
        cylinderRings: assembly.geometryValue("cylinderRings", 8)
        leverMaterial: assembly.sharedMaterials.leverMaterial
        tailRodMaterial: assembly.sharedMaterials.tailRodMaterial
        cylinderMaterial: assembly.sharedMaterials.cylinderMaterial
        pistonBodyMaterial: assembly.sharedMaterials.pistonBodyMaterial
        pistonRodMaterial: assembly.sharedMaterials.pistonRodMaterial
        jointTailMaterial: assembly.sharedMaterials.jointTailMaterial
        jointArmMaterial: assembly.sharedMaterials.jointArmMaterial
        jointRodMaterial: AnimatedRodMaterial {
            okColor: assembly.sharedMaterials.jointRodOkColor
            warningColor: assembly.sharedMaterials.jointRodErrorColor
            warning: frCorner.rodLengthError > assembly.rodWarningThreshold
        }
    }

    SuspensionCorner {
        id: rlCorner
        j_arm: assembly.cornerArmPosition("rl")
        j_tail: assembly.cornerTailPosition("rl")
        leverAngle: assembly.leverAngleFor("rl")
        pistonPositionM: assembly.pistonPositionFor("rl")
        leverLengthM: assembly.geometryValue("leverLength", 0.75)
        rodPosition: assembly.geometryValue("rodPosition", 0.34)
        cylinderLength: assembly.geometryValue("cylinderLength", 0.46)
        boreHead: assembly.geometryValue("boreHead", 0.11)
        rodDiameter: assembly.geometryValue("rodDiameter", 0.035)
        pistonThickness: assembly.geometryValue("pistonThickness", 0.025)
        pistonRodLength: assembly.geometryValue("pistonRodLength", 0.32)
        tailRodLength: assembly.geometryValue("tailRodLength", 0.18)
        cylinderSegments: assembly.geometryValue("cylinderSegments", 64)
        cylinderRings: assembly.geometryValue("cylinderRings", 8)
        leverMaterial: assembly.sharedMaterials.leverMaterial
        tailRodMaterial: assembly.sharedMaterials.tailRodMaterial
        cylinderMaterial: assembly.sharedMaterials.cylinderMaterial
        pistonBodyMaterial: assembly.sharedMaterials.pistonBodyMaterial
        pistonRodMaterial: assembly.sharedMaterials.pistonRodMaterial
        jointTailMaterial: assembly.sharedMaterials.jointTailMaterial
        jointArmMaterial: assembly.sharedMaterials.jointArmMaterial
        jointRodMaterial: AnimatedRodMaterial {
            okColor: assembly.sharedMaterials.jointRodOkColor
            warningColor: assembly.sharedMaterials.jointRodErrorColor
            warning: rlCorner.rodLengthError > assembly.rodWarningThreshold
        }
    }

    SuspensionCorner {
        id: rrCorner
        j_arm: assembly.cornerArmPosition("rr")
        j_tail: assembly.cornerTailPosition("rr")
        leverAngle: assembly.leverAngleFor("rr")
        pistonPositionM: assembly.pistonPositionFor("rr")
        leverLengthM: assembly.geometryValue("leverLength", 0.75)
        rodPosition: assembly.geometryValue("rodPosition", 0.34)
        cylinderLength: assembly.geometryValue("cylinderLength", 0.46)
        boreHead: assembly.geometryValue("boreHead", 0.11)
        rodDiameter: assembly.geometryValue("rodDiameter", 0.035)
        pistonThickness: assembly.geometryValue("pistonThickness", 0.025)
        pistonRodLength: assembly.geometryValue("pistonRodLength", 0.32)
        tailRodLength: assembly.geometryValue("tailRodLength", 0.18)
        cylinderSegments: assembly.geometryValue("cylinderSegments", 64)
        cylinderRings: assembly.geometryValue("cylinderRings", 8)
        leverMaterial: assembly.sharedMaterials.leverMaterial
        tailRodMaterial: assembly.sharedMaterials.tailRodMaterial
        cylinderMaterial: assembly.sharedMaterials.cylinderMaterial
        pistonBodyMaterial: assembly.sharedMaterials.pistonBodyMaterial
        pistonRodMaterial: assembly.sharedMaterials.pistonRodMaterial
        jointTailMaterial: assembly.sharedMaterials.jointTailMaterial
        jointArmMaterial: assembly.sharedMaterials.jointArmMaterial
        jointRodMaterial: AnimatedRodMaterial {
            okColor: assembly.sharedMaterials.jointRodOkColor
            warningColor: assembly.sharedMaterials.jointRodErrorColor
            warning: rrCorner.rodLengthError > assembly.rodWarningThreshold
        }
    }
}
