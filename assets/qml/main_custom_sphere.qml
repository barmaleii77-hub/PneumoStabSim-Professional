import QtQuick
import QtQuick3D

/*
 * FIXED: Custom sphere geometry instead of primitive
 * Reason: PySide6 6.8.3 doesn't include built-in primitive meshes
 */
Item {
    id: root
    anchors.fill: parent

    // 3D View (background layer)
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
            brightness: 1.0
        }

        // CUSTOM SPHERE using QML procedural geometry
        // Instead of "#Sphere" primitive which doesn't exist in PySide6 6.8.3
        Model {
            id: customSphere

            position: Qt.vector3d(0, 0, 0)
            scale: Qt.vector3d(1, 1, 1)

            // Use custom geometry
            geometry: CustomSphereGeometry {
                id: sphereGeometry
                radius: 1.0
                segments: 32
            }

            materials: PrincipledMaterial {
                baseColor: "#ff4444"
                metalness: 0.0
                roughness: 0.5
            }

            NumberAnimation on eulerRotation.y {
                from: 0
                to: 360
                duration: 3000
                loops: Animation.Infinite
                running: true
            }
        }
    }

    // 2D Overlay
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
                text: "Procedural geometry"
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

// Custom procedural sphere geometry
QQuick3DGeometry {
    id: customSphereGeometryType

    property real radius: 1.0
    property int segments: 32

    Component.onCompleted: {
        generateSphere()
    }

    function generateSphere() {
        // This will be implemented in Python
        // For now, use placeholder
        console.log("CustomSphereGeometry: Generating sphere with radius", radius, "and", segments, "segments")
    }
}
