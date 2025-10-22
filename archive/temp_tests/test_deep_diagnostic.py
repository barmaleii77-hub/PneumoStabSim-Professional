#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DEEP DIAGNOSTIC - Test with maximum Qt Quick 3D logging
"""
import sys
import os

# MAXIMUM LOGGING
os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"
os.environ["QSG_RHI_DEBUG_LAYER"] = "1"
os.environ["QT_LOGGING_RULES"] = (
    "qt.scenegraph*=true;"
    "qt.rhi*=true;"
    "qt.quick3d*=true;"
    "qt.quick.3d*=true;"
    "qt.qml*=true"
)
os.environ["QT_QPA_VERBOSE"] = "1"

from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl

# Simplest possible 3D QML
DIAGNOSTIC_QML = """
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent

    Rectangle {
        anchors.fill: parent
        color: "#ff0000"

        Text {
            anchors.centerIn: parent
            text: "RED BACKGROUND\\nShould see sphere below"
            color: "#ffffff"
            font.pixelSize: 24
            horizontalAlignment: Text.AlignHCenter
        }
    }

    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
            clearColor: "#00000000"
        }

        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }

        DirectionalLight {
            brightness: 2.0
        }

        Model {
            id: testSphere
            source: "#Sphere"
            scale: Qt.vector3d(2, 2, 2)

            materials: PrincipledMaterial {
                baseColor: "#00ff00"
            }

            Component.onCompleted: {
                console.log("Model onCompleted - source:", source)
                console.log("Model onCompleted - geometry:", geometry)
            }

            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
        }
    }
}
"""


class DiagnosticWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DEEP DIAGNOSTIC - Qt Quick 3D")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        info = QLabel("DIAGNOSTIC: Check console for Qt Quick 3D messages")
        info.setStyleSheet(
            "background: #000; color: #0f0; padding: 10px; font-size: 14pt;"
        )
        layout.addWidget(info)

        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        qml_path = Path("deep_diagnostic.qml")
        qml_path.write_text(DIAGNOSTIC_QML, encoding="utf-8")
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))

        print("\n" + "=" * 80)
        print("LOADING QML...")
        print("=" * 80)

        self.qml_widget.setSource(qml_url)

        layout.addWidget(self.qml_widget, 1)

        status = self.qml_widget.status()
        if status == QQuickWidget.Status.Error:
            errors = "\n".join([e.toString() for e in self.qml_widget.errors()])
            print(f"\n? QML ERRORS:\n{errors}\n")
        elif status == QQuickWidget.Status.Ready:
            print("\n? QML Ready\n")
            print("Check window: Should see GREEN sphere on RED background")

        print("=" * 80)
        print("LOOK FOR THESE MESSAGES IN CONSOLE:")
        print("  - 'Model onCompleted'")
        print("  - 'source: #Sphere'")
        print("  - 'geometry: ...'")
        print("  - Qt Quick 3D loading messages")
        print("=" * 80 + "\n")


def main():
    print("=" * 80)
    print("DEEP DIAGNOSTIC TEST - Qt Quick 3D")
    print("=" * 80)
    print("This test will show MAXIMUM logging from Qt Quick 3D")
    print("Watch console for clues about why 3D doesn't render")
    print("=" * 80 + "\n")

    app = QApplication(sys.argv)
    window = DiagnosticWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
