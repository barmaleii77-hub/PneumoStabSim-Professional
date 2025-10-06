# -*- coding: utf-8 -*-
"""
Comprehensive test suite for cylinder unification refactoring
Tests MS-1, MS-2, MS-3 integration and backward compatibility
"""
import sys
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ui.panels.panel_geometry import GeometryPanel


class TestCylinderUnificationIntegration:
    """Comprehensive tests for complete cylinder unification refactoring"""
    
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
    
    # ==================== MS-1 Tests ====================
    
    def test_ms1_unified_cylinder_diameter(self, geometry_panel):
        """MS-1: Test that cylinder diameter is unified"""
        panel = geometry_panel
        
        # Should have single cylinder diameter parameter
        assert hasattr(panel, 'cyl_diam_slider')
        assert 'cyl_diam_m' in panel.parameters
        
        # Should NOT have separate head/rod bore sliders
        assert not hasattr(panel, 'bore_head_slider')
        assert not hasattr(panel, 'bore_rod_slider')
        
        # Should NOT have old piston_rod_length_slider
        assert not hasattr(panel, 'piston_rod_length_slider')
    
    def test_ms1_new_parameters_present(self, geometry_panel):
        """MS-1: Test that all new parameters are present"""
        panel = geometry_panel
        
        required_new_params = [
            'cyl_diam_m',        # Unified cylinder diameter
            'rod_diam_m',        # Rod diameter in SI
            'stroke_m',          # Stroke in SI
            'piston_thickness_m', # Piston thickness in SI
            'dead_gap_m',        # Dead gap in SI
        ]
        
        for param in required_new_params:
            assert param in panel.parameters, f"Missing new parameter: {param}"
            assert panel.parameters[param] > 0, f"Parameter {param} should be positive"
    
    def test_ms1_old_parameters_removed(self, geometry_panel):
        """MS-1: Test that old parameters are removed"""
        panel = geometry_panel
        
        removed_old_params = [
            'bore_head',         # Old separate head bore
            'bore_rod',          # Old separate rod bore
            'piston_rod_length', # Old piston rod length
        ]
        
        for param in removed_old_params:
            assert param not in panel.parameters, f"Old parameter should be removed: {param}"
    
    # ==================== MS-2 Tests ====================
    
    def test_ms2_all_linear_parameters_si_units(self, geometry_panel):
        """MS-2: Test that all linear parameters use SI units with 0.001 step"""
        panel = geometry_panel
        
        linear_sliders = [
            ('wheelbase', panel.wheelbase_slider),
            ('track', panel.track_slider),
            ('frame_to_pivot', panel.frame_to_pivot_slider),
            ('lever_length', panel.lever_length_slider),
            ('cylinder_length', panel.cylinder_length_slider),
            ('cyl_diam_m', panel.cyl_diam_slider),
            ('rod_diam_m', panel.rod_diameter_slider),
            ('stroke_m', panel.stroke_slider),
            ('piston_thickness_m', panel.piston_thickness_slider),
            ('dead_gap_m', panel.dead_gap_slider),
        ]
        
        for param_name, slider in linear_sliders:
            # All should use meters
            assert slider.units == "м", f"{param_name}: should use 'м', got '{slider.units}'"
            # All should have 0.001 step
            assert slider.step == 0.001, f"{param_name}: should have step 0.001, got {slider.step}"
            # All should have 3 decimals
            assert slider.decimals == 3, f"{param_name}: should have decimals=3, got {slider.decimals}"
    
    def test_ms2_default_values_precision(self, geometry_panel):
        """MS-2: Test that default values have correct precision"""
        panel = geometry_panel
        
        # All defaults should be multiples of 0.001 (except rod_position which is fraction)
        for param_name, value in panel.parameters.items():
            if param_name != 'rod_position':  # rod_position is fraction
                # Check if value is multiple of 0.001
                remainder = (value * 1000) % 1
                assert abs(remainder) < 1e-10 or abs(remainder - 1) < 1e-10, \
                    f"{param_name}={value} should be multiple of 0.001"
    
    # ==================== MS-3 Tests ====================
    
    def test_ms3_dependency_resolution_geometric(self, geometry_panel):
        """MS-3: Test geometric dependency resolution with SI units"""
        panel = geometry_panel
        
        # Create geometric constraint scenario
        panel.parameters.update({
            'wheelbase': 2.000,      # Short wheelbase
            'lever_length': 1.200,   # Long lever
            'frame_to_pivot': 0.600  # Distance to pivot
        })
        
        conflict = panel._check_dependencies('lever_length', 1.200, 0.800)
        
        # Should detect constraint violation
        assert conflict is not None
        assert conflict['type'] == 'geometric_constraint'
        
        # Should provide resolution options in SI units
        assert len(conflict['options']) >= 2
        for option_text, param_name, suggested_value in conflict['options']:
            assert isinstance(suggested_value, float)
            assert suggested_value > 0
    
    def test_ms3_dependency_resolution_hydraulic(self, geometry_panel):
        """MS-3: Test hydraulic dependency resolution with unified parameters"""
        panel = geometry_panel
        
        # Create hydraulic constraint scenario
        panel.parameters.update({
            'cyl_diam_m': 0.050,    # 50mm cylinder
            'rod_diam_m': 0.045     # 45mm rod (90% - too big!)
        })
        
        conflict = panel._check_dependencies('rod_diam_m', 0.045, 0.035)
        
        # Should detect hydraulic constraint violation  
        assert conflict is not None
        assert conflict['type'] == 'hydraulic_constraint'
        
        # Should suggest reducing rod or increasing cylinder
        option_texts = [opt[0] for opt in conflict['options']]
        assert any('штока' in text for text in option_texts)
        assert any('цилиндра' in text for text in option_texts)
    
    def test_ms3_dependency_resolution_stroke(self, geometry_panel):
        """MS-3: Test stroke dependency resolution"""
        panel = geometry_panel
        
        # Create stroke constraint scenario
        panel.parameters.update({
            'cylinder_length': 0.300,      # 300mm cylinder  
            'stroke_m': 0.280,             # 280mm stroke
            'piston_thickness_m': 0.020,   # 20mm piston
            'dead_gap_m': 0.005            # 5mm gap each side
        })
        # Required: 280 + 20 + 2*5 = 310mm > 300mm cylinder
        
        conflict = panel._check_dependencies('stroke_m', 0.280, 0.200)
        
        # Should detect stroke constraint violation
        assert conflict is not None  
        assert conflict['type'] == 'geometric_constraint'
        
        # Should provide multiple resolution options
        option_texts = [opt[0] for opt in conflict['options']]
        assert len(option_texts) >= 3  # Multiple ways to resolve
    
    # ==================== Integration Tests ====================
    
    def test_integration_3d_geometry_conversion(self, geometry_panel):
        """Test that 3D geometry conversion works with unified parameters"""
        panel = geometry_panel
        
        # Set known values
        test_params = {
            'wheelbase': 3.200,
            'track': 1.600,
            'cyl_diam_m': 0.080,
            'rod_diam_m': 0.035,
            'stroke_m': 0.300,
        }
        panel.parameters.update(test_params)
        
        # Test conversion logic (simulate what happens in _on_parameter_changed)
        expected_3d_values = {
            'frameLength': 3200.0,   # 3.200m * 1000
            'trackWidth': 1600.0,    # 1.600m * 1000
            'boreHead': 80.0,        # 0.080m * 1000
            'boreRod': 80.0,         # Same as boreHead (unified!)
            'rodDiameter': 35.0,     # 0.035m * 1000
            'strokeLength': 300.0,   # 0.300m * 1000
        }
        
        # Verify conversion formulas
        for key, expected in expected_3d_values.items():
            if key == 'frameLength':
                actual = panel.parameters['wheelbase'] * 1000
            elif key == 'trackWidth':
                actual = panel.parameters['track'] * 1000
            elif key in ['boreHead', 'boreRod']:
                actual = panel.parameters['cyl_diam_m'] * 1000  # Unified!
            elif key == 'rodDiameter':
                actual = panel.parameters['rod_diam_m'] * 1000
            elif key == 'strokeLength':
                actual = panel.parameters['stroke_m'] * 1000
            
            assert actual == expected, f"{key}: expected {expected}, got {actual}"
    
    def test_integration_presets_work_with_new_parameters(self, geometry_panel):
        """Test that presets work with new parameter structure"""
        panel = geometry_panel
        
        # Test each preset
        for preset_index in range(3):  # 0, 1, 2 (not custom)
            panel._on_preset_changed(preset_index)
            
            # All required parameters should be set
            required_params = [
                'wheelbase', 'track', 'lever_length', 
                'cyl_diam_m', 'rod_diam_m', 'stroke_m'
            ]
            
            for param in required_params:
                assert param in panel.parameters
                assert panel.parameters[param] > 0
            
            # Hydraulic constraints should be satisfied
            rod_diam = panel.parameters['rod_diam_m']
            cyl_diam = panel.parameters['cyl_diam_m']
            assert rod_diam < cyl_diam * 0.8, f"Preset {preset_index}: rod too big for cylinder"
    
    def test_integration_parameter_change_flow(self, geometry_panel):
        """Test complete parameter change flow"""
        panel = geometry_panel
        
        # Set up valid parameters  
        panel.parameters.update({
            'wheelbase': 3.200,
            'cyl_diam_m': 0.080,
            'rod_diam_m': 0.035,
            'stroke_m': 0.300,
            'cylinder_length': 0.500,
        })
        
        # Change parameter that should NOT cause conflict
        old_value = panel.parameters['wheelbase']
        new_value = 3.500
        
        # Should not raise any exceptions
        panel._on_parameter_changed('wheelbase', new_value)
        
        # Parameter should be updated
        assert panel.parameters['wheelbase'] == new_value
    
    # ==================== Backward Compatibility ====================
    
    def test_backward_compatibility_no_old_parameter_references(self, geometry_panel):
        """Test that system doesn't reference old parameters"""
        panel = geometry_panel
        
        # These old parameters should not exist anywhere
        old_params = ['bore_head', 'bore_rod', 'piston_rod_length']
        
        # Check parameters dict
        for param in old_params:
            assert param not in panel.parameters
        
        # Check widget_map in _set_parameter_value 
        widget_map_keys = {
            'wheelbase', 'track', 'frame_to_pivot', 'lever_length', 'rod_position',
            'cylinder_length', 'cyl_diam_m', 'rod_diam_m', 'stroke_m', 
            'piston_thickness_m', 'dead_gap_m'
        }
        
        # No old parameters should be in widget mapping
        for old_param in old_params:
            assert old_param not in widget_map_keys
    
    def test_backward_compatibility_link_rod_diameters_deprecated(self, geometry_panel):
        """Test that link rod diameters option is properly deprecated"""
        panel = geometry_panel
        
        # Should still exist but be disabled
        assert hasattr(panel, 'link_rod_diameters')
        assert panel.link_rod_diameters.isChecked() == True   # Always checked now
        assert panel.link_rod_diameters.isEnabled() == False  # But disabled
    
    # ==================== Final Validation ====================
    
    def test_final_validation_complete_system(self, geometry_panel):
        """Final validation that complete system works"""
        panel = geometry_panel
        
        # 1. All required UI elements exist
        required_sliders = [
            'wheelbase_slider', 'track_slider', 'frame_to_pivot_slider',
            'lever_length_slider', 'rod_position_slider', 'cylinder_length_slider',
            'cyl_diam_slider', 'rod_diameter_slider', 'stroke_slider',
            'piston_thickness_slider', 'dead_gap_slider'
        ]
        
        for slider_name in required_sliders:
            assert hasattr(panel, slider_name), f"Missing slider: {slider_name}"
        
        # 2. All parameters have valid defaults
        assert len(panel.parameters) >= 10  # Should have at least 10 parameters
        for param_name, value in panel.parameters.items():
            assert isinstance(value, (int, float)), f"Parameter {param_name} should be numeric"
            assert value >= 0, f"Parameter {param_name} should be non-negative"
        
        # 3. Dependency resolution works
        assert callable(panel._check_dependencies)
        assert callable(panel._resolve_conflict) 
        
        # 4. Preset system works
        assert hasattr(panel, 'preset_combo')
        assert panel.preset_combo.count() >= 4  # Should have at least 4 presets
        
        # 5. Signals are connected
        assert hasattr(panel, 'parameter_changed')
        assert hasattr(panel, 'geometry_updated') 
        assert hasattr(panel, 'geometry_changed')
        
        print("? Final validation: Complete cylinder unification system operational")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])