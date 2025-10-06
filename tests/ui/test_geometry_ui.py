# -*- coding: utf-8 -*-
"""
Тесты для унификации параметров цилиндра (МШ-1)
Test unified cylinder parameters (MS-1)
"""
import sys
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ui.panels.panel_geometry import GeometryPanel


class TestCylinderUnification:
    """Тесты унификации параметров цилиндра"""
    
    @pytest.fixture
    def app(self):
        """Qt application fixture"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        # No app.quit() - causes issues with other tests
    
    @pytest.fixture
    def geometry_panel(self, app):
        """GeometryPanel fixture"""
        panel = GeometryPanel()
        yield panel
        panel.deleteLater()
    
    def test_old_parameters_removed(self, geometry_panel):
        """Проверить что старые раздельные параметры убраны"""
        panel = geometry_panel
        
        # Check that old widgets don't exist
        assert not hasattr(panel, 'bore_head_slider'), "bore_head_slider должен быть удалён"
        assert not hasattr(panel, 'bore_rod_slider'), "bore_rod_slider должен быть удалён"
        assert not hasattr(panel, 'piston_rod_length_slider'), "piston_rod_length_slider должен быть удалён"
        
        # Check that old parameters are not in defaults
        assert 'bore_head' not in panel.parameters, "bore_head не должно быть в параметрах"
        assert 'bore_rod' not in panel.parameters, "bore_rod не должно быть в параметрах"
        assert 'piston_rod_length' not in panel.parameters, "piston_rod_length не должно быть в параметрах"
    
    def test_new_parameters_present(self, geometry_panel):
        """Проверить что новые унифицированные параметры присутствуют"""
        panel = geometry_panel
        
        # Check that new widgets exist
        assert hasattr(panel, 'cyl_diam_slider'), "cyl_diam_slider должен существовать"
        assert hasattr(panel, 'stroke_slider'), "stroke_slider должен существовать"
        assert hasattr(panel, 'piston_thickness_slider'), "piston_thickness_slider должен существовать"
        assert hasattr(panel, 'dead_gap_slider'), "dead_gap_slider должен существовать"
        
        # Check that new parameters are in defaults
        required_params = ['cyl_diam_m', 'rod_diam_m', 'stroke_m', 'piston_thickness_m', 'dead_gap_m']
        for param in required_params:
            assert param in panel.parameters, f"{param} должен быть в параметрах"
    
    def test_si_units_and_steps(self, geometry_panel):
        """Проверить единицы СИ и шаг 0.001"""
        panel = geometry_panel
        
        # Test cylinder diameter
        cyl_slider = panel.cyl_diam_slider
        assert cyl_slider.step == 0.001, "Шаг cyl_diam_slider должен быть 0.001"
        assert cyl_slider.decimals == 3, "Decimals cyl_diam_slider должен быть 3"
        assert cyl_slider.units == "м", "Единицы cyl_diam_slider должны быть 'м'"
        
        # Test rod diameter
        rod_slider = panel.rod_diameter_slider
        assert rod_slider.step == 0.001, "Шаг rod_diameter_slider должен быть 0.001"
        assert rod_slider.decimals == 3, "Decimals rod_diameter_slider должен быть 3"
        assert rod_slider.units == "м", "Единицы rod_diameter_slider должны быть 'м'"
        
        # Test stroke
        stroke_slider = panel.stroke_slider
        assert stroke_slider.step == 0.001, "Шаг stroke_slider должен быть 0.001"
        assert stroke_slider.decimals == 3, "Decimals stroke_slider должен быть 3"
        assert stroke_slider.units == "м", "Единицы stroke_slider должны быть 'м'"
    
    def test_default_values_si(self, geometry_panel):
        """Проверить дефолтные значения в СИ"""
        panel = geometry_panel
        
        expected_defaults = {
            'cyl_diam_m': 0.080,    # 80mm -> 0.080m
            'rod_diam_m': 0.035,    # 35mm -> 0.035m
            'stroke_m': 0.300,      # 300mm -> 0.300m
            'piston_thickness_m': 0.020,  # 20mm -> 0.020m
            'dead_gap_m': 0.005,    # 5mm -> 0.005m
        }
        
        for param, expected_value in expected_defaults.items():
            actual_value = panel.parameters.get(param)
            assert actual_value == expected_value, f"{param}: ожидалось {expected_value}, получено {actual_value}"
    
    def test_parameter_ranges_valid(self, geometry_panel):
        """Проверить что диапазоны параметров валидны"""
        panel = geometry_panel
        
        # Cylinder diameter: 30-150mm -> 0.030-0.150m
        cyl_slider = panel.cyl_diam_slider
        assert cyl_slider.minimum == 0.030, "Минимум cyl_diam_slider должен быть 0.030"
        assert cyl_slider.maximum == 0.150, "Максимум cyl_diam_slider должен быть 0.150"
        
        # Rod diameter: 10-60mm -> 0.010-0.060m  
        rod_slider = panel.rod_diameter_slider
        assert rod_slider.minimum == 0.010, "Минимум rod_diameter_slider должен быть 0.010"
        assert rod_slider.maximum == 0.060, "Максимум rod_diameter_slider должен быть 0.060"
        
        # Stroke: 100-500mm -> 0.100-0.500m
        stroke_slider = panel.stroke_slider
        assert stroke_slider.minimum == 0.100, "Минимум stroke_slider должен быть 0.100"
        assert stroke_slider.maximum == 0.500, "Максимум stroke_slider должен быть 0.500"
    
    def test_hydraulic_constraint_validation(self, geometry_panel):
        """Проверить валидацию гидравлического ограничения"""
        panel = geometry_panel
        
        # Set rod diameter too large (>80% of cylinder)
        panel.parameters['cyl_diam_m'] = 0.080  # 80mm
        panel.parameters['rod_diam_m'] = 0.070  # 70mm (87.5% > 80%)
        
        # Check dependency validation
        conflict = panel._check_dependencies('rod_diam_m', 0.070, 0.035)
        
        assert conflict is not None, "Должен быть обнаружен конфликт"
        assert conflict['type'] == 'hydraulic_constraint', "Тип конфликта должен быть hydraulic_constraint"
        assert 'Диаметр штока слишком велик' in conflict['message'], "Сообщение должно содержать информацию о размере штока"
    
    def test_stroke_constraint_validation(self, geometry_panel):
        """Проверить валидацию ограничения хода"""
        panel = geometry_panel
        
        # Set stroke too large for cylinder length
        panel.parameters['cylinder_length'] = 0.400  # 400mm
        panel.parameters['stroke_m'] = 0.350  # 350mm
        panel.parameters['piston_thickness_m'] = 0.020  # 20mm
        panel.parameters['dead_gap_m'] = 0.005  # 5mm
        # Required: 350 + 20 + 2*5 = 380mm, but cylinder is only 400mm
        
        # Check dependency validation
        conflict = panel._check_dependencies('stroke_m', 0.350, 0.300)
        
        assert conflict is not None, "Должен быть обнаружен конфликт"
        assert conflict['type'] == 'geometric_constraint', "Тип конфликта должен быть geometric_constraint"
        assert 'длина цилиндра недостаточна' in conflict['message'].lower(), "Сообщение должно содержать информацию о длине"
    
    def test_3d_scene_parameters_conversion(self, geometry_panel):
        """Проверить конвертацию параметров для 3D сцены"""
        panel = geometry_panel
        
        # Set known values
        panel.parameters['cyl_diam_m'] = 0.080  # 80mm
        panel.parameters['rod_diam_m'] = 0.035  # 35mm
        panel.parameters['stroke_m'] = 0.300   # 300mm
        panel.parameters['piston_thickness_m'] = 0.020  # 20mm
        
        # Trigger parameter change to get 3D conversion
        geometry_3d_data = None
        
        def capture_geometry_3d(data):
            nonlocal geometry_3d_data
            geometry_3d_data = data
        
        panel.geometry_changed.connect(capture_geometry_3d)
        panel._on_parameter_changed('cyl_diam_m', 0.080)
        
        assert geometry_3d_data is not None, "Должны быть получены данные для 3D сцены"
        
        # Check conversions (m -> mm)
        assert geometry_3d_data['boreHead'] == 80.0, "boreHead должен быть 80.0 мм"
        assert geometry_3d_data['boreRod'] == 80.0, "boreRod должен быть 80.0 мм (унифицирован)"
        assert geometry_3d_data['rodDiameter'] == 35.0, "rodDiameter должен быть 35.0 мм"
        assert geometry_3d_data['pistonThickness'] == 20.0, "pistonThickness должен быть 20.0 мм"
        assert geometry_3d_data['strokeLength'] == 300.0, "strokeLength должен быть 300.0 мм"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])