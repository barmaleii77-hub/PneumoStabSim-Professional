# -*- coding: utf-8 -*-
"""
UI Panel Functionality Tests - PROMPT #1 Validation
Tests for panel signal emissions and parameter handling
“есты функциональности панелей и обработки параметров
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSignalSpy
import sys

from src.ui.panels.panel_geometry import GeometryPanel
from src.ui.panels.panel_pneumo import PneumoPanel


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def geometry_panel(qapp):
    """Create standalone GeometryPanel for testing"""
    panel = GeometryPanel()
    yield panel


@pytest.fixture
def pneumo_panel(qapp):
    """Create standalone PneumoPanel for testing"""
    panel = PneumoPanel()
    yield panel


# ============================================================================
# GEOMETRY PANEL FUNCTIONALITY TESTS
# ============================================================================

class TestGeometryPanelFunctionality:
    """Test GeometryPanel parameter handling and signals"""
    
    def test_default_parameters_loaded(self, geometry_panel):
        """Verify default parameters are set correctly"""
        params = geometry_panel.get_parameters()
        
        # Check key parameters exist
        assert 'wheelbase' in params, "wheelbase parameter should exist"
        assert 'track' in params, "track parameter should exist"
        assert 'lever_length' in params, "lever_length parameter should exist"
        
        # Check default values
        assert params['wheelbase'] == 3.2, \
            f"Default wheelbase should be 3.2, got {params['wheelbase']}"
        assert params['track'] == 1.6, \
            f"Default track should be 1.6, got {params['track']}"
    
    def test_preset_changes_parameters(self, geometry_panel):
        """Verify preset selection changes parameters"""
        # Select "ЋЄгкий коммерческий" preset (index 1)
        geometry_panel.preset_combo.setCurrentIndex(1)
        
        params = geometry_panel.get_parameters()
        
        # Light commercial should have smaller dimensions
        assert params['wheelbase'] == 2.8, \
            f"Light commercial wheelbase should be 2.8, got {params['wheelbase']}"
        assert params['track'] == 1.4, \
            f"Light commercial track should be 1.4, got {params['track']}"
    
    def test_slider_change_emits_signal(self, geometry_panel, qapp):
        """Verify slider changes emit parameter_changed signal"""
        spy = QSignalSpy(geometry_panel.parameter_changed)
        
        # Change wheelbase slider
        geometry_panel.wheelbase_slider.setValue(3.5)
        
        # Process events
        qapp.processEvents()
        
        # Check signal was emitted
        assert spy.count() > 0, \
            "parameter_changed signal should be emitted"
        
        # Verify signal parameters
        signal_data = spy.at(0)
        param_name = signal_data[0]
        param_value = signal_data[1]
        
        assert param_name == 'wheelbase', \
            f"Expected 'wheelbase' parameter, got '{param_name}'"
        assert abs(param_value - 3.5) < 0.01, \
            f"Expected value 3.5, got {param_value}"
    
    def test_geometry_changed_signal_emitted(self, geometry_panel, qapp):
        """Verify geometry_changed signal is emitted with 3D format"""
        spy = QSignalSpy(geometry_panel.geometry_changed)
        
        # Change lever length
        geometry_panel.lever_length_slider.setValue(0.9)
        
        # Process events
        qapp.processEvents()
        
        # Check signal was emitted
        assert spy.count() > 0, \
            "geometry_changed signal should be emitted"
        
        # Verify signal contains 3D geometry data
        signal_data = spy.at(0)
        geometry_3d = signal_data[0]
        
        assert 'leverLength' in geometry_3d, \
            "geometry_changed should contain leverLength"
        assert 'frameLength' in geometry_3d, \
            "geometry_changed should contain frameLength"
        
        # Check units conversion (m -> mm)
        expected_lever_mm = 0.9 * 1000
        assert abs(geometry_3d['leverLength'] - expected_lever_mm) < 1.0, \
            f"Expected leverLength ~{expected_lever_mm}mm, got {geometry_3d['leverLength']}"
    
    def test_reset_button_restores_defaults(self, geometry_panel, qapp):
        """Verify reset button restores default parameters"""
        # Change parameters
        geometry_panel.wheelbase_slider.setValue(4.0)
        geometry_panel.track_slider.setValue(2.0)
        
        # Click reset button
        geometry_panel.reset_button.click()
        qapp.processEvents()
        
        # Check defaults restored
        params = geometry_panel.get_parameters()
        assert params['wheelbase'] == 3.2, \
            f"Reset should restore wheelbase to 3.2, got {params['wheelbase']}"
        assert params['track'] == 1.6, \
            f"Reset should restore track to 1.6, got {params['track']}"
    
    def test_set_parameters_updates_sliders(self, geometry_panel):
        """Verify set_parameters updates slider widgets"""
        new_params = {
            'wheelbase': 3.8,
            'track': 1.9,
            'lever_length': 0.95
        }
        
        geometry_panel.set_parameters(new_params)
        
        # Check sliders updated
        assert abs(geometry_panel.wheelbase_slider.value() - 3.8) < 0.01, \
            "wheelbase slider should be updated"
        assert abs(geometry_panel.track_slider.value() - 1.9) < 0.01, \
            "track slider should be updated"
        assert abs(geometry_panel.lever_length_slider.value() - 0.95) < 0.01, \
            "lever_length slider should be updated"


# ============================================================================
# PNEUMO PANEL FUNCTIONALITY TESTS
# ============================================================================

class TestPneumoPanelFunctionality:
    """Test PneumoPanel parameter handling and signals"""
    
    def test_default_parameters_loaded(self, pneumo_panel):
        """Verify default parameters are set correctly"""
        params = pneumo_panel.get_parameters()
        
        # Check key parameters exist
        assert 'cv_atmo_dp' in params, "cv_atmo_dp parameter should exist"
        assert 'relief_min_pressure' in params, "relief_min_pressure should exist"
        assert 'atmo_temp' in params, "atmo_temp should exist"
        
        # Check default values
        assert params['cv_atmo_dp'] == 0.01, \
            f"Default cv_atmo_dp should be 0.01, got {params['cv_atmo_dp']}"
        assert params['atmo_temp'] == 20.0, \
            f"Default atmo_temp should be 20.0, got {params['atmo_temp']}"
    
    def test_thermo_mode_change_emits_signal(self, pneumo_panel, qapp):
        """Verify thermo mode radio button emits signal"""
        spy = QSignalSpy(pneumo_panel.mode_changed)
        
        # Change to adiabatic mode
        pneumo_panel.adiabatic_radio.setChecked(True)
        qapp.processEvents()
        
        # Check signal was emitted
        assert spy.count() > 0, \
            "mode_changed signal should be emitted"
        
        # Verify signal parameters
        signal_data = spy.at(0)
        mode_type = signal_data[0]
        mode_value = signal_data[1]
        
        assert mode_type == 'thermo_mode', \
            f"Expected 'thermo_mode', got '{mode_type}'"
        assert mode_value == 'ADIABATIC', \
            f"Expected 'ADIABATIC', got '{mode_value}'"
    
    def test_pressure_units_change_logged(self, pneumo_panel, qapp, capsys):
        """Verify pressure units change is logged"""
        # Change to kPa
        pneumo_panel.pressure_units_combo.setCurrentIndex(2)
        qapp.processEvents()
        
        # Check console output
        captured = capsys.readouterr()
        assert "кѕа" in captured.out or "кѕа" in str(pneumo_panel.parameters.get('pressure_units', '')), \
            "Pressure units change should be logged"
    
    def test_relief_pressure_validation(self, pneumo_panel, qapp):
        """Verify relief pressure ordering is enforced"""
        # Try to set stiffness pressure below minimum
        pneumo_panel.relief_min_pressure_knob.setValue(5.0)
        pneumo_panel.relief_stiff_pressure_knob.setValue(4.0)  # Invalid!
        qapp.processEvents()
        
        # Check auto-correction happened
        params = pneumo_panel.get_parameters()
        min_p = params['relief_min_pressure']
        stiff_p = params['relief_stiff_pressure']
        
        assert stiff_p > min_p, \
            f"Stiffness pressure ({stiff_p}) should be auto-corrected above min ({min_p})"
    
    def test_master_isolation_checkbox_emits_signal(self, pneumo_panel, qapp):
        """Verify master isolation checkbox emits signal"""
        spy = QSignalSpy(pneumo_panel.parameter_changed)
        
        # Toggle master isolation
        pneumo_panel.master_isolation_check.setChecked(True)
        qapp.processEvents()
        
        # Check signal was emitted
        assert spy.count() > 0, \
            "parameter_changed signal should be emitted"
        
        # Verify checkbox state saved
        params = pneumo_panel.get_parameters()
        assert params['master_isolation_open'] == True, \
            "master_isolation_open should be True"
    
    def test_reset_button_restores_defaults(self, pneumo_panel, qapp):
        """Verify reset button restores default parameters"""
        # Change parameters
        pneumo_panel.relief_min_pressure_knob.setValue(5.0)
        pneumo_panel.atmo_temp_knob.setValue(30.0)
        pneumo_panel.adiabatic_radio.setChecked(True)
        
        # Click reset button
        pneumo_panel.reset_button.click()
        qapp.processEvents()
        
        # Check defaults restored
        params = pneumo_panel.get_parameters()
        assert params['relief_min_pressure'] == 2.5, \
            f"Reset should restore relief_min_pressure to 2.5"
        assert params['atmo_temp'] == 20.0, \
            f"Reset should restore atmo_temp to 20.0"
        assert params['thermo_mode'] == 'ISOTHERMAL', \
            f"Reset should restore thermo_mode to ISOTHERMAL"


# ============================================================================
# SIGNAL INTEGRATION TESTS
# ============================================================================

class TestPanelSignalIntegration:
    """Test signal connections between panels and main window"""
    
    def test_geometry_panel_signals_connected(self, geometry_panel):
        """Verify GeometryPanel has correct signals defined"""
        # Check signal attributes exist
        assert hasattr(geometry_panel, 'parameter_changed'), \
            "GeometryPanel should have parameter_changed signal"
        assert hasattr(geometry_panel, 'geometry_updated'), \
            "GeometryPanel should have geometry_updated signal"
        assert hasattr(geometry_panel, 'geometry_changed'), \
            "GeometryPanel should have geometry_changed signal"
    
    def test_pneumo_panel_signals_connected(self, pneumo_panel):
        """Verify PneumoPanel has correct signals defined"""
        # Check signal attributes exist
        assert hasattr(pneumo_panel, 'parameter_changed'), \
            "PneumoPanel should have parameter_changed signal"
        assert hasattr(pneumo_panel, 'mode_changed'), \
            "PneumoPanel should have mode_changed signal"
        assert hasattr(pneumo_panel, 'pneumatic_updated'), \
            "PneumoPanel should have pneumatic_updated signal"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-s"])
