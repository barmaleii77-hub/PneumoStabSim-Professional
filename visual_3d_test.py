#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visual 3D Test - Direct test of custom geometry
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QT_LOGGING_RULES"] = "js.debug=true"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# Import geometry
from src.ui.custom_geometry import SphereGeometry

# Simple test QML
test_qml = '''
import QtQuick
import QtQuick3D
import CustomGeometry 1.0

Item {
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#ff0000"
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }
        
        DirectionalLight {
            brightness: 2.0
        }
        
        Model {
            geometry: SphereGeometry { }
            scale: Qt.vector3d(2, 2, 2)
            
            materials: PrincipledMaterial {
                baseColor: "#00ff00"
            }
            
            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
            
            Component.onCompleted: {
                console.log("SPHERE CREATED WITH GEOMETRY:", geometry)
                console.log("SPHERE VISIBLE:", visible)
            }
        }
    }
}
'''

def main():
    print("=== VISUAL 3D TEST ===")
    print("Creating window with rotating GREEN sphere on RED background")
    print()
    
    app = QApplication(sys.argv)
    
    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(800, 600)
    widget.setWindowTitle("VISUAL TEST: Green Sphere on Red Background")
    
    # Write QML to file
    qml_path = Path("visual_test.qml")
    qml_path.write_text(test_qml, encoding='utf-8')
    
    # Load QML
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))
    
    if widget.status() == QQuickWidget.Status.Error:
        print("QML ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
        return 1
    
    print("QML loaded successfully")
    widget.show()
    
    print()
    print("=" * 60)
    print("VISUAL TEST - WHAT DO YOU SEE?")
    print("=" * 60)
    print("Expected:")
    print("  - RED background")
    print("  - GREEN rotating sphere in center")
    print("  - Smooth animation")
    print()
    print("If you see this, custom 3D geometry WORKS!")
    print("Close window when done.")
    print("=" * 60)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())