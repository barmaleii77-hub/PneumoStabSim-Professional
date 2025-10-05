#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test piston movement - Manual control to verify QML integration
"""
import sys
import os

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
os.environ.setdefault("QT_LOGGING_RULES", "js.debug=true;qt.qml.debug=true")

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider, QLabel
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, Qt, QMetaObject, Q_ARG
from pathlib import Path


class PistonTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("?? PISTON MOVEMENT TEST - Manual Control")
        self.resize(1600, 900)
        
        # Central widget with layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # QML 3D View
        self.qml_widget = QQuickWidget()
        self.qml_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
        
        # Load main.qml from assets
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
        
        # Control sliders
        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        
        controls_layout.addWidget(QLabel("?? MANUAL CONTROL - Test Python?QML Integration"))
        
        # FL controls
        controls_layout.addWidget(QLabel("??? FRONT LEFT (FL) ???"))
        fl_piston_label = QLabel("FL Piston Position: 125mm")
        self.fl_slider = QSlider(Qt.Horizontal)
        self.fl_slider.setMinimum(25)   # 10% of 250mm
        self.fl_slider.setMaximum(225)  # 90% of 250mm
        self.fl_slider.setValue(125)    # Center
        self.fl_slider.valueChanged.connect(lambda v: self._on_fl_piston_changed(v, fl_piston_label))
        
        fl_angle_label = QLabel("FL Lever Angle: 0.0°")
        self.fl_angle_slider = QSlider(Qt.Horizontal)
        self.fl_angle_slider.setMinimum(-100)  # -10.0°
        self.fl_angle_slider.setMaximum(100)   # +10.0°
        self.fl_angle_slider.setValue(0)       # 0°
        self.fl_angle_slider.valueChanged.connect(lambda v: self._on_fl_angle_changed(v, fl_angle_label))
        
        controls_layout.addWidget(fl_piston_label)
        controls_layout.addWidget(self.fl_slider)
        controls_layout.addWidget(fl_angle_label)
        controls_layout.addWidget(self.fl_angle_slider)
        
        # FR controls
        controls_layout.addWidget(QLabel("??? FRONT RIGHT (FR) ???"))
        fr_piston_label = QLabel("FR Piston Position: 125mm")
        self.fr_slider = QSlider(Qt.Horizontal)
        self.fr_slider.setMinimum(25)
        self.fr_slider.setMaximum(225)
        self.fr_slider.setValue(125)
        self.fr_slider.valueChanged.connect(lambda v: self._on_fr_piston_changed(v, fr_piston_label))
        
        fr_angle_label = QLabel("FR Lever Angle: 0.0°")
        self.fr_angle_slider = QSlider(Qt.Horizontal)
        self.fr_angle_slider.setMinimum(-100)
        self.fr_angle_slider.setMaximum(100)
        self.fr_angle_slider.setValue(0)
        self.fr_angle_slider.valueChanged.connect(lambda v: self._on_fr_angle_changed(v, fr_angle_label))
        
        controls_layout.addWidget(fr_piston_label)
        controls_layout.addWidget(self.fr_slider)
        controls_layout.addWidget(fr_angle_label)
        controls_layout.addWidget(self.fr_angle_slider)
        
        layout.addWidget(controls)
        
        print("? Piston test window loaded")
        print("?? Use sliders to control:")
        print("   - Piston positions (watch PINK pistons move inside cylinders)")
        print("   - Lever angles (watch GRAY levers rotate)")
        print("?? If BOTH work - Python?QML integration is 100% functional!")
    
    def _on_fl_piston_changed(self, value, label):
        label.setText(f"FL Piston Position: {value}mm")
        self._update_positions()
    
    def _on_fl_angle_changed(self, value, label):
        angle_deg = value / 10.0  # Convert to degrees (-10.0 to +10.0)
        label.setText(f"FL Lever Angle: {angle_deg:.1f}°")
        self._update_angles()
    
    def _on_fr_piston_changed(self, value, label):
        label.setText(f"FR Piston Position: {value}mm")
        self._update_positions()
    
    def _on_fr_angle_changed(self, value, label):
        angle_deg = value / 10.0
        label.setText(f"FR Lever Angle: {angle_deg:.1f}°")
        self._update_angles()
    
    def _update_positions(self):
        """Send current slider values to QML"""
        if not self.qml_root:
            return
        
        positions = {
            'fl': float(self.fl_slider.value()),
            'fr': float(self.fr_slider.value()),
            'rl': 125.0,  # Not controlled yet
            'rr': 125.0   # Not controlled yet
        }
        
        # Call QML function
        success = QMetaObject.invokeMethod(
            self.qml_root,
            "updatePistonPositions",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", positions)
        )
        
        if not success:
            print("? Failed to call updatePistonPositions()")
    
    def _update_angles(self):
        """Send lever angles to QML"""
        if not self.qml_root:
            return
        
        angles = {
            'fl': self.fl_angle_slider.value() / 10.0,
            'fr': self.fr_angle_slider.value() / 10.0,
            'rl': 0.0,
            'rr': 0.0
        }
        
        # Call QML function
        success = QMetaObject.invokeMethod(
            self.qml_root,
            "updateAnimation",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", angles)
        )
        
        if not success:
            print("? Failed to call updateAnimation()")


def main():
    print("="*70)
    print("?? PISTON & LEVER MOVEMENT TEST")
    print("="*70)
    print("PURPOSE: Verify complete Python?QML integration")
    print()
    print("WHAT TO TEST:")
    print("1. Move PISTON sliders ? Pink pistons should MOVE inside cylinders")
    print("2. Move ANGLE sliders ? Gray levers should ROTATE")
    print("3. Rod lengths should adjust automatically")
    print()
    print("SUCCESS CRITERIA:")
    print("? Pistons move smoothly when sliders change")
    print("? Levers rotate when angle sliders change")
    print("? Rod connects piston to lever attachment point")
    print("="*70)
    print()
    
    app = QApplication(sys.argv)
    window = PistonTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
