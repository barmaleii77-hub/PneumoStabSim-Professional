import QtQuick
import QtQuick3D

/*
 * SIMPLE U-SHAPED FRAME IN ZY PLANE
 * Clean rectangular (square) cross-section beam  
 * Bottom beam from origin (0,0,0) along +Z axis
 * Horns from origin and end up along +Y axis
 * Frame lies entirely in ZY plane (X=0)
 * Scene rotates around origin (0,0,0)
 * FIXED: Scale, auto-zoom, and correct ZY plane orientation
 */
Item {
    id: root
    anchors.fill: parent
    
    // Mouse interaction state - ROTATE AROUND ORIGIN
    property real cameraDistance: 5000  // Further back to see frame from origin
    property real cameraAngleX: -20     // Look down slightly
    property real cameraAngleY: 45      // Side angle to see U-shape clearly
    property bool mousePressed: false
    property real lastMouseX: 0
    property real lastMouseY: 0
    
    // Camera target (for panning) - ROTATE AROUND ORIGIN!
    property vector3d cameraTarget: Qt.vector3d(0, 0, 0)  // Origin, not frame center!
    
    View3D {
        id: view3d
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#1a1a1a"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }
        
        // CAMERA - Orbiting around target (with panning support)
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(
                cameraTarget.x + cameraDistance * Math.sin(cameraAngleY * Math.PI / 180) * Math.cos(cameraAngleX * Math.PI / 180),
                cameraTarget.y + cameraDistance * Math.sin(cameraAngleX * Math.PI / 180),
                cameraTarget.z + cameraDistance * Math.cos(cameraAngleY * Math.PI / 180) * Math.cos(cameraAngleX * Math.PI / 180)
            )
            eulerRotation: Qt.vector3d(cameraAngleX, cameraAngleY, 0)
            fieldOfView: 45
            clipNear: 1      // Reduced for close viewing
            clipFar: 50000
        }
        
        // LIGHTING - MULTIPLE SOURCES FOR PROPER ILLUMINATION
        DirectionalLight {
            eulerRotation.x: -45
            eulerRotation.y: -30
            brightness: 2.5  // Brighter
            color: "#ffffff"
        }
        
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: 140
            brightness: 1.8  // Brighter
            color: "#ffffff"
        }
        
        // Additional lights for better visibility
        DirectionalLight {
            eulerRotation.x: 30
            eulerRotation.y: 60
            brightness: 1.5
            color: "#ffffff"
        }
        
        DirectionalLight {
            eulerRotation.x: 10
            eulerRotation.y: -120
            brightness: 1.2
            color: "#ffffff"
        }
        
        // Top-down light
        DirectionalLight {
            eulerRotation.x: -80
            eulerRotation.y: 0
            brightness: 1.0
            color: "#ffffff"
        }
        
        // =====================================================
        // U-SHAPED FRAME (FIXED SCALE)
        // =====================================================
        
        // Frame parameters (SQUARE cross-section, ZY plane)
        readonly property real beamWidth: 200      // Square cross-section size (mm)
        readonly property real beamHeight: 300     // Height of bottom beam (mm) 
        readonly property real frameSpan: 2000     // Not used in ZY plane
        readonly property real frameHeight: 800    // Height of horns (mm)
        readonly property real frameLength: 3000   // Length along +Z axis (mm)
        
        Node {
            id: uFrame
            
            // BOTTOM BEAM (from origin 0,0,0 along +Z axis) - IN ZY PLANE
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamWidth/2, view3d.frameLength/2)
                scale: Qt.vector3d(view3d.beamWidth/100, view3d.beamWidth/100, view3d.frameLength/100)
                materials: PrincipledMaterial {
                    baseColor: "#888888"  // Brighter gray
                    metalness: 0.6
                    roughness: 0.3
                }
            }
            
            // FIRST HORN (from beam center, not edge) - FIXED POSITIONING
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamWidth + view3d.frameHeight/2, view3d.beamWidth/2)
                scale: Qt.vector3d(view3d.beamWidth/100, view3d.frameHeight/100, view3d.beamWidth/100)
                materials: PrincipledMaterial {
                    baseColor: "#888888"  // Brighter gray
                    metalness: 0.6
                    roughness: 0.3
                }
            }
            
            // SECOND HORN (from beam center at end) - FIXED POSITIONING  
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamWidth + view3d.frameHeight/2, view3d.frameLength - view3d.beamWidth/2)
                scale: Qt.vector3d(view3d.beamWidth/100, view3d.frameHeight/100, view3d.beamWidth/100)
                materials: PrincipledMaterial {
                    baseColor: "#888888"  // Brighter gray
                    metalness: 0.6
                    roughness: 0.3
                }
            }
        }
        
        // =====================================================
        // COORDINATE AXES (LARGER for visibility)
        // =====================================================
        
        Node {
            id: axes
            
            // X Axis (RED) - SCALED TO FRAME
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(800, 0, 0)  // Scaled to frame
                scale: Qt.vector3d(0.3, 0.3, 8)  // Smaller, proportional
                eulerRotation.y: 90
                materials: PrincipledMaterial {
                    baseColor: "#ff0000"  // RED
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            // Y Axis (GREEN) - SCALED TO FRAME
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(0, 800, 0)  // Scaled to frame
                scale: Qt.vector3d(0.3, 8, 0.3)  // Smaller, proportional
                materials: PrincipledMaterial {
                    baseColor: "#00ff00"  // GREEN
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            // Z Axis (BLUE) - SCALED TO FRAME
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(0, 0, 800)  // Scaled to frame
                scale: Qt.vector3d(0.3, 0.3, 8)  // Smaller, proportional
                materials: PrincipledMaterial {
                    baseColor: "#0000ff"  // BLUE
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            // Origin marker (WHITE) - SCALED TO FRAME
            Model {
                source: "#Sphere"
                position: Qt.vector3d(0, 0, 0)
                scale: Qt.vector3d(1, 1, 1)  // Smaller, proportional
                materials: PrincipledMaterial {
                    baseColor: "#ffffff"  // WHITE
                    lighting: PrincipledMaterial.NoLighting
                }
            }
        }
    }
    
    // =====================================================
    // ENHANCED MOUSE INTERACTION + AUTO-ZOOM
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
            
            // Check for panning mode (Shift+Mouse or Right mouse button)
            var isPanning = (mouse.modifiers & Qt.ShiftModifier) || (mouse.buttons & Qt.RightButton)
            
            if (isPanning) {
                // PANNING - Move camera target (REDUCED SENSITIVITY)
                var panSensitivity = cameraDistance * 0.0003  // Much less sensitive!
                
                // Calculate camera right and up vectors for proper panning
                var angleYRad = cameraAngleY * Math.PI / 180
                var angleXRad = cameraAngleX * Math.PI / 180
                
                // Right vector (for horizontal panning)
                var rightX = Math.cos(angleYRad)
                var rightZ = -Math.sin(angleYRad)
                
                // Up vector (for vertical panning)  
                var upX = Math.sin(angleYRad) * Math.sin(angleXRad)
                var upY = Math.cos(angleXRad)
                var upZ = Math.cos(angleYRad) * Math.sin(angleXRad)
                
                // Apply panning (SMALLER MOVEMENTS)
                cameraTarget.x -= rightX * deltaX * panSensitivity
                cameraTarget.y += upY * deltaY * panSensitivity
                cameraTarget.z -= rightZ * deltaX * panSensitivity
                
                // Update target property to trigger camera update
                cameraTarget = Qt.vector3d(cameraTarget.x, cameraTarget.y, cameraTarget.z)
            } else {
                // ROTATION - Rotate around target (REDUCED SENSITIVITY)
                cameraAngleY += deltaX * 0.3  // Less sensitive
                cameraAngleX -= deltaY * 0.3  // Less sensitive
                
                // Clamp vertical angle
                cameraAngleX = Math.max(-89, Math.min(89, cameraAngleX))
            }
            
            lastMouseX = mouse.x
            lastMouseY = mouse.y
        }
        
        onWheel: function(wheel) {
            // Zoom in/out - FIXED LIMITS
            var zoomFactor = 1.0 + (wheel.angleDelta.y / 1200.0)  // Less sensitive
            cameraDistance *= zoomFactor
            cameraDistance = Math.max(1000, Math.min(20000, cameraDistance))  // Better limits
        }
        
        // AUTO-ZOOM on double-click - ROTATE AROUND ORIGIN
        onDoubleClicked: function(mouse) {
            console.log("Double-click: Auto-zooming, rotating around origin (0,0,0)")
            
            // Animate to optimal viewing distance - ORIGIN CENTERED
            cameraDistanceAnimation.to = 5000   // Distance to see frame from origin
            cameraAngleXAnimation.to = -20      // Look down at frame
            cameraAngleYAnimation.to = 45       // Side angle to see U-shape
            
            // Reset target to ORIGIN (not frame center!)
            cameraTarget = Qt.vector3d(0, 0, 0)  // ORIGIN
            
            cameraDistanceAnimation.start()
            cameraAngleXAnimation.start() 
            cameraAngleYAnimation.start()
        }
    }
    
    // Smooth animations for auto-zoom
    NumberAnimation {
        id: cameraDistanceAnimation
        target: root
        property: "cameraDistance"
        duration: 800
        easing.type: Easing.OutCubic
    }
    
    NumberAnimation {
        id: cameraAngleXAnimation
        target: root
        property: "cameraAngleX"
        duration: 800
        easing.type: Easing.OutCubic
    }
    
    NumberAnimation {
        id: cameraAngleYAnimation
        target: root
        property: "cameraAngleY"
        duration: 800
        easing.type: Easing.OutCubic
    }
    
    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_R) {
            // Reset camera - ROTATE AROUND ORIGIN
            cameraDistance = 5000
            cameraAngleX = -20
            cameraAngleY = 45
            cameraTarget = Qt.vector3d(0, 0, 0)  // ORIGIN
        }
    }
    
    focus: true
    
    // =====================================================
    // ENHANCED INFO OVERLAY - UPDATED
    // =====================================================
    
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 350
        height: 160
        color: "#cc000000"
        border.color: "#60ffffff"
        border.width: 1
        radius: 6
        
        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 4
            
            Text {
                text: "U-Shaped Frame (ZY Plane)"
                color: "#ffffff"
                font.pixelSize: 16
                font.bold: true
            }
            
            Text {
                text: "Square cross-section: " + view3d.beamWidth + "?" + view3d.beamWidth + " mm"
                color: "#cccccc"
                font.pixelSize: 11
            }
            
            Text {
                text: "????????????????????????????????"
                color: "#444444"
                font.pixelSize: 10
            }
            
            Text {
                text: "?? Axes: RED=X, GREEN=Y, BLUE=Z, WHITE=Origin"
                color: "#aaaaaa"
                font.pixelSize: 10
                font.bold: true
            }
            
            Text {
                text: "?? Frame in ZY plane: Bottom along +Z, horns up +Y"
                color: "#aaaaaa"
                font.pixelSize: 10
            }
            
            Text {
                text: "?? Horns positioned at beam centers (fixed)"
                color: "#88ff88"
                font.pixelSize: 10
            }
            
            Text {
                text: "?? Rotate around ORIGIN | Shift+Mouse: Pan | Wheel: Zoom"
                color: "#888888"
                font.pixelSize: 9
            }
            
            Text {
                text: "?? Scene rotates around (0,0,0) | R: Reset"
                color: "#ffaa00"
                font.pixelSize: 9
                font.bold: true
            }
        }
    }
    
    Component.onCompleted: {
        console.log("U-shaped frame loaded (FIXED SCALE)")
        console.log("Axes colors: RED=X, GREEN=Y, BLUE=Z, WHITE=Origin")
        console.log("Double-click for auto-zoom")
    }
}
