pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import "components" as Components

Item {
    id: root

    implicitWidth: 140
    implicitHeight: 340

    property real minPressure: 0.0
    property real maxPressure: 250000.0
    property real userMinPressure: minPressure
    property real userMaxPressure: maxPressure
    property real atmosphericPressure: 101325.0
    property real pressure: minPressure
    property int tickCount: 6
    property var customTickLabelFormatter: null

    /** Optional explicit list of markers: { value, color, label }. */
    property var markers: []
    property bool showLegend: true

    readonly property real effectiveMinimum: _minValue(_rangeCandidates(), 0.0)
    readonly property real effectiveMaximum: _maxValue(_rangeCandidates(), 1.0)
    readonly property bool hasValidRange: effectiveMaximum > effectiveMinimum
    readonly property real normalizedPressure: hasValidRange ? _normalize(pressure) : 0.0
    readonly property real normalizedAtmosphere: hasValidRange ? _normalize(atmosphericPressure) : 0.0
    readonly property var effectiveMarkers: _normaliseMarkers()

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
        push(pressure)
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

    function _defaultMarkers() {
        return [
            { value: userMinPressure, color: Qt.rgba(0.46, 0.86, 0.52, 0.95), label: qsTr("Мин") },
            { value: userMaxPressure, color: Qt.rgba(0.95, 0.55, 0.4, 0.95), label: qsTr("Макс") },
            { value: atmosphericPressure, color: Qt.rgba(0.42, 0.72, 0.96, 0.95), label: qsTr("Атм") },
            { value: pressure, color: Qt.rgba(0.99, 0.83, 0.43, 0.95), label: qsTr("Тек") }
        ]
    }

    function _normaliseMarkers() {
        var list = Array.isArray(markers) && markers.length ? markers : _defaultMarkers()
        var normalized = []
        for (var i = 0; i < list.length; ++i) {
            var entry = list[i] || {}
            var value = Number(entry.value)
            if (!Number.isFinite(value))
                continue
            normalized.push({
                value: value,
                color: entry.color !== undefined ? entry.color : Qt.rgba(0.7, 0.85, 1.0, 0.95),
                label: entry.label !== undefined ? entry.label : ""
            })
        }
        return normalized
    }

    Rectangle {
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
                duration: 180
                easing.type: Easing.OutCubic
            }
        }
    }

    Canvas {
        id: scaleCanvas
        anchors.fill: parent
        anchors.margins: 12
        opacity: 0.92
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
                ctx.lineTo(w * 0.38, Math.round(y) + 0.5)
                ctx.stroke()

                var value = root.effectiveMinimum + range * ratio
                ctx.textAlign = "left"
                ctx.fillText(root._formatTickLabel(value), w * 0.42, Math.round(y))
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

    Item {
        id: markersLayer
        anchors.fill: parent
        anchors.margins: 12

        Repeater {
            model: root.effectiveMarkers
            delegate: Item {
                id: delegateRoot

                required property var modelData

                readonly property real _normalized: root.hasValidRange ? root._normalize(delegateRoot.modelData.value) : 0.0
                anchors.fill: parent

                Components.SphericalMarker {
                    id: sphere
                    width: 16
                    height: 16
                    color: delegateRoot.modelData.color || Qt.rgba(0.7, 0.85, 1.0, 0.95)
                    borderColor: Qt.rgba(0.18, 0.24, 0.32, 0.9)
                    anchors.right: parent.right
                    anchors.rightMargin: 2
                    y: Math.round((parent.height - height) * (1.0 - Math.max(0, Math.min(1, delegateRoot._normalized))))
                }

                Label {
                    id: legendLabel
                    text: delegateRoot.modelData.label || ""
                    visible: root.showLegend && legendLabel.text.length > 0
                    font.pixelSize: 10
                    color: "#c9d2e4"
                    anchors.verticalCenter: sphere.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 2
                    elide: Text.ElideRight
                }
            }
        }
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
                duration: 160
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
        function onMarkersChanged() { scaleCanvas.requestPaint() }
        function onWidthChanged() { scaleCanvas.requestPaint() }
        function onHeightChanged() { scaleCanvas.requestPaint() }
    }
}
