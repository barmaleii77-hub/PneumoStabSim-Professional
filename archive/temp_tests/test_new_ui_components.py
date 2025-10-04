# -*- coding: utf-8 -*-
"""
Test new UI components - Accordion and ParameterSlider
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from src.ui.accordion import AccordionWidget
from src.ui.parameter_slider import ParameterSlider


class TestWindow(QMainWindow):
    """Test window for new UI components"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Test: Accordion + ParameterSlider")
        self.resize(400, 800)
        
        # Create accordion
        accordion = AccordionWidget()
        
        # === SECTION 1: Geometry ===
        geometry_content = QWidget()
        geometry_layout = QVBoxLayout(geometry_content)
        geometry_layout.setSpacing(4)
        
        # Wheelbase
        wheelbase_slider = ParameterSlider(
            name="Wheelbase (L)",
            initial_value=3.0,
            min_value=2.0,
            max_value=5.0,
            step=0.01,
            decimals=3,
            unit="m",
            allow_range_edit=True
        )
        wheelbase_slider.value_changed.connect(
            lambda v: print(f"Wheelbase changed: {v:.3f} m")
        )
        geometry_layout.addWidget(wheelbase_slider)
        
        # Track width
        track_slider = ParameterSlider(
            name="Track Width (B)",
            initial_value=1.8,
            min_value=1.0,
            max_value=2.5,
            step=0.01,
            decimals=3,
            unit="m",
            allow_range_edit=True
        )
        track_slider.value_changed.connect(
            lambda v: print(f"Track width changed: {v:.3f} m")
        )
        geometry_layout.addWidget(track_slider)
        
        # Lever arm
        lever_slider = ParameterSlider(
            name="Lever Arm (r)",
            initial_value=0.3,
            min_value=0.1,
            max_value=0.6,
            step=0.001,
            decimals=3,
            unit="m",
            allow_range_edit=True
        )
        lever_slider.value_changed.connect(
            lambda v: print(f"Lever arm changed: {v:.3f} m")
        )
        geometry_layout.addWidget(lever_slider)
        
        accordion.add_section("geometry", "Geometry", geometry_content, expanded=True)
        
        # === SECTION 2: Pneumatics ===
        pneumo_content = QWidget()
        pneumo_layout = QVBoxLayout(pneumo_content)
        pneumo_layout.setSpacing(4)
        
        # Cylinder head volume
        vol_head_slider = ParameterSlider(
            name="Head Volume (V_h)",
            initial_value=500.0,
            min_value=100.0,
            max_value=1000.0,
            step=10.0,
            decimals=1,
            unit="cm?",
            allow_range_edit=True
        )
        vol_head_slider.value_changed.connect(
            lambda v: print(f"Head volume changed: {v:.1f} cm?")
        )
        pneumo_layout.addWidget(vol_head_slider)
        
        # Cylinder rod volume
        vol_rod_slider = ParameterSlider(
            name="Rod Volume (V_r)",
            initial_value=300.0,
            min_value=50.0,
            max_value=800.0,
            step=10.0,
            decimals=1,
            unit="cm?",
            allow_range_edit=True
        )
        vol_rod_slider.value_changed.connect(
            lambda v: print(f"Rod volume changed: {v:.1f} cm?")
        )
        pneumo_layout.addWidget(vol_rod_slider)
        
        # Line pressure
        pressure_slider = ParameterSlider(
            name="Line Pressure",
            initial_value=150.0,
            min_value=50.0,
            max_value=500.0,
            step=5.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True
        )
        pressure_slider.value_changed.connect(
            lambda v: print(f"Line pressure changed: {v:.1f} kPa")
        )
        pneumo_layout.addWidget(pressure_slider)
        
        # Tank pressure
        tank_slider = ParameterSlider(
            name="Tank Pressure",
            initial_value=200.0,
            min_value=100.0,
            max_value=600.0,
            step=10.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True
        )
        tank_slider.value_changed.connect(
            lambda v: print(f"Tank pressure changed: {v:.1f} kPa")
        )
        pneumo_layout.addWidget(tank_slider)
        
        accordion.add_section("pneumo", "Pneumatics", pneumo_content, expanded=False)
        
        # === SECTION 3: Simulation ===
        sim_content = QWidget()
        sim_layout = QVBoxLayout(sim_content)
        sim_layout.setSpacing(4)
        
        # Time step
        dt_slider = ParameterSlider(
            name="Time Step (dt)",
            initial_value=0.001,
            min_value=0.0001,
            max_value=0.01,
            step=0.0001,
            decimals=4,
            unit="s",
            allow_range_edit=True
        )
        dt_slider.value_changed.connect(
            lambda v: print(f"Time step changed: {v:.4f} s")
        )
        sim_layout.addWidget(dt_slider)
        
        # Simulation speed
        speed_slider = ParameterSlider(
            name="Simulation Speed",
            initial_value=1.0,
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            decimals=1,
            unit="x",
            allow_range_edit=True
        )
        speed_slider.value_changed.connect(
            lambda v: print(f"Simulation speed changed: {v:.1f}x")
        )
        sim_layout.addWidget(speed_slider)
        
        accordion.add_section("simulation", "Simulation", sim_content, expanded=False)
        
        # === SECTION 4: Advanced ===
        advanced_content = QWidget()
        advanced_layout = QVBoxLayout(advanced_content)
        advanced_layout.setSpacing(4)
        
        # Spring stiffness
        spring_slider = ParameterSlider(
            name="Spring Stiffness (k)",
            initial_value=50000.0,
            min_value=10000.0,
            max_value=200000.0,
            step=1000.0,
            decimals=0,
            unit="N/m",
            allow_range_edit=True
        )
        spring_slider.value_changed.connect(
            lambda v: print(f"Spring stiffness changed: {v:.0f} N/m")
        )
        advanced_layout.addWidget(spring_slider)
        
        # Damper coefficient
        damper_slider = ParameterSlider(
            name="Damper Coeff (c)",
            initial_value=2000.0,
            min_value=500.0,
            max_value=10000.0,
            step=100.0,
            decimals=0,
            unit="N*s/m",  # Fixed encoding
            allow_range_edit=True
        )
        damper_slider.value_changed.connect(
            lambda v: print(f"Damper coefficient changed: {v:.0f} N*s/m")
        )
        advanced_layout.addWidget(damper_slider)
        
        accordion.add_section("advanced", "Advanced", advanced_content, expanded=False)
        
        # Set as central widget
        self.setCentralWidget(accordion)
        
        print("\n" + "="*60)
        print("TEST WINDOW READY")
        print("="*60)
        print("\nFeatures:")
        print("  - Click section headers to expand/collapse")
        print("  - Drag sliders to change values")
        print("  - Edit spinboxes for precise input")
        print("  - Adjust min/max ranges at the bottom of each slider")
        print("  - All changes printed to console")
        print("\nSections:")
        print("  1. Geometry (expanded by default)")
        print("  2. Pneumatics")
        print("  3. Simulation")
        print("  4. Advanced")
        print("\n" + "="*60 + "\n")


def main():
    app = QApplication(sys.argv)
    
    # Dark theme
    app.setStyle("Fusion")
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
