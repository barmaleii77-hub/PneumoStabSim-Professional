#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test geometry built with EXACT documentation API
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path


test_qml = """
import QtQuick
import QtQuick3D
import CorrectGeometry 1.0

View3D {
    anchors.fill: parent

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#800080"
    }

    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }

    DirectionalLight {
        brightness: 5.0
    }

    Model {
        geometry: DocumentationBasedTriangle {
            id: docTriangle
        }

        materials: PrincipledMaterial {
            baseColor: "#ffff00"
            lighting: PrincipledMaterial.NoLighting
        }

        Component.onCompleted: {
            console.log("=== DOCUMENTATION TEST ===")
            console.log("Triangle from docs:", docTriangle)
            console.log("Model geometry:", geometry)
            console.log("Model visible:", visible)
            console.log("=========================")
        }
    }
}
"""


def main():
    print("=" * 80)
    print("DOCUMENTATION-BASED GEOMETRY TEST")
    print("=" * 80)
    print("Using EXACT API patterns discovered from documentation study")
    print("Expected: LARGE YELLOW TRIANGLE on PURPLE background")
    print()

    app = QApplication(sys.argv)

    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(600, 400)
    widget.setWindowTitle("Documentation-Based Geometry")

    qml_path = Path("test_documentation_geometry.qml")
    qml_path.write_text(test_qml, encoding="utf-8")

    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))

    if widget.status() == QQuickWidget.Status.Error:
        print("ERRORS:")
        for error in widget.errors():
            print(f"  {error.toString()}")
        return 1

    widget.show()

    print()
    print("=" * 80)
    print("CRITICAL: Do you see LARGE YELLOW TRIANGLE on PURPLE background?")
    print("This uses EXACT API from documentation study!")
    print("=" * 80)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
