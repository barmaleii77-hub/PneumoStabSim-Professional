#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test simple sphere without indices
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QT_LOGGING_RULES"] = "js.debug=true"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# Import simple geometry

test_qml = """
import QtQuick
import QtQuick3D
import SimpleGeometry 1.0

Item {
    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#ff0000"
        }

        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 3)
        }

        DirectionalLight {
            brightness: 3.0
        }

        Model {
            geometry: SimpleSphere { }

            materials: PrincipledMaterial {
                baseColor: "#00ff00"
                lighting: PrincipledMaterial.NoLighting
            }

            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }

            Component.onCompleted: {
                console.log("SimpleSphere Model created")
                console.log("Geometry:", geometry)
            }
        }
    }
}
"""


def main():
    print("=== TESTING SIMPLE SPHERE (NO INDICES) ===")

    app = QApplication(sys.argv)

    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(800, 600)
    widget.setWindowTitle("Simple Sphere Test")

    qml_path = Path("test_simple_sphere_v2.qml")
    qml_path.write_text(test_qml, encoding="utf-8")

    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))

    if widget.status() == QQuickWidget.Status.Error:
        print("ERRORS:")
        for error in widget.errors():
            print(f"  {error.toString()}")
        return 1

    print("Simple sphere test launched")
    print("Expected: GREEN sphere on RED background")
    print("This version uses direct triangles (no indices)")

    widget.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
