import QtQuick
import QtQuick3D

/*
 * Qt Quick 3D scene with PBR materials
 * Uses RHI backend (Direct3D on Windows, no OpenGL)
 */
View3D {
    id: root
    width: 800
    height: 600
    
    // Dark background
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#101418"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: SceneEnvironment.High
    }
    
    // Camera setup (isometric-like view)
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 1.5, 5)
        eulerRotation.x: -15
        eulerRotation.y: 0
        
        // Allow runtime camera adjustment via properties
        property real distance: 5.0
        property real pitch: -15.0
        property real yaw: 0.0
    }
    
    // Main directional light
    DirectionalLight {
        eulerRotation.x: -45
        eulerRotation.y: 30
        brightness: 1000
        castsShadow: true
    }
    
    // Ambient/fill light
    DirectionalLight {
        eulerRotation.x: 20
        eulerRotation.y: -110
        brightness: 300
        color: "#6080a0"
    }
    
    // Ground plane (simple reference)
    Model {
        id: ground
        source: "#Rectangle"
        y: -0.5
        scale: Qt.vector3d(10, 10, 1)
        eulerRotation.x: -90
        materials: PrincipledMaterial {
            baseColor: "#2a2a3e"
            metalness: 0.1
            roughness: 0.9
        }
    }
    
    // Main demonstration sphere (PBR metal)
    Model {
        id: sphere
        source: "#Sphere"
        position: Qt.vector3d(0, 0.5, 0)
        scale: Qt.vector3d(1.2, 1.2, 1.2)
        
        materials: PrincipledMaterial {
            baseColor: "#b0b6c2"
            metalness: 0.85
            roughness: 0.2
            normalMap: Texture {}
        }
        
        // Smooth rotation animation
        NumberAnimation on eulerRotation.y {
            from: 0
            to: 360
            duration: 6000
            loops: Animation.Infinite
        }
    }
    
    // Additional cube (for visual interest)
    Model {
        id: cube
        source: "#Cube"
        position: Qt.vector3d(2, 0.3, 0)
        scale: Qt.vector3d(0.6, 0.6, 0.6)
        
        materials: PrincipledMaterial {
            baseColor: "#ff6b35"
            metalness: 0.3
            roughness: 0.5
        }
        
        // Counter-rotation
        NumberAnimation on eulerRotation.y {
            from: 0
            to: -360
            duration: 8000
            loops: Animation.Infinite
        }
    }
    
    // Text overlay (simulation info will be added here)
    Rectangle {
        id: overlay
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 10
        width: 250
        height: 120
        color: "#20000000"
        border.color: "#40ffffff"
        border.width: 1
        radius: 5
        
        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5
            
            Text {
                text: "Qt Quick 3D (RHI/Direct3D)"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true
            }
            
            Text {
                id: backendInfo
                text: "Backend: D3D11"
                color: "#a0a0a0"
                font.pixelSize: 11
            }
            
            Text {
                id: simInfo
                text: "Simulation: Idle"
                color: "#a0a0a0"
                font.pixelSize: 11
            }
            
            Text {
                id: fpsInfo
                text: "FPS: 60"
                color: "#a0a0a0"
                font.pixelSize: 11
            }
        }
    }
    
    // Expose properties for C++ integration
    property alias cameraDistance: camera.distance
    property alias cameraPitch: camera.pitch
    property alias cameraYaw: camera.yaw
    property alias simulationText: simInfo.text
    property alias fpsText: fpsInfo.text
}
