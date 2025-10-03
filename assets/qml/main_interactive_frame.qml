import QtQuick
import QtQuick3D

/*
 * SIMPLE U-SHAPED FRAME - WORKING VERSION
 * Frame immediately visible with proper camera control
 */
Item {
    id: root
    anchors.fill: parent
    
    // Simple camera state
    property real cameraDistance: 3000     // Closer to frame
    property real cameraAngleX: -15        // Look down at frame  
    property real cameraAngleY: 45         // Angle to see U-shape
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
        
        // SIMPLE WORKING CAMERA
        PerspectiveCamera {
            id: camera
            
            // FIXED: Correct spherical to cartesian conversion
            position: Qt.vector3d(
                cameraDistance * Math.cos(cameraAngleX * Math.PI / 180) * Math.sin(cameraAngleY * Math.PI / 180),
                cameraDistance * Math.sin(cameraAngleX * Math.PI / 180),
                cameraDistance * Math.cos(cameraAngleX * Math.PI / 180) * Math.cos(cameraAngleY * Math.PI / 180)
            )
            
            // FIXED: Look towards center
            eulerRotation: Qt.vector3d(cameraAngleX, cameraAngleY + 180, 0)
            
            fieldOfView: 45
            clipNear: 1         // FIXED: Very close clipping
            clipFar: 100000     // FIXED: Very far clipping - no disappearing!
        }
        
        // Good lighting
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
        
        // =====================================================
        // U-SHAPED FRAME - VISIBLE IMMEDIATELY
        // =====================================================
        
        readonly property real beamSize: 100      // Beam cross-section (mm)
        readonly property real frameHeight: 600   // Height of horns (mm)
        readonly property real frameLength: 2000  // Length along Z axis (mm)
        
        Node {
            id: frame
            
            // BOTTOM BEAM (along Z from origin)
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
            
            // FIRST HORN (at origin)
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
            
            // SECOND HORN (at end)
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
        
        // COORDINATE AXES
        Node {
            id: axes
            
            // X Axis (RED)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(300, 0, 0)
                scale: Qt.vector3d(0.2, 0.2, 6)
                eulerRotation.y: 90
                materials: PrincipledMaterial {
                    baseColor: "#ff0000"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            // Y Axis (GREEN)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(0, 300, 0)
                scale: Qt.vector3d(0.2, 6, 0.2)
                materials: PrincipledMaterial {
                    baseColor: "#00ff00"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            // Z Axis (BLUE)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(0, 0, 300)
                scale: Qt.vector3d(0.2, 0.2, 6)
                materials: PrincipledMaterial {
                    baseColor: "#0000ff"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            // Origin (WHITE)
            Model {
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
    
    // =====================================================
    // SIMPLE MOUSE CONTROL
    // =====================================================
    
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        
        onPressed: function(mouse) {
            mousePressed = true
            lastMouseX = mouse.x
            lastMouseY = mouse.y
        }
        
        onReleased: function(mouse) {
            mousePressed = false
        }
        
        onPositionChanged: function(mouse) {
            if (!mousePressed) return
            
            var deltaX = mouse.x - lastMouseX
            var deltaY = mouse.y - lastMouseY
            
            // FIXED rotation with proper clamping
            cameraAngleY += deltaX * 0.5
            cameraAngleX -= deltaY * 0.5
            
            // FIXED: Clamp X to prevent flipping
            cameraAngleX = Math.max(-89, Math.min(89, cameraAngleX))
            
            lastMouseX = mouse.x
            lastMouseY = mouse.y
        }
        
        onWheel: function(wheel) {
            var zoomFactor = 1.0 + (wheel.angleDelta.y / 1000.0)
            cameraDistance *= zoomFactor
            
            // FIXED: Prevent zoom from making frame disappear
            cameraDistance = Math.max(500, Math.min(50000, cameraDistance))
        }
        
        onDoubleClicked: function(mouse) {
            // FIXED: Reset to frame-visible view
            cameraDistance = 3000
            cameraAngleX = -15
            cameraAngleY = 45
        }
    }
    
    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_R) {
            // FIXED: Reset to frame-visible position
            cameraDistance = 3000
            cameraAngleX = -15
            cameraAngleY = 45
        }
    }
    
    focus: true
    
    // Simple info
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 250
        height: 80
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 5
        
        Column {
            anchors.centerIn: parent
            spacing: 5
            
            Text {
                text: "U-Frame (Simple Version)"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true
            }
            
            Text {
                text: "Mouse: Rotate | Wheel: Zoom | R: Reset"
                color: "#cccccc"
                font.pixelSize: 10
            }
        }
    }
    
    Component.onCompleted: {
        console.log("Simple U-frame loaded")
    }
}
