pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import "components" as Components

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

    function _defaultMarkers() {
        return [
            { value: userMinPressure, color: Qt.rgba(0.46, 0.86, 0.52, 0.95), label: qsTr("Мин") },
            { value: userMaxPressure, color: Qt.rgba(0.95, 0.55, 0.4, 0.95), label: qsTr("Макс") },
            { value: atmosphericPressure, color: Qt.rgba(0.42, 0.72, 0.96, 0.95), label: qsTr("Атм") },
            { value: pressure, color: Qt.rgba(0.99, 0.83, 0.43, 0.95), label: qsTr("Рез") }
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

        Item {
            id: markersLayer
            z: 2
            anchors.fill: parent

            Repeater {
                model: root.effectiveMarkers
                delegate: Item {
                    id: delegateRoot

                    required property var modelData

                    readonly property real _normalized: root.hasValidRange ? root._normalize(delegateRoot.modelData.value) : 0.0
                    width: parent.width
                    height: parent.height

                    Components.SphericalMarker {
                        id: markerSphere
                        width: 18
                        height: 18
                        color: delegateRoot.modelData.color || Qt.rgba(0.7, 0.85, 1.0, 0.95)
                        borderColor: Qt.rgba(0.16, 0.22, 0.3, 0.9)
                        anchors.horizontalCenter: parent.horizontalCenter
                        y: Math.round((parent.height - height) * (1.0 - Math.max(0, Math.min(1, delegateRoot._normalized))))
                    }

                    Label {
                        id: legendLabel
                        text: delegateRoot.modelData.label || ""
                        visible: root.showLegend && legendLabel.text.length > 0
                        font.pixelSize: 11
                        color: "#d9e1f2"
                        anchors.horizontalCenter: markerSphere.horizontalCenter
                        anchors.top: markerSphere.bottom
                        anchors.topMargin: 2
                    }
                }
            }
        }

        Canvas {
            id: overlay
            z: 1
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
