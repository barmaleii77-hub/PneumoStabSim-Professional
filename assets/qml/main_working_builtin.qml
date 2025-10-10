import QtQuick
import QtQuick3D

/*
 * WORKING SOLUTION: Using built-in Qt Quick 3D primitives
 * Based on working example from barmaleii77-hub directory
 */
Item {
    id: root
    anchors.fill: parent
    
    View3D {
        id: view3d
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#1a1a2e"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }
        
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 600)
            fieldOfView: 60
            clipNear: 1
            clipFar: 10000
        }
        
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: -30
            brightness: 1.5
            color: "#ffffff"
        }
        
        // WORKING SPHERE using built-in primitive
        Model {
            id: mainSphere
            
            source: "#Sphere"  // Built-in Qt Quick 3D sphere primitive
            position: Qt.vector3d(0, 0, 0)
            scale: Qt.vector3d(2, 2, 2)  // Scale up for visibility
            
            materials: PrincipledMaterial {
                baseColor: "#ff4444"
                metalness: 0.0
                roughness: 0.5
            }
            
            // Smooth rotation animation
            NumberAnimation on eulerRotation.y {
                from: 0
                to: 360
                duration: 3000
                loops: Animation.Infinite
                running: true
            }
            
            Component.onCompleted: {
                console.log("Built-in sphere created successfully")
                console.log("Position:", position)
                console.log("Scale:", scale)
            }
        }
    }
    
    // Info overlay
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 20
        width: 300
        height: 80
        color: "#20000000"
        border.color: "#40ffffff"
        border.width: 1
        radius: 5
        
        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5
            
            Text {
                text: "Built-in 3D Sphere"
                color: "#ffffff"
                font.pixelSize: 16
                font.bold: true
            }
            
            Text {
                text: "Using Qt Quick 3D primitives"
                color: "#aaaaaa"
                font.pixelSize: 12
            }
            
            Text {
                text: "source: \"#Sphere\""
                color: "#888888"
                font.pixelSize: 10
            }
        }
    }
}
