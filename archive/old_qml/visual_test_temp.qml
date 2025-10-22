
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent

    // Background indicator (should always be visible)
    Rectangle {
        anchors.fill: parent
        color: "#1a1a2e"

        // Visual test pattern
        Column {
            anchors.centerIn: parent
            spacing: 20

            Text {
                text: "2D QML IS WORKING"
                color: "#00ff00"
                font.pixelSize: 32
                font.bold: true
            }

            Rectangle {
                width: 200
                height: 200
                color: "#ff00ff"
                radius: 100

                Text {
                    anchors.centerIn: parent
                    text: "2D CIRCLE"
                    color: "#ffffff"
                    font.pixelSize: 16
                }
            }

            Text {
                text: "If you see this, 2D QML works!"
                color: "#ffff00"
                font.pixelSize: 16
            }
        }
    }

    // 3D View (will it render on top?)
    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
            antialiasingMode: SceneEnvironment.MSAA
        }

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 5)
        }

        DirectionalLight {
            eulerRotation.x: -30
            brightness: 2.0
        }

        // Red sphere
        Model {
            source: "#Sphere"
            position: Qt.vector3d(-1.5, 1, 0)
            scale: Qt.vector3d(0.8, 0.8, 0.8)
            materials: PrincipledMaterial {
                baseColor: "#ff0000"
                metalness: 0.0
                roughness: 0.5
            }

            NumberAnimation on eulerRotation.y {
                from: 0
                to: 360
                duration: 3000
                loops: Animation.Infinite
            }
        }

        // Green cube
        Model {
            source: "#Cube"
            position: Qt.vector3d(1.5, 1, 0)
            scale: Qt.vector3d(0.6, 0.6, 0.6)
            materials: PrincipledMaterial {
                baseColor: "#00ff00"
                metalness: 0.0
                roughness: 0.5
            }

            NumberAnimation on eulerRotation.x {
                from: 0
                to: 360
                duration: 4000
                loops: Animation.Infinite
            }
        }

        // Blue cylinder
        Model {
            source: "#Cylinder"
            position: Qt.vector3d(0, -1, 0)
            scale: Qt.vector3d(0.5, 1.0, 0.5)
            materials: PrincipledMaterial {
                baseColor: "#0000ff"
                metalness: 0.0
                roughness: 0.5
            }

            NumberAnimation on eulerRotation.z {
                from: 0
                to: 360
                duration: 5000
                loops: Animation.Infinite
            }
        }
    }

    // Overlay info (should be on top)
    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 20
        width: 300
        height: 150
        color: "#80000000"
        border.color: "#ffffff"
        border.width: 2
        radius: 5

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5

            Text {
                text: "3D Test Status"
                color: "#ffffff"
                font.pixelSize: 16
                font.bold: true
            }

            Text {
                text: "Expected:"
                color: "#aaaaaa"
                font.pixelSize: 12
            }

            Text {
                text: "- Red sphere (rotating)"
                color: "#ff4444"
                font.pixelSize: 11
            }

            Text {
                text: "- Green cube (rotating)"
                color: "#44ff44"
                font.pixelSize: 11
            }

            Text {
                text: "- Blue cylinder (rotating)"
                color: "#4444ff"
                font.pixelSize: 11
            }

            Text {
                text: "If you see only 2D -> 3D broken"
                color: "#ffaa00"
                font.pixelSize: 10
                font.italic: true
            }
        }
    }
}
