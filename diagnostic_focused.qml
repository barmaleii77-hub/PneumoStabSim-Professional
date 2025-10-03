
import QtQuick
import QtQuick3D
import CustomGeometry 1.0

Item {
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#1a1a2e"
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }
        
        DirectionalLight {
            brightness: 2.0
        }
        
        Model {
            geometry: SphereGeometry { }
            
            materials: PrincipledMaterial {
                baseColor: "#ff4444"
            }
            
            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
            
            Component.onCompleted: {
                console.log("=== MODEL DIAGNOSTIC ===")
                console.log("geometry:", geometry)
                console.log("geometry !== null:", geometry !== null)
                console.log("visible:", visible)
                console.log("opacity:", opacity)
                console.log("position:", position)
                console.log("scale:", scale)
                console.log("materials:", materials)
                console.log("=== END DIAGNOSTIC ===")
            }
        }
    }
}
