pragma ComponentBehavior: Bound

import QtQuick 6.10

Item {
    id: root

    implicitWidth: 120
    implicitHeight: 320

    /**
     * Minimum simulated pressure (Pa).
     * Bound by SimulationPanel to SettingsManager snapshot: current.pneumatic.* thresholds.
     */
    property real minPressure: 0.0

    /**
     * Maximum simulated pressure (Pa).
     * Bound by SimulationPanel to SettingsManager snapshot: current.pneumatic.* thresholds.
     */
    property real maxPressure: 250000.0

    /**
     * User supplied minimum pressure override (Pa).
     * Mirrors config key receiver.user_min_pressure_pa when provided.
     */
    property real userMinPressure: minPressure

    /**
     * User supplied maximum pressure override (Pa).
     * Mirrors config key receiver.user_max_pressure_pa when provided.
     */
    property real userMaxPressure: maxPressure

    /**
     * Atmospheric pressure used as reference (Pa).
     * Linked to graphics.scene.environment.atmosphere.pressure or default 101325 Па.
     */
    property real atmosphericPressure: 101325.0

    /**
     * Current pressure value to visualise (Pa).
     */
    property real pressure: minPressure

    /**
     * Number of scale divisions.
     */
    property int tickCount: 6

    /**
     * Optional custom formatter for tick labels.
     */
    property var customTickLabelFormatter: null

    /**
     * Derived effective minimum that respects user limits and atmosphere.
     */
    readonly property real effectiveMinimum: _minValue(_rangeCandidates(), 0.0)

    /**
     * Derived effective maximum that respects user limits and atmosphere.
     */
    readonly property real effectiveMaximum: _maxValue(_rangeCandidates(), 1.0)

    /**
     * Flag indicating the range can be normalised.
     */
    readonly property bool hasValidRange: effectiveMaximum > effectiveMinimum

    /**
     * Normalised pressure in range 0..1.
     */
    readonly property real normalizedPressure: hasValidRange ? _normalize(pressure) : 0.0

    /**
     * Normalised atmospheric pressure in range 0..1.
     */
    readonly property real normalizedAtmosphere: hasValidRange ? _normalize(atmosphericPressure) : 0.0

    /**
     * Helper that gathers finite range candidates.
     */
    function _rangeCandidates() {
        var values = []
        function push(value) {
            var numeric = Number(value)
            if (Number.isFinite(numeric))
                values.push(numeric)
        }
        push(minPressure)
        push(maxPressure)
        push(userMinPressure)
        push(userMaxPressure)
        push(atmosphericPressure)
        if (values.length === 0) {
            values.push(0.0)
            values.push(1.0)
        } else if (values.length === 1) {
            values.push(values[0] + 1.0)
        }
        return values
    }

    function _minValue(values, fallback) {
        if (!values.length)
            return fallback
        var min = values[0]
        for (var i = 1; i < values.length; ++i) {
            if (values[i] < min)
                min = values[i]
        }
        return min
    }

    function _maxValue(values, fallback) {
        if (!values.length)
            return fallback
        var max = values[0]
        for (var i = 1; i < values.length; ++i) {
            if (values[i] > max)
                max = values[i]
        }
        return max
    }

    function _normalize(value) {
        var min = effectiveMinimum
        var max = effectiveMaximum
        if (!hasValidRange)
            return 0.0
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = min
        var ratio = (numeric - min) / (max - min)
        if (!Number.isFinite(ratio))
            ratio = 0.0
        if (ratio < 0.0)
            ratio = 0.0
        else if (ratio > 1.0)
            ratio = 1.0
        return ratio
    }

    function _formatTickLabel(value) {
        var formatter = customTickLabelFormatter
        if (formatter && typeof formatter === "function") {
            try {
                return formatter(value)
            } catch (error) {
                console.warn("PressureScale: custom formatter failed", error)
            }
        }
        return Number(value).toLocaleString(Qt.locale(), {
            maximumFractionDigits: 0,
            minimumFractionDigits: 0
        })
    }

    Rectangle {
        id: background
        anchors.fill: parent
        radius: 12
        color: Qt.rgba(0.07, 0.09, 0.13, 0.88)
        border.width: 1
        border.color: Qt.rgba(0.2, 0.27, 0.35, 0.9)
    }

    Rectangle {
        id: levelFill
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            margins: 12
        }
        radius: 8
        height: Math.round((root.height - 24) * root.normalizedPressure)
        color: Qt.rgba(0.36, 0.67, 1.0, 0.3)
        border.width: 0
        Behavior on height {
            NumberAnimation {
                duration: 160
                easing.type: Easing.OutCubic
            }
        }
    }

    Canvas {
        id: scaleCanvas
        anchors.fill: parent
        anchors.margins: 12
        opacity: 0.9
        onPaint: {
            var ctx = getContext("2d")
            var w = width
            var h = height
            ctx.reset()
            ctx.clearRect(0, 0, w, h)

            ctx.strokeStyle = "rgba(255, 255, 255, 0.15)"
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.rect(0.5, 0.5, w - 1, h - 1)
            ctx.stroke()

            var ticks = Math.max(2, root.tickCount)
            var range = root.effectiveMaximum - root.effectiveMinimum
            ctx.fillStyle = "rgba(220, 225, 235, 0.75)"
            ctx.textBaseline = "middle"
            ctx.font = "10px 'Fira Sans', 'Segoe UI', sans-serif"

            for (var i = 0; i <= ticks; ++i) {
                var ratio = i / ticks
                var y = h - ratio * h
                ctx.strokeStyle = i === 0 || i === ticks ? "rgba(255, 255, 255, 0.35)" : "rgba(255, 255, 255, 0.18)"
                ctx.lineWidth = i === 0 || i === ticks ? 2 : 1
                ctx.beginPath()
                ctx.moveTo(0, Math.round(y) + 0.5)
                ctx.lineTo(w * 0.35, Math.round(y) + 0.5)
                ctx.stroke()

                var value = root.effectiveMinimum + range * ratio
                ctx.textAlign = "left"
                ctx.fillText(root._formatTickLabel(value), w * 0.4, Math.round(y))
            }

            if (root.hasValidRange) {
                var atmoY = h - root.normalizedAtmosphere * h
                ctx.save()
                ctx.strokeStyle = "rgba(100, 180, 255, 0.9)"
                ctx.lineWidth = 1
                ctx.setLineDash([4, 3])
                ctx.beginPath()
                ctx.moveTo(0, Math.round(atmoY) + 0.5)
                ctx.lineTo(w, Math.round(atmoY) + 0.5)
                ctx.stroke()
                ctx.restore()
            }
        }

        Component.onCompleted: requestPaint()
    }

    Rectangle {
        id: indicator
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 6
        height: 4
        radius: 2
        color: Qt.rgba(1, 0.47, 0.34, 0.9)
        y: Math.round((root.height - 12) * (1.0 - root.normalizedPressure)) + 2
        Behavior on y {
            NumberAnimation {
                duration: 140
                easing.type: Easing.OutQuad
            }
        }
    }

    Connections {
        target: root
        function onPressureChanged() { scaleCanvas.requestPaint() }
        function onAtmosphericPressureChanged() { scaleCanvas.requestPaint() }
        function onMinPressureChanged() { scaleCanvas.requestPaint() }
        function onMaxPressureChanged() { scaleCanvas.requestPaint() }
        function onUserMinPressureChanged() { scaleCanvas.requestPaint() }
        function onUserMaxPressureChanged() { scaleCanvas.requestPaint() }
        function onTickCountChanged() { scaleCanvas.requestPaint() }
        function onWidthChanged() { scaleCanvas.requestPaint() }
        function onHeightChanged() { scaleCanvas.requestPaint() }
    }
}
