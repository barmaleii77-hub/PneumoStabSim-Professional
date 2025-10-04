
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

View3D {
    id: view3d
    anchors.fill: parent

    // ========== FIXED CORRECT PARAMETERS ==========
    property real beamSize: 120        // CORRECT beam size
    property real frameHeight: 650     // CORRECT horn height  
    property real frameLength: 1500    // CORRECT frame length

    // CORRECT lever joint coordinates ONLY (from geometry_bridge.py)
    property vector3d fl_j_arm: Qt.vector3d(-160, 210, -450)
    property vector3d fr_j_arm: Qt.vector3d(160, 210, -450)
    property vector3d rl_j_arm: Qt.vector3d(-160, 210, 450)
    property vector3d rr_j_arm: Qt.vector3d(160, 210, 450)

    // Camera control properties
    property real cameraDistance: 2000
    property real cameraPitch: -20
    property real cameraYaw: 30

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#f0f0f0"
        antialiasingMode: SceneEnvironment.MSAA
    }

    // Orbit camera setup
    Node {
        id: rig
        position: Qt.vector3d(0, frameHeight/2, frameLength/2)
        eulerRotation: Qt.vector3d(cameraPitch, cameraYaw, 0)

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, cameraDistance)
            fieldOfView: 45
            clipNear: 10
            clipFar: 20000
        }
    }

    // Light
    DirectionalLight {
        eulerRotation.x: -30
        eulerRotation.y: -45
        brightness: 2.0
    }

    // ========== U-FRAME (CORRECT SIZES) ==========
    
    // Bottom beam
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, frameLength/2)
        scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100)
        materials: PrincipledMaterial {
            baseColor: "#cc0000"
            metalness: 0.8
            roughness: 0.4
        }
    }

    // Front horn
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, beamSize/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial {
            baseColor: "#cc0000"
            metalness: 0.8
            roughness: 0.4
        }
    }

    // Rear horn
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, frameLength - beamSize/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial {
            baseColor: "#cc0000"
            metalness: 0.8
            roughness: 0.4
        }
    }

    // ========== ORIGIN MARKER FOR COORDINATE SYSTEM CHECK ==========
    
    // Origin marker (0,0,0) - YELLOW
    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        scale: Qt.vector3d(3.0, 3.0, 3.0)
        materials: PrincipledMaterial {
            baseColor: "#ffff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }

    // ========== LEVER JOINTS ONLY (GREEN) ==========
    
    // FL lever joint
    Model {
        source: "#Sphere"
        position: fl_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }
    
    // FR lever joint
    Model {
        source: "#Sphere"
        position: fr_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }
    
    // RL lever joint
    Model {
        source: "#Sphere"
        position: rl_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }
    
    // RR lever joint
    Model {
        source: "#Sphere"
        position: rr_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }

    // Mouse control
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        
        property real lastX: 0
        property real lastY: 0
        property bool dragging: false
        
        onPressed: function(mouse) {
            lastX = mouse.x
            lastY = mouse.y
            dragging = true
        }
        
        onReleased: function(mouse) {
            dragging = false
        }
        
        onPositionChanged: function(mouse) {
            if (!dragging) return
            
            var deltaX = mouse.x - lastX
            var deltaY = mouse.y - lastY
            
            cameraYaw += deltaX * 0.5
            cameraPitch -= deltaY * 0.5
            cameraPitch = Math.max(-89, Math.min(89, cameraPitch))
            
            lastX = mouse.x
            lastY = mouse.y
        }
        
        onWheel: function(wheel) {
            var factor = 1.0 + (wheel.angleDelta.y / 1200.0)
            cameraDistance *= factor
            cameraDistance = Math.max(500, Math.min(10000, cameraDistance))
        }
        
        onDoubleClicked: function(mouse) {
            cameraDistance = 2000
            cameraPitch = -20
            cameraYaw = 30
        }
    }

    // Keyboard controls
    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_R) {
            cameraDistance = 2000
            cameraPitch = -20
            cameraYaw = 30
        }
    }

    Component.onCompleted: {
        console.log("=== SIMPLIFIED LEVER JOINTS TEST ===")
        console.log("Frame: size=" + beamSize + "mm, height=" + frameHeight + "mm, length=" + frameLength + "mm")
        console.log("Lever joints:")
        console.log("  FL:", fl_j_arm)
        console.log("  FR:", fr_j_arm)
        console.log("  RL:", rl_j_arm)
        console.log("  RR:", rr_j_arm)
        
        var frameEdge = beamSize/2
        var distance = Math.abs(fl_j_arm.x) - frameEdge
        
        console.log("Distance from frame edge:", distance + "mm")
        console.log("Expected: ~100mm for proper attachment")
        
        if (Math.abs(distance - 100) < 20) {
            console.log("? LEVER JOINTS POSITIONED CORRECTLY!")
        } else {
            console.log("? LEVER JOINTS STILL WRONG POSITION!")
        }
        
        view3d.forceActiveFocus()
    }
}
