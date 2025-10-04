
import QtQuick

Rectangle {
    width: 400
    height: 300
    color: "#ff0000"
    
    Text {
        anchors.centerIn: parent
        text: "RHI D3D11 Test"
        color: "#ffffff"
        font.pixelSize: 24
    }
    
    Component.onCompleted: {
        console.log("QML Component loaded successfully")
    }
}
