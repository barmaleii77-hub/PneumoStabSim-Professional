
import QtQuick
import QtQuick3D
import GeometryExample 1.0

Item {
    id: root
    
    View3D {
        id: view3d
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#404040"
        }
        
        camera: PerspectiveCamera {
            position: Qt.vector3d(0, 0, 3)
            clipNear: 0.1
            clipFar: 100.0
        }
        
        DirectionalLight {
            position: Qt.vector3d(0, 10, 10)
            brightness: 1.0
        }
        
        Model {
            id: triangleModel
            
            geometry: ExampleTriangleGeometry {
                id: triangleGeometry
            }
            
            materials: [
                PrincipledMaterial {
                    baseColor: "#ff0000"
                    roughness: 0.1
                    metalness: 0.0
                }
            ]
            
            Component.onCompleted: {
                console.log("=== DOCUMENTATION TEST ===")
                console.log("Model completed")
                console.log("Geometry:", geometry)  
                console.log("Geometry type:", typeof geometry)
                console.log("Materials:", materials)
                console.log("=========================")
            }
        }
    }
    
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.margins: 10
        width: 200
        height: 40
        color: "#80000000"
        radius: 5
        
        Text {
            anchors.centerIn: parent
            text: "Documentation Pattern Test"
            color: "#ffffff"
            font.pixelSize: 12
        }
    }
}
