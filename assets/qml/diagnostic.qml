import QtQuick

/*
 * DIAGNOSTIC: Minimal visible QML to test if anything renders at all
 */
Rectangle {
    id: root
    width: 800
    height: 600

    // Bright red background - should be VERY visible!
    color: "#ff0000"

    // Big white text
    Text {
        anchors.centerIn: parent
        text: "? QML РЕНДЕРИТСЯ!\n\nЕсли видите это - Qt Quick работает\n\nСейчас загружу 3D сцену..."
        color: "#ffffff"
        font.pixelSize: 24
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
    }

    // Small info in corner
    Text {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 20
        text: "Diagnostic QML\n800x600\nRed background"
        color: "#ffffff"
        font.pixelSize: 14
    }

    // Animation to prove it's live
    Rectangle {
        id: spinner
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 50
        width: 100
        height: 100
        color: "#00ff00"

        RotationAnimation on rotation {
            from: 0
            to: 360
            duration: 2000
            loops: Animation.Infinite
        }
    }
}
