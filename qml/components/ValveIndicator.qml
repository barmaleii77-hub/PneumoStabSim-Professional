pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10

Item {
    id: root

    implicitWidth: 180
    implicitHeight: 56

    /** Label describing the valve. */
    property string label: ""

    /** Whether the valve is open. */
    property bool open: false

    /** Flow direction label ("intake" or "exhaust"). */
    property string direction: "intake"

    /** Mass flow in kg/s (signed). */
    property real flowValue: 0.0

    /** Optional textual hint displayed under the state label. */
    property string hint: ""

    property string units: qsTr("кг/с")

    readonly property string _stateText: root.open ? qsTr("Открыт") : qsTr("Закрыт")
    readonly property color _stateColor: root.open
        ? Qt.rgba(0.32, 0.78, 0.48, 0.95)
        : Qt.rgba(0.86, 0.33, 0.33, 0.95)

    function _directionLabel() {
        var key = root.direction.toLowerCase()
        if (key === "exhaust")
            return qsTr("Сброс")
        if (key === "bypass")
            return qsTr("Обвод")
        return qsTr("Подача")
    }

    function _formatFlow(value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        var loc = Qt.locale()
        // Формат с фиксированным числом знаков после запятой
        return loc.toString(numeric, "f", 2)
    }

    Rectangle {
        id: background
        anchors.fill: parent
        radius: 12
        color: Qt.rgba(0.09, 0.12, 0.18, 0.9)
        border.width: 1
        border.color: Qt.rgba(0.24, 0.29, 0.38, 0.9)
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        Canvas {
            id: sphere
            Layout.preferredWidth: 30
            Layout.preferredHeight: 30
            Layout.alignment: Qt.AlignVCenter
            onPaint: {
                var ctx = getContext("2d")
                var size = Math.min(width, height)
                ctx.reset()
                ctx.clearRect(0, 0, width, height)

                var radius = size / 2 - 1
                var centerX = width / 2
                var centerY = height / 2

                var gradient = ctx.createRadialGradient(centerX - radius * 0.3, centerY - radius * 0.3, radius * 0.2,
                                                         centerX, centerY, radius)
                var color = root._stateColor
                var base = "rgba(" + Math.round(color.r * 255) + ", " + Math.round(color.g * 255) + ", " + Math.round(color.b * 255) + ", "
                gradient.addColorStop(0, base + "0.95)")
                gradient.addColorStop(0.65, base + "0.75)")
                gradient.addColorStop(1, "rgba(0, 0, 0, 0.45)")

                ctx.beginPath()
                ctx.arc(centerX, centerY, radius, 0, Math.PI * 2, false)
                ctx.closePath()
                ctx.fillStyle = gradient
                ctx.fill()

                ctx.strokeStyle = "rgba(255, 255, 255, 0.12)"
                ctx.lineWidth = 1
                ctx.stroke()
            }

            Connections {
                target: root
                function onOpenChanged() { sphere.requestPaint() }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            Label {
                text: root.label
                font.pixelSize: 13
                font.bold: true
                color: "#dfe6f4"
                elide: Text.ElideRight
            }

            Label {
                text: root._stateText + " • " + root._directionLabel()
                font.pixelSize: 12
                color: root._stateColor
                elide: Text.ElideRight
            }

            Label {
                text: qsTr("Поток: %1 %2").arg(root._formatFlow(root.flowValue)).arg(root.units)
                font.pixelSize: 11
                color: "#b6c1d4"
            }

            Label {
                text: root.hint
                visible: root.hint.length > 0
                font.pixelSize: 10
                color: "#9aa4b7"
                elide: Text.ElideRight
            }
        }
    }
}
