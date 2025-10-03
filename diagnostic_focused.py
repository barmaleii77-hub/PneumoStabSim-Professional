#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Focused diagnostic - why sphere is not visible
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QT_LOGGING_RULES"] = "js.debug=true"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, qInstallMessageHandler, QtMsgType
from pathlib import Path

# Import geometry
from src.ui.custom_geometry import SphereGeometry

def message_handler(mode, context, message):
    print(f"QT: {message}")

# Test QML - exactly same as main.qml but simpler
test_qml = '''
import QtQuick
import QtQuick3D
import CustomGeometry 1.0

Item {
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#1a1a2e"
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }
        
        DirectionalLight {
            brightness: 2.0
        }
        
        Model {
            geometry: SphereGeometry { }
            
            materials: PrincipledMaterial {
                baseColor: "#ff4444"
            }
            
            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
            
            Component.onCompleted: {
                console.log("=== MODEL DIAGNOSTIC ===")
                console.log("geometry:", geometry)
                console.log("geometry !== null:", geometry !== null)
                console.log("visible:", visible)
                console.log("opacity:", opacity)
                console.log("position:", position)
                console.log("scale:", scale)
                console.log("materials:", materials)
                console.log("=== END DIAGNOSTIC ===")
            }
        }
    }
}
'''

def main():
    print("=== FOCUSED DIAGNOSTIC ===")
    print("Testing exact same setup as main app but simpler")
    print()
    
    app = QApplication(sys.argv)
    qInstallMessageHandler(message_handler)
    
    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(800, 600)
    widget.setWindowTitle("DIAGNOSTIC: Why sphere not visible?")
    
    qml_path = Path("diagnostic_focused.qml")
    qml_path.write_text(test_qml, encoding='utf-8')
    
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))
    
    if widget.status() == QQuickWidget.Status.Error:
        print("QML ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
        return 1
    
    print("QML loaded - showing window")
    widget.show()
    
    print("Look for MODEL DIAGNOSTIC messages in output above...")
    print("Close window when done.")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())