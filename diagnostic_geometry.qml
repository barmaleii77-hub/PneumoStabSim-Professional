
import QtQuick
import QtQuick3D
import CustomGeometry 1.0

Item {
    anchors.fill: parent
    
    Rectangle {
        anchors.fill: parent
        color: "#ff0000"  // RED background to verify View3D transparency
    }
    
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }
        
        DirectionalLight {
            brightness: 3.0
        }
        
        Model {
            id: testSphere
            
            geometry: SphereGeometry {
                Component.onCompleted: {
                    console.log("SphereGeometry created")
                }
            }
            
            scale: Qt.vector3d(2, 2, 2)
            
            materials: PrincipledMaterial {
                baseColor: "#00ff00"  // GREEN
                lighting: PrincipledMaterial.FragmentLighting
            }
            
            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
            
            Component.onCompleted: {
                console.log("Model created")
                console.log("Geometry object:", geometry)
                console.log("Geometry valid:", geometry !== null)
            }
        }
    }
    
    Text {
        anchors.centerIn: parent
        text: "Look for GREEN sphere\non RED background"
        color: "#ffffff"
        font.pixelSize: 24
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
    }
}
