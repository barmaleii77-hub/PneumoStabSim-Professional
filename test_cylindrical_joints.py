#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2-meter suspension system with CYLINDRICAL JOINTS along Z-axis
"""
import sys
import os

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# 2-meter suspension system with cylindrical joints QML
SUSPENSION_QML = """
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    // 2-meter suspension system coordinates
    property real beamSize: 120
    property real frameHeight: 650
    property real frameLength: 2000

    // Lever joints (300mm apart)
    property vector3d fl_j_arm: Qt.vector3d(-150, 60, -1000)
    property vector3d fr_j_arm: Qt.vector3d(150, 60, -1000)
    property vector3d rl_j_arm: Qt.vector3d(-150, 60, 1000)
    property vector3d rr_j_arm: Qt.vector3d(150, 60, 1000)

    // Cylinder tail joints (200mm apart)
    property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)
    property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)
    property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)
    property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)

    // Rod attachments (horizontal levers)
    property vector3d fl_j_rod: Qt.vector3d(-465, 60, -1000)
    property vector3d fr_j_rod: Qt.vector3d(465, 60, -1000)
    property vector3d rl_j_rod: Qt.vector3d(-465, 60, 1000)
    property vector3d rr_j_rod: Qt.vector3d(465, 60, 1000)

    // Camera
    property real cameraDistance: 3000
    property real cameraPitch: -20
    property real cameraYaw: 30

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#f0f0f0"
        antialiasingMode: SceneEnvironment.MSAA
    }

    Node {
        id: rig
        position: Qt.vector3d(0, frameHeight/2, 0)
        eulerRotation: Qt.vector3d(cameraPitch, cameraYaw, 0)

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, cameraDistance)
            fieldOfView: 45
        }
    }

    DirectionalLight {
        eulerRotation.x: -30
        eulerRotation.y: -45
        brightness: 2.0
    }

    // Origin marker
    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        scale: Qt.vector3d(3.0, 3.0, 3.0)
        materials: PrincipledMaterial { baseColor: "#ffff00"; lighting: PrincipledMaterial.NoLighting }
    }

    // U-Frame
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, 0)
        scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, -1000)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, 1000)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // SUSPENSION COMPONENT WITH CYLINDRICAL JOINTS
    component SuspensionCorner: Node {
        property vector3d j_arm
        property vector3d j_tail  
        property vector3d j_rod
        
        // Lever (horizontal bar)
        Model {
            source: "#Cube"
            position: Qt.vector3d((j_arm.x + j_rod.x)/2, (j_arm.y + j_rod.y)/2, j_arm.z)
            scale: Qt.vector3d(Math.hypot(j_rod.x - j_arm.x, j_rod.y - j_arm.y, 0)/100, 0.8, 0.8)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - j_arm.y, j_rod.x - j_arm.x) * 180 / Math.PI)
            materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
        }
        
        // FIXED CYLINDER (250mm)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real fixedCylLength: 250
            property vector3d cylEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (fixedCylLength / cylDirectionLength),
                j_tail.y + cylDirection.y * (fixedCylLength / cylDirectionLength),
                j_tail.z
            )
            
            position: Qt.vector3d((j_tail.x + cylEnd.x)/2, (j_tail.y + cylEnd.y)/2, j_tail.z)
            scale: Qt.vector3d(1.2, fixedCylLength/100, 1.2)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylEnd.y - j_tail.y, cylEnd.x - j_tail.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.2; alphaMode: PrincipledMaterial.Blend }
        }
        
        // PISTON (inside cylinder, visible through transparent walls)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real fixedCylLength: 250
            property real rodExtension: cylDirectionLength - fixedCylLength
            property real pistonPositionRatio: Math.max(0.0, Math.min(1.0, rodExtension / 200.0))
            
            // Piston position (80% when retracted, moves toward 20% when extended)
            property vector3d pistonPos: Qt.vector3d(
                j_tail.x + cylDirection.x * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
                j_tail.y + cylDirection.y * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
                j_tail.z
            )
            
            position: pistonPos
            scale: Qt.vector3d(1.05, 1.0, 1.05)  // Thick visible disc
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ff0000"; metalness: 0.8; roughness: 0.2 }
        }
        
        // ROD (from piston to j_rod) - CONNECTED TO PISTON!
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real fixedCylLength: 250
            property real rodExtension: cylDirectionLength - fixedCylLength
            property real pistonPositionRatio: Math.max(0.0, Math.min(1.0, rodExtension / 200.0))
            
            // Rod starts from SAME position as piston
            property vector3d rodStart: Qt.vector3d(
                j_tail.x + cylDirection.x * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
                j_tail.y + cylDirection.y * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
                j_tail.z
            )
            
            position: Qt.vector3d((rodStart.x + j_rod.x)/2, (rodStart.y + j_rod.y)/2, j_rod.z)
            scale: Qt.vector3d(0.25, Math.hypot(j_rod.x - rodStart.x, j_rod.y - rodStart.y, 0)/100, 0.25)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - rodStart.y, j_rod.x - rodStart.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.9; roughness: 0.1 }
        }
        
        // ========== CYLINDRICAL JOINTS (along Z-axis) ==========
        
        // Cylinder tail joint (thick cylindrical hinge at frame)
        Model {
            source: "#Cylinder"
            position: j_tail
            scale: Qt.vector3d(2.4, 2.4, 1.2)  // Wide cylinder along Z-axis
            eulerRotation: Qt.vector3d(0, 0, 0)  // Aligned with Z-axis (no rotation needed)
            materials: PrincipledMaterial { baseColor: "#333333"; metalness: 0.9; roughness: 0.2 }
        }
        
        // Lever pivot joint (medium cylindrical hinge at frame)
        Model {
            source: "#Cylinder"
            position: j_arm
            scale: Qt.vector3d(2.0, 2.0, 1.0)  // Medium cylinder along Z-axis
            eulerRotation: Qt.vector3d(0, 0, 0)  // Aligned with Z-axis
            materials: PrincipledMaterial { baseColor: "#555555"; metalness: 0.9; roughness: 0.2 }
        }
        
        // Rod attachment joint (small cylindrical bushing)
        Model {
            source: "#Cylinder"
            position: j_rod
            scale: Qt.vector3d(1.6, 1.6, 0.8)  // Small cylinder along Z-axis
            eulerRotation: Qt.vector3d(0, 0, 0)  // Aligned with Z-axis
            materials: PrincipledMaterial { baseColor: "#777777"; metalness: 0.8; roughness: 0.3 }
        }
    }

    // Four suspension corners with cylindrical joints
    SuspensionCorner { j_arm: fl_j_arm; j_tail: fl_j_tail; j_rod: fl_j_rod }
    SuspensionCorner { j_arm: fr_j_arm; j_tail: fr_j_tail; j_rod: fr_j_rod }
    SuspensionCorner { j_arm: rl_j_arm; j_tail: rl_j_tail; j_rod: rl_j_rod }
    SuspensionCorner { j_arm: rr_j_arm; j_tail: rr_j_tail; j_rod: rr_j_rod }

    // Reference markers (spherical for contrast with cylindrical joints)
    Model { source: "#Sphere"; position: fl_j_arm; scale: Qt.vector3d(1.0, 1.0, 1.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_arm; scale: Qt.vector3d(1.0, 1.0, 1.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_arm; scale: Qt.vector3d(1.0, 1.0, 1.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_arm; scale: Qt.vector3d(1.0, 1.0, 1.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    
    Model { source: "#Sphere"; position: fl_j_tail; scale: Qt.vector3d(0.8, 0.8, 0.8); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_tail; scale: Qt.vector3d(0.8, 0.8, 0.8); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_tail; scale: Qt.vector3d(0.8, 0.8, 0.8); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_tail; scale: Qt.vector3d(0.8, 0.8, 0.8); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    
    Model { source: "#Sphere"; position: fl_j_rod; scale: Qt.vector3d(0.6, 0.6, 0.6); materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_rod; scale: Qt.vector3d(0.6, 0.6, 0.6); materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_rod; scale: Qt.vector3d(0.6, 0.6, 0.6); materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_rod; scale: Qt.vector3d(0.6, 0.6, 0.6); materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting } }

    // Mouse control
    MouseArea {
        anchors.fill: parent
        property real lastX: 0; property real lastY: 0; property bool dragging: false
        onPressed: function(mouse) { lastX = mouse.x; lastY = mouse.y; dragging = true }
        onReleased: function(mouse) { dragging = false }
        onPositionChanged: function(mouse) {
            if (!dragging) return
            cameraYaw += (mouse.x - lastX) * 0.5
            cameraPitch -= (mouse.y - lastY) * 0.5
            cameraPitch = Math.max(-89, Math.min(89, cameraPitch))
            lastX = mouse.x; lastY = mouse.y
        }
        onWheel: function(wheel) {
            var factor = 1.0 + (wheel.angleDelta.y / 1200.0)
            cameraDistance *= factor
            cameraDistance = Math.max(500, Math.min(8000, cameraDistance))
        }
    }

    Component.onCompleted: {
        console.log("=== 2-METER SUSPENSION WITH CYLINDRICAL JOINTS ===")
        console.log("? All joints are CYLINDERS along Z-axis")
        console.log("? Tail joints: 2.4x2.4x1.2 scale (thick)")
        console.log("? Arm joints: 2.0x2.0x1.0 scale (medium)")
        console.log("? Rod joints: 1.6x1.6x0.8 scale (small)")
        console.log("? Realistic suspension joint appearance")
        view3d.forceActiveFocus()
    }
}
"""

class CylindricalJointsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("2-METER SUSPENSION - CYLINDRICAL JOINTS")
        self.resize(1400, 900)
        
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
        
        qml_path = Path("cylindrical_joints.qml")
        qml_path.write_text(SUSPENSION_QML, encoding='utf-8')
        
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)
        
        if self.qml_widget.status() == QQuickWidget.Status.Error:
            errors = self.qml_widget.errors()
            print(f"? QML ERRORS: {[str(e) for e in errors]}")
        else:
            print("? Cylindrical joints suspension loaded successfully")
        
        self.setCentralWidget(self.qml_widget)

def main():
    print("="*60)
    print("2-METER SUSPENSION - CYLINDRICAL JOINTS")
    print("="*60)
    print("REALISTIC JOINTS:")
    print("? All joints are CYLINDERS oriented along Z-axis")
    print("? Tail joints: Wide cylinders (frame attachments)")
    print("? Arm joints: Medium cylinders (lever pivots)")
    print("? Rod joints: Small cylinders (bushing connections)")
    print("? Proper suspension appearance like real machinery")
    print("="*60)
    
    app = QApplication(sys.argv)
    window = CylindricalJointsWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()