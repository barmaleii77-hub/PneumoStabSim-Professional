
import QtQuick
import QtQuick3D
import GeometryExample 1.0

View3D {
    id: view3d
    anchors.fill: parent
    
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#008000"
    }
    
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 2)
    }
    
    DirectionalLight {
        brightness: 10.0
    }
    
    Model {
        geometry: ExampleTriangleGeometry { }
        
        materials: PrincipledMaterial {
            baseColor: "#ffffff"
            lighting: PrincipledMaterial.NoLighting
        }
        
        Component.onCompleted: {
            console.log("?? DEEP DIAGNOSTIC")
            console.log("Model position:", position)
            console.log("Model scale:", scale)
            console.log("Model visible:", visible)
            console.log("Model opacity:", opacity)
            console.log("Model eulerRotation:", eulerRotation)
            console.log("Geometry bounds:", geometry ? "present" : "null")
            console.log("Materials count:", materials.length)
        }
    }
}
