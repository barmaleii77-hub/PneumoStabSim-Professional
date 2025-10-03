
import QtQuick
import QtQuick3D
import TestGeometry 1.0

Item {
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#0000ff"
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 3)
        }
        
        DirectionalLight {
            brightness: 5.0
        }
        
        Model {
            geometry: SimpleTriangle { }
            
            materials: PrincipledMaterial {
                baseColor: "#ffff00"
                lighting: PrincipledMaterial.NoLighting
            }
            
            Component.onCompleted: {
                console.log("TRIANGLE TEST")
                console.log("Geometry:", geometry)
            }
        }
    }
}
