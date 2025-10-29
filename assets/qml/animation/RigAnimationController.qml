import QtQuick 6.10

QtObject {
    id: root

    // ------------------------------------------------------------------
    // Configuration (injected from SimulationRoot)
    // ------------------------------------------------------------------
    property bool smoothingEnabled: true
    property real smoothingDurationMs: 120.0
    property real angleSnapThresholdDeg: 65.0
    property real pistonSnapThresholdM: 0.05
    property string smoothingEasingName: "OutCubic"

    property int smoothingEasingType: Easing.OutCubic
    onSmoothingEasingNameChanged: smoothingEasingType = easingTypeForName(smoothingEasingName)
    Component.onCompleted: smoothingEasingType = easingTypeForName(smoothingEasingName)

    readonly property real animationDuration: Math.max(16, Number(smoothingDurationMs))

    // When true behaviours are temporarily disabled so values snap immediately
    property bool _smoothingOverride: false
    readonly property bool _behavioursEnabled: smoothingEnabled && !_smoothingOverride

    // ------------------------------------------------------------------
    // Lever angles (stored in radians, exposed in degrees via aliases)
    // ------------------------------------------------------------------
    property real flAngleRad: 0.0
    Behavior on flAngleRad {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    property real frAngleRad: 0.0
    Behavior on frAngleRad {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    property real rlAngleRad: 0.0
    Behavior on rlAngleRad {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    property real rrAngleRad: 0.0
    Behavior on rrAngleRad {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    // ------------------------------------------------------------------
    // Frame motion (heave/pitch/roll)
    // ------------------------------------------------------------------
    property real frameHeave: 0.0
    Behavior on frameHeave {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    property real frameRollRad: 0.0
    Behavior on frameRollRad {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    property real framePitchRad: 0.0
    Behavior on framePitchRad {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    // ------------------------------------------------------------------
    // Piston positions (metres)
    // ------------------------------------------------------------------
    property real pistonFl: 0.0
    Behavior on pistonFl {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    property real pistonFr: 0.0
    Behavior on pistonFr {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    property real pistonRl: 0.0
    Behavior on pistonRl {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    property real pistonRr: 0.0
    Behavior on pistonRr {
        enabled: root._behavioursEnabled
        NumberAnimation {
            duration: root.animationDuration
            easing.type: root.smoothingEasingType
        }
    }

    // ------------------------------------------------------------------
    // Derived helpers
    // ------------------------------------------------------------------
    readonly property real flAngleDeg: flAngleRad * 180 / Math.PI
    readonly property real frAngleDeg: frAngleRad * 180 / Math.PI
    readonly property real rlAngleDeg: rlAngleRad * 180 / Math.PI
    readonly property real rrAngleDeg: rrAngleRad * 180 / Math.PI

    readonly property real frameRollDeg: frameRollRad * 180 / Math.PI
    readonly property real framePitchDeg: framePitchRad * 180 / Math.PI

    readonly property var leverAnglesRad: ({
        fl: flAngleRad,
        fr: frAngleRad,
        rl: rlAngleRad,
        rr: rrAngleRad
    })

    readonly property var leverAnglesDeg: ({
        fl: flAngleDeg,
        fr: frAngleDeg,
        rl: rlAngleDeg,
        rr: rrAngleDeg
    })

    readonly property var pistonPositions: ({
        fl: pistonFl,
        fr: pistonFr,
        rl: pistonRl,
        rr: pistonRr
    })

    function easingTypeForName(name) {
        var key = String(name || "OutCubic").toLowerCase()
        switch (key) {
        case "linear": return Easing.Linear
        case "inquad": return Easing.InQuad
        case "outquad": return Easing.OutQuad
        case "inoutquad": return Easing.InOutQuad
        case "incubic": return Easing.InCubic
        case "outcubic": return Easing.OutCubic
        case "inoutcubic": return Easing.InOutCubic
        case "inquart": return Easing.InQuart
        case "outquart": return Easing.OutQuart
        case "inoutquart": return Easing.InOutQuart
        case "insine": return Easing.InSine
        case "outsine": return Easing.OutSine
        case "inoutsine": return Easing.InOutSine
        default:
            return Easing.OutCubic
        }
    }

    function _withOverride(fn) {
        var previous = _smoothingOverride
        _smoothingOverride = true
        try {
            fn()
        } finally {
            _smoothingOverride = previous
        }
    }

    function _applyRad(propertyName, rawValue, immediate) {
        if (rawValue === undefined || rawValue === null)
            return false
        var numeric = Number(rawValue)
        if (!isFinite(numeric))
            return false
        var snap = immediate
        if (!snap && angleSnapThresholdDeg > 0) {
            var current = Number(root[propertyName])
            if (isFinite(current)) {
                var delta = Math.abs((numeric - current) * 180 / Math.PI)
                if (delta >= angleSnapThresholdDeg)
                    snap = true
            }
        }
        if (snap || !smoothingEnabled) {
            _withOverride(function() { root[propertyName] = numeric })
        } else {
            root[propertyName] = numeric
        }
        return true
    }

    function _applyLinear(propertyName, rawValue, threshold, immediate) {
        if (rawValue === undefined || rawValue === null)
            return false
        var numeric = Number(rawValue)
        if (!isFinite(numeric))
            return false
        var snap = immediate
        if (!snap && threshold > 0) {
            var current = Number(root[propertyName])
            if (isFinite(current) && Math.abs(numeric - current) >= threshold)
                snap = true
        }
        if (snap || !smoothingEnabled) {
            _withOverride(function() { root[propertyName] = numeric })
        } else {
            root[propertyName] = numeric
        }
        return true
    }

    function applyLeverAnglesRadians(angles, options) {
        if (!angles)
            return false
        var immediate = options && options.immediate === true
        var updated = false
        if (angles.fl !== undefined)
            updated = _applyRad("flAngleRad", angles.fl, immediate) || updated
        if (angles.fr !== undefined)
            updated = _applyRad("frAngleRad", angles.fr, immediate) || updated
        if (angles.rl !== undefined)
            updated = _applyRad("rlAngleRad", angles.rl, immediate) || updated
        if (angles.rr !== undefined)
            updated = _applyRad("rrAngleRad", angles.rr, immediate) || updated
        return updated
    }

    function applyFrameMotion(frame, options) {
        if (!frame)
            return false
        var immediate = options && options.immediate === true
        var updated = false
        if (frame.heave !== undefined)
            updated = _applyLinear("frameHeave", frame.heave, pistonSnapThresholdM, immediate) || updated
        if (frame.roll !== undefined)
            updated = _applyRad("frameRollRad", frame.roll, immediate) || updated
        if (frame.pitch !== undefined)
            updated = _applyRad("framePitchRad", frame.pitch, immediate) || updated
        return updated
    }

    function applyPistonPositions(pistons, options) {
        if (!pistons)
            return false
        var immediate = options && options.immediate === true
        var updated = false
        if (pistons.fl !== undefined)
            updated = _applyLinear("pistonFl", pistons.fl, pistonSnapThresholdM, immediate) || updated
        if (pistons.fr !== undefined)
            updated = _applyLinear("pistonFr", pistons.fr, pistonSnapThresholdM, immediate) || updated
        if (pistons.rl !== undefined)
            updated = _applyLinear("pistonRl", pistons.rl, pistonSnapThresholdM, immediate) || updated
        if (pistons.rr !== undefined)
            updated = _applyLinear("pistonRr", pistons.rr, pistonSnapThresholdM, immediate) || updated
        return updated
    }

    function reset() {
        _withOverride(function() {
            flAngleRad = 0.0
            frAngleRad = 0.0
            rlAngleRad = 0.0
            rrAngleRad = 0.0
            frameHeave = 0.0
            frameRollRad = 0.0
            framePitchRad = 0.0
            pistonFl = 0.0
            pistonFr = 0.0
            pistonRl = 0.0
            pistonRr = 0.0
        })
    }
}
