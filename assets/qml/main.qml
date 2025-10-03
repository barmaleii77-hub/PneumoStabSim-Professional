import QtQuick
import QtQuick3D
import QtQuick.Controls

/*
 * MAIN PNEUMATIC SUSPENSION VISUALIZATION
 * Interactive 3D frame with unlimited mouse controls
 */
ApplicationWindow {
    id: mainWindow
    visible: true
    width: 1200
    height: 800
    title: "PneumoStabSim - 3D Interactive Frame"
    
    // Camera state for U-shaped frame
    property real cameraDistance: 3000
    property real cameraAngleX: -15
    property real cameraAngleY: 45
    property bool mousePressed: false
    property real lastMouseX: 0
    property real lastMouseY: 0
    
    View3D {
        id: view3d
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#2a2a2a"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }
        
        // Camera for U-shaped frame
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(
                mainWindow.cameraDistance * Math.cos(mainWindow.cameraAngleX * Math.PI / 180) * Math.sin(mainWindow.cameraAngleY * Math.PI / 180),
                mainWindow.cameraDistance * Math.sin(mainWindow.cameraAngleX * Math.PI / 180),
                mainWindow.cameraDistance * Math.cos(mainWindow.cameraAngleX * Math.PI / 180) * Math.cos(mainWindow.cameraAngleY * Math.PI / 180)
            )
            eulerRotation: Qt.vector3d(mainWindow.cameraAngleX, mainWindow.cameraAngleY + 180, 0)
            fieldOfView: 45
            clipNear: 1
            clipFar: 100000
        }
        
        // Lighting
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: -45
            brightness: 1.5
        }
        
        DirectionalLight {
            eulerRotation.x: 30
            eulerRotation.y: 135
            brightness: 1.0
        }
        
        // U-SHAPED FRAME IN ZY PLANE
        readonly property real beamSize: 100
        readonly property real frameHeight: 600
        readonly property real frameLength: 2000
        
        Node {
            id: uFrame
            
            // Bottom beam along Z axis
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamSize/2, view3d.frameLength/2)
                scale: Qt.vector3d(view3d.beamSize/100, view3d.beamSize/100, view3d.frameLength/100)
                materials: PrincipledMaterial {
                    baseColor: "#999999"
                    metalness: 0.7
                    roughness: 0.3
                }
            }
            
            // First horn at origin
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamSize + view3d.frameHeight/2, view3d.beamSize/2)
                scale: Qt.vector3d(view3d.beamSize/100, view3d.frameHeight/100, view3d.beamSize/100)
                materials: PrincipledMaterial {
                    baseColor: "#999999"
                    metalness: 0.7
                    roughness: 0.3
                }
            }
            
            // Second horn at end
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamSize + view3d.frameHeight/2, view3d.frameLength - view3d.beamSize/2)
                scale: Qt.vector3d(view3d.beamSize/100, view3d.frameHeight/100, view3d.beamSize/100)
                materials: PrincipledMaterial {
                    baseColor: "#999999"
                    metalness: 0.7
                    roughness: 0.3
                }
            }
        }
        
        // Coordinate axes
        Node {
            id: axes
            
            Model { // X axis (red)
                source: "#Cylinder"
                position: Qt.vector3d(300, 0, 0)
                scale: Qt.vector3d(0.2, 0.2, 6)
                eulerRotation.y: 90
                materials: PrincipledMaterial {
                    baseColor: "#ff0000"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            Model { // Y axis (green)
                source: "#Cylinder"
                position: Qt.vector3d(0, 300, 0)
                scale: Qt.vector3d(0.2, 6, 0.2)
                materials: PrincipledMaterial {
                    baseColor: "#00ff00"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            Model { // Z axis (blue)
                source: "#Cylinder"
                position: Qt.vector3d(0, 0, 300)
                scale: Qt.vector3d(0.2, 0.2, 6)
                materials: PrincipledMaterial {
                    baseColor: "#0000ff"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            Model { // Origin (white)
                source: "#Sphere"
                position: Qt.vector3d(0, 0, 0)
                scale: Qt.vector3d(0.8, 0.8, 0.8)
                materials: PrincipledMaterial {
                    baseColor: "#ffffff"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
        }
    }
    
    // Mouse interaction
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        
        onPressed: function(mouse) {
            mainWindow.mousePressed = true
            mainWindow.lastMouseX = mouse.x
            mainWindow.lastMouseY = mouse.y
        }
        
        onReleased: function(mouse) {
            mainWindow.mousePressed = false
        }
        
        onPositionChanged: function(mouse) {
            if (!mainWindow.mousePressed) return
            
            var deltaX = mouse.x - mainWindow.lastMouseX
            var deltaY = mouse.y - mainWindow.lastMouseY
            
            mainWindow.cameraAngleY += deltaX * 0.5
            mainWindow.cameraAngleX -= deltaY * 0.5
            mainWindow.cameraAngleX = Math.max(-89, Math.min(89, mainWindow.cameraAngleX))
            
            mainWindow.lastMouseX = mouse.x
            mainWindow.lastMouseY = mouse.y
        }
        
        onWheel: function(wheel) {
            var zoomFactor = 1.0 + (wheel.angleDelta.y / 1000.0)
            mainWindow.cameraDistance *= zoomFactor
            mainWindow.cameraDistance = Math.max(500, Math.min(50000, mainWindow.cameraDistance))
        }
        
        onDoubleClicked: function(mouse) {
            mainWindow.cameraDistance = 3000
            mainWindow.cameraAngleX = -15
            mainWindow.cameraAngleY = 45
        }
    }
    
    // Info overlay
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 300
        height: 100
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 5
        
        Column {
            anchors.centerIn: parent
            spacing: 5
            
            Text {
                text: "PneumoStabSim - Interactive 3D Frame"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true
            }
            
            Text {
                text: "U-shaped frame in ZY plane"
                color: "#cccccc"
                font.pixelSize: 11
            }
            
            Text {
                text: "Mouse: Rotate | Wheel: Zoom | Double-click: Reset"
                color: "#aaaaaa"
                font.pixelSize: 10
            }
        }
    }
    
    Component.onCompleted: {
        console.log("PneumoStabSim 3D Frame loaded")
    }
}
