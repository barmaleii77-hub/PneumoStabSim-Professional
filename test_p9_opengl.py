#!/usr/bin/env python
"""
P9 Test: OpenGL rendering verification
Tests isometric view, transparent cylinders, mouse controls
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer

from src.ui import GLView
from src.runtime.state import StateSnapshot, FrameState
from src.physics import create_default_rigid_body
import numpy as np


class TestWindow(QMainWindow):
    """Test window for P9 OpenGL rendering"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("P9 OpenGL Test: Isometric Scene with Transparent Cylinders")
        self.resize(1200, 800)
        
        # Create GLView
        self.gl_view = GLView(self)
        self.setCentralWidget(self.gl_view)
        
        # Create test data
        self.time = 0.0
        self.rigid_body = create_default_rigid_body()
        
        # Simulation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_simulation)
        self.timer.start(16)  # ~60 FPS
        
        print("P9 Test Started")
        print("=" * 60)
        print("Controls:")
        print("  - Mouse Wheel: Zoom in/out")
        print("  - Left Mouse: Rotate camera")
        print("  - Middle Mouse: Pan camera")
        print("=" * 60)
        
    def _update_simulation(self):
        """Update simulation state for testing"""
        self.time += 0.016
        
        # Create test snapshot with animated frame
        snapshot = StateSnapshot()
        snapshot.simulation_time = self.time
        snapshot.step_number = int(self.time / 0.001)
        snapshot.dt_physics = 0.001
        
        # Animated frame state (sinusoidal motion)
        snapshot.frame = FrameState(
            heave=0.05 * np.sin(self.time),           # +/-5cm heave
            roll=0.02 * np.sin(self.time * 1.5),      # +/-1.15deg roll
            pitch=0.03 * np.cos(self.time * 0.8),     # +/-1.72deg pitch
            heave_rate=0.05 * np.cos(self.time),
            roll_rate=0.03 * np.cos(self.time * 1.5),
            pitch_rate=-0.024 * np.sin(self.time * 0.8)
        )
        
        # Send to GLView
        self.gl_view.set_current_state(snapshot)
        self.gl_view.update()


def main():
    """Run P9 test"""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
