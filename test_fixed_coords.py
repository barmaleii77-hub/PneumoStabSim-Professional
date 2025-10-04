#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test with FIXED coordinates directly in QML
"""
import sys
import os

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
os.environ.setdefault("QSG_INFO", "1")

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# ”œ–ŒŸ®ÕÕ€… QML “ŒÀ‹ Œ — ÿ¿–Õ»–¿Ã» –€◊¿√Œ¬ » ”œ–¿¬À≈Õ»≈Ã
FIXED_QML = """
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

    // NEW COMPACT coordinates centered around origin (from geometry_bridge.py)
    property vector3d fl_j_arm: Qt.vector3d(-80, 120, -45)
    property vector3d fr_j_arm: Qt.vector3d(80, 120, -45)
    property vector3d rl_j_arm: Qt.vector3d(-80, 120, 45)
    property vector3d rr_j_arm: Qt.vector3d(80, 120, 45)

    // Camera control properties - ¡À»∆≈ Í ˆÂÌÚÛ
    property real cameraDistance: 800   // Closer camera
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

    // ========== U-FRAME CENTERED AT ORIGIN ==========
    
    // Bottom beam - CENTERED at origin
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, 0)  // Center at Y=60, Z=0
        scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100)
        materials: PrincipledMaterial {
            baseColor: "#cc0000"
            metalness: 0.8
            roughness: 0.4
        }
    }

    // Front horn - CENTERED
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, -frameLength/2 + beamSize/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial {
            baseColor: "#cc0000"
            metalness: 0.8
            roughness: 0.4
        }
    }

    // Rear horn - CENTERED
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, frameLength/2 - beamSize/2)
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
"""

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("FIXED COORDINATES TEST")
        self.resize(1200, 800)
        
        # —ÓÁ‰‡∏Ï QML widget Ò ÙËÍÒËÓ‚‡ÌÌ˚ÏË ÍÓÓ‰ËÌ‡Ú‡ÏË
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
        
        # «‡ÔËÒ˚‚‡ÂÏ QML ‚ ‚ÂÏÂÌÌ˚È Ù‡ÈÎ
        qml_path = Path("test_fixed.qml")
        qml_path.write_text(FIXED_QML, encoding='utf-8')
        
        # «‡„ÛÊ‡ÂÏ QML
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        print(f"Loading QML: {qml_url.toString()}")
        self.qml_widget.setSource(qml_url)
        
        # œÓ‚ÂˇÂÏ Ó¯Ë·ÍË
        if self.qml_widget.status() == QQuickWidget.Status.Error:
            errors = self.qml_widget.errors()
            error_msg = "\n".join(str(e) for e in errors)
            print(f"? QML ERRORS:\n{error_msg}")
        else:
            print("? QML loaded successfully")
        
        self.setCentralWidget(self.qml_widget)

def main():
    print("="*60)
    print("FIXED COORDINATES TEST")
    print("="*60)
    print("Using hardcoded correct coordinates directly in QML")
    print("No Python property passing - everything fixed")
    print()
    
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print()
    print("="*60)
    print("EXPECTED:")
    print("  - Red U-frame (correct size: 120x650x1500)")
    print("  - White spheres at frame corners")
    print("  - Green/Blue/Red spheres NEAR frame (not far away)")
    print("  - All markers should be CLOSE together")
    print("="*60)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()