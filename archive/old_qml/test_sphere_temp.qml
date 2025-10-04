
import QtQuick
import QtQuick3D

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
        eulerRotation.x: -30
        brightness: 1.0
    }
    
    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        
        materials: PrincipledMaterial {
            baseColor: "#ff4444"
            metalness: 0.0
            roughness: 0.5
        }
        
        NumberAnimation on eulerRotation.y {
            from: 0
            to: 360
            duration: 3000
            loops: Animation.Infinite
        }
    }
    
    Text {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -200
        text: "RED ROTATING SPHERE"
        color: "#ffffff"
        font.pixelSize: 24
        font.bold: true
        style: Text.Outline
        styleColor: "#000000"
    }
}
