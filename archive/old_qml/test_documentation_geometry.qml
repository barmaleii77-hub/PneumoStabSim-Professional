
import QtQuick
import QtQuick3D
import CorrectGeometry 1.0

View3D {
    anchors.fill: parent

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#800080"
    }

    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }

    DirectionalLight {
        brightness: 5.0
    }

    Model {
        geometry: DocumentationBasedTriangle {
            id: docTriangle
        }

        materials: PrincipledMaterial {
            baseColor: "#ffff00"
            lighting: PrincipledMaterial.NoLighting
        }

        Component.onCompleted: {
            console.log("=== DOCUMENTATION TEST ===")
            console.log("Triangle from docs:", docTriangle)
            console.log("Model geometry:", geometry)
            console.log("Model visible:", visible)
            console.log("=========================")
        }
    }
}
