
import QtQuick
import QtQuick3D
import StableGeometry 1.0

View3D {
    id: view3d
    anchors.fill: parent

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#800080"
    }

    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 0, 6)
        clipNear: 0.1
        clipFar: 100.0
    }

    DirectionalLight {
        eulerRotation.x: -30
        brightness: 5.0
    }

    GeometryProvider {
        id: provider
    }

    Model {
        id: triangleModel

        geometry: provider.geometry

        materials: PrincipledMaterial {
            baseColor: "#ffff00"
            lighting: PrincipledMaterial.NoLighting
        }

        Component.onCompleted: {
            console.log("=== STABLE GEOMETRY TEST ===")
            console.log("Provider:", provider)
            console.log("Geometry from provider:", provider.geometry)
            console.log("Model geometry:", geometry)
            console.log("Model visible:", visible)
            console.log("Model position:", position)
            console.log("Model scale:", scale)
            console.log("Camera position:", camera.position)
            console.log("===========================")
        }
    }
}
