#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test animation of suspension system - changing lever angles
"""
import sys
import os

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QVector3D

from src.ui.qml_host import SuspensionSceneHost


class AnimationTestWindow(QMainWindow):
    """Test window with sliders to animate suspension"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SUSPENSION ANIMATION TEST")
        self.resize(1600, 1000)
        
        # Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Create layout
        layout = QHBoxLayout(main_widget)
        
        # Create suspension scene
        print("Creating SuspensionSceneHost with geometry_bridge...")
        self.scene = SuspensionSceneHost(self)
        layout.addWidget(self.scene, 3)  # 75% width
        
        # Create control panel
        controls = self.create_control_panel()
        layout.addWidget(controls, 1)  # 25% width
        
        print("? Animation test window created")
    
    def create_control_panel(self):
        """Create control panel with sliders"""
        panel = QWidget()
        panel.setMaximumWidth(300)
        panel.setStyleSheet("""
            QWidget { background-color: #2d2d2d; color: white; }
            QLabel { font-size: 12px; font-weight: bold; }
            QSlider::groove:horizontal { height: 6px; background: #555; }
            QSlider::handle:horizontal { width: 16px; background: #0078d4; border-radius: 8px; }
        """)
        
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("SUSPENSION ANIMATION")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # FL Angle Slider
        self.fl_slider = self.create_angle_slider("FL Lever Angle", self.on_fl_angle_changed)
        layout.addWidget(self.fl_slider)
        
        # FR Angle Slider
        self.fr_slider = self.create_angle_slider("FR Lever Angle", self.on_fr_angle_changed)
        layout.addWidget(self.fr_slider)
        
        # RL Angle Slider
        self.rl_slider = self.create_angle_slider("RL Lever Angle", self.on_rl_angle_changed)
        layout.addWidget(self.rl_slider)
        
        # RR Angle Slider
        self.rr_slider = self.create_angle_slider("RR Lever Angle", self.on_rr_angle_changed)
        layout.addWidget(self.rr_slider)
        
        # Auto Animation
        layout.addWidget(QLabel("AUTO ANIMATION"))
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.update_auto_animation)
        self.auto_angle = 0.0
        
        from PySide6.QtWidgets import QPushButton
        auto_btn = QPushButton("Start Auto Animation")
        auto_btn.clicked.connect(self.toggle_auto_animation)
        layout.addWidget(auto_btn)
        self.auto_btn = auto_btn
        
        layout.addStretch()
        
        return panel
    
    def create_angle_slider(self, title, callback):
        """Create angle slider widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(title)
        layout.addWidget(label)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(-30, 30)  # -30° to +30°
        slider.setValue(0)
        slider.valueChanged.connect(callback)
        layout.addWidget(slider)
        
        value_label = QLabel("0deg")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        # Store value label for updates
        slider.value_label = value_label
        
        return widget
    
    def on_fl_angle_changed(self, value):
        """FL lever angle changed"""
        angle_deg = value
        self.fl_slider.findChild(QSlider).value_label.setText(f"{angle_deg}deg")
        
        # Update geometry and recalculate coordinates
        self.update_corner_angle('fl', angle_deg)
        
    def on_fr_angle_changed(self, value):
        """FR lever angle changed"""
        angle_deg = value
        self.fr_slider.findChild(QSlider).value_label.setText(f"{angle_deg}deg")
        self.update_corner_angle('fr', angle_deg)
        
    def on_rl_angle_changed(self, value):
        """RL lever angle changed"""
        angle_deg = value
        self.rl_slider.findChild(QSlider).value_label.setText(f"{angle_deg}deg")
        self.update_corner_angle('rl', angle_deg)
        
    def on_rr_angle_changed(self, value):
        """RR lever angle changed"""
        angle_deg = value
        self.rr_slider.findChild(QSlider).value_label.setText(f"{angle_deg}deg")
        self.update_corner_angle('rr', angle_deg)
    
    def update_corner_angle(self, corner, angle_deg):
        """Update corner with new lever angle"""
        print(f"?? Updating {corner.upper()} angle to {angle_deg}deg")
        
        # Get updated coordinates from geometry bridge
        corner_data = self.scene.geometry_converter.get_corner_3d_coords(corner, angle_deg)
        
        print(f"   j_arm: {corner_data['j_arm']} [FIXED]")
        print(f"   j_rod: {corner_data['j_rod']} [MOVING]")
        print(f"   rod_extension: {corner_data['rod_extension']:.1f}mm")
        
        # Update QML with all relevant parameters
        self.scene.update_corner(corner, 
                                armAngleDeg=angle_deg,
                                j_rod=corner_data['j_rod'],
                                j_cylinder_end=corner_data.get('j_cylinder_end'),
                                j_piston=corner_data.get('j_piston'))
    
    def toggle_auto_animation(self):
        """Toggle auto animation"""
        if self.auto_timer.isActive():
            self.auto_timer.stop()
            self.auto_btn.setText("Start Auto Animation")
        else:
            self.auto_timer.start(50)  # 20 FPS
            self.auto_btn.setText("Stop Auto Animation")
    
    def update_auto_animation(self):
        """Update auto animation"""
        import math
        
        self.auto_angle += 2.0  # degrees per frame
        
        # Sine wave for different corners
        fl_angle = 15.0 * math.sin(math.radians(self.auto_angle))
        fr_angle = 15.0 * math.sin(math.radians(self.auto_angle + 90))
        rl_angle = 15.0 * math.sin(math.radians(self.auto_angle + 180))  
        rr_angle = 15.0 * math.sin(math.radians(self.auto_angle + 270))
        
        # Update sliders (will trigger callbacks)
        self.fl_slider.findChild(QSlider).setValue(int(fl_angle))
        self.fr_slider.findChild(QSlider).setValue(int(fr_angle))
        self.rl_slider.findChild(QSlider).setValue(int(rl_angle))
        self.rr_slider.findChild(QSlider).setValue(int(rr_angle))


def main():
    print("="*60)
    print("SUSPENSION ANIMATION TEST")
    print("="*60)
    print("Testing real-time coordinate updates")
    print("Controls:")
    print("  - Use sliders to change lever angles")
    print("  - Watch suspension geometry update")
    print("  - Start auto animation for demo")
    print("="*60)
    
    app = QApplication(sys.argv)
    window = AnimationTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()