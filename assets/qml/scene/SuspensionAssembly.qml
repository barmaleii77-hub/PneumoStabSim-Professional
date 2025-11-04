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
    required property var materialsDefaults
    property var geometryDefaults: null
    property var emptyGeometryDefaults: null

    QtObject {
        id: defaultsBridge
        readonly property var emptyGeometryDefaults: ({})
    }

    readonly property var resolvedEmptyGeometryDefaults: emptyGeometryDefaults && typeof emptyGeometryDefaults === "object"
        ? emptyGeometryDefaults
        : defaultsBridge.emptyGeometryDefaults

    readonly property var resolvedGeometryDefaults: geometryDefaults && typeof geometryDefaults === "object"
        ? geometryDefaults
        : resolvedEmptyGeometryDefaults

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
    // Padding stored in metres; SimulationRoot provides SI values.
    property real reflectionProbePaddingM: 0.15
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

        readonly property var aliasMap: ({
            frameLength: ["frame_length", "frame_length_m", "wheelbase"],
            frameHeight: ["frame_height", "frame_height_m"],
            beamSize: ["beam_size", "frame_beam_size", "frame_beam_size_m"],
            trackWidth: ["track", "track_width", "track_width_m"],
            frameToPivot: ["frame_to_pivot", "frame_to_pivot_m"],
            leverLength: ["lever_length", "lever_length_m"],
            rodPosition: ["rod_position", "attachFrac"],
            cylinderLength: ["cylinder_length", "cylinder_body_length", "cylinder_body_length_m"],
            boreHead: ["bore_head", "bore", "bore_d", "cyl_diam", "cyl_diam_m"],
            rodDiameter: ["rod_diameter", "rod_diameter_m", "rod_diameter_rear_m"],
            pistonThickness: ["piston_thickness", "piston_thickness_m"],
            pistonRodLength: ["piston_rod_length", "piston_rod_length_m"],
            tailRodLength: ["tail_rod_length", "tail_rod_length_m"],
            cylinderSegments: ["cylinder_segments"],
            cylinderRings: ["cylinder_rings"]
        })

        function _lookup(source, key) {
            if (!source || typeof source !== "object")
                return undefined
            if (source[key] !== undefined)
                return source[key]
            var aliases = aliasMap[key] || []
            for (var i = 0; i < aliases.length; ++i) {
                var alias = aliases[i]
                if (source[alias] !== undefined)
                    return source[alias]
            }
            return undefined
        }

        function _numeric(value) {
            var numeric = Number(value)
            return isFinite(numeric) ? numeric : undefined
        }

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
            var stateValue = _numeric(_lookup(assembly.geometryState, key))
            if (stateValue !== undefined)
                return stateValue
            var defaultValue = _numeric(_lookup(assembly.resolvedGeometryDefaults, key))
            if (defaultValue !== undefined)
                return defaultValue
            var fallbackValue = _numeric(fallback)
            if (fallbackValue !== undefined)
                return fallbackValue
            return 0.0
        }

        function armZ(side) {
            const frameLength = geometryValue("frameLength")
            const pivot = geometryValue("frameToPivot")
            const halfLength = frameLength / 2
            const offset = halfLength - pivot
            return isRear(side) ? offset : -offset
        }

        function armPosition(side) {
            const trackWidth = geometryValue("trackWidth")
            const beamSize = geometryValue("beamSize")
            const x = (isLeft(side) ? -1 : 1) * trackWidth / 2
            return Qt.vector3d(x, beamSize, armZ(side))
        }

        function tailPosition(side) {
            const arm = armPosition(side)
            const beamSize = geometryValue("beamSize")
            const frameHeight = geometryValue("frameHeight")
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
        beamSizeM: assembly.geometryValue("beamSize")
        frameHeightM: assembly.geometryValue("frameHeight")
        frameLengthM: assembly.geometryValue("frameLength")
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
            const beam = Math.max(assembly.geometryValue("beamSize"), 0)
            const frameHeight = Math.max(assembly.geometryValue("frameHeight"), 0)
            return Qt.vector3d(0, assembly.toSceneLength((beam / 2) + (frameHeight / 2)), 0)
        }
        boxSize: {
            const track = Math.max(assembly.geometryValue("trackWidth"), 0)
            const frameHeight = Math.max(assembly.geometryValue("frameHeight"), 0)
            const beam = Math.max(assembly.geometryValue("beamSize"), 0)
            const frameLength = Math.max(assembly.geometryValue("frameLength"), 0)
            const padding = Math.max(0, assembly.reflectionProbePaddingM) * 2
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
        leverLengthM: assembly.geometryValue("leverLength")
        rodPosition: assembly.geometryValue("rodPosition")
        cylinderLength: assembly.geometryValue("cylinderLength")
        boreHead: assembly.geometryValue("boreHead")
        rodDiameter: assembly.geometryValue("rodDiameter")
        pistonThickness: assembly.geometryValue("pistonThickness")
        pistonRodLength: assembly.geometryValue("pistonRodLength")
        tailRodLength: assembly.geometryValue("tailRodLength")
        cylinderSegments: Math.max(3, Math.round(assembly.geometryValue("cylinderSegments")))
        cylinderRings: Math.max(1, Math.round(assembly.geometryValue("cylinderRings")))
        leverMaterial: assembly.sharedMaterials.leverMaterial
        tailRodMaterial: assembly.sharedMaterials.tailRodMaterial
        cylinderMaterial: assembly.sharedMaterials.cylinderMaterial
        pistonBodyMaterial: assembly.sharedMaterials.pistonBodyMaterial
        pistonRodMaterial: assembly.sharedMaterials.pistonRodMaterial
        jointTailMaterial: assembly.sharedMaterials.jointTailMaterial
        jointArmMaterial: assembly.sharedMaterials.jointArmMaterial
        jointRodMaterial: AnimatedRodMaterial {
            materialsDefaults: assembly.materialsDefaults
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
        leverLengthM: assembly.geometryValue("leverLength")
        rodPosition: assembly.geometryValue("rodPosition")
        cylinderLength: assembly.geometryValue("cylinderLength")
        boreHead: assembly.geometryValue("boreHead")
        rodDiameter: assembly.geometryValue("rodDiameter")
        pistonThickness: assembly.geometryValue("pistonThickness")
        pistonRodLength: assembly.geometryValue("pistonRodLength")
        tailRodLength: assembly.geometryValue("tailRodLength")
        cylinderSegments: Math.max(3, Math.round(assembly.geometryValue("cylinderSegments")))
        cylinderRings: Math.max(1, Math.round(assembly.geometryValue("cylinderRings")))
        leverMaterial: assembly.sharedMaterials.leverMaterial
        tailRodMaterial: assembly.sharedMaterials.tailRodMaterial
        cylinderMaterial: assembly.sharedMaterials.cylinderMaterial
        pistonBodyMaterial: assembly.sharedMaterials.pistonBodyMaterial
        pistonRodMaterial: assembly.sharedMaterials.pistonRodMaterial
        jointTailMaterial: assembly.sharedMaterials.jointTailMaterial
        jointArmMaterial: assembly.sharedMaterials.jointArmMaterial
        jointRodMaterial: AnimatedRodMaterial {
            materialsDefaults: assembly.materialsDefaults
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
        leverLengthM: assembly.geometryValue("leverLength")
        rodPosition: assembly.geometryValue("rodPosition")
        cylinderLength: assembly.geometryValue("cylinderLength")
        boreHead: assembly.geometryValue("boreHead")
        rodDiameter: assembly.geometryValue("rodDiameter")
        pistonThickness: assembly.geometryValue("pistonThickness")
        pistonRodLength: assembly.geometryValue("pistonRodLength")
        tailRodLength: assembly.geometryValue("tailRodLength")
        cylinderSegments: Math.max(3, Math.round(assembly.geometryValue("cylinderSegments")))
        cylinderRings: Math.max(1, Math.round(assembly.geometryValue("cylinderRings")))
        leverMaterial: assembly.sharedMaterials.leverMaterial
        tailRodMaterial: assembly.sharedMaterials.tailRodMaterial
        cylinderMaterial: assembly.sharedMaterials.cylinderMaterial
        pistonBodyMaterial: assembly.sharedMaterials.pistonBodyMaterial
        pistonRodMaterial: assembly.sharedMaterials.pistonRodMaterial
        jointTailMaterial: assembly.sharedMaterials.jointTailMaterial
        jointArmMaterial: assembly.sharedMaterials.jointArmMaterial
        jointRodMaterial: AnimatedRodMaterial {
            materialsDefaults: assembly.materialsDefaults
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
        leverLengthM: assembly.geometryValue("leverLength")
        rodPosition: assembly.geometryValue("rodPosition")
        cylinderLength: assembly.geometryValue("cylinderLength")
        boreHead: assembly.geometryValue("boreHead")
        rodDiameter: assembly.geometryValue("rodDiameter")
        pistonThickness: assembly.geometryValue("pistonThickness")
        pistonRodLength: assembly.geometryValue("pistonRodLength")
        tailRodLength: assembly.geometryValue("tailRodLength")
        cylinderSegments: Math.max(3, Math.round(assembly.geometryValue("cylinderSegments")))
        cylinderRings: Math.max(1, Math.round(assembly.geometryValue("cylinderRings")))
        leverMaterial: assembly.sharedMaterials.leverMaterial
        tailRodMaterial: assembly.sharedMaterials.tailRodMaterial
        cylinderMaterial: assembly.sharedMaterials.cylinderMaterial
        pistonBodyMaterial: assembly.sharedMaterials.pistonBodyMaterial
        pistonRodMaterial: assembly.sharedMaterials.pistonRodMaterial
        jointTailMaterial: assembly.sharedMaterials.jointTailMaterial
        jointArmMaterial: assembly.sharedMaterials.jointArmMaterial
        jointRodMaterial: AnimatedRodMaterial {
            materialsDefaults: assembly.materialsDefaults
            okColor: assembly.sharedMaterials.jointRodOkColor
            warningColor: assembly.sharedMaterials.jointRodErrorColor
            warning: rrCorner.rodLengthError > assembly.rodWarningThreshold
        }
    }

    Component.onCompleted: {
        console.log("✅ SuspensionAssembly loaded (all components initialized)")
    }
}
