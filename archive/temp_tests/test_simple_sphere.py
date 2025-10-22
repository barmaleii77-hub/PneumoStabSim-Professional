# -*- coding: utf-8 -*-
"""
Test Qt Quick 3D - simple sphere
Without MainWindow, panels, SimulationManager
Just window + QML + sphere
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl

# Simple QML code
SIMPLE_QML = """
import QtQuick
import QtQuick3D

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
        eulerRotation.x: -30
        brightness: 1.0
    }

    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        scale: Qt.vector3d(1.5, 1.5, 1.5)

        materials: PrincipledMaterial {
            baseColor: "#ff4444"
            metalness: 0.0
            roughness: 0.5
        }

        NumberAnimation on eulerRotation.y {
            from: 0
            to: 360
            duration: 3000
            loops: Animation.Infinite
        }
    }

    Text {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -200
        text: "RED ROTATING SPHERE"
        color: "#ffffff"
        font.pixelSize: 24
        font.bold: true
        style: Text.Outline
        styleColor: "#000000"
    }
}
"""


class SimpleTestWindow(QWidget):
    """Simple window with Qt Quick 3D"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Qt Quick 3D - Sphere Test")
        self.resize(800, 600)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # QQuickWidget
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        # Save QML to temp file
        qml_path = Path("test_sphere_temp.qml")
        qml_path.write_text(SIMPLE_QML, encoding="utf-8")

        # Load QML
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)

        # Check errors
        if self.qml_widget.status() == QQuickWidget.Status.Error:
            print("ERROR: QML ERRORS:")
            for error in self.qml_widget.errors():
                print(f"   {error.toString()}")
        else:
            print("SUCCESS: QML loaded")
            print(f"   Status: {self.qml_widget.status()}")
            print(f"   Root object: {self.qml_widget.rootObject()}")

        layout.addWidget(self.qml_widget)

        print("\n" + "=" * 60)
        print("SIMPLE Qt Quick 3D TEST")
        print("=" * 60)
        print("Expected:")
        print("  - Dark blue background (#1a1a2e)")
        print("  - Red rotating sphere in center")
        print("  - White text on top")
        print("\nIf not visible:")
        print("  1. Check console for QML errors")
        print("  2. Check Qt Quick 3D is installed")
        print("  3. Check RHI backend = D3D11")
        print("=" * 60 + "\n")


def main():
    # Set RHI backend BEFORE QApplication
    import os

    os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
    os.environ.setdefault("QSG_INFO", "1")

    app = QApplication(sys.argv)

    print("Creating window...")
    window = SimpleTestWindow()

    print("Showing window...")
    window.show()

    print("Starting event loop...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
