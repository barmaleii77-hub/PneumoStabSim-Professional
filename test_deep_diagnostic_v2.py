#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deep diagnostic - check every aspect of custom geometry rendering
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.quick3d*=true;qt.scenegraph*=true;qt.rhi*=true"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, qInstallMessageHandler, QtMsgType
from pathlib import Path

from src.ui.example_geometry import ExampleTriangleGeometry

def debug_message_handler(mode, context, message):
    """Capture all Qt debug messages"""
    if any(keyword in message.lower() for keyword in [
        'geometry', 'triangle', 'vertex', 'buffer', 'render', 'draw', 'primitive'
    ]):
        print(f"?? DEBUG: {message}")

# Minimal test QML
test_qml = '''
import QtQuick
import QtQuick3D
import GeometryExample 1.0

View3D {
    id: view3d
    anchors.fill: parent
    
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#008000"
    }
    
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 2)
    }
    
    DirectionalLight {
        brightness: 10.0
    }
    
    Model {
        geometry: ExampleTriangleGeometry { }
        
        materials: PrincipledMaterial {
            baseColor: "#ffffff"
            lighting: PrincipledMaterial.NoLighting
        }
        
        Component.onCompleted: {
            console.log("?? DEEP DIAGNOSTIC")
            console.log("Model position:", position)
            console.log("Model scale:", scale)
            console.log("Model visible:", visible)
            console.log("Model opacity:", opacity)
            console.log("Model eulerRotation:", eulerRotation)
            console.log("Geometry bounds:", geometry ? "present" : "null")
            console.log("Materials count:", materials.length)
        }
    }
}
'''

def main():
    print("="*80)
    print("DEEP DIAGNOSTIC: EVERY ASPECT OF CUSTOM GEOMETRY")
    print("="*80)
    
    app = QApplication(sys.argv)
    qInstallMessageHandler(debug_message_handler)
    
    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(400, 300)
    widget.setWindowTitle("Deep Diagnostic")
    
    qml_path = Path("deep_diagnostic_v2.qml")
    qml_path.write_text(test_qml, encoding='utf-8')
    
    print("Loading minimal diagnostic QML...")
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))
    
    if widget.status() == QQuickWidget.Status.Error:
        print("? ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
    
    widget.show()
    
    print()
    print("="*80)
    print("EXPECTED: WHITE TRIANGLE on GREEN background")
    print("Look for DEBUG messages about geometry/rendering")
    print("="*80)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())