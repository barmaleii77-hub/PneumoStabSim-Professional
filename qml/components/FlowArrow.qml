pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10

Item {
    id: root

    implicitWidth: 200
    implicitHeight: 68

    /**
     * Name of the flow line (e.g. "A1").
     */
    property string label: ""

    /**
     * Direction of flow. Supported values: "intake" (towards the tank) or
     * "exhaust" (towards atmosphere).
     */
    property string direction: "intake"

    /**
     * Actual mass flow in kg/s. Positive values correspond to the declared
     * direction. The value is clamped to a finite number before rendering.
     */
    property real flowValue: 0.0

    /**
     * Normalised intensity in range [0, 1] used for animations.
     */
    property real intensity: 0.0

    /**
     * Optional display units (defaults to kg/s).
     */
    property string units: qsTr("кг/с")

    /**
     * Suggested animation speed normalised to [0, 1]. When NaN the component
     * falls back to the provided intensity.
     */
    property real animationSpeed: NaN

    /** Absolute line pressure (Па). */
    property real linePressure: NaN

    /** Reference pressure used to compute the delta (Па). */
    property real referencePressure: NaN

    /** Normalised pressure ratio [0, 1] used for colour blending. */
    property real pressureRatio: 0.0

    /** Highlight phase accumulator, driven by the animation. */
    property real phase: 0.0

    /** Whether the highlight animation is currently active. */
    property bool animationRunning: false

    readonly property real _normalizedIntensity: {
        var numeric = Number(intensity)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        if (numeric < 0.0)
            numeric = 0.0
        if (numeric > 1.0)
            numeric = 1.0
        return numeric
    }

    readonly property real _normalizedAnimationSpeed: {
        var numeric = Number(animationSpeed)
        if (!Number.isFinite(numeric))
            numeric = _normalizedIntensity
        if (numeric < 0.0)
            numeric = 0.0
        if (numeric > 1.0)
            numeric = 1.0
        return numeric
    }

    readonly property real _clampedPressureRatio: {
        var numeric = Number(pressureRatio)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        if (numeric < 0.0)
            numeric = 0.0
        if (numeric > 1.0)
            numeric = 1.0
        return numeric
    }

    readonly property int _animationDuration: {
        var base = 900 - 620 * _normalizedAnimationSpeed
        if (!Number.isFinite(base))
            base = 900
        base = Math.max(160, Math.min(1200, Math.round(base)))
        return base
    }

    readonly property real _directionSign: direction.toLowerCase() === "exhaust" ? -1 : 1
    readonly property bool _isExhaust: direction.toLowerCase() === "exhaust"

    function _formatFlow(value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        var loc = Qt.locale()
        return loc.toString(numeric, "f", 2)
    }

    function _mixColor(colorA, colorB, ratio) {
        var clamped = Number(ratio)
        if (!Number.isFinite(clamped))
            clamped = 0.0
        if (clamped < 0.0)
            clamped = 0.0
        if (clamped > 1.0)
            clamped = 1.0
        return Qt.rgba(
            colorA.r + (colorB.r - colorA.r) * clamped,
            colorA.g + (colorB.g - colorA.g) * clamped,
            colorA.b + (colorB.b - colorA.b) * clamped,
            colorA.a + (colorB.a - colorA.a) * clamped
        )
    }

    function _colorToCss(color) {
        return "rgba(" + Math.round(color.r * 255) + ", "
            + Math.round(color.g * 255) + ", " + Math.round(color.b * 255) + ", "
            + Math.max(0, Math.min(1, color.a)) + ")"
    }

    function _gradientColors() {
        var ratio = _clampedPressureRatio
        var intakeStart = Qt.rgba(0.16, 0.44, 0.9, 0.55)
        var intakeEnd = Qt.rgba(0.35, 0.82, 1.0, 0.9)
        var exhaustStart = Qt.rgba(0.88, 0.36, 0.28, 0.55)
        var exhaustEnd = Qt.rgba(0.99, 0.64, 0.38, 0.9)
        if (_isExhaust) {
            return {
                base: _colorToCss(_mixColor(exhaustStart, exhaustEnd, ratio)),
                tip: _colorToCss(_mixColor(exhaustStart, Qt.rgba(1.0, 0.76, 0.45, 0.98), ratio)),
                highlight: _colorToCss(_mixColor(Qt.rgba(1.0, 0.75, 0.55, 0.6), Qt.rgba(1.0, 0.9, 0.7, 0.95), ratio))
            }
        }
        return {
            base: _colorToCss(_mixColor(intakeStart, intakeEnd, ratio)),
            tip: _colorToCss(_mixColor(intakeStart, Qt.rgba(0.65, 0.98, 1.0, 0.98), ratio)),
            highlight: _colorToCss(_mixColor(Qt.rgba(0.55, 0.9, 1.0, 0.6), Qt.rgba(0.75, 1.0, 1.0, 0.95), ratio))
        }
    }

    function _refreshAnimationRunning() {
        var active = _normalizedAnimationSpeed > 0.01 && _normalizedIntensity > 0.01 && root.visible
        if (animationRunning !== active)
            animationRunning = active
    }

    function _deltaLabel() {
        var delta = Number(linePressure) - Number(referencePressure)
        if (!Number.isFinite(delta))
            delta = 0.0
        var locale = Qt.locale()
        var absolute = locale.toString(Math.abs(delta), "f", 0)
        var prefix = delta >= 0 ? qsTr("ΔP +") : qsTr("ΔP -")
        return prefix + absolute + qsTr(" Па")
    }

    Rectangle {
        id: background
        anchors.fill: parent
        radius: 12
        color: Qt.rgba(0.08, 0.11, 0.17, 0.92)
        border.width: 1
        border.color: Qt.rgba(0.22, 0.29, 0.4, 0.95)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        Label {
            id: titleLabel
            Layout.fillWidth: true
            text: root.label
            font.bold: true
            font.pixelSize: 14
            color: "#dfe7f3"
            elide: Text.ElideRight
        }

        Item {
            id: arrowContainer
            Layout.fillWidth: true
            Layout.preferredHeight: 26

            Canvas {
                id: arrowCanvas
                anchors.fill: parent
                antialiasing: true
                onPaint: {
                    var ctx = getContext("2d")
                    var w = width
                    var h = height
                    ctx.reset()
                    ctx.clearRect(0, 0, w, h)

                    var arrowLength = w * 0.72
                    var arrowHeight = h * 0.48
                    var centerY = h / 2
                    var startX = (w - arrowLength) / 2

                    var directionSign = root._directionSign
                    if (directionSign < 0)
                        ctx.translate(w, 0)
                    ctx.save()
                    ctx.scale(directionSign < 0 ? -1 : 1, 1)

                    var colors = root._gradientColors()
                    var gradient = ctx.createLinearGradient(startX, centerY, startX + arrowLength, centerY)
                    gradient.addColorStop(0, colors.base)
                    gradient.addColorStop(0.55, "rgba(255, 255, 255, " + (0.25 + 0.5 * root._normalizedIntensity) + ")")
                    gradient.addColorStop(1, colors.tip)

                    ctx.fillStyle = gradient
                    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)"
                    ctx.lineWidth = 1

                    ctx.beginPath()
                    ctx.moveTo(startX, centerY)
                    ctx.lineTo(startX + arrowLength - arrowHeight, centerY - arrowHeight)
                    ctx.lineTo(startX + arrowLength - arrowHeight, centerY - arrowHeight / 2)
                    ctx.lineTo(startX + arrowLength, centerY)
                    ctx.lineTo(startX + arrowLength - arrowHeight, centerY + arrowHeight / 2)
                    ctx.lineTo(startX + arrowLength - arrowHeight, centerY + arrowHeight)
                    ctx.closePath()
                    ctx.fill()
                    ctx.stroke()

                    if (root.animationRunning) {
                        var waveCount = Math.max(3, Math.round(4 + root._normalizedIntensity * 6))
                        var travel = arrowLength - arrowHeight
                        var spacing = travel / waveCount
                        var offset = root.phase * spacing
                        ctx.fillStyle = colors.highlight
                        ctx.globalAlpha = 0.28 + 0.45 * root._normalizedIntensity
                        for (var i = -1; i <= waveCount + 1; ++i) {
                            var baseX = startX + i * spacing + offset
                            if (baseX < startX || baseX > startX + travel)
                                continue
                            ctx.beginPath()
                            ctx.moveTo(baseX, centerY - arrowHeight * 0.55)
                            ctx.lineTo(baseX + arrowHeight * 0.28, centerY)
                            ctx.lineTo(baseX, centerY + arrowHeight * 0.55)
                            ctx.closePath()
                            ctx.fill()
                        }
                        ctx.globalAlpha = 1.0
                    }

                    ctx.restore()
                }

                Behavior on opacity {
                    NumberAnimation {
                        duration: 220
                        easing.type: Easing.InOutQuad
                    }
                }

                opacity: 0.55 + 0.45 * root._normalizedIntensity
            }
        }

        Label {
            Layout.fillWidth: true
            text: {
                const dir = root.direction.toLowerCase() === "exhaust"
                    ? qsTr("→ Атмосфера")
                    : qsTr("→ Резервуар")
                return qsTr("%1 %2 %3 • %4")
                    .arg(dir)
                    .arg(root._formatFlow(root.flowValue))
                    .arg(root.units)
                    .arg(root._deltaLabel())
            }
            font.pixelSize: 12
            color: "#b6c1d4"
            elide: Text.ElideRight
        }
    }

    NumberAnimation on phase {
        id: phaseAnimation
        from: 0.0
        to: 1.0
        loops: Animation.Infinite
        duration: root._animationDuration
        running: root.animationRunning
        easing.type: Easing.Linear
    }

    Connections {
        target: root
        function onIntensityChanged() { arrowCanvas.requestPaint(); root._refreshAnimationRunning() }
        function onDirectionChanged() { arrowCanvas.requestPaint() }
        function onWidthChanged() { arrowCanvas.requestPaint() }
        function onHeightChanged() { arrowCanvas.requestPaint() }
        function onPhaseChanged() { arrowCanvas.requestPaint() }
        function onAnimationSpeedChanged() { root._refreshAnimationRunning(); arrowCanvas.requestPaint() }
        function onAnimationRunningChanged() {
            if (!root.animationRunning)
                root.phase = 0.0
            arrowCanvas.requestPaint()
        }
        function onPressureRatioChanged() { arrowCanvas.requestPaint() }
        function onLinePressureChanged() { arrowCanvas.requestPaint() }
        function onReferencePressureChanged() { arrowCanvas.requestPaint() }
        function onVisibleChanged() { root._refreshAnimationRunning() }
    }

    Component.onCompleted: _refreshAnimationRunning()
}
