pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import "../singletons" as Singletons

Item {
    id: root

    baselineOffset: titleLabel.baselineOffset

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

    /** Lower bound used to normalise pressure colours. */
    property real minPressure: NaN
    /** Upper bound used to normalise pressure colours. */
    property real maxPressure: NaN

    /** Absolute line pressure (Па). */
    property real linePressure: NaN

    /** Reference pressure used to compute the delta (Па). */
    property real referencePressure: NaN

    /** Normalised pressure ratio [0, 1] used for colour blending. */
    property real pressureRatio: 0.0
    /** Derived pressure ratio computed from line/reference pressure when possible. */
    readonly property real effectivePressureRatio: _effectivePressureRatio()

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
            numeric = NaN
        return numeric
    }

    readonly property var _flowAnimation: Singletons.UiConstants.flow.animation
    readonly property var _flowCard: Singletons.UiConstants.flow.card

    readonly property int _animationDuration: {
        var base = _flowAnimation.baseMs - _flowAnimation.speedFactor * _normalizedAnimationSpeed
        if (!Number.isFinite(base))
            base = _flowAnimation.baseMs
        base = Math.max(_flowAnimation.minMs, Math.min(_flowAnimation.maxMs, Math.round(base)))
        return base
    }

    readonly property real _directionSign: direction.toLowerCase() === "exhaust" ? -1 : 1
    readonly property bool _isExhaust: direction.toLowerCase() === "exhaust"
    readonly property var _gradientPalette: Singletons.UiConstants.flowPalette(_isExhaust, effectivePressureRatio)

    function _formatFlow(value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        var loc = Qt.locale()
        return loc.toString(numeric, "f", 2)
    }

    function _effectivePressureRatio() {
        var normalized = _clampedPressureRatio
        var hasOverride = Number.isFinite(normalized)
        if (!hasOverride) {
            var minP = Number(minPressure)
            var maxP = Number(maxPressure)
            var lineP = Number(linePressure)
            if (Number.isFinite(minP) && Number.isFinite(maxP) && maxP > minP && Number.isFinite(lineP)) {
                normalized = (lineP - minP) / (maxP - minP)
                if (!Number.isFinite(normalized))
                    normalized = 0.0
                if (normalized < 0.0)
                    normalized = 0.0
                else if (normalized > 1.0)
                    normalized = 1.0
            } else {
                normalized = 0.0
            }
        }
        return normalized
    }

    function _colorToCss(color) {
        return "rgba(" + Math.round(color.r * 255) + ", "
            + Math.round(color.g * 255) + ", " + Math.round(color.b * 255) + ", "
            + Math.max(0, Math.min(1, color.a)) + ")"
    }

    function _refreshAnimationRunning() {
        var threshold = _flowAnimation.activationThreshold
        var active = _normalizedAnimationSpeed > threshold && _normalizedIntensity > threshold && root.visible
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
        color: _flowCard.background
        border.width: 1
        border.color: _flowCard.border
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
            color: _flowCard.title
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

                    var palette = root._gradientPalette
                    var gradient = ctx.createLinearGradient(startX, centerY, startX + arrowLength, centerY)
                    gradient.addColorStop(0, root._colorToCss(palette.base))
                    gradient.addColorStop(0.55, "rgba(255, 255, 255, " + (0.25 + 0.5 * root._normalizedIntensity) + ")")
                    gradient.addColorStop(1, root._colorToCss(palette.tip))

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
                        ctx.fillStyle = root._colorToCss(palette.highlight)
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
            color: _flowCard.subtitle
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
        function onMinPressureChanged() { arrowCanvas.requestPaint() }
        function onMaxPressureChanged() { arrowCanvas.requestPaint() }
        function onVisibleChanged() { root._refreshAnimationRunning() }
    }

    Component.onCompleted: _refreshAnimationRunning()
}
