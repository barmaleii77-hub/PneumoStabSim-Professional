# -*- coding: utf-8 -*-
"""
Visual diagnostic test - check what is actually rendered
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, QTimer

# Test with visual feedback IN the QML
VISUAL_TEST_QML = """
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent

    // Background indicator (should always be visible)
    Rectangle {
        anchors.fill: parent
        color: "#1a1a2e"

        // Visual test pattern
        Column {
            anchors.centerIn: parent
            spacing: 20

            Text {
                text: "2D QML IS WORKING"
                color: "#00ff00"
                font.pixelSize: 32
                font.bold: true
            }

            Rectangle {
                width: 200
                height: 200
                color: "#ff00ff"
                radius: 100

                Text {
                    anchors.centerIn: parent
                    text: "2D CIRCLE"
                    color: "#ffffff"
                    font.pixelSize: 16
                }
            }

            Text {
                text: "If you see this, 2D QML works!"
                color: "#ffff00"
                font.pixelSize: 16
            }
        }
    }

    // 3D View (will it render on top?)
    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
            antialiasingMode: SceneEnvironment.MSAA
        }

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 5)
        }

        DirectionalLight {
            eulerRotation.x: -30
            brightness: 2.0
        }

        // Red sphere
        Model {
            source: "#Sphere"
            position: Qt.vector3d(-1.5, 1, 0)
            scale: Qt.vector3d(0.8, 0.8, 0.8)
            materials: PrincipledMaterial {
                baseColor: "#ff0000"
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

        // Green cube
        Model {
            source: "#Cube"
            position: Qt.vector3d(1.5, 1, 0)
            scale: Qt.vector3d(0.6, 0.6, 0.6)
            materials: PrincipledMaterial {
                baseColor: "#00ff00"
                metalness: 0.0
                roughness: 0.5
            }

            NumberAnimation on eulerRotation.x {
                from: 0
                to: 360
                duration: 4000
                loops: Animation.Infinite
            }
        }

        // Blue cylinder
        Model {
            source: "#Cylinder"
            position: Qt.vector3d(0, -1, 0)
            scale: Qt.vector3d(0.5, 1.0, 0.5)
            materials: PrincipledMaterial {
                baseColor: "#0000ff"
                metalness: 0.0
                roughness: 0.5
            }

            NumberAnimation on eulerRotation.z {
                from: 0
                to: 360
                duration: 5000
                loops: Animation.Infinite
            }
        }
    }

    // Overlay info (should be on top)
    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 20
        width: 300
        height: 150
        color: "#80000000"
        border.color: "#ffffff"
        border.width: 2
        radius: 5

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5

            Text {
                text: "3D Test Status"
                color: "#ffffff"
                font.pixelSize: 16
                font.bold: true
            }

            Text {
                text: "Expected:"
                color: "#aaaaaa"
                font.pixelSize: 12
            }

            Text {
                text: "- Red sphere (rotating)"
                color: "#ff4444"
                font.pixelSize: 11
            }

            Text {
                text: "- Green cube (rotating)"
                color: "#44ff44"
                font.pixelSize: 11
            }

            Text {
                text: "- Blue cylinder (rotating)"
                color: "#4444ff"
                font.pixelSize: 11
            }

            Text {
                text: "If you see only 2D -> 3D broken"
                color: "#ffaa00"
                font.pixelSize: 10
                font.italic: true
            }
        }
    }
}
"""


class VisualTestWindow(QWidget):
    """Visual test window"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Qt Quick 3D - Visual Test")
        self.resize(900, 700)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Info label
        info = QLabel("Visual Test: Check what you actually SEE")
        info.setStyleSheet(
            """
            QLabel {
                background-color: #333;
                color: #fff;
                padding: 10px;
                font-size: 14pt;
                font-weight: bold;
            }
        """
        )
        layout.addWidget(info)

        # QML widget
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        # Save and load QML
        qml_path = Path("visual_test_temp.qml")
        qml_path.write_text(VISUAL_TEST_QML, encoding="utf-8")
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)

        layout.addWidget(self.qml_widget)

        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            """
            QLabel {
                background-color: #222;
                color: #0f0;
                padding: 10px;
                font-family: monospace;
            }
        """
        )
        layout.addWidget(self.status_label)

        # Check status
        status = self.qml_widget.status()
        if status == QQuickWidget.Status.Error:
            errors = "\n".join([e.toString() for e in self.qml_widget.errors()])
            self.status_label.setText(f"ERROR:\n{errors}")
            print(f"\nERROR: QML failed to load\n{errors}")
        elif status == QQuickWidget.Status.Ready:
            self.status_label.setText("QML Status: Ready\nRoot Object: OK")
            print("\nSUCCESS: QML loaded")
            print(f"Root object: {self.qml_widget.rootObject()}")

            # Start diagnostic timer
            self.diagnostic_timer = QTimer(self)
            self.diagnostic_timer.timeout.connect(self.update_diagnostics)
            self.diagnostic_timer.start(1000)  # Every second
        else:
            self.status_label.setText(f"Status: {status}")

        print("\n" + "=" * 70)
        print("VISUAL TEST - WHAT TO EXPECT:")
        print("=" * 70)
        print("Scenario A: 3D WORKS")
        print("  - You see: Rotating red sphere, green cube, blue cylinder")
        print("  - Background: Dark blue")
        print("  - 2D text is BEHIND 3D objects")
        print()
        print("Scenario B: 3D BROKEN")
        print("  - You see: Only 2D text '2D QML IS WORKING'")
        print("  - You see: Magenta circle with '2D CIRCLE'")
        print("  - Background: Dark blue")
        print("  - NO 3D objects visible")
        print()
        print("Scenario C: BOTH BROKEN")
        print("  - You see: Nothing or blank screen")
        print("=" * 70 + "\n")

    def update_diagnostics(self):
        """Update diagnostic info"""
        root = self.qml_widget.rootObject()
        if root:
            size = self.qml_widget.size()
            self.status_label.setText(
                f"QML Status: Ready | Root: OK | Size: {size.width()}x{size.height()}\n"
                f"Check window: See 2D text? See 3D shapes?"
            )


def main():
    import os

    os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
    os.environ.setdefault("QSG_INFO", "1")

    # Try to enable debug output
    os.environ.setdefault("QSG_RHI_DEBUG_LAYER", "1")
    os.environ.setdefault("QT_LOGGING_RULES", "qt.scenegraph*=true;qt.rhi*=true")

    app = QApplication(sys.argv)

    window = VisualTestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
