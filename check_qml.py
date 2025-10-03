# -*- coding: utf-8 -*-
"""Qt Quick 3D animation diagnostic"""
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path
import sys

app = QApplication(sys.argv)

widget = QQuickWidget()
widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

qml_path = Path("assets/qml/main.qml").absolute()
print(f"Loading: {qml_path}")
print(f"Exists: {qml_path.exists()}")

if qml_path.exists():
    widget.setSource(QUrl.fromLocalFile(str(qml_path)))
    
    status = widget.status()
    print(f"\nStatus: {status}")
    
    if status == QQuickWidget.Status.Error:
        print("ERRORS:")
        for err in widget.errors():
            print(f"  {err}")
    elif status == QQuickWidget.Status.Ready:
        print("READY")
        root = widget.rootObject()
        if root:
            print(f"Root: {root.metaObject().className()}")
    
    widget.resize(800, 600)
    widget.show()
    print("\nWindow shown")
    
    sys.exit(app.exec())
