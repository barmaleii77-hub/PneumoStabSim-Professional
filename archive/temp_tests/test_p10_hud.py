#!/usr/bin/env python
"""
P10 Test: Pressure gradient scale + HUD tank visualization
Tests pressure scale widget, tank overlay, valve markers, line spheres
"""

import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget
from PySide6.QtCore import QTimer

from src.ui import GLView, PressureScaleWidget
from src.runtime.state import StateSnapshot, FrameState, TankState, LineState
from src.pneumo.enums import Line


class TestP10Window(QMainWindow):
    """Test window for P10 HUD visualization"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("P10 Test: Pressure Scale + Tank HUD")
        self.resize(1400, 900)
        
        # Create central widget with layout
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create GL view
        self.gl_view = GLView()
        layout.addWidget(self.gl_view, stretch=1)
        
        # Create pressure scale
        self.pressure_scale = PressureScaleWidget()
        self.pressure_scale.set_range(0, 6000000.0)  # 0-60 bar
        self.pressure_scale.set_markers(
            p_atm=101325.0,
            p_min=250000.0,      # 2.5 bar
            p_stiff=1500000.0,   # 15 bar
            p_safety=5000000.0   # 50 bar
        )
        layout.addWidget(self.pressure_scale)
        
        self.setCentralWidget(central)
        
        # Simulation state
        self.time = 0.0
        self.phase = 0.0
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_simulation)
        self.timer.start(16)  # ~60 FPS
        
        print("P10 Test Started")
        print("=" * 70)
        print("Features:")
        print("  - Vertical pressure gradient scale (right side)")
        print("  - Tank HUD overlay with fill level")
        print("  - 4 floating pressure spheres (A1, B1, A2, B2)")
        print("  - Valve markers at setpoint heights")
        print("  - Animated pressures (sinusoidal)")
        print("=" * 70)
        
    def _update_simulation(self):
        """Update simulation state for testing"""
        self.time += 0.016
        self.phase += 0.05
        
        # Create test snapshot
        snapshot = StateSnapshot()
        snapshot.simulation_time = self.time
        snapshot.step_number = int(self.time / 0.001)
        snapshot.dt_physics = 0.001
        
        # Animated frame state
        snapshot.frame = FrameState(
            heave=0.05 * np.sin(self.time),
            roll=0.02 * np.sin(self.time * 1.5),
            pitch=0.03 * np.cos(self.time * 0.8)
        )
        
        # Animated tank pressure (oscillating between 2 and 20 bar)
        p_center = 1000000.0  # 10 bar
        p_amplitude = 800000.0  # +/- 8 bar
        p_tank = p_center + p_amplitude * np.sin(self.phase)
        p_tank = max(101325.0, p_tank)  # Clamp to atmospheric minimum
        
        snapshot.tank = TankState(
            pressure=p_tank,
            temperature=293.15,
            volume=0.0005,
            relief_min_open=(p_tank > 250000.0),
            relief_stiff_open=(p_tank > 1500000.0),
            relief_safety_open=(p_tank > 5000000.0)
        )
        
        # Animated line pressures (different phases)
        line_pressures = [
            p_center + p_amplitude * 0.8 * np.sin(self.phase + 0.0),  # A1
            p_center + p_amplitude * 0.6 * np.sin(self.phase + 1.5),  # B1
            p_center + p_amplitude * 0.7 * np.sin(self.phase + 3.0),  # A2
            p_center + p_amplitude * 0.5 * np.sin(self.phase + 4.5),  # B2
        ]
        
        for i, (line_enum, pressure) in enumerate(zip([Line.A1, Line.B1, Line.A2, Line.B2], line_pressures)):
            snapshot.lines[line_enum] = LineState(
                line=line_enum,
                pressure=max(101325.0, pressure),
                temperature=293.15
            )
        
        # Update GL view and pressure scale
        self.gl_view.set_current_state(snapshot)
        self.pressure_scale.update_from_snapshot(snapshot)


def main():
    """Run P10 test"""
    app = QApplication(sys.argv)
    
    window = TestP10Window()
    window.show()
    
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
