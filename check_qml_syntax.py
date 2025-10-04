#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic: Check QML files for syntax errors
"""
import sys
import os
from pathlib import Path

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl

def check_qml(qml_path: Path, description: str):
    """Check QML file for errors"""
    print(f"\n{'='*60}")
    print(f"Checking: {description}")
    print(f"File: {qml_path}")
    print(f"Exists: {qml_path.exists()}")
    
    if not qml_path.exists():
        print(f"? FILE NOT FOUND")
        return False
    
    widget = QQuickWidget()
    widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))
    
    if widget.status() == QQuickWidget.Status.Error:
        print(f"? QML ERRORS:")
        for error in widget.errors():
            print(f"   Line {error.line()}: {error.description()}")
        return False
    elif widget.status() == QQuickWidget.Status.Ready:
        print(f"? QML VALID")
        return True
    else:
        print(f"?? UNKNOWN STATUS: {widget.status()}")
        return False

def main():
    print("="*60)
    print("QML SYNTAX VALIDATION")
    print("="*60)
    
    app = QApplication(sys.argv)
    
    # Check Materials.qml
    materials_path = Path("assets/qml/components/Materials.qml")
    materials_ok = check_qml(materials_path, "Materials.qml (Singleton)")
    
    # Check MechCorner.qml
    corner_path = Path("assets/qml/mech/MechCorner.qml")
    corner_ok = check_qml(corner_path, "MechCorner.qml (Component)")
    
    # Check UFrameScene.qml
    scene_path = Path("assets/qml/UFrameScene.qml")
    scene_ok = check_qml(scene_path, "UFrameScene.qml (Main scene)")
    
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"  Materials.qml: {'?' if materials_ok else '?'}")
    print(f"  MechCorner.qml: {'?' if corner_ok else '?'}")
    print(f"  UFrameScene.qml: {'?' if scene_ok else '?'}")
    
    if all([materials_ok, corner_ok, scene_ok]):
        print("\n? ALL QML FILES VALID - Ready to run app")
        return 0
    else:
        print("\n? FIX ERRORS ABOVE before running app")
        return 1

if __name__ == "__main__":
    sys.exit(main())
