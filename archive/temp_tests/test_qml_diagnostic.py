# -*- coding: utf-8 -*-
"""
Diagnostic app - test if QML renders at all
"""
import sys
import os

# Force D3D backend
os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
os.environ.setdefault("QSG_INFO", "1")

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtQuick import QQuickView
from PySide6.QtCore import QUrl
from pathlib import Path

print("=== QML DIAGNOSTIC TEST ===\n")

app = QApplication(sys.argv)

# Create window
window = QMainWindow()
window.setWindowTitle("QML Diagnostic - Should see RED background")
window.resize(800, 600)

# Create QQuickView
view = QQuickView()
view.setResizeMode(QQuickView.SizeRootObjectToView)

# Load diagnostic QML
qml_file = Path("assets/qml/diagnostic.qml")
if not qml_file.exists():
    print(f"ERROR: QML file not found: {qml_file.absolute()}")
    sys.exit(1)

qml_url = QUrl.fromLocalFile(str(qml_file.absolute()))
print(f"Loading: {qml_url.toString()}\n")

view.setSource(qml_url)

# Check for errors
if view.status() == QQuickView.Status.Error:
    print("ERROR: QML ERRORS:")
    for error in view.errors():
        print(f"   {error}")
    sys.exit(1)

print("OK: QML loaded successfully\n")

# Get root object
root = view.rootObject()
if not root:
    print("ERROR: No root object!")
    sys.exit(1)

print("OK: Root object exists\n")

# Embed in window
container = QWidget.createWindowContainer(view, window)
container.setMinimumSize(800, 600)
window.setCentralWidget(container)

print("=" * 60)
print("WINDOW SHOULD SHOW:")
print("  - Bright RED background")
print("  - White text in center")
print("  - Green rotating square")
print("=" * 60)
print("\nIf you DON'T see it - Qt Quick rendering broken")
print("If you SEE it - QML works, problem is Qt Quick 3D\n")

window.show()
window.raise_()
window.activateWindow()

print("OK: Window shown\n")
print("Close window to exit...\n")

sys.exit(app.exec())
