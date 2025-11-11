pragma ComponentBehavior: Bound

import QtQuick 6.10

Item {
    id: root

    implicitWidth: 220
    implicitHeight: 160

    /**
     * Pressure bounds provided by SimulationPanel from SettingsManager snapshots.
     * Keys: current.pneumatic.relief_* and receiver.user_*_pressure_pa when available.
     */
    property real minPressure: 0.0
    property real maxPressure: 250000.0
    property real userMinPressure: minPressure
    property real userMaxPressure: maxPressure

    /**
     * Atmospheric and reservoir pressures (Па) resolved via graphics.scene.environment
     * and pneumo.receiver.initial_pressure_pa respectively.
     */
    property real atmosphericPressure: 101325.0
    property real pressure: minPressure

    property color fluidColor: Qt.rgba(0.27, 0.6, 0.95, 0.65)
    property color surfaceHighlightColor: Qt.rgba(1, 1, 1, 0.45)
    property color borderColor: Qt.rgba(0.24, 0.31, 0.42, 0.9)
    property color atmosphericLineColor: Qt.rgba(0.55, 0.78, 1.0, 0.8)

    readonly property real effectiveMinimum: _minValue(_rangeCandidates(), 0.0)
    readonly property real effectiveMaximum: _maxValue(_rangeCandidates(), 1.0)
    readonly property bool hasValidRange: effectiveMaximum > effectiveMinimum
    readonly property real normalizedPressure: hasValidRange ? _normalize(pressure) : 0.0
    readonly property real normalizedAtmosphere: hasValidRange ? _normalize(atmosphericPressure) : 0.0

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

    Rectangle {
        id: vessel
        anchors.fill: parent
        radius: 16
        color: Qt.rgba(0.06, 0.09, 0.13, 0.88)
        border.width: 1
        border.color: root.borderColor
    }

    Item {
        id: cavity
        anchors {
            fill: parent
            margins: 16
        }
        clip: true

        Rectangle {
            id: fluid
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: Math.max(0, parent.height * root.normalizedPressure)
            color: root.fluidColor
            border.width: 0
            Behavior on height {
                NumberAnimation {
                    duration: 180
                    easing.type: Easing.OutCubic
                }
            }
        }

        Rectangle {
            id: surfaceHighlight
            anchors.left: parent.left
            anchors.right: parent.right
            height: 6
            radius: 3
            y: fluid.y - height
            visible: fluid.height > 8
            gradient: Gradient {
                GradientStop { position: 0.0; color: root.surfaceHighlightColor }
                GradientStop {
                    position: 1.0
                    color: Qt.rgba(
                        root.surfaceHighlightColor.r,
                        root.surfaceHighlightColor.g,
                        root.surfaceHighlightColor.b,
                        0.0)
                }
            }
            Behavior on y {
                NumberAnimation {
                    duration: 140
                    easing.type: Easing.OutQuad
                }
            }
        }

        Canvas {
            id: overlay
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d")
                var w = width
                var h = height
                ctx.reset()
                ctx.clearRect(0, 0, w, h)

                ctx.strokeStyle = "rgba(255, 255, 255, 0.12)"
                ctx.lineWidth = 1
                var divisions = 4
                for (var i = 1; i < divisions; ++i) {
                    var ratio = i / divisions
                    var y = h - ratio * h
                    ctx.beginPath()
                    ctx.moveTo(w * 0.05, Math.round(y) + 0.5)
                    ctx.lineTo(w * 0.95, Math.round(y) + 0.5)
                    ctx.stroke()
                }

                if (root.hasValidRange) {
                    var atmoY = h - root.normalizedAtmosphere * h
                    var stroke = root.atmosphericLineColor
                    if (!stroke || stroke === "" || stroke === "transparent")
                        stroke = "rgba(120, 180, 255, 0.85)"
                    ctx.save()
                    ctx.strokeStyle = stroke
                    ctx.lineWidth = 2
                    ctx.setLineDash([5, 4])
                    ctx.beginPath()
                    ctx.moveTo(0, Math.round(atmoY) + 0.5)
                    ctx.lineTo(w, Math.round(atmoY) + 0.5)
                    ctx.stroke()
                    ctx.restore()
                }
            }

            Component.onCompleted: requestPaint()
        }
    }

    Text {
        id: pressureLabel
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            bottomMargin: 8
        }
        text: qsTr("Давление: %1 Па").arg(Number(root.pressure).toLocaleString(Qt.locale(), {
            maximumFractionDigits: 0,
            minimumFractionDigits: 0
        }))
        horizontalAlignment: Text.AlignHCenter
        color: "#d7dee7"
        font.pixelSize: 14
    }

    Connections {
        target: root
        function onPressureChanged() { overlay.requestPaint() }
        function onAtmosphericPressureChanged() { overlay.requestPaint() }
        function onMinPressureChanged() { overlay.requestPaint() }
        function onMaxPressureChanged() { overlay.requestPaint() }
        function onUserMinPressureChanged() { overlay.requestPaint() }
        function onUserMaxPressureChanged() { overlay.requestPaint() }
        function onWidthChanged() { overlay.requestPaint() }
        function onHeightChanged() { overlay.requestPaint() }
    }
}
