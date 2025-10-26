import QtQuick 6.10
import QtQuick.Controls 6.10

Item {
    id: root
    width: 100
    height: 100

signal triggered()

    Button {
        anchors.centerIn: parent
    text: "Linted"
        onClicked: root.triggered()
    }
}
