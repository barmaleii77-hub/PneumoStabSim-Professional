#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick diagnostic - Check if custom geometry is actually rendering
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.quick3d*=true"

from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl

# Import custom geometry
from src.ui.custom_geometry import SphereGeometry

# Test QML - absolute simplest case
TEST_QML = """
import QtQuick
import QtQuick3D
import CustomGeometry 1.0

Item {
    anchors.fill: parent
    
    Rectangle {
        anchors.fill: parent
        color: "#ff0000"  // RED background to verify View3D transparency
    }
    
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }
        
        DirectionalLight {
            brightness: 3.0
        }
        
        Model {
            id: testSphere
            
            geometry: SphereGeometry {
                Component.onCompleted: {
                    console.log("SphereGeometry created")
                }
            }
            
            scale: Qt.vector3d(2, 2, 2)
            
            materials: PrincipledMaterial {
                baseColor: "#00ff00"  // GREEN
                lighting: PrincipledMaterial.FragmentLighting
            }
            
            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
            
            Component.onCompleted: {
                console.log("Model created")
                console.log("Geometry object:", geometry)
                console.log("Geometry valid:", geometry !== null)
            }
        }
    }
    
    Text {
        anchors.centerIn: parent
        text: "Look for GREEN sphere\\non RED background"
        color: "#ffffff"
        font.pixelSize: 24
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
    }
}
"""

class QuickDiagnostic(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DIAGNOSTIC: Custom Geometry")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        info = QLabel("DIAGNOSTIC: Check console for geometry messages")
        info.setStyleSheet("background: #000; color: #0f0; padding: 10px; font-size: 14pt;")
        layout.addWidget(info)
        
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        
        qml_path = Path("diagnostic_geometry.qml")
        qml_path.write_text(TEST_QML, encoding='utf-8')
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        
        print("="*80)
        print("DIAGNOSTIC: Custom Geometry Test")
        print("="*80)
        print("Loading QML...")
        
        self.qml_widget.setSource(qml_url)
        
        layout.addWidget(self.qml_widget, 1)
        
        status = self.qml_widget.status()
        if status == QQuickWidget.Status.Error:
            errors = "\n".join([e.toString() for e in self.qml_widget.errors()])
            print(f"\nERROR:\n{errors}\n")
        elif status == QQuickWidget.Status.Ready:
            print("\nQML Ready")
        
        print("="*80)
        print("EXPECTED:")
        print("  Console: 'SphereGeometry created'")
        print("  Console: 'Model created'")
        print("  Console: 'Geometry object: ...'")
        print("  Console: 'Geometry valid: true'")
        print()
        print("  Window: GREEN sphere on RED background")
        print("="*80)

def main():
    app = QApplication(sys.argv)
    window = QuickDiagnostic()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
