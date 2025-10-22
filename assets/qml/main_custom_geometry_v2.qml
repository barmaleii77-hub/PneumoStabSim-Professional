import QtQuick
import QtQuick3D
import CustomGeometry 1.0

/*
 * SOLUTION: Custom 3D geometry using QQuick3DGeometry
 * This works because we create geometry procedurally in Python
 */
Item {
    id: root
    anchors.fill: parent

    // 3D View
    View3D {
        id: view3d
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#1a1a2e"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 5)
            eulerRotation: Qt.vector3d(0, 0, 0)
        }

        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: 30
            brightness: 1.5
        }

        // CUSTOM SPHERE using Python-generated geometry
        Model {
            id: customSphere

            position: Qt.vector3d(0, 0, 0)
            scale: Qt.vector3d(1, 1, 1)

            // Use custom geometry from Python
            geometry: SphereGeometry {
                id: sphereGeom
                // Properties can be set here if exposed
            }

            materials: PrincipledMaterial {
                baseColor: "#ff4444"
                metalness: 0.0
                roughness: 0.5
            }

            // Rotation animation
            NumberAnimation on eulerRotation.y {
                from: 0
                to: 360
                duration: 3000
                loops: Animation.Infinite
                running: true
            }

            Component.onCompleted: {
                console.log("Custom sphere created")
                console.log("Geometry:", geometry)
            }
        }
    }

    // Info overlay
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 20
        width: 300
        height: 80
        color: "#20000000"
        border.color: "#40ffffff"
        border.width: 1
        radius: 5

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5

            Text {
                text: "Custom 3D Sphere"
                color: "#ffffff"
                font.pixelSize: 16
                font.bold: true
            }

            Text {
                text: "Procedural geometry (Python)"
                color: "#aaaaaa"
                font.pixelSize: 12
            }

            Text {
                text: "Qt Quick 3D (RHI/D3D11)"
                color: "#888888"
                font.pixelSize: 10
            }
        }
    }
}
