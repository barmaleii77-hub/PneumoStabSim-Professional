#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST: Custom 3D Geometry - Procedural Sphere
"""
import sys
import os
from pathlib import Path

# Set backend
os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl

# Import custom geometry


class CustomGeometryTestWindow(QWidget):
    """Test window for custom 3D geometry"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Qt Quick 3D - Custom Geometry Test")
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Info label
        info = QLabel(
            "<b>Custom 3D Geometry Test</b><br>" "Using procedural sphere from Python"
        )
        info.setStyleSheet(
            "background: #000; color: #0f0; padding: 10px; font-size: 12pt;"
        )
        layout.addWidget(info)

        # QML widget
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        # Load QML
        qml_path = Path("assets/qml/main_custom_geometry_v2.qml")
        if not qml_path.exists():
            print(f"ERROR: {qml_path} not found!")
            return

        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))

        print("=" * 80)
        print("LOADING CUSTOM GEOMETRY QML")
        print("=" * 80)
        print(f"QML file: {qml_path.absolute()}")
        print()

        self.qml_widget.setSource(qml_url)

        layout.addWidget(self.qml_widget, 1)

        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            "background: #000; color: #0f0; padding: 5px; font-family: monospace;"
        )
        layout.addWidget(self.status_label)

        # Check status
        status = self.qml_widget.status()
        if status == QQuickWidget.Status.Error:
            errors = "\n".join([e.toString() for e in self.qml_widget.errors()])
            self.status_label.setText(f"ERROR: {errors}")
            print(f"\nERROR:\n{errors}\n")
        elif status == QQuickWidget.Status.Ready:
            self.status_label.setText("QML Ready | Check for rotating sphere!")
            print("\nSUCCESS: QML loaded")
            print("Expected: Rotating RED sphere with custom geometry")
            print()

        print("=" * 80)


def main():
    print("=" * 80)
    print("CUSTOM 3D GEOMETRY TEST")
    print("=" * 80)
    print()
    print("This test uses QQuick3DGeometry from Python")
    print("to create a procedural sphere")
    print()
    print("Expected:")
    print("  - Dark blue background")
    print("  - RED rotating sphere (procedurally generated)")
    print("  - Smooth animation")
    print()
    print("=" * 80)
    print()

    app = QApplication(sys.argv)

    # Register custom QML types
    print("Registering custom QML types...")
    # Types are auto-registered with @QmlElement decorator
    print("  CustomGeometry.SphereGeometry")
    print("  CustomGeometry.CubeGeometry")
    print()

    window = CustomGeometryTestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
