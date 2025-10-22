#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test RHI and D3D11 support
"""
import sys
import os

# Set D3D11 backend
os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# Minimal QML to test RHI
test_qml = """
import QtQuick

Rectangle {
    width: 400
    height: 300
    color: "#ff0000"

    Text {
        anchors.centerIn: parent
        text: "RHI D3D11 Test"
        color: "#ffffff"
        font.pixelSize: 24
    }

    Component.onCompleted: {
        console.log("QML Component loaded successfully")
    }
}
"""


def main():
    print("=" * 60)
    print("RHI D3D11 TEST")
    print("=" * 60)
    print("Testing basic Qt Quick rendering with D3D11 backend")
    print()

    app = QApplication(sys.argv)

    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.resize(400, 300)
    widget.setWindowTitle("RHI D3D11 Test")

    # Write QML
    qml_path = Path("rhi_test.qml")
    qml_path.write_text(test_qml, encoding="utf-8")

    print("Loading QML...")
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
    print("EXPECT: Red window with white text 'RHI D3D11 Test'")
    print("Look for 'rhi: backend:' messages in console")
    print("Close window to continue")
    print("=" * 60)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
