#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test CORRECT kinematics - Lever angle controls piston position
NO independent piston control - rod has FIXED length!
"""
import sys
import os

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider, QLabel
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, Qt, QMetaObject, Q_ARG
from pathlib import Path

# Import geometry bridge for CORRECT calculations
sys.path.insert(0, str(Path(__file__).parent))
from src.ui.geometry_bridge import create_geometry_converter


class CorrectKinematicsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("? CORRECT KINEMATICS - Fixed Rod Length")
        self.resize(1600, 900)
        
        # Create geometry converter
        self.geo_converter = create_geometry_converter()
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # QML 3D View
        self.qml_widget = QQuickWidget()
        self.qml_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
        
        qml_path = Path("assets/qml/main.qml")
        if not qml_path.exists():
            print(f"? ERROR: {qml_path} not found!")
            sys.exit(1)
        
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)
        
        if self.qml_widget.status() == QQuickWidget.Status.Error:
            errors = self.qml_widget.errors()
            print(f"? QML ERRORS: {[str(e) for e in errors]}")
            sys.exit(1)
        
        self.qml_root = self.qml_widget.rootObject()
        layout.addWidget(self.qml_widget, stretch=1)
        
        # Controls
        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        
        controls_layout.addWidget(QLabel("? CORRECT KINEMATICS TEST"))
        controls_layout.addWidget(QLabel("Lever angle controls EVERYTHING (rod has FIXED length!)"))
        
        # FL controls
        controls_layout.addWidget(QLabel("=== FRONT LEFT (FL) ==="))
        
        self.fl_angle_label = QLabel("FL Lever Angle: 0.0 deg ? Piston: ??? mm")
        self.fl_angle_slider = QSlider(Qt.Horizontal)
        self.fl_angle_slider.setMinimum(-100)  # -10 deg
        self.fl_angle_slider.setMaximum(100)   # +10 deg
        self.fl_angle_slider.setValue(0)
        self.fl_angle_slider.valueChanged.connect(self._on_fl_angle_changed)
        
        controls_layout.addWidget(self.fl_angle_label)
        controls_layout.addWidget(self.fl_angle_slider)
        
        # Info
        controls_layout.addWidget(QLabel(""))
        controls_layout.addWidget(QLabel("?? HOW IT WORKS:"))
        controls_layout.addWidget(QLabel("1. You change lever angle"))
        controls_layout.addWidget(QLabel("2. Python calculates rod attachment point on lever"))
        controls_layout.addWidget(QLabel("3. Python calculates piston position (FIXED rod length!)"))
        controls_layout.addWidget(QLabel("4. QML displays BOTH lever AND piston"))
        controls_layout.addWidget(QLabel("5. Rod length NEVER changes!"))
        
        layout.addWidget(controls)
        
        print("? Correct kinematics window loaded")
        print("?? Move angle slider - watch BOTH lever AND piston move together!")
        print("?? Rod length stays CONSTANT (as it should in reality)")
    
    def _on_fl_angle_changed(self, value):
        angle_deg = value / 10.0
        
        # Calculate CORRECT piston position from lever angle using GeometryBridge
        corner_data = self.geo_converter.get_corner_3d_coords(
            corner='fl',
            lever_angle_deg=angle_deg,
            cylinder_state=None  # No physics, pure geometry
        )
        
        # DEBUG: Print what we got
        print(f"\nDEBUG: angle={angle_deg:.1f} deg")
        print(f"  pistonPositionMm: {corner_data.get('pistonPositionMm')} (type: {type(corner_data.get('pistonPositionMm')).__name__})")
        print(f"  pistonRatio: {corner_data.get('pistonRatio')}")
        
        piston_pos_mm = corner_data.get('pistonPositionMm', 125.0)
        
        # Ensure it's a float
        if piston_pos_mm is None or not isinstance(piston_pos_mm, (int, float)):
            print(f"  ERROR: piston_pos_mm is {piston_pos_mm}, using default 125.0")
            piston_pos_mm = 125.0
        
        # Update label
        self.fl_angle_label.setText(
            f"FL Lever Angle: {angle_deg:.1f} deg -> Piston: {piston_pos_mm:.1f} mm"
        )
        
        # Send BOTH to QML
        angles = {'fl': angle_deg, 'fr': 0.0, 'rl': 0.0, 'rr': 0.0}
        positions = {'fl': float(piston_pos_mm), 'fr': 125.0, 'rl': 125.0, 'rr': 125.0}
        
        print(f"  -> Sending to QML: angles={angles['fl']}, positions={positions['fl']}")
        
        QMetaObject.invokeMethod(
            self.qml_root, "updateAnimation",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", angles)
        )
        
        QMetaObject.invokeMethod(
            self.qml_root, "updatePistonPositions",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", positions)
        )


def main():
    print("="*70)
    print("? CORRECT KINEMATICS TEST")
    print("="*70)
    print("PURPOSE: Test PROPER mechanical linkage")
    print()
    print("WHAT'S DIFFERENT:")
    print("? BEFORE: Lever and piston moved INDEPENDENTLY (wrong!)")
    print("? NOW: Lever angle ? Python calculates piston pos (correct!)")
    print()
    print("EXPECTED BEHAVIOR:")
    print("1. Move lever angle slider")
    print("2. Lever rotates in 3D")
    print("3. Piston moves AUTOMATICALLY (calculated by Python)")
    print("4. Rod length STAYS CONSTANT (realistic!)")
    print("="*70)
    print()
    
    app = QApplication(sys.argv)
    window = CorrectKinematicsWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
