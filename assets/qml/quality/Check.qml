import QtQuick 6.5
import QtQuick.Controls 6.5

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
