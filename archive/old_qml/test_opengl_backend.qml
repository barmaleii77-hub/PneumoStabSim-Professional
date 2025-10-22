
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent

    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#ff0000"  // RED to verify View3D works
        }

        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }

        DirectionalLight {
            brightness: 2.0
        }

        // Try primitive with OpenGL backend
        Model {
            source: "#Sphere"
            scale: Qt.vector3d(2, 2, 2)

            materials: PrincipledMaterial {
                baseColor: "#00ff00"  // GREEN
            }

            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }

            Component.onCompleted: {
                console.log("Model created with source:", source)
                console.log("Geometry:", geometry)
            }
        }
    }

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 10
        width: 250
        height: 60
        color: "#80000000"
        border.color: "#ffffff"

        Column {
            anchors.centerIn: parent
            spacing: 5

            Text {
                text: "OpenGL Backend Test"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true
            }

            Text {
                text: "Testing #Sphere with OpenGL"
                color: "#aaaaaa"
                font.pixelSize: 10
            }
        }
    }
}
