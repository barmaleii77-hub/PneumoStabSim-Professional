#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test with stable geometry and proper lifetime management
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

from src.ui.stable_geometry import StableTriangleGeometry, GeometryProvider

# QML with stable geometry
test_qml = '''
import QtQuick
import QtQuick3D
import StableGeometry 1.0

View3D {
    id: view3d
    anchors.fill: parent
    
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#800080"
    }
    
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 0, 6)
        clipNear: 0.1
        clipFar: 100.0
    }
    
    DirectionalLight {
        eulerRotation.x: -30
        brightness: 5.0
    }
    
    GeometryProvider {
        id: provider
    }
    
    Model {
        id: triangleModel
        
        geometry: provider.geometry
        
        materials: PrincipledMaterial {
            baseColor: "#ffff00"
            lighting: PrincipledMaterial.NoLighting
        }
        
        Component.onCompleted: {
            console.log("=== STABLE GEOMETRY TEST ===")
            console.log("Provider:", provider)
            console.log("Geometry from provider:", provider.geometry)
            console.log("Model geometry:", geometry)
            console.log("Model visible:", visible)
            console.log("Model position:", position)
            console.log("Model scale:", scale)
            console.log("Camera position:", camera.position)
            console.log("===========================")
        }
    }
}
'''

def main():
    print("="*70)
    print("STABLE GEOMETRY TEST - PROPER LIFETIME MANAGEMENT")
    print("="*70)
    print("Testing geometry with guaranteed lifetime")
    print("Expected: LARGE YELLOW TRIANGLE on PURPLE background")
    print()
    
    app = QApplication(sys.argv)
    
    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(600, 400)
    widget.setWindowTitle("Stable Geometry Test")
    
    qml_path = Path("test_stable_geometry.qml")
    qml_path.write_text(test_qml, encoding='utf-8')
    
    print("Loading QML with stable geometry...")
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))
    
    if widget.status() == QQuickWidget.Status.Error:
        print("? ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
        return 1
    
    widget.show()
    
    print()
    print("="*70)
    print("CRITICAL: Do you see LARGE YELLOW TRIANGLE on PURPLE background?")
    print("Triangle should be 4x4 units (very large)")
    print("="*70)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())