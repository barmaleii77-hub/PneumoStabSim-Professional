#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Qt Quick 3D with BUILT-IN primitives
Based on working solution from barmaleii77-hub directory
"""
import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path


def main():
    print("=" * 80)
    print("TESTING BUILT-IN QT QUICK 3D PRIMITIVES")
    print("=" * 80)
    print("Using working solution pattern from barmaleii77-hub directory")
    print("Expected: RED ROTATING SPHERE (built-in primitive)")
    print()

    app = QApplication(sys.argv)

    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(800, 600)
    widget.setWindowTitle("Built-in Qt Quick 3D Primitives")

    # Use the working QML
    qml_path = Path("assets/qml/main_working_builtin.qml")

    print(f"Loading working QML: {qml_path}")
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))

    if widget.status() == QQuickWidget.Status.Error:
        print("? ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
        return 1
    elif widget.status() == QQuickWidget.Status.Ready:
        print("? QML loaded successfully")

    widget.show()

    print()
    print("=" * 80)
    print("CRITICAL TEST: Do you see RED ROTATING SPHERE?")
    print('This uses source: "#Sphere" (built-in primitive)')
    print("=" * 80)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
