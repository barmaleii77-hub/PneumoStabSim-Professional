#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test user-controlled geometry integration
Tests the complete pipeline: UI controls ? geometry bridge ? 3D scene
"""
import sys
import os

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSlider, QSpinBox, QPushButton
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, Qt, QTimer
from pathlib import Path

# Import the corrected suspension QML
from test_2m_suspension import SUSPENSION_QML

class UserControlledSuspensionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("USER-CONTROLLED SUSPENSION GEOMETRY - INTEGRATION TEST")
        self.resize(1600, 1000)
        
        # Create main widget with splitter layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QHBoxLayout(main_widget)
        
        # Left panel: User controls
        controls_widget = self.create_controls_panel()
        controls_widget.setMaximumWidth(300)
        main_layout.addWidget(controls_widget)
        
        # Right panel: 3D scene
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
        
        # Create enhanced QML with user parameter integration
        enhanced_qml = self.create_enhanced_suspension_qml()
        
        qml_path = Path("user_controlled_suspension.qml")
        qml_path.write_text(enhanced_qml, encoding='utf-8')
        
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)
        
        if self.qml_widget.status() == QQuickWidget.Status.Error:
            errors = self.qml_widget.errors()
            print(f"? QML ERRORS: {[str(e) for e in errors]}")
        else:
            print("? User-controlled suspension loaded successfully")
        
        main_layout.addWidget(self.qml_widget, 1)  # Give 3D scene more space
        
        # Get QML root for direct communication
        self.qml_root = self.qml_widget.rootObject()
        
        # Connect controls to QML updates
        self.connect_controls()
        
        # Auto-update timer for smooth animation
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_geometry_from_controls)
        self.update_timer.start(100)  # 10 FPS geometry updates
        
    def create_controls_panel(self):
        """Create user control panel with sliders and spinboxes"""
        controls = QWidget()
        layout = QVBoxLayout(controls)
        
        # Title
        title = QLabel("?? SUSPENSION GEOMETRY CONTROLS")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #0088ff; margin: 10px;")
        layout.addWidget(title)
        
        # Frame dimensions
        frame_group = QLabel("?? FRAME DIMENSIONS")
        frame_group.setStyleSheet("font-weight: bold; color: #ff8800; margin-top: 15px;")
        layout.addWidget(frame_group)
        
        # Frame length
        layout.addWidget(QLabel("Frame Length (mm):"))
        self.frame_length_slider = QSlider(Qt.HORIZONTAL)
        self.frame_length_slider.setRange(1000, 3000)
        self.frame_length_slider.setValue(2000)
        self.frame_length_spinbox = QSpinBox()
        self.frame_length_spinbox.setRange(1000, 3000)
        self.frame_length_spinbox.setValue(2000)
        layout.addWidget(self.frame_length_slider)
        layout.addWidget(self.frame_length_spinbox)
        
        # Frame height
        layout.addWidget(QLabel("Frame Height (mm):"))
        self.frame_height_slider = QSlider(Qt.HORIZONTAL)
        self.frame_height_slider.setRange(400, 800)
        self.frame_height_slider.setValue(650)
        self.frame_height_spinbox = QSpinBox()
        self.frame_height_spinbox.setRange(400, 800)
        self.frame_height_spinbox.setValue(650)
        layout.addWidget(self.frame_height_slider)
        layout.addWidget(self.frame_height_spinbox)
        
        # Beam size
        layout.addWidget(QLabel("Beam Size (mm):"))
        self.beam_size_slider = QSlider(Qt.HORIZONTAL)
        self.beam_size_slider.setRange(80, 200)
        self.beam_size_slider.setValue(120)
        self.beam_size_spinbox = QSpinBox()
        self.beam_size_spinbox.setRange(80, 200)
        self.beam_size_spinbox.setValue(120)
        layout.addWidget(self.beam_size_slider)
        layout.addWidget(self.beam_size_spinbox)
        
        # Suspension components
        suspension_group = QLabel("?? SUSPENSION COMPONENTS")
        suspension_group.setStyleSheet("font-weight: bold; color: #ff8800; margin-top: 15px;")
        layout.addWidget(suspension_group)
        
        # Lever length
        layout.addWidget(QLabel("Lever Length (mm):"))
        self.lever_length_slider = QSlider(Qt.HORIZONTAL)
        self.lever_length_slider.setRange(200, 500)
        self.lever_length_slider.setValue(315)
        self.lever_length_spinbox = QSpinBox()
        self.lever_length_spinbox.setRange(200, 500)
        self.lever_length_spinbox.setValue(315)
        layout.addWidget(self.lever_length_slider)
        layout.addWidget(self.lever_length_spinbox)
        
        # Cylinder length
        layout.addWidget(QLabel("Cylinder Length (mm):"))
        self.cylinder_length_slider = QSlider(Qt.HORIZONTAL)
        self.cylinder_length_slider.setRange(150, 400)
        self.cylinder_length_slider.setValue(250)
        self.cylinder_length_spinbox = QSpinBox()
        self.cylinder_length_spinbox.setRange(150, 400)
        self.cylinder_length_spinbox.setValue(250)
        layout.addWidget(self.cylinder_length_slider)
        layout.addWidget(self.cylinder_length_spinbox)
        
        # Tail rod length
        layout.addWidget(QLabel("Tail Rod Length (mm):"))
        self.tail_rod_slider = QSlider(Qt.HORIZONTAL)
        self.tail_rod_slider.setRange(50, 200)
        self.tail_rod_slider.setValue(100)
        self.tail_rod_spinbox = QSpinBox()
        self.tail_rod_spinbox.setRange(50, 200)
        self.tail_rod_spinbox.setValue(100)
        layout.addWidget(self.tail_rod_slider)
        layout.addWidget(self.tail_rod_spinbox)
        
        # Reset button
        reset_button = QPushButton("?? RESET TO DEFAULTS")
        reset_button.setStyleSheet("font-weight: bold; background: #ff6b6b; color: white; margin: 10px; padding: 8px;")
        reset_button.clicked.connect(self.reset_to_defaults)
        layout.addWidget(reset_button)
        
        # Status info
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #00ff44; font-size: 10px; margin: 5px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        return controls
    
    def connect_controls(self):
        """Connect sliders and spinboxes bidirectionally"""
        # Frame length
        self.frame_length_slider.valueChanged.connect(self.frame_length_spinbox.setValue)
        self.frame_length_spinbox.valueChanged.connect(self.frame_length_slider.setValue)
        
        # Frame height  
        self.frame_height_slider.valueChanged.connect(self.frame_height_spinbox.setValue)
        self.frame_height_spinbox.valueChanged.connect(self.frame_height_slider.setValue)
        
        # Beam size
        self.beam_size_slider.valueChanged.connect(self.beam_size_spinbox.setValue)
        self.beam_size_spinbox.valueChanged.connect(self.beam_size_slider.setValue)
        
        # Lever length
        self.lever_length_slider.valueChanged.connect(self.lever_length_spinbox.setValue)
        self.lever_length_spinbox.valueChanged.connect(self.lever_length_slider.setValue)
        
        # Cylinder length
        self.cylinder_length_slider.valueChanged.connect(self.cylinder_length_spinbox.setValue)
        self.cylinder_length_spinbox.valueChanged.connect(self.cylinder_length_slider.setValue)
        
        # Tail rod length
        self.tail_rod_slider.valueChanged.connect(self.tail_rod_spinbox.setValue)
        self.tail_rod_spinbox.valueChanged.connect(self.tail_rod_slider.setValue)
    
    def update_geometry_from_controls(self):
        """Update QML scene with current control values"""
        if not self.qml_root:
            return
        
        try:
            # Get current values from controls
            geometry_params = {
                'frameLength': float(self.frame_length_spinbox.value()),
                'frameHeight': float(self.frame_height_spinbox.value()),
                'frameBeamSize': float(self.beam_size_spinbox.value()),
                'leverLength': float(self.lever_length_spinbox.value()),
                'cylinderBodyLength': float(self.cylinder_length_spinbox.value()),
                'tailRodLength': float(self.tail_rod_spinbox.value())
            }
            
            # Update QML properties
            for param, value in geometry_params.items():
                qml_property = f"user{param[0].upper()}{param[1:]}"  # frameLength -> userFrameLength
                self.qml_root.setProperty(qml_property, value)
            
            # Update status
            self.status_label.setText(f"? Updated: {geometry_params['frameLength']:.0f}x{geometry_params['frameHeight']:.0f}mm")
            
        except Exception as e:
            self.status_label.setText(f"? Error: {e}")
            print(f"?? Geometry update error: {e}")
    
    def reset_to_defaults(self):
        """Reset all controls to default values"""
        self.frame_length_spinbox.setValue(2000)
        self.frame_height_spinbox.setValue(650)  
        self.beam_size_spinbox.setValue(120)
        self.lever_length_spinbox.setValue(315)
        self.cylinder_length_spinbox.setValue(250)
        self.tail_rod_spinbox.setValue(100)
        
        self.status_label.setText("?? Reset to defaults")
    
    def create_enhanced_suspension_qml(self):
        """Create enhanced QML with user parameter integration"""
        return SUSPENSION_QML.replace(
            "// 2-meter suspension system coordinates",
            '''// USER-CONTROLLABLE GEOMETRY PARAMETERS (connected to UI sliders)
    property real userFrameLength: 2000     // mm - controlled by UI
    property real userFrameHeight: 650      // mm - controlled by UI  
    property real userFrameBeamSize: 120    // mm - controlled by UI
    property real userLeverLength: 315      // mm - controlled by UI
    property real userCylinderLength: 250   // mm - controlled by UI
    property real userTailRodLength: 100    // mm - controlled by UI

    // 2-meter suspension system coordinates (DYNAMIC - updated from user controls)'''
        ).replace(
            "property real beamSize: 120",
            "property real beamSize: userFrameBeamSize"
        ).replace(
            "property real frameHeight: 650",
            "property real frameHeight: userFrameHeight"  
        ).replace(
            "property real frameLength: 2000",
            "property real frameLength: userFrameLength"
        ).replace(
            "property real leverLength: 315",
            "property real leverLength: userLeverLength"
        ).replace(
            "property real lBody: 250  // CONSTANT cylinder working length",
            "property real lBody: view3d.userCylinderLength  // USER-CONTROLLED cylinder length"
        ).replace(
            "property real lTailRod: 100  // Tail rod length", 
            "property real lTailRod: view3d.userTailRodLength  // USER-CONTROLLED tail rod length"
        ).replace(
            "property real lTailRod: 100  // Fixed 100mm tail rod length",
            "property real lTailRod: view3d.userTailRodLength  // USER-CONTROLLED tail rod length"
        ).replace(
            "console.log(\"=== FULLY CORRECTED 2-METER SUSPENSION ===\")",
            '''console.log("?? USER-CONTROLLABLE SUSPENSION LOADED")
        console.log("   Frame:", frameLength + "x" + frameHeight + "x" + beamSize + "mm")
        console.log("   Lever:", leverLength + "mm")
        console.log("   Cylinder:", userCylinderLength + "mm + " + userTailRodLength + "mm tail")
        console.log("? Connected to UI controls - geometry updates in real-time!")'''
        )

def main():
    print("="*70)
    print("USER-CONTROLLED SUSPENSION GEOMETRY - INTEGRATION TEST")
    print("="*70)
    print("?? FEATURES:")
    print("? Real-time geometry control via UI sliders")
    print("? Corrected suspension mechanics (round joints, steel rods)")
    print("? Live 3D updates as user changes parameters") 
    print("? Integration ready for main application")
    print("="*70)
    
    app = QApplication(sys.argv)
    window = UserControlledSuspensionWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()