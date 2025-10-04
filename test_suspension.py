#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test for suspension 3D visualization
"""
import sys
import os

# Set RHI backend BEFORE importing PySide6
os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
os.environ.setdefault("QSG_INFO", "1")

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

from src.ui.qml_host import SuspensionSceneHost


class TestWindow(QMainWindow):
    """Simple test window for suspension scene"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Suspension 3D Visualization Test")
        self.resize(1200, 800)
        
        # Create suspension scene
        print("Creating SuspensionSceneHost...")
        self.scene = SuspensionSceneHost(self)
        
        # Coordinates will be set automatically from geometry_bridge.py
        print("? Using coordinates from geometry_bridge.py")
        
        # Set as central widget
        self.setCentralWidget(self.scene)
        
        print("? Window created")
    
    def showEvent(self, event):
        super().showEvent(event)
        print("? Window shown")


def main():
    print("="*60)
    print("SUSPENSION 3D VISUALIZATION TEST")
    print("="*60)
    print()
    
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print()
    print("="*60)
    print("EXPECTED:")
    print("  - White background")
    print("  - Red U-frame (3 cubes)")
    print("  - 4 corners with:")
    print("    - Steel levers")
    print("    - Glass cylinders (transparent)")
    print("    - Chrome rods")
    print("    - Blue spheres (masses)")
    print("  - Realistic shadows and reflections")
    print()
    print("Controls:")
    print("  - Left mouse: Rotate")
    print("  - Mouse wheel: Zoom")
    print("  - F: Auto-fit")
    print("  - R: Reset view")
    print("  - Double-click: Auto-fit")
    print("="*60)
    print()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
