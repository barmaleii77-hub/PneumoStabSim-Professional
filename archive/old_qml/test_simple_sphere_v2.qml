
import QtQuick
import QtQuick3D
import SimpleGeometry 1.0

Item {
    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#ff0000"
        }

        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 3)
        }

        DirectionalLight {
            brightness: 3.0
        }

        Model {
            geometry: SimpleSphere { }

            materials: PrincipledMaterial {
                baseColor: "#00ff00"
                lighting: PrincipledMaterial.NoLighting
            }

            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }

            Component.onCompleted: {
                console.log("SimpleSphere Model created")
                console.log("Geometry:", geometry)
            }
        }
    }
}
