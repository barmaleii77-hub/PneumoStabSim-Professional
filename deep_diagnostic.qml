
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent

    Rectangle {
        anchors.fill: parent
        color: "#ff0000"

        Text {
            anchors.centerIn: parent
            text: "RED BACKGROUND\nShould see sphere below"
            color: "#ffffff"
            font.pixelSize: 24
            horizontalAlignment: Text.AlignHCenter
        }
    }

    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
            clearColor: "#00000000"
        }

        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }

        DirectionalLight {
            brightness: 2.0
        }

        Model {
            id: testSphere
            source: "#Sphere"
            scale: Qt.vector3d(2, 2, 2)

            materials: PrincipledMaterial {
                baseColor: "#00ff00"
            }

            Component.onCompleted: {
                console.log("Model onCompleted - source:", source)
                console.log("Model onCompleted - geometry:", geometry)
            }

            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
        }
    }
}
