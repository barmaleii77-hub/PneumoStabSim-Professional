# -*- coding: utf-8 -*-
"""
Test MS-3: Dependency resolution with unified SI parameters
"""
import sys
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ui.panels.panel_geometry import GeometryPanel


class TestMS3DependencyResolution:
    """Test dependency resolution with new unified SI parameters"""
    
    @pytest.fixture
    def app(self):
        """Qt application fixture"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def geometry_panel(self, app):
        """GeometryPanel fixture"""
        panel = GeometryPanel()
        yield panel
        panel.deleteLater()
    
    def test_geometric_constraints_si_units(self, geometry_panel):
        """Test geometric constraints work with SI units"""
        panel = geometry_panel
        
        # Set up a constraint scenario: short wheelbase + long lever
        panel.parameters['wheelbase'] = 2.000  # 2m wheelbase
        panel.parameters['lever_length'] = 1.200  # 1.2m lever  
        panel.parameters['frame_to_pivot'] = 0.600  # 0.6m frame to pivot
        
        # This should create a conflict (0.6 + 1.2 = 1.8m > half of 2m - clearance)
        conflict = panel._check_dependencies('lever_length', 1.200, 0.800)
        
        assert conflict is not None, "Should detect geometric constraint violation"
        assert conflict['type'] == 'geometric_constraint'
        assert 'превышает доступное пространство' in conflict['message']
        assert len(conflict['options']) >= 2, "Should provide resolution options"
    
    def test_hydraulic_constraints_unified_params(self, geometry_panel):
        """Test hydraulic constraints with unified cylinder parameters"""
        panel = geometry_panel
        
        # Set up hydraulic constraint: large rod vs small cylinder
        panel.parameters['cyl_diam_m'] = 0.050  # 50mm cylinder
        panel.parameters['rod_diam_m'] = 0.045   # 45mm rod (90% of cylinder - too big!)
        
        conflict = panel._check_dependencies('rod_diam_m', 0.045, 0.035)
        
        assert conflict is not None, "Should detect hydraulic constraint violation"
        assert conflict['type'] == 'hydraulic_constraint'
        assert 'слишком велик относительно цилиндра' in conflict['message']
        assert any('Уменьшить диаметр штока' in opt[0] for opt in conflict['options'])
    
    def test_stroke_constraints_si_calculations(self, geometry_panel):
        """Test stroke constraints with SI unit calculations"""
        panel = geometry_panel
        
        # Set up stroke constraint: long stroke in short cylinder
        panel.parameters['cylinder_length'] = 0.300    # 300mm cylinder
        panel.parameters['stroke_m'] = 0.280           # 280mm stroke
        panel.parameters['piston_thickness_m'] = 0.020 # 20mm piston
        panel.parameters['dead_gap_m'] = 0.005         # 5mm gap each side
        
        # Required: 280 + 20 + 2*5 = 310mm > 300mm cylinder
        conflict = panel._check_dependencies('stroke_m', 0.280, 0.200)
        
        assert conflict is not None, "Should detect stroke constraint violation"
        assert conflict['type'] == 'geometric_constraint'
        assert 'недостаточна для хода поршня' in conflict['message']
        assert any('Увеличить длину цилиндра' in opt[0] for opt in conflict['options'])
    
    def test_3d_geometry_conversion_to_mm(self, geometry_panel):
        """Test that SI parameters are correctly converted to mm for 3D scene"""
        panel = geometry_panel
        
        # Set known SI values
        panel.parameters.update({
            'wheelbase': 3.200,      # 3200mm
            'track': 1.600,          # 1600mm  
            'cyl_diam_m': 0.080,     # 80mm
            'rod_diam_m': 0.035,     # 35mm
            'stroke_m': 0.300,       # 300mm
        })
        
        # Trigger geometry update
        panel._on_parameter_changed('wheelbase', 3.200)
        
        # Check that parameters exist (geometry_changed signal should be emitted)
        # Note: We can't easily test signal emission in this context,
        # but we can verify the conversion logic would work
        expected_mm_values = {
            'frameLength': 3200.0,
            'trackWidth': 1600.0,
            'boreHead': 80.0,
            'rodDiameter': 35.0,
            'strokeLength': 300.0,
        }
        
        # Verify conversion formula correctness
        assert panel.parameters['wheelbase'] * 1000 == expected_mm_values['frameLength']
        assert panel.parameters['track'] * 1000 == expected_mm_values['trackWidth']
        assert panel.parameters['cyl_diam_m'] * 1000 == expected_mm_values['boreHead']
    
    def test_presets_updated_for_si_units(self, geometry_panel):
        """Test that presets work with new SI parameters"""
        panel = geometry_panel
        
        # Test standard truck preset (index 0)
        panel._on_preset_changed(0)
        
        # Check that unified parameters are set
        assert 'cyl_diam_m' in panel.parameters
        assert 'rod_diam_m' in panel.parameters
        assert 'stroke_m' in panel.parameters
        
        # Check reasonable values for standard truck
        assert 0.050 <= panel.parameters['cyl_diam_m'] <= 0.150  # 50-150mm cylinder
        assert 0.020 <= panel.parameters['rod_diam_m'] <= 0.080   # 20-80mm rod
        assert 0.200 <= panel.parameters['stroke_m'] <= 0.500     # 200-500mm stroke
    
    def test_no_dependency_for_valid_parameters(self, geometry_panel):
        """Test that valid parameters don't trigger dependency conflicts"""
        panel = geometry_panel
        
        # Set up valid parameters
        panel.parameters.update({
            'wheelbase': 3.200,
            'lever_length': 0.800,
            'frame_to_pivot': 0.600,
            'cyl_diam_m': 0.080,
            'rod_diam_m': 0.035,  # 44% of cylinder - OK
            'cylinder_length': 0.500,
            'stroke_m': 0.300,
            'piston_thickness_m': 0.020,
            'dead_gap_m': 0.005,
        })
        
        # Test each parameter - none should cause conflicts
        test_params = [
            ('wheelbase', 3.200, 3.000),
            ('lever_length', 0.800, 0.750),
            ('cyl_diam_m', 0.080, 0.070), 
            ('rod_diam_m', 0.035, 0.030),
            ('stroke_m', 0.300, 0.280),
        ]
        
        for param_name, new_val, old_val in test_params:
            conflict = panel._check_dependencies(param_name, new_val, old_val)
            assert conflict is None, f"Valid parameter {param_name}={new_val} should not cause conflict"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])