# -*- coding: utf-8 -*-
"""
Тесты для единиц СИ и шага 0.001м (МШ-2)
"""
import sys
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ui.panels.panel_geometry import GeometryPanel


class TestSIUnitsAndSteps:
    """Тесты приведения всех линейных параметров к СИ и шагу 0.001м"""
    
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
    
    def test_frame_dimensions_si_units(self, geometry_panel):
        """Test frame dimensions in SI units"""
        panel = geometry_panel
        
        # Test wheelbase slider
        wheelbase_slider = panel.wheelbase_slider
        assert wheelbase_slider.units == "м"
        assert wheelbase_slider.step == 0.001
        assert wheelbase_slider.decimals == 3
        
        # Test track slider
        track_slider = panel.track_slider
        assert track_slider.units == "м"
        assert track_slider.step == 0.001
        assert track_slider.decimals == 3
    
    def test_suspension_geometry_si_units(self, geometry_panel):
        """Test suspension geometry in SI units"""
        panel = geometry_panel
        
        # Test frame_to_pivot slider
        frame_to_pivot_slider = panel.frame_to_pivot_slider
        assert frame_to_pivot_slider.units == "м"
        assert frame_to_pivot_slider.step == 0.001
        assert frame_to_pivot_slider.decimals == 3
        
        # Test lever_length slider
        lever_length_slider = panel.lever_length_slider
        assert lever_length_slider.units == "м"
        assert lever_length_slider.step == 0.001
        assert lever_length_slider.decimals == 3
    
    def test_default_values_precision(self, geometry_panel):
        """Test default values have correct precision"""
        panel = geometry_panel
        
        # Check key default values
        expected_defaults = {
            'wheelbase': 3.200,
            'track': 1.600,
            'frame_to_pivot': 0.600,
            'lever_length': 0.800,
            'rod_position': 0.600,
            'additional_param_1': 0.050,  # New parameter
            'additional_param_2': 1.250,  # New parameter
        }
        
        for param, expected_value in expected_defaults.items():
            actual_value = panel.parameters.get(param)
            assert actual_value == expected_value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
