import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

pragma ComponentBehavior: Bound

Control {
    id: root

    property string label: qsTr("Signals")
    property int count: 0
    property alias iconVisible: icon.visible
    property color accentColor: Qt.rgba(0.18, 0.64, 0.44, 1)
    property color backgroundColor: Qt.rgba(0.1, 0.1, 0.12, 0.9)
    property color textColor: "#f5f5f5"
    property bool pulseOnChange: true

    implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
    implicitHeight: Math.max(contentItem.implicitHeight + topPadding + bottomPadding, 36)
    padding: 10

    background: Rectangle {
        color: root.backgroundColor
        radius: 18
        border.width: 1
        border.color: Qt.rgba(
            root.accentColor.r,
            root.accentColor.g,
            root.accentColor.b,
            0.4
        )
    }

    contentItem: RowLayout {
        spacing: 8
        anchors.fill: parent

        Rectangle {
            id: icon
            visible: true
            implicitWidth: 16
            implicitHeight: 16
            radius: 8
            color: root.accentColor
            Layout.preferredWidth: implicitWidth
            Layout.preferredHeight: implicitHeight
            Layout.alignment: Qt.AlignVCenter
            transformOrigin: Item.Center
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            Label {
                text: root.label
                color: root.textColor
                font.bold: true
                Layout.fillWidth: true
            }

            Label {
                id: counter
                text: root.count.toString()
                color: Qt.rgba(0.78, 0.86, 0.9, 1)
                font.family: "Monospace"
                font.pixelSize: 14
            }
        }
    }

    onCountChanged: {
        if (!root.pulseOnChange || root.count <= 0) {
            return
        }
        pulseAnimation.restart()
    }

    SequentialAnimation {
        id: pulseAnimation
        running: false
        NumberAnimation { target: icon; property: "scale"; to: 1.25; duration: 120 }
        NumberAnimation {
            target: icon
            property: "scale"
            to: 1.0
            duration: 220
            easing.type: Easing.InOutQuad
        }
    }

    function increment(step) {
        const delta = step === undefined ? 1 : step
        root.count += delta
    }

    function reset() {
        icon.scale = 1.0
        root.count = 0
    }
}
