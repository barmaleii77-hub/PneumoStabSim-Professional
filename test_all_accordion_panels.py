# -*- coding: utf-8 -*-
"""
Test all accordion panels together
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

from src.ui.accordion import AccordionWidget
from src.ui.panels_accordion import (
    GeometryPanelAccordion,
    PneumoPanelAccordion,
    SimulationPanelAccordion,
    RoadPanelAccordion,
    AdvancedPanelAccordion
)


class TestAccordionPanels(QMainWindow):
    """Test window for all accordion panels"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Test: All Accordion Panels")
        self.resize(450, 900)
        
        # Create accordion
        accordion = AccordionWidget()
        
        # === GEOMETRY SECTION ===
        geometry_panel = GeometryPanelAccordion()
        geometry_panel.parameter_changed.connect(
            lambda name, value: print(f"[GEOMETRY] {name} = {value}")
        )
        accordion.add_section("geometry", "Geometry", geometry_panel, expanded=True)
        
        # === PNEUMATICS SECTION ===
        pneumo_panel = PneumoPanelAccordion()
        pneumo_panel.parameter_changed.connect(
            lambda name, value: print(f"[PNEUMO] {name} = {value}")
        )
        pneumo_panel.thermo_mode_changed.connect(
            lambda mode: print(f"[PNEUMO] Thermo mode = {mode}")
        )
        accordion.add_section("pneumo", "Pneumatics", pneumo_panel, expanded=False)
        
        # === SIMULATION SECTION ===
        sim_panel = SimulationPanelAccordion()
        sim_panel.sim_mode_changed.connect(
            lambda mode: print(f"[SIMULATION] Mode = {mode}")
        )
        sim_panel.option_changed.connect(
            lambda name, enabled: print(f"[SIMULATION] {name} = {enabled}")
        )
        sim_panel.parameter_changed.connect(
            lambda name, value: print(f"[SIMULATION] {name} = {value}")
        )
        accordion.add_section("simulation", "Simulation", sim_panel, expanded=False)
        
        # === ROAD SECTION ===
        road_panel = RoadPanelAccordion()
        road_panel.road_mode_changed.connect(
            lambda mode: print(f"[ROAD] Mode = {mode}")
        )
        road_panel.profile_type_changed.connect(
            lambda ptype: print(f"[ROAD] Profile type = {ptype}")
        )
        road_panel.parameter_changed.connect(
            lambda name, value: print(f"[ROAD] {name} = {value}")
        )
        accordion.add_section("road", "Road Input", road_panel, expanded=False)
        
        # === ADVANCED SECTION ===
        advanced_panel = AdvancedPanelAccordion()
        advanced_panel.parameter_changed.connect(
            lambda name, value: print(f"[ADVANCED] {name} = {value}")
        )
        accordion.add_section("advanced", "Advanced", advanced_panel, expanded=False)
        
        self.setCentralWidget(accordion)
        
        print("\n" + "="*60)
        print("ALL ACCORDION PANELS TEST")
        print("="*60)
        print("\nSections:")
        print("  1. Geometry (expanded)")
        print("     - Basic dimensions (wheelbase, track)")
        print("     - Lever geometry")
        print("     - Cylinder geometry")
        print("     - Masses")
        print("\n  2. Pneumatics")
        print("     - Thermo mode (isothermal/adiabatic)")
        print("     - Cylinder volumes (calculated)")
        print("     - Line pressures (A1, B1, A2, B2)")
        print("     - Tank/relief pressures")
        print("     - Temperature")
        print("\n  3. Simulation")
        print("     - Mode (kinematics/dynamics)")
        print("     - Kinematic options (springs/dampers)")
        print("     - Interference check")
        print("     - Timing (dt, speed)")
        print("\n  4. Road Input")
        print("     - Mode (manual/profile)")
        print("     - Manual: amplitude, frequency, phase")
        print("     - Profile: type, avg speed")
        print("\n  5. Advanced")
        print("     - Suspension (spring, damper)")
        print("     - Dead zones")
        print("     - Graphics settings")
        print("\n" + "="*60 + "\n")
        print("Try:")
        print("  - Click section headers to expand/collapse")
        print("  - Adjust sliders")
        print("  - Change modes/options")
        print("  - All changes logged to console")
        print("\n" + "="*60 + "\n")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = TestAccordionPanels()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
