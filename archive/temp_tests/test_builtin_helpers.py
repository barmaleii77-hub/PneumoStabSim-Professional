#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test with built-in QtQuick3D helpers and standard models
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# Test with QtQuick3D Helpers
test_qml = """
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

View3D {
    anchors.fill: parent

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#000080"
    }

    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 3)
    }

    DirectionalLight {
        brightness: 2.0
    }

    // Try AxisHelper - should show colored axes
    AxisHelper {
        id: axisHelper
    }

    // Try WasdController if available
    Node {
        id: testNode

        Model {
            // Try using a basic mesh file if available
            source: "qrc:/meshes/sphere.mesh"  // This might exist in Qt

            materials: PrincipledMaterial {
                baseColor: "#ff0000"
            }

            Component.onCompleted: {
                console.log("Built-in model test")
                console.log("Source:", source)
            }
        }
    }

    Component.onCompleted: {
        console.log("Built-in helpers test loaded")
        console.log("AxisHelper:", axisHelper)
    }
}
"""


def main():
    print("=" * 60)
    print("TEST: BUILT-IN QTQUICK3D HELPERS")
    print("=" * 60)
    print("Testing standard Qt Quick 3D components")
    print("Expected: Blue background + colored axes helper")

    app = QApplication(sys.argv)

    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(500, 400)
    widget.setWindowTitle("Built-in Helpers Test")

    qml_path = Path("test_builtin_helpers.qml")
    qml_path.write_text(test_qml, encoding="utf-8")

    print("Loading QML with built-in helpers...")
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))

    if widget.status() == QQuickWidget.Status.Error:
        print("? ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")

    widget.show()

    print()
    print("=" * 60)
    print("Do you see COLORED AXES on blue background?")
    print("Red=X, Green=Y, Blue=Z axes should be visible")
    print("=" * 60)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
