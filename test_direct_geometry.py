#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test direct geometry without Property system
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

from src.ui.direct_geometry import DirectTriangle

# Simplest possible QML
test_qml = '''
import QtQuick
import QtQuick3D
import DirectGeometry 1.0

View3D {
    anchors.fill: parent
    
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#ff8000"
    }
    
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 2)
    }
    
    DirectionalLight {
        brightness: 10.0
    }
    
    Model {
        geometry: DirectTriangle {
            id: triangle
        }
        
        materials: PrincipledMaterial {
            baseColor: "#000000"
            lighting: PrincipledMaterial.NoLighting
        }
        
        Component.onCompleted: {
            console.log("DIRECT TEST: Model completed")
            console.log("Triangle geometry:", triangle)
            console.log("Model geometry:", geometry)
        }
    }
}
'''

def main():
    print("="*60)
    print("DIRECT GEOMETRY TEST - NO PROPERTY SYSTEM")
    print("="*60)
    print("Bypassing Property system completely")
    print("Expected: BLACK TRIANGLE on ORANGE background")
    
    app = QApplication(sys.argv)
    
    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(400, 300)
    widget.setWindowTitle("Direct Geometry Test")
    
    qml_path = Path("test_direct_geometry.qml")
    qml_path.write_text(test_qml, encoding='utf-8')
    
    print("Loading direct geometry QML...")
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))
    
    if widget.status() == QQuickWidget.Status.Error:
        print("? ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
        return 1
    
    widget.show()
    
    print()
    print("="*60)
    print("ULTRA CRITICAL: Do you see BLACK TRIANGLE on ORANGE?")
    print("This is the simplest possible custom geometry!")
    print("="*60)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())