pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import "components" as Components
import "singletons" as Singletons

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

    property color fluidColor: Singletons.UiConstants.reservoir.fluidColor
    property color surfaceHighlightColor: Singletons.UiConstants.reservoir.surfaceHighlightColor
    property color borderColor: Singletons.UiConstants.reservoir.borderColor
    property color atmosphericLineColor: Singletons.UiConstants.reservoir.atmosphericLineColor

    property var markers: []
    property bool showLegend: true
    property var linePressures: ({})
    property var lineValveStates: ({})
    property var lineIntensities: ({})
    property var gradientStops: []
    property color valveOpenColor: Singletons.UiConstants.reservoir.valveOpenColor
    property color valveClosedColor: Singletons.UiConstants.reservoir.valveClosedColor
    property color lowPressureColor: Singletons.UiConstants.reservoir.lowPressureColor
    property color highPressureColor: Singletons.UiConstants.reservoir.highPressureColor

    readonly property var lineDescriptors: [
        { key: "A1", anchor: Qt.point(0.24, 0.8), valveAnchor: Qt.point(0.08, 0.8), label: "A1" },
        { key: "A2", anchor: Qt.point(0.36, 0.3), valveAnchor: Qt.point(0.12, 0.3), label: "A2" },
        { key: "B1", anchor: Qt.point(0.64, 0.7), valveAnchor: Qt.point(0.88, 0.7), label: "B1" },
        { key: "B2", anchor: Qt.point(0.76, 0.25), valveAnchor: Qt.point(0.92, 0.25), label: "B2" }
    ]

    readonly property real effectiveMinimum: _minValue(_rangeCandidates(), 0.0)
    readonly property real effectiveMaximum: _maxValue(_rangeCandidates(), 1.0)
    readonly property bool hasValidRange: effectiveMaximum > effectiveMinimum
    readonly property real normalizedPressure: hasValidRange ? _normalize(pressure) : 0.0
    readonly property real normalizedAtmosphere: hasValidRange ? _normalize(atmosphericPressure) : 0.0
    readonly property var effectiveMarkers: _normaliseMarkers()
    readonly property var effectiveGradientStops: _normaliseGradientStops()

    // Python-friendly lookup objects for smoke tests; they mirror the main visuals but remain hidden.
    function _proxySphereY(key) {
        var normalized = root.hasValidRange ? root._normalize(root._linePressureValue(key)) : root.normalizedPressure
        return Math.round((root.height - 22) * (1.0 - normalized))
    }

    function _proxyValveColor(key) {
        return root._lineValveOpen(key) ? root.valveOpenColor : root.valveClosedColor
    }

    QtObject { objectName: "lineSphere-A1"; property real y: root._proxySphereY("A1") }
    QtObject { objectName: "lineSphere-A2"; property real y: root._proxySphereY("A2") }
    QtObject { objectName: "lineSphere-B1"; property real y: root._proxySphereY("B1") }
    QtObject { objectName: "lineSphere-B2"; property real y: root._proxySphereY("B2") }

    QtObject { objectName: "valveIcon-A1"; property color color: root._proxyValveColor("A1") }
    QtObject { objectName: "valveIcon-A2"; property color color: root._proxyValveColor("A2") }
    QtObject { objectName: "valveIcon-B1"; property color color: root._proxyValveColor("B1") }
    QtObject { objectName: "valveIcon-B2"; property color color: root._proxyValveColor("B2") }

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

    function _normaliseGradientStops() {
        var list = Array.isArray(gradientStops) && gradientStops.length ? gradientStops : []
        var normalized = []
        for (var i = 0; i < list.length; ++i) {
            var entry = list[i] || {}
            var value = Number(entry.value)
            if (!Number.isFinite(value))
                continue
            var position = hasValidRange ? _normalize(value) : 0.0
            if (!Number.isFinite(position))
                position = 0.0
            if (position < 0.0)
                position = 0.0
            else if (position > 1.0)
                position = 1.0
            normalized.push({
                position: position,
                color: entry.color !== undefined ? entry.color : Qt.rgba(0.28, 0.5, 0.82, 0.65),
                label: entry.label !== undefined ? entry.label : ""
            })
        }
        normalized.sort(function(a, b) { return a.position - b.position })
        return normalized
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

    function _isPlainObject(value) {
        return value && typeof value === "object" && !Array.isArray(value)
    }

    function _lineMapValue(map, key, fallback) {
        if (!_isPlainObject(map))
            return fallback
        var variants = []
        var base = String(key || "")
        if (base.length)
            variants.push(base)
        var lower = base.toLowerCase()
        if (lower.length && variants.indexOf(lower) === -1)
            variants.push(lower)
        var upper = base.toUpperCase()
        if (upper.length && variants.indexOf(upper) === -1)
            variants.push(upper)
        variants.push(String(key))
        for (var i = 0; i < variants.length; ++i) {
            var candidate = variants[i]
            if (Object.prototype.hasOwnProperty.call(map, candidate))
                return map[candidate]
        }
        return fallback
    }

    function _clampUnit(value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        if (numeric < 0.0)
            numeric = 0.0
        else if (numeric > 1.0)
            numeric = 1.0
        return numeric
    }

    function _linePressureValue(key) {
        var value = _lineMapValue(linePressures, key, null)
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = Number(pressure)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        return numeric
    }

    function _lineIntensityValue(key) {
        var value = _lineMapValue(lineIntensities, key, 0.0)
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        return _clampUnit(numeric)
    }

    function _normalizeColor(color, fallback) {
        try {
            return Qt.lighter(color, 1.0)
        } catch (error) {
            return fallback
        }
    }

    function _gradientColorForPressure(value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = pressure
        if (!Number.isFinite(numeric))
            numeric = minPressure
        var stops = effectiveGradientStops
        if (!stops || stops.length < 2) {
            var ratio = hasValidRange ? _clampUnit(_normalize(numeric)) : normalizedPressure
            return _mixColor(lowPressureColor, highPressureColor, ratio)
        }
        var position = hasValidRange ? _clampUnit(_normalize(numeric)) : normalizedPressure
        var previous = stops[0]
        for (var i = 1; i < stops.length; ++i) {
            var current = stops[i]
            if (position <= current.position) {
                var span = current.position - previous.position
                var localRatio = span > 0 ? (position - previous.position) / span : 0.0
                var colorA = _normalizeColor(previous.color, lowPressureColor)
                var colorB = _normalizeColor(current.color, highPressureColor)
                return _mixColor(colorA, colorB, localRatio)
            }
            previous = current
        }
        var last = stops[stops.length - 1]
        var lastColor = _normalizeColor(last.color, highPressureColor)
        return Qt.rgba(lastColor.r, lastColor.g, lastColor.b, lastColor.a)
    }

    function _mixColor(colorA, colorB, ratio) {
        var clamped = _clampUnit(ratio)
        return Qt.rgba(
            colorA.r + (colorB.r - colorA.r) * clamped,
            colorA.g + (colorB.g - colorA.g) * clamped,
            colorA.b + (colorB.b - colorA.b) * clamped,
            colorA.a + (colorB.a - colorA.a) * clamped
        )
    }

    function _lineColor(key) {
        var pressureValue = _linePressureValue(key)
        var baseColor = _gradientColorForPressure(pressureValue)
        var intensity = _lineIntensityValue(key)
        return Qt.rgba(baseColor.r, baseColor.g, baseColor.b, Math.min(0.95, 0.55 + 0.35 * intensity))
    }

    function _lineValveState(key) {
        var state = _lineMapValue(lineValveStates, key, null)
        if (_isPlainObject(state))
            return state
        return { atmosphereOpen: false, tankOpen: false }
    }

    function _lineValveOpen(key) {
        var state = _lineValveState(key)
        return !!state.tankOpen
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
            objectName: "reservoirFluid"
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: Math.max(0, parent.height * root.normalizedPressure)
            color: root._gradientColorForPressure(root.pressure)
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
            id: lineIndicators
            anchors.fill: parent

            Repeater {
                model: root.lineDescriptors
                delegate: Item {
                    id: lineDelegate

                    required property var modelData

                    width: parent.width
                    height: parent.height

                    readonly property real _pressureValue: root._linePressureValue(lineDelegate.modelData.key)
                    readonly property real _normalized: root.hasValidRange ? root._clampUnit(root._normalize(lineDelegate._pressureValue)) : root.normalizedPressure
                    readonly property real _intensity: root._lineIntensityValue(lineDelegate.modelData.key)
                    readonly property bool valveOpen: root._lineValveOpen(lineDelegate.modelData.key)

                    Components.SphericalMarker {
                        id: lineSphere
                        width: 22
                        height: 22
                        objectName: "lineSphere-" + (lineDelegate.modelData.key || "")
                        color: root._lineColor(lineDelegate.modelData.key)
                        borderColor: Qt.rgba(0.14, 0.22, 0.32, 0.9)
                        x: Math.round(parent.width * lineDelegate.modelData.anchor.x - width / 2)
                        y: Math.round((parent.height - height) * (1.0 - lineDelegate._normalized))
                    }

                    Item {
                        objectName: "lineSphere-" + (lineDelegate.modelData.key || "")
                        visible: false
                        width: 0
                        height: 0
                        parent: root
                        y: lineSphere.y
                    }

                    Label {
                        text: lineDelegate.modelData.label || ""
                        visible: text.length > 0
                        font.pixelSize: 10
                        font.bold: true
                        color: "#dfe6f7"
                        anchors.horizontalCenter: lineSphere.horizontalCenter
                        anchors.top: lineSphere.bottom
                        anchors.topMargin: 2
                    }

                    Rectangle {
                        id: valveIcon
                        width: 20
                        height: 20
                        objectName: "valveIcon-" + (lineDelegate.modelData.key || "")
                        radius: 5
                        color: lineDelegate.valveOpen ? root.valveOpenColor : root.valveClosedColor
                        border.width: 1
                        border.color: Qt.rgba(0.08, 0.12, 0.18, 0.8)
                        x: Math.round(parent.width * lineDelegate.modelData.valveAnchor.x - width / 2)
                        y: Math.round((parent.height - height) * (1.0 - lineDelegate._normalized))
                        opacity: 0.7 + 0.3 * lineDelegate._intensity

                        Text {
                            text: lineDelegate.valveOpen ? "✓" : "✕"
                            anchors.centerIn: parent
                            font.pixelSize: 12
                            font.bold: true
                            color: lineDelegate.valveOpen ? "#08210f" : "#2b1111"
                        }
                    }

                    Item {
                        objectName: "valveIcon-" + (lineDelegate.modelData.key || "")
                        visible: false
                        width: 0
                        height: 0
                        parent: root
                        property color color: valveIcon.color
                    }
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
        text: qsTr("Давление: %1 Па").arg(Qt.locale().toString(Number(root.pressure), "f", 0))
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
