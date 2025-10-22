#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test interactive 3D pneumatic suspension frame
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
    print("INTERACTIVE 3D PNEUMATIC SUSPENSION FRAME")
    print("=" * 80)
    print("Features:")
    print("  - Real coordinates from kinematics system")
    print("  - Frame: 2500x1800mm (wheelbase x track)")
    print("  - Arms: 400mm, Pivot offset: 300mm")
    print("  - 4 animated suspension corners")
    print("  - Unlimited mouse interaction:")
    print("    * Rotate: Mouse drag")
    print("    * Pan: Shift+Mouse or Right mouse")
    print("    * Zoom: Mouse wheel (no restrictions!)")
    print("    * Reset: R key")
    print()

    app = QApplication(sys.argv)

    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(1200, 800)
    widget.setWindowTitle("Interactive 3D Pneumatic Suspension Frame")

    qml_path = Path("assets/qml/main_interactive_frame.qml")

    print(f"Loading: {qml_path}")
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))

    if widget.status() == QQuickWidget.Status.Error:
        print("ERRORS:")
        for error in widget.errors():
            print(f"   {error.toString()}")
        return 1
    elif widget.status() == QQuickWidget.Status.Ready:
        print("Interactive frame loaded successfully")

    widget.show()

    print()
    print("=" * 80)
    print("CONTROLS:")
    print("  Mouse:       Rotate camera (unlimited angles!)")
    print("  Shift+Mouse: Pan camera")
    print("  Right Mouse: Pan camera")
    print("  Mouse Wheel: Zoom (unlimited scale!)")
    print("  R Key:       Reset camera position")
    print()
    print("EXPECTED: 3D frame with 4 animated suspension corners")
    print("   - Gray frame structure")
    print("   - Colored pivot points (Red/Green/Blue/Yellow)")
    print("   - Animated lever arms")
    print("   - Orange pneumatic cylinders")
    print("   - Black wheels")
    print("   - XYZ coordinate axes")
    print("=" * 80)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
