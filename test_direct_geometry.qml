
import QtQuick
import QtQuick3D
import DirectGeometry 1.0

View3D {
    anchors.fill: parent
    
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#ff8000"
    }
    
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 2)
    }
    
    DirectionalLight {
        brightness: 10.0
    }
    
    Model {
        geometry: DirectTriangle {
            id: triangle
        }
        
        materials: PrincipledMaterial {
            baseColor: "#000000"
            lighting: PrincipledMaterial.NoLighting
        }
        
        Component.onCompleted: {
            console.log("DIRECT TEST: Model completed")
            console.log("Triangle geometry:", triangle)
            console.log("Model geometry:", geometry)
        }
    }
}
