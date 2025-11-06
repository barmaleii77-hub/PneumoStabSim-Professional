import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10

pragma ComponentBehavior: Bound

Control {
    id: root

    property string label: qsTr("State")
    property string detailText: ""
    property string secondaryText: ""
    property bool active: false
    property bool warning: false
    property color activeColor: Qt.rgba(0.20, 0.75, 0.50, 1.0)
    property color inactiveColor: Qt.rgba(0.28, 0.30, 0.36, 0.92)
    property color warningColor: Qt.rgba(0.85, 0.43, 0.25, 1.0)
    property color textColor: "#f5f5f5"
    property color mutedTextColor: Qt.rgba(0.76, 0.82, 0.86, 1.0)
    property bool pulse: false
    property int pulseDuration: 220

    implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
    implicitHeight: contentItem.implicitHeight + topPadding + bottomPadding
    padding: 10

    background: Rectangle {
        readonly property color baseColor: root.warning
            ? Qt.rgba(root.warningColor.r, root.warningColor.g, root.warningColor.b, 0.25)
            : root.active
                ? Qt.rgba(root.activeColor.r, root.activeColor.g, root.activeColor.b, 0.22)
                : Qt.rgba(root.inactiveColor.r, root.inactiveColor.g, root.inactiveColor.b, 0.20)
        color: baseColor
        radius: 12
        border.width: 1
        border.color: root.warning
            ? root.warningColor
            : root.active
                ? Qt.rgba(root.activeColor.r, root.activeColor.g, root.activeColor.b, 0.65)
                : Qt.rgba(root.inactiveColor.r, root.inactiveColor.g, root.inactiveColor.b, 0.45)
    }

    contentItem: RowLayout {
        spacing: 10
        anchors.fill: parent

        Rectangle {
            id: indicator
            width: 14
            height: 14
            radius: 7
            color: root.warning
                ? root.warningColor
                : root.active
                    ? root.activeColor
                    : Qt.rgba(0.62, 0.66, 0.72, 1.0)
            Layout.alignment: Qt.AlignVCenter
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
                text: root.detailText
                visible: text.length > 0
                color: root.mutedTextColor
                font.pixelSize: 13
                Layout.fillWidth: true
            }

            Label {
                text: root.secondaryText
                visible: text.length > 0
                color: Qt.rgba(root.mutedTextColor.r, root.mutedTextColor.g, root.mutedTextColor.b, 0.85)
                font.pixelSize: 11
                Layout.fillWidth: true
            }
        }
    }

    onPulseChanged: {
        if (pulse)
            pulseAnimation.restart()
    }

    SequentialAnimation {
        id: pulseAnimation
        running: false
        NumberAnimation {
            target: indicator
            property: "scale"
            to: 1.22
            duration: root.pulseDuration
            easing.type: Easing.OutQuad
        }
        NumberAnimation {
            target: indicator
            property: "scale"
            to: 1.0
            duration: root.pulseDuration
            easing.type: Easing.InQuad
        }
    }
}
