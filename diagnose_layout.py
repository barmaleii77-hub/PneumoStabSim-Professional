# -*- coding: utf-8 -*-
"""
Diagnostic: Check widget layout and visibility
Traces the "white strip" problem in Canvas
"""
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path
import sys

app = QApplication(sys.argv)

# Create minimal window
window = QMainWindow()
window.setWindowTitle("Layout Diagnostic")
window.resize(1500, 950)

# Create QQuickWidget
qquick = QQuickWidget(window)
qquick.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

qml_path = Path("assets/qml/main.qml").absolute()
qquick.setSource(QUrl.fromLocalFile(str(qml_path)))

# Set as central widget
window.setCentralWidget(qquick)

# Print diagnostics
print("="*60)
print("LAYOUT DIAGNOSTIC")
print("="*60)
print(f"Window size: {window.size().width()}x{window.size().height()}")
print(f"Central widget: {window.centralWidget()}")
print(f"Central widget size: {window.centralWidget().size().width()}x{window.centralWidget().size().height()}")
print(f"QQuickWidget size: {qquick.size().width()}x{qquick.size().height()}")
print(f"QQuickWidget minimum size: {qquick.minimumSize().width()}x{qquick.minimumSize().height()}")
print(f"QQuickWidget visible: {qquick.isVisible()}")
print(f"QQuickWidget enabled: {qquick.isEnabled()}")
print(f"QML Status: {qquick.status()}")

if qquick.status() == QQuickWidget.Status.Ready:
    root = qquick.rootObject()
    print(f"QML root object: {root}")
    if root:
        print(f"  width: {root.property('width')}")
        print(f"  height: {root.property('height')}")
        print(f"  visible: {root.property('visible')}")

window.show()

print("\n"+"="*60)
print("AFTER SHOW")
print("="*60)
print(f"Window visible: {window.isVisible()}")
print(f"Window size: {window.size().width()}x{window.size().height()}")
print(f"Central widget size: {window.centralWidget().size().width()}x{window.centralWidget().size().height()}")
print(f"QQuickWidget size: {qquick.size().width()}x{qquick.size().height()}")

sys.exit(app.exec())
