
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
            position: Qt.vector3d(0, 0, 3)
        }
        
        DirectionalLight {
            brightness: 10.0
            eulerRotation.x: -45
        }
        
        Model {
            geometry: SphereGeometry { }
            
            materials: PrincipledMaterial {
                baseColor: "#ffffff"
                lighting: PrincipledMaterial.NoLighting
            }
            
            Component.onCompleted: {
                console.log("=== MODEL DEBUG ===")
                console.log("Model created")
                console.log("Geometry:", geometry)
                console.log("Geometry != null:", geometry !== null)
                console.log("Materials:", materials)
                console.log("Visible:", visible)
                console.log("Scale:", scale)
                console.log("Position:", position)
                console.log("=== END DEBUG ===")
            }
        }
    }
}
