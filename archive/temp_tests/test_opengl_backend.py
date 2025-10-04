#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST: Qt Quick 3D with OPENGL backend (instead of D3D11)
"""
import sys
import os
from pathlib import Path

# TRY OPENGL INSTEAD OF D3D11
os.environ["QSG_RHI_BACKEND"] = "opengl"  # ? KEY CHANGE!
os.environ["QSG_INFO"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.quick3d*=true"

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl

# Try original QML with #Sphere primitive
ORIGINAL_QML = """
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent
    
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#ff0000"  // RED to verify View3D works
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }
        
        DirectionalLight {
            brightness: 2.0
        }
        
        // Try primitive with OpenGL backend
        Model {
            source: "#Sphere"
            scale: Qt.vector3d(2, 2, 2)
            
            materials: PrincipledMaterial {
                baseColor: "#00ff00"  // GREEN
            }
            
            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
            
            Component.onCompleted: {
                console.log("Model created with source:", source)
                console.log("Geometry:", geometry)
            }
        }
    }
    
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 10
        width: 250
        height: 60
        color: "#80000000"
        border.color: "#ffffff"
        
        Column {
            anchors.centerIn: parent
            spacing: 5
            
            Text {
                text: "OpenGL Backend Test"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true
            }
            
            Text {
                text: "Testing #Sphere with OpenGL"
                color: "#aaaaaa"
                font.pixelSize: 10
            }
        }
    }
}
"""


class OpenGLTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Qt Quick 3D - OpenGL Backend Test")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        info = QLabel("<b>OpenGL Backend Test</b><br>"
                     "Using QSG_RHI_BACKEND=opengl instead of d3d11")
        info.setStyleSheet("background: #000; color: #ff0; padding: 10px; font-size: 12pt;")
        layout.addWidget(info)
        
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        
        qml_path = Path("test_opengl_backend.qml")
        qml_path.write_text(ORIGINAL_QML, encoding='utf-8')
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        
        print("="*80)
        print("TESTING #Sphere WITH OPENGL BACKEND")
        print("="*80)
        print("Backend: OpenGL (not D3D11)")
        print("Expected: RED background + GREEN sphere")
        print("="*80)
        print()
        
        self.qml_widget.setSource(qml_url)
        
        layout.addWidget(self.qml_widget, 1)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("background: #000; color: #0f0; padding: 5px; font-family: monospace;")
        layout.addWidget(self.status_label)
        
        status = self.qml_widget.status()
        if status == QQuickWidget.Status.Error:
            errors = "\n".join([e.toString() for e in self.qml_widget.errors()])
            self.status_label.setText(f"ERROR: {errors}")
            print(f"\nERROR:\n{errors}\n")
        elif status == QQuickWidget.Status.Ready:
            self.status_label.setText("QML Ready | Check for GREEN sphere on RED background")
            print("\nQML Ready")
        
        print("="*80)
        print("WHAT TO EXPECT:")
        print("  If OpenGL works with primitives:")
        print("    - RED background")
        print("    - GREEN rotating sphere")
        print("  If not:")
        print("    - RED background only (no sphere)")
        print("="*80)


def main():
    app = QApplication(sys.argv)
    window = OpenGLTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
