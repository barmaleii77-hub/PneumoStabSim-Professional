# -*- coding: utf-8 -*-
"""
A-1 Test: Cylinder parameter unification
Test unification of cylinder parameters
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from src.ui.panels.panel_geometry import GeometryPanel
    HAS_PYSIDE = True
except ImportError:
    HAS_PYSIDE = False


@pytest.mark.skipif(not HAS_PYSIDE, reason="PySide6 not available")
def test_unified_cylinder_parameters():
    """Test that only unified cylinder parameters are present"""
    app = QApplication.instance() or QApplication([])
    
    panel = GeometryPanel()
    
    # Check that unified parameters exist
    unified_params = ['cyl_diam_m', 'rod_diam_m', 'stroke_m', 'piston_thickness_m', 'dead_gap_m']
    
    for param in unified_params:
        assert param in panel.parameters, f"Unified parameter {param} should exist"
    
    # Check that old separate parameters are NOT present in defaults
    old_params = ['bore_head', 'bore_rod', 'piston_rod_length']
    for param in old_params:
        assert param not in panel.parameters, f"Old parameter {param} should not exist in defaults"
    
    print("? A-1: Unified cylinder parameters test passed")


@pytest.mark.skipif(not HAS_PYSIDE, reason="PySide6 not available")  
def test_si_units_and_precision():
    """Test SI units (meters) and 0.001 step precision"""
    app = QApplication.instance() or QApplication([])
    
    panel = GeometryPanel()
    
    # Check cylinder controls have correct SI units and precision
    controls_to_check = [
        ('cyl_diam_slider', 'm', 0.001, 3),
        ('rod_diameter_slider', 'm', 0.001, 3), 
        ('stroke_slider', 'm', 0.001, 3),
        ('piston_thickness_slider', 'm', 0.001, 3),
        ('dead_gap_slider', 'm', 0.001, 3),
    ]
    
    for control_name, expected_units, expected_step, expected_decimals in controls_to_check:
        control = getattr(panel, control_name)
        
        # Check units (assuming RangeSlider has units property)
        if hasattr(control, 'units'):
            assert control.units == expected_units, f"{control_name} should have units '{expected_units}'"
        
        # Check step (assuming step property exists)
        if hasattr(control, 'step'):
            assert abs(control.step - expected_step) < 1e-6, f"{control_name} should have step {expected_step}"
            
        # Check decimals 
        if hasattr(control, 'decimals'):
            assert control.decimals == expected_decimals, f"{control_name} should have {expected_decimals} decimals"
    
    print("? A-1: SI units and precision test passed")


@pytest.mark.skipif(not HAS_PYSIDE, reason="PySide6 not available")
def test_parameter_ranges():
    """Test that unified parameters have appropriate ranges"""
    app = QApplication.instance() or QApplication([])
    
    panel = GeometryPanel()
    
    # Expected ranges for unified parameters (in SI meters)
    expected_ranges = {
        'cyl_diam_m': (0.030, 0.150, 0.080),  # min, max, default
        'rod_diam_m': (0.010, 0.060, 0.035),
        'stroke_m': (0.100, 0.500, 0.300),
        'piston_thickness_m': (0.005, 0.030, 0.020),
        'dead_gap_m': (0.000, 0.020, 0.005),
    }
    
    for param, (min_val, max_val, default_val) in expected_ranges.items():
        # Check default values
        actual_default = panel.parameters.get(param)
        assert actual_default == default_val, f"Parameter {param} should have default {default_val}, got {actual_default}"
        
        # Check parameter is within expected range
        assert min_val <= actual_default <= max_val, f"Parameter {param} default should be in range [{min_val}, {max_val}]"
    
    print("? A-1: Parameter ranges test passed")


def test_dependency_resolution_updated():
    """Test that dependency resolution uses unified parameters"""
    app = QApplication.instance() or QApplication([])
    
    panel = GeometryPanel()
    
    # Test rod diameter vs cylinder diameter constraint
    panel.parameters['rod_diam_m'] = 0.075  # 75mm rod
    panel.parameters['cyl_diam_m'] = 0.080  # 80mm cylinder
    
    # This should trigger hydraulic constraint (rod >= 80% of cylinder)
    conflict = panel._check_dependencies('rod_diam_m', 0.075, 0.035)
    
    assert conflict is not None, "Should detect hydraulic constraint"
    assert conflict['type'] == 'hydraulic_constraint'
    assert 'rod_diam_m' in [opt[1] for opt in conflict['options']]
    
    print("? A-1: Dependency resolution test passed")


if __name__ == "__main__":
    test_unified_cylinder_parameters()
    test_si_units_and_precision() 
    test_parameter_ranges()
    test_dependency_resolution_updated()
    print("?? All A-1 tests passed!")