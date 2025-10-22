#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test our custom geometry in minimal View3D setup
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

# Import our geometry

# Test QML - minimal setup with our geometry
test_qml = """
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
            position: Qt.vector3d(0, 0, 3)
        }

        DirectionalLight {
            brightness: 10.0
            eulerRotation.x: -45
        }

        Model {
            geometry: SphereGeometry { }

            materials: PrincipledMaterial {
                baseColor: "#ffffff"
                lighting: PrincipledMaterial.NoLighting
            }

            Component.onCompleted: {
                console.log("=== MODEL DEBUG ===")
                console.log("Model created")
                console.log("Geometry:", geometry)
                console.log("Geometry != null:", geometry !== null)
                console.log("Materials:", materials)
                console.log("Visible:", visible)
                console.log("Scale:", scale)
                console.log("Position:", position)
                console.log("=== END DEBUG ===")
            }
        }
    }
}
"""


def main():
    print("=" * 60)
    print("MINIMAL CUSTOM GEOMETRY IN VIEW3D TEST")
    print("=" * 60)
    print("Red background + White sphere (no lighting)")
    print()

    app = QApplication(sys.argv)

    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(600, 400)
    widget.setWindowTitle("Custom Geometry in View3D")

    qml_path = Path("test_custom_in_view3d.qml")
    qml_path.write_text(test_qml, encoding="utf-8")

    print("Loading QML with custom geometry...")
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))

    if widget.status() == QQuickWidget.Status.Error:
        print("? QML ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
        return 1
    elif widget.status() == QQuickWidget.Status.Ready:
        print("? QML loaded successfully")

    widget.show()

    print()
    print("=" * 60)
    print("CRITICAL TEST:")
    print("Do you see a WHITE SPHERE on RED background?")
    print()
    print("Expected console output:")
    print("  - Model created")
    print("  - Geometry: SphereGeometry(...)")
    print("  - Geometry != null: true")
    print("  - Visible: true")
    print("=" * 60)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
