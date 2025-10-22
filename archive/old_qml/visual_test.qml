
import QtQuick
import QtQuick3D
import CustomGeometry 1.0

Item {
    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#ff0000"
        }

        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }

        DirectionalLight {
            brightness: 2.0
        }

        Model {
            geometry: SphereGeometry { }
            scale: Qt.vector3d(2, 2, 2)

            materials: PrincipledMaterial {
                baseColor: "#00ff00"
            }

            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }

            Component.onCompleted: {
                console.log("SPHERE CREATED WITH GEOMETRY:", geometry)
                console.log("SPHERE VISIBLE:", visible)
            }
        }
    }
}
