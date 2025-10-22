
import QtQuick

Rectangle {
    anchors.fill: parent
    color: "#1a1a2e"

    // Red circle
    Rectangle {
        id: circle
        width: 200
        height: 200
        radius: 100
        color: "#ff4444"
        anchors.centerIn: parent

        // Rotation animation
        RotationAnimation on rotation {
            from: 0
            to: 360
            duration: 3000
            loops: Animation.Infinite
        }

        // White dot in center to show rotation
        Rectangle {
            width: 20
            height: 20
            radius: 10
            color: "#ffffff"
            x: parent.width / 2 - 10
            y: 20
        }
    }

    // Title text
    Text {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 50
        text: "2D ROTATING CIRCLE (RED)"
        color: "#ffffff"
        font.pixelSize: 24
        font.bold: true
    }

    // Info text
    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 50
        text: "White dot shows rotation"
        color: "#aaaaaa"
        font.pixelSize: 16
    }
}
