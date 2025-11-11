pragma ComponentBehavior: Bound

import QtQuick 6.10

Item {
    id: root

    implicitWidth: 16
    implicitHeight: 16

    property color color: Qt.rgba(0.6, 0.8, 1.0, 0.95)
    property string label: ""
    property real borderWidth: 1.0
    property color borderColor: Qt.rgba(0.24, 0.31, 0.42, 0.9)

    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            var w = width
            var h = height
            ctx.reset()
            ctx.clearRect(0, 0, w, h)

            var radius = Math.min(w, h) / 2 - root.borderWidth
            var centerX = w / 2
            var centerY = h / 2
            var color = root.color
            var base = "rgba(" + Math.round(color.r * 255) + ", "
                + Math.round(color.g * 255) + ", " + Math.round(color.b * 255) + ", "
            var gradient = ctx.createRadialGradient(centerX - radius * 0.35, centerY - radius * 0.35, radius * 0.2,
                                                     centerX, centerY, radius)
            gradient.addColorStop(0, base + Math.min(0.95, Math.max(0.4, color.a)) + ")")
            gradient.addColorStop(0.75, base + Math.min(0.85, Math.max(0.35, color.a * 0.9)) + ")")
            gradient.addColorStop(1, base + "0.25)")

            ctx.beginPath()
            ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
            ctx.closePath()
            ctx.fillStyle = gradient
            ctx.fill()

            ctx.strokeStyle = root.borderColor
            ctx.lineWidth = Math.max(0.5, root.borderWidth)
            ctx.stroke()
        }

        Behavior on opacity {
            NumberAnimation {
                duration: 160
                easing.type: Easing.OutQuad
            }
        }
    }

    Connections {
        target: root
        function onColorChanged() { canvas.requestPaint() }
        function onBorderColorChanged() { canvas.requestPaint() }
        function onBorderWidthChanged() { canvas.requestPaint() }
        function onWidthChanged() { canvas.requestPaint() }
        function onHeightChanged() { canvas.requestPaint() }
    }
}
