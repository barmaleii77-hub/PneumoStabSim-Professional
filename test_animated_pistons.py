#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Animated 2-meter suspension system test with visible pistons
"""
import sys
import os

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, QTimer
from pathlib import Path
import math

# Animated 2-meter suspension system QML
SUSPENSION_QML = """
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    // Animation properties
    property real animationTime: 0.0
    property real animationSpeed: 2.0

    // 2-meter suspension system coordinates (ANIMATED)
    property real beamSize: 120
    property real frameHeight: 650
    property real frameLength: 2000

    // Animated lever angles (sine waves)
    property real fl_angle: 15 * Math.sin(animationTime)
    property real fr_angle: 15 * Math.sin(animationTime + Math.PI/2)
    property real rl_angle: 15 * Math.sin(animationTime + Math.PI)
    property real rr_angle: 15 * Math.sin(animationTime + 3*Math.PI/2)

    // Base coordinates
    property vector3d fl_j_arm_base: Qt.vector3d(-150, 60, -1000)
    property vector3d fr_j_arm_base: Qt.vector3d(150, 60, -1000)
    property vector3d rl_j_arm_base: Qt.vector3d(-150, 60, 1000)
    property vector3d rr_j_arm_base: Qt.vector3d(150, 60, 1000)

    property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)
    property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)
    property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)
    property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)

    // Animated rod positions (70% along 450mm lever from pivot)
    property real leverLength: 450
    property real attachFrac: 0.7
    
    property vector3d fl_j_rod: Qt.vector3d(
        fl_j_arm_base.x + leverLength * attachFrac * Math.cos(fl_angle * Math.PI / 180),
        fl_j_arm_base.y + leverLength * attachFrac * Math.sin(fl_angle * Math.PI / 180),
        fl_j_arm_base.z
    )
    property vector3d fr_j_rod: Qt.vector3d(
        fr_j_arm_base.x + leverLength * attachFrac * Math.cos(fr_angle * Math.PI / 180),
        fr_j_arm_base.y + leverLength * attachFrac * Math.sin(fr_angle * Math.PI / 180),
        fr_j_arm_base.z
    )
    property vector3d rl_j_rod: Qt.vector3d(
        rl_j_arm_base.x + leverLength * attachFrac * Math.cos(rl_angle * Math.PI / 180),
        rl_j_arm_base.y + leverLength * attachFrac * Math.sin(rl_angle * Math.PI / 180),
        rl_j_arm_base.z
    )
    property vector3d rr_j_rod: Qt.vector3d(
        rr_j_arm_base.x + leverLength * attachFrac * Math.cos(rr_angle * Math.PI / 180),
        rr_j_arm_base.y + leverLength * attachFrac * Math.sin(rr_angle * Math.PI / 180),
        rr_j_arm_base.z
    )

    // Camera
    property real cameraDistance: 3000
    property real cameraPitch: -20
    property real cameraYaw: 30

    // Animation timer
    Timer {
        running: true
        interval: 16  // ~60 FPS
        repeat: true
        onTriggered: {
            animationTime += animationSpeed * 0.016  // 16ms timestep
        }
    }

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

    // FL Suspension - ANIMATED WITH VISIBLE PISTON
    // Lever (animated rotation)
    Model {
        source: "#Cube"
        position: Qt.vector3d((fl_j_arm_base.x + fl_j_rod.x)/2, (fl_j_arm_base.y + fl_j_rod.y)/2, fl_j_arm_base.z)
        scale: Qt.vector3d(leverLength/100, 0.8, 0.8)
        eulerRotation: Qt.vector3d(0, 0, fl_angle)
        materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
    }
    
    // Fixed cylinder (250mm)
    Model {
        source: "#Cylinder"
        property vector3d cylDirection: Qt.vector3d(fl_j_rod.x - fl_j_tail.x, fl_j_rod.y - fl_j_tail.y, 0)
        property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
        property real fixedCylLength: 250
        property vector3d cylEnd: Qt.vector3d(
            fl_j_tail.x + cylDirection.x * (fixedCylLength / cylDirectionLength),
            fl_j_tail.y + cylDirection.y * (fixedCylLength / cylDirectionLength),
            fl_j_tail.z
        )
        
        position: Qt.vector3d((fl_j_tail.x + cylEnd.x)/2, (fl_j_tail.y + cylEnd.y)/2, fl_j_tail.z)
        
        property real cylAngle: Math.atan2(cylEnd.y - fl_j_tail.y, cylEnd.x - fl_j_tail.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(1.2, fixedCylLength/100, 1.2)
        eulerRotation: Qt.vector3d(0, 0, cylAngle)
        materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.6; alphaMode: PrincipledMaterial.Blend }
    }
    
    // ANIMATED PISTON (visible inside transparent cylinder)
    Model {
        source: "#Cylinder"
        property vector3d cylDirection: Qt.vector3d(fl_j_rod.x - fl_j_tail.x, fl_j_rod.y - fl_j_tail.y, 0)
        property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
        property real fixedCylLength: 250
        property real rodExtension: cylDirectionLength - fixedCylLength
        property real pistonPositionRatio: Math.max(0.0, Math.min(1.0, rodExtension / 150.0))
        
        property vector3d pistonPos: Qt.vector3d(
            fl_j_tail.x + cylDirection.x * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
            fl_j_tail.y + cylDirection.y * ((fixedCylLength * (0.8 - pistonPositionRatio * 0.6)) / cylDirectionLength),
            fl_j_tail.z
        )
        
        position: pistonPos
        
        property real pistonAngle: Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(1.15, 0.5, 1.15)  // Visible thick disc
        eulerRotation: Qt.vector3d(0, 0, pistonAngle)
        materials: PrincipledMaterial { baseColor: "#ff3333"; metalness: 0.8; roughness: 0.3 }  // RED for visibility
    }
    
    // Extending rod
    Model {
        source: "#Cylinder"
        property vector3d cylDirection: Qt.vector3d(fl_j_rod.x - fl_j_tail.x, fl_j_rod.y - fl_j_tail.y, 0)
        property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
        property real fixedCylLength: 250
        property vector3d rodStart: Qt.vector3d(
            fl_j_tail.x + cylDirection.x * (fixedCylLength / cylDirectionLength),
            fl_j_tail.y + cylDirection.y * (fixedCylLength / cylDirectionLength),
            fl_j_tail.z
        )
        
        position: Qt.vector3d((rodStart.x + fl_j_rod.x)/2, (rodStart.y + fl_j_rod.y)/2, fl_j_rod.z)
        
        property real rodLength: Math.hypot(fl_j_rod.x - rodStart.x, fl_j_rod.y - rodStart.y, 0)
        property real rodAngle: Math.atan2(fl_j_rod.y - rodStart.y, fl_j_rod.x - rodStart.x) * 180 / Math.PI + 90
        
        scale: Qt.vector3d(0.5, rodLength/100, 0.5)
        eulerRotation: Qt.vector3d(0, 0, rodAngle)
        materials: PrincipledMaterial { baseColor: "#e6e6e6"; metalness: 1.0; roughness: 0.1 }
    }
    
    // Attachments  
    Model { source: "#Sphere"; position: fl_j_tail; scale: Qt.vector3d(1.8, 1.8, 1.8); materials: PrincipledMaterial { baseColor: "#666666"; metalness: 0.8; roughness: 0.3 } }
    Model { source: "#Sphere"; position: fl_j_arm_base; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#ffaa00"; metalness: 0.8; roughness: 0.3 } }
    Model { source: "#Sphere"; position: fl_j_rod; scale: Qt.vector3d(2.0, 2.0, 2.0); materials: PrincipledMaterial { baseColor: "#00aaff"; metalness: 0.5; roughness: 0.4 } }

    // FR, RL, RR Suspensions (similar structure but simplified for demo)
    // ... (other corners would have same structure)

    // Markers for reference
    Model { source: "#Sphere"; position: fl_j_arm_base; scale: Qt.vector3d(2.0, 2.0, 2.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_arm_base; scale: Qt.vector3d(2.0, 2.0, 2.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_arm_base; scale: Qt.vector3d(2.0, 2.0, 2.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_arm_base; scale: Qt.vector3d(2.0, 2.0, 2.0); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    
    Model { source: "#Sphere"; position: fl_j_tail; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_tail; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_tail; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_tail; scale: Qt.vector3d(1.5, 1.5, 1.5); materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting } }

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
        console.log("=== ANIMATED 2-METER SUSPENSION WITH VISIBLE PISTONS ===")
        console.log("Watch the RED pistons move inside transparent cylinders!")
        view3d.forceActiveFocus()
    }
}
"""

class AnimatedSuspensionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("ANIMATED SUSPENSION - VISIBLE PISTONS")
        self.resize(1400, 900)
        
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
        
        qml_path = Path("animated_suspension.qml")
        qml_path.write_text(SUSPENSION_QML, encoding='utf-8')
        
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)
        
        if self.qml_widget.status() == QQuickWidget.Status.Error:
            errors = self.qml_widget.errors()
            print(f"QML ERRORS: {[str(e) for e in errors]}")
        else:
            print("? Animated suspension loaded successfully")
        
        self.setCentralWidget(self.qml_widget)

def main():
    print("="*60)
    print("ANIMATED SUSPENSION - VISIBLE PISTONS DEMO")
    print("="*60)
    print("Features:")
    print("- Lever rotates around pivot")
    print("- Cylinder fixed 250mm length")
    print("- Rod extends/retracts from cylinder")
    print("- RED PISTON visible inside transparent cylinder")
    print("- Piston moves with rod extension")
    print("="*60)
    
    app = QApplication(sys.argv)
    window = AnimatedSuspensionWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()