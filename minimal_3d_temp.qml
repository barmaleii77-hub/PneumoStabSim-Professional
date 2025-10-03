
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent
    
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#ff0000"
        antialiasingMode: SceneEnvironment.MSAA
    }
    
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }
    
    DirectionalLight {
        eulerRotation.x: -30
        brightness: 2.0
    }
    
    Model {
        source: "#Sphere"
        scale: Qt.vector3d(2, 2, 2)
        
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            metalness: 0.0
            roughness: 0.5
        }
        
        NumberAnimation on eulerRotation.y {
            from: 0
            to: 360
            duration: 5000
            loops: Animation.Infinite
            running: true
        }
    }
}
