#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test with COMPACT coordinates centered at origin
"""
import sys
import os

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# QML with COMPACT coordinates centered at origin
COMPACT_QML = """
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    // UPDATED coordinates with 2-meter spacing and correct lever/tail distances
    property real beamSize: 120
    property real frameHeight: 650
    property real frameLength: 2000  // 2-meter frame length

    // Lever joints (300mm apart: ±150mm)
    property vector3d fl_j_arm: Qt.vector3d(-150, 60, -1000)   // Front plane
    property vector3d fr_j_arm: Qt.vector3d(150, 60, -1000)    // Front plane
    property vector3d rl_j_arm: Qt.vector3d(-150, 60, 1000)    // Rear plane
    property vector3d rr_j_arm: Qt.vector3d(150, 60, 1000)     // Rear plane

    // Cylinder tail joints (200mm apart: ±100mm)
    property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)  // At horn height
    property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)   // At horn height
    property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)   // At horn height
    property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)    // At horn height

    // Rod attachment points (70% along 450mm levers)
    property vector3d fl_j_rod: Qt.vector3d(-465, 60, -1000)
    property vector3d fr_j_rod: Qt.vector3d(465, 60, -1000)
    property vector3d rl_j_rod: Qt.vector3d(-465, 60, 1000)
    property vector3d rr_j_rod: Qt.vector3d(465, 60, 1000)

    // Camera - farther back for larger scene
    property real cameraDistance: 3000
    property real cameraPitch: -20
    property real cameraYaw: 30

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#f0f0f0"
        antialiasingMode: SceneEnvironment.MSAA
    }

    // Camera rig
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

    // U-FRAME with horns in proper 2-meter spacing
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, 0)  // Bottom beam centered
        scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100)  // 2-meter length
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // Front horn at Z = -1000
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, -1000)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // Rear horn at Z = 1000
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, 1000)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // Lever joints (GREEN) - where levers attach to frame
    Model {
        source: "#Sphere"
        position: fl_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: fr_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rl_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rr_j_arm
        scale: Qt.vector3d(2.0, 2.0, 2.0)
        materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
    }

    // Cylinder tail joints (BLUE) - where cylinders attach to frame
    Model {
        source: "#Sphere"
        position: fl_j_tail
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: fr_j_tail
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rl_j_tail
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rr_j_tail
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
    }

    // Rod attachment joints (RED) - where rods attach to levers
    Model {
        source: "#Sphere"
        position: fl_j_rod
        scale: Qt.vector3d(1.2, 1.2, 1.2)
        materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: fr_j_rod
        scale: Qt.vector3d(1.2, 1.2, 1.2)
        materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rl_j_rod
        scale: Qt.vector3d(1.2, 1.2, 1.2)
        materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting }
    }
    
    Model {
        source: "#Sphere"
        position: rr_j_rod
        scale: Qt.vector3d(1.2, 1.2, 1.2)
        materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting }
    }

    // ===== SUSPENSION GRAPHICS =====

    // FL Suspension
    // Lever (arm to rod attachment)
    Model {
        source: "#Cube"
        position: Qt.vector3d((fl_j_arm.x + fl_j_rod.x)/2, (fl_j_arm.y + fl_j_rod.y)/2, fl_j_arm.z)
        property real leverLength: Math.hypot(fl_j_rod.x - fl_j_arm.x, fl_j_rod.y - fl_j_arm.y, fl_j_rod.z - fl_j_arm.z)
        scale: Qt.vector3d(0.8, leverLength/100, 0.8)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }
    
    // Cylinder body (tail to front cover)
    Model {
        source: "#Cylinder"
        property vector3d cylStart: Qt.vector3d(fl_j_tail.x + (fl_j_rod.x - fl_j_tail.x) * 0.1, fl_j_tail.y - 150, fl_j_tail.z)
        property vector3d cylEnd: Qt.vector3d(fl_j_tail.x + (fl_j_rod.x - fl_j_tail.x) * 0.8, fl_j_tail.y - 150, fl_j_tail.z)
        position: Qt.vector3d((cylStart.x + cylEnd.x)/2, (cylStart.y + cylEnd.y)/2, cylStart.z)
        property real cylLength: Math.hypot(cylEnd.x - cylStart.x, cylEnd.y - cylStart.y, cylEnd.z - cylStart.z)
        scale: Qt.vector3d(1.0, cylLength/100, 1.0)
        materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.6; alphaMode: PrincipledMaterial.Blend }
    }
    
    // Rod (cylinder to lever)
    Model {
        source: "#Cylinder"
        position: Qt.vector3d((fl_j_rod.x + fl_j_tail.x * 0.8)/2, (fl_j_rod.y + (fl_j_tail.y - 150))/2, fl_j_rod.z)
        property real rodLength: Math.hypot(fl_j_rod.x - fl_j_tail.x * 0.8, fl_j_rod.y - (fl_j_tail.y - 150), 0)
        scale: Qt.vector3d(0.4, rodLength/100, 0.4)
        materials: PrincipledMaterial { baseColor: "#e6e6e6"; metalness: 1.0; roughness: 0.1 }
    }

    // FR Suspension (mirror of FL)
    Model {
        source: "#Cube"
        position: Qt.vector3d((fr_j_arm.x + fr_j_rod.x)/2, (fr_j_arm.y + fr_j_rod.y)/2, fr_j_arm.z)
        property real leverLength: Math.hypot(fr_j_rod.x - fr_j_arm.x, fr_j_rod.y - fr_j_arm.y, fr_j_rod.z - fr_j_arm.z)
        scale: Qt.vector3d(0.8, leverLength/100, 0.8)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }
    
    Model {
        source: "#Cylinder"
        property vector3d cylStart: Qt.vector3d(fr_j_tail.x + (fr_j_rod.x - fr_j_tail.x) * 0.1, fr_j_tail.y - 150, fr_j_tail.z)
        property vector3d cylEnd: Qt.vector3d(fr_j_tail.x + (fr_j_rod.x - fr_j_tail.x) * 0.8, fr_j_tail.y - 150, fr_j_tail.z)
        position: Qt.vector3d((cylStart.x + cylEnd.x)/2, (cylStart.y + cylEnd.y)/2, cylStart.z)
        property real cylLength: Math.hypot(cylEnd.x - cylStart.x, cylEnd.y - cylStart.y, cylEnd.z - cylStart.z)
        scale: Qt.vector3d(1.0, cylLength/100, 1.0)
        materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.6; alphaMode: PrincipledMaterial.Blend }
    }
    
    Model {
        source: "#Cylinder"
        position: Qt.vector3d((fr_j_rod.x + fr_j_tail.x * 0.8)/2, (fr_j_rod.y + (fr_j_tail.y - 150))/2, fr_j_rod.z)
        property real rodLength: Math.hypot(fr_j_rod.x - fr_j_tail.x * 0.8, fr_j_rod.y - (fr_j_tail.y - 150), 0)
        scale: Qt.vector3d(0.4, rodLength/100, 0.4)
        materials: PrincipledMaterial { baseColor: "#e6e6e6"; metalness: 1.0; roughness: 0.1 }
    }

    // RL Suspension
    Model {
        source: "#Cube"
        position: Qt.vector3d((rl_j_arm.x + rl_j_rod.x)/2, (rl_j_arm.y + rl_j_rod.y)/2, rl_j_arm.z)
        property real leverLength: Math.hypot(rl_j_rod.x - rl_j_arm.x, rl_j_rod.y - rl_j_arm.y, rl_j_rod.z - rl_j_arm.z)
        scale: Qt.vector3d(0.8, leverLength/100, 0.8)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }
    
    Model {
        source: "#Cylinder"
        property vector3d cylStart: Qt.vector3d(rl_j_tail.x + (rl_j_rod.x - rl_j_tail.x) * 0.1, rl_j_tail.y - 150, rl_j_tail.z)
        property vector3d cylEnd: Qt.vector3d(rl_j_tail.x + (rl_j_rod.x - rl_j_tail.x) * 0.8, rl_j_tail.y - 150, rl_j_tail.z)
        position: Qt.vector3d((cylStart.x + cylEnd.x)/2, (cylStart.y + cylEnd.y)/2, cylStart.z)
        property real cylLength: Math.hypot(cylEnd.x - cylStart.x, cylEnd.y - cylStart.y, cylEnd.z - cylStart.z)
        scale: Qt.vector3d(1.0, cylLength/100, 1.0)
        materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.6; alphaMode: PrincipledMaterial.Blend }
    }
    
    Model {
        source: "#Cylinder"
        position: Qt.vector3d((rl_j_rod.x + rl_j_tail.x * 0.8)/2, (rl_j_rod.y + (rl_j_tail.y - 150))/2, rl_j_rod.z)
        property real rodLength: Math.hypot(rl_j_rod.x - rl_j_tail.x * 0.8, rl_j_rod.y - (rl_j_tail.y - 150), 0)
        scale: Qt.vector3d(0.4, rodLength/100, 0.4)
        materials: PrincipledMaterial { baseColor: "#e6e6e6"; metalness: 1.0; roughness: 0.1 }
    }

    // RR Suspension  
    Model {
        source: "#Cube"
        position: Qt.vector3d((rr_j_arm.x + rr_j_rod.x)/2, (rr_j_arm.y + rr_j_rod.y)/2, rr_j_arm.z)
        property real leverLength: Math.hypot(rr_j_rod.x - rr_j_arm.x, rr_j_rod.y - rr_j_arm.y, rr_j_rod.z - rr_j_arm.z)
        scale: Qt.vector3d(0.8, leverLength/100, 0.8)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }
    
    Model {
        source: "#Cylinder"
        property vector3d cylStart: Qt.vector3d(rr_j_tail.x + (rr_j_rod.x - rr_j_tail.x) * 0.1, rr_j_tail.y - 150, rr_j_tail.z)
        property vector3d cylEnd: Qt.vector3d(rr_j_tail.x + (rr_j_rod.x - rr_j_tail.x) * 0.8, rr_j_tail.y - 150, rr_j_tail.z)
        position: Qt.vector3d((cylStart.x + cylEnd.x)/2, (cylStart.y + cylEnd.y)/2, cylStart.z)
        property real cylLength: Math.hypot(cylEnd.x - cylStart.x, cylEnd.y - cylStart.y, cylEnd.z - cylStart.z)
        scale: Qt.vector3d(1.0, cylLength/100, 1.0)
        materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.6; alphaMode: PrincipledMaterial.Blend }
    }
    
    Model {
        source: "#Cylinder"
        position: Qt.vector3d((rr_j_rod.x + rr_j_tail.x * 0.8)/2, (rr_j_rod.y + (rr_j_tail.y - 150))/2, rr_j_rod.z)
        property real rodLength: Math.hypot(rr_j_rod.x - rr_j_tail.x * 0.8, rr_j_rod.y - (rr_j_tail.y - 150), 0)
        scale: Qt.vector3d(0.4, rodLength/100, 0.4)
        materials: PrincipledMaterial { baseColor: "#e6e6e6"; metalness: 1.0; roughness: 0.1 }
    }

    // ===== MARKERS =====
    Model {
        source: "#Sphere"
        position: Qt.vector3d(fl_j_arm.x, fl_j_arm.y, fl_j_arm.z)
        scale: Qt.vector3d(4.0, 4.0, 4.0)
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }
    
    Model {
        source: "#Sphere"
        position: Qt.vector3d(fr_j_arm.x, fr_j_arm.y, fr_j_arm.z)
        scale: Qt.vector3d(4.0, 4.0, 4.0)
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }
    
    Model {
        source: "#Sphere"
        position: Qt.vector3d(rl_j_arm.x, rl_j_arm.y, rl_j_arm.z)
        scale: Qt.vector3d(4.0, 4.0, 4.0)
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }
    
    Model {
        source: "#Sphere"
        position: Qt.vector3d(rr_j_arm.x, rr_j_arm.y, rr_j_arm.z)
        scale: Qt.vector3d(4.0, 4.0, 4.0)
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            lighting: PrincipledMaterial.NoLighting
        }
    }

    Component.onCompleted: {
        console.log("=== 2-METER SUSPENSION SYSTEM ===")
        console.log("Origin (0,0,0) = YELLOW sphere")
        console.log("Frame: 2000mm long, horns at Z = ±1000mm")
        console.log("Lever joints (GREEN) - 300mm apart:")
        console.log("  FL j_arm:", fl_j_arm)
        console.log("  FR j_arm:", fr_j_arm)
        console.log("Cylinder tail joints (BLUE) - 200mm apart:")
        console.log("  FL j_tail:", fl_j_tail)
        console.log("  FR j_tail:", fr_j_tail)
        console.log("Rod attachments (RED):")
        console.log("  FL j_rod:", fl_j_rod)
        console.log("  FR j_rod:", fr_j_rod)
        
        console.log("Spacing check:")
        console.log("  Lever spacing:", Math.abs(fr_j_arm.x - fl_j_arm.x) + "mm (should be 300mm)")
        console.log("  Tail spacing:", Math.abs(fr_j_tail.x - fl_j_tail.x) + "mm (should be 200mm)")
        console.log("  Plane spacing:", Math.abs(rl_j_arm.z - fl_j_arm.z) + "mm (should be 2000mm)")
        
        view3d.forceActiveFocus()
    }
}
"""

class CompactTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("COMPACT COORDINATES TEST")
        self.resize(1200, 800)
        
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
        
        qml_path = Path("test_compact.qml")
        qml_path.write_text(COMPACT_QML, encoding='utf-8')
        
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)
        
        if self.qml_widget.status() == QQuickWidget.Status.Error:
            errors = self.qml_widget.errors()
            print(f"? QML ERRORS: {[str(e) for e in errors]}")
        else:
            print("? QML loaded successfully")
        
        self.setCentralWidget(self.qml_widget)

def main():
    print("="*60)
    print("COMPACT COORDINATES TEST")
    print("="*60)
    print("All coordinates within +/-150mm from origin")
    print("Yellow sphere = origin (0,0,0)")
    print("Green spheres = lever joints")
    print("Red frame = U-shaped frame")
    print("Blue spheres = cylinder tail joints")
    print("="*60)
    
    app = QApplication(sys.argv)
    window = CompactTestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()