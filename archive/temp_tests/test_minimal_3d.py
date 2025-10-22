# -*- coding: utf-8 -*-
"""Minimal Qt Quick 3D test - View3D with one sphere only"""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl

# Minimal QML - only 3D, no 2D elements
MINIMAL_3D_QML = """
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#ff0000"
        antialiasingMode: SceneEnvironment.MSAA
    }

    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }

    DirectionalLight {
        eulerRotation.x: -30
        brightness: 2.0
    }

    Model {
        source: "#Sphere"
        scale: Qt.vector3d(2, 2, 2)

        materials: PrincipledMaterial {
            baseColor: "#00ff00"
            metalness: 0.0
            roughness: 0.5
        }

        NumberAnimation on eulerRotation.y {
            from: 0
            to: 360
            duration: 5000
            loops: Animation.Infinite
            running: true
        }
    }
}
"""


class MinimalTestWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MINIMAL 3D TEST")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        info = QLabel("MINIMAL TEST: View3D + Sphere")
        info.setStyleSheet(
            "background-color: #000; color: #0f0; padding: 5px; font-size: 12pt; font-weight: bold;"
        )
        layout.addWidget(info)

        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        qml_path = Path("minimal_3d_temp.qml")
        qml_path.write_text(MINIMAL_3D_QML, encoding="utf-8")
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)

        layout.addWidget(self.qml_widget)

        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            "background-color: #000; color: #0f0; padding: 5px; font-family: monospace;"
        )
        layout.addWidget(self.status_label)

        status = self.qml_widget.status()
        if status == QQuickWidget.Status.Error:
            errors = "\n".join([e.toString() for e in self.qml_widget.errors()])
            self.status_label.setText(f"ERROR: {errors}")
            print(f"\nQML ERROR:\n{errors}\n")
        elif status == QQuickWidget.Status.Ready:
            self.status_label.setText("QML Ready | Check window!")
            print("\nQML loaded successfully\n")

        print("=" * 70)
        print("MINIMAL 3D TEST - WHAT TO EXPECT:")
        print("=" * 70)
        print("Option 1: RED background + GREEN rotating sphere = 3D WORKS!")
        print("Option 2: RED background only (no sphere) = Primitives issue")
        print("Option 3: Black/gray screen = View3D not initializing")
        print("=" * 70)


def main():
    os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
    os.environ.setdefault("QSG_INFO", "1")

    app = QApplication(sys.argv)
    window = MinimalTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
