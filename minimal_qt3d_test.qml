
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent
    
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#00ff00"
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 1)
        }
        
        Component.onCompleted: {
            console.log("View3D loaded")
        }
    }
    
    Text {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 10
        text: "QtQuick3D Minimal Test"
        color: "#ffffff"
        font.pixelSize: 16
    }
}
