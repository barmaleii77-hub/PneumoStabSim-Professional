pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10

Item {
    id: root

    implicitWidth: 200
    implicitHeight: 60

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

    readonly property real _directionSign: direction.toLowerCase() === "exhaust" ? -1 : 1

    function _formatFlow(value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        return numeric.toLocaleString(Qt.locale(), {
            maximumFractionDigits: 4,
            minimumFractionDigits: 2
        })
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
            Layout.preferredHeight: 24

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
                    var arrowHeight = h * 0.45
                    var centerY = h / 2
                    var startX = (w - arrowLength) / 2

                    var directionSign = root._directionSign
                    if (directionSign < 0)
                        ctx.translate(w, 0)
                    ctx.save()
                    ctx.scale(directionSign < 0 ? -1 : 1, 1)

                    var gradient = ctx.createLinearGradient(startX, centerY, startX + arrowLength, centerY)
                    var baseColor = directionSign < 0
                        ? "rgba(255, 120, 100, 0.65)"
                        : "rgba(120, 200, 255, 0.65)"
                    var highlightAlpha = Math.max(0.35, root._normalizedIntensity)
                    var highlightColor = directionSign < 0
                        ? "rgba(255, 160, 120, " + highlightAlpha + ")"
                        : "rgba(150, 230, 255, " + highlightAlpha + ")"

                    var bright = root._normalizedIntensity
                    gradient.addColorStop(0, baseColor)
                    gradient.addColorStop(0.5, "rgba(255, 255, 255, " + (0.3 + 0.6 * bright) + ")")
                    gradient.addColorStop(1, highlightColor)

                    ctx.fillStyle = gradient
                    ctx.strokeStyle = "rgba(255, 255, 255, 0.25)"
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
                const dir = root.direction.toLowerCase() === "exhaust" ? qsTr("→ Атмосфера") : qsTr("→ Резервуар")
                return qsTr("%1 %2 %3").arg(dir).arg(root._formatFlow(root.flowValue)).arg(root.units)
            }
            font.pixelSize: 12
            color: "#b6c1d4"
            elide: Text.ElideRight
        }
    }

    Connections {
        target: root
        function onIntensityChanged() { arrowCanvas.requestPaint() }
        function onDirectionChanged() { arrowCanvas.requestPaint() }
        function onWidthChanged() { arrowCanvas.requestPaint() }
        function onHeightChanged() { arrowCanvas.requestPaint() }
    }
}
