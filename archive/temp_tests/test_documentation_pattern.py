#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test geometry following Qt documentation patterns exactly
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.scenegraph*=false;js.debug=true"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# Import geometry following documentation

# QML following Qt documentation structure
test_qml = """
import QtQuick
import QtQuick3D
import GeometryExample 1.0

Item {
    id: root

    View3D {
        id: view3d
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#404040"
        }

        camera: PerspectiveCamera {
            position: Qt.vector3d(0, 0, 3)
            clipNear: 0.1
            clipFar: 100.0
        }

        DirectionalLight {
            position: Qt.vector3d(0, 10, 10)
            brightness: 1.0
        }

        Model {
            id: triangleModel

            geometry: ExampleTriangleGeometry {
                id: triangleGeometry
            }

            materials: [
                PrincipledMaterial {
                    baseColor: "#ff0000"
                    roughness: 0.1
                    metalness: 0.0
                }
            ]

            Component.onCompleted: {
                console.log("=== DOCUMENTATION TEST ===")
                console.log("Model completed")
                console.log("Geometry:", geometry)
                console.log("Geometry type:", typeof geometry)
                console.log("Materials:", materials)
                console.log("=========================")
            }
        }
    }

    Rectangle {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.margins: 10
        width: 200
        height: 40
        color: "#80000000"
        radius: 5

        Text {
            anchors.centerIn: parent
            text: "Documentation Pattern Test"
            color: "#ffffff"
            font.pixelSize: 12
        }
    }
}
"""


def main():
    print("=" * 70)
    print("QT DOCUMENTATION PATTERN TEST")
    print("=" * 70)
    print("Testing geometry following official Qt patterns")
    print("Expected: RED TRIANGLE on GRAY background")
    print()

    app = QApplication(sys.argv)

    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(600, 400)
    widget.setWindowTitle("Qt Documentation Pattern Test")

    qml_path = Path("test_documentation_pattern.qml")
    qml_path.write_text(test_qml, encoding="utf-8")

    print("Loading QML with documentation pattern...")
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))

    status = widget.status()
    if status == QQuickWidget.Status.Error:
        print("? QML ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
        return 1
    elif status == QQuickWidget.Status.Ready:
        print("? QML loaded successfully")

    widget.show()

    print()
    print("=" * 70)
    print("CRITICAL: Do you see RED TRIANGLE on GRAY background?")
    print("This follows Qt documentation exactly!")
    print("=" * 70)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
