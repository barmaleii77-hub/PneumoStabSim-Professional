#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test ultra simple triangle - if this doesn't show, problem is fundamental
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"
os.environ["QT_LOGGING_RULES"] = "js.debug=true"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

from src.ui.triangle_geometry import SimpleTriangle

test_qml = '''
import QtQuick
import QtQuick3D
import TestGeometry 1.0

Item {
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#0000ff"
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 3)
        }
        
        DirectionalLight {
            brightness: 5.0
        }
        
        Model {
            geometry: SimpleTriangle { }
            
            materials: PrincipledMaterial {
                baseColor: "#ffff00"
                lighting: PrincipledMaterial.NoLighting
            }
            
            Component.onCompleted: {
                console.log("TRIANGLE TEST")
                console.log("Geometry:", geometry)
            }
        }
    }
}
'''

def main():
    print("="*60)
    print("ULTIMATE TEST: SINGLE TRIANGLE")
    print("="*60)
    print("BLUE background + YELLOW triangle")
    print("If this doesn't work - fundamental problem!")
    print()
    
    app = QApplication(sys.argv)
    
    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(400, 300)
    widget.setWindowTitle("Ultimate Triangle Test")
    
    qml_path = Path("test_triangle.qml")
    qml_path.write_text(test_qml, encoding='utf-8')
    
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))
    
    if widget.status() == QQuickWidget.Status.Error:
        print("ERRORS:")
        for error in widget.errors():
            print(f"  {error.toString()}")
    
    widget.show()
    
    print("="*60)
    print("EXPECT: YELLOW TRIANGLE on BLUE background")
    print("="*60)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())