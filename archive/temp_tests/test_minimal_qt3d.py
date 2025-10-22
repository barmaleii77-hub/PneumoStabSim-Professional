#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Minimal QtQuick3D test - just View3D
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.rhi*=true;qt.scenegraph*=true"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# MINIMAL QtQuick3D - just View3D with environment
test_qml = """
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent

    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#00ff00"
        }

        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 1)
        }

        Component.onCompleted: {
            console.log("View3D loaded")
        }
    }

    Text {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 10
        text: "QtQuick3D Minimal Test"
        color: "#ffffff"
        font.pixelSize: 16
    }
}
"""


def main():
    print("=" * 60)
    print("MINIMAL QTQUICK3D TEST")
    print("=" * 60)
    print("Testing just View3D with green background")
    print()

    app = QApplication(sys.argv)

    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(600, 400)
    widget.setWindowTitle("Minimal QtQuick3D Test")

    qml_path = Path("minimal_qt3d_test.qml")
    qml_path.write_text(test_qml, encoding="utf-8")

    print("Loading minimal QtQuick3D QML...")
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))

    if widget.status() == QQuickWidget.Status.Error:
        print("? QML ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
        return 1
    elif widget.status() == QQuickWidget.Status.Ready:
        print("? QML loaded successfully")

    print("Showing widget...")
    widget.show()

    print()
    print("=" * 60)
    print("EXPECT: GREEN background (View3D working)")
    print("If you see GREEN - View3D works!")
    print("If you see WHITE - View3D failed")
    print("=" * 60)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
