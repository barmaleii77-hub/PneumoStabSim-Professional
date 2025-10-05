"""
Integration tests for UI panels
"""
import pytest
from src.ui.panels import GeometryPanel, ModesPanel, PneumoPanel


@pytest.mark.integration
@pytest.mark.gui
class TestPanelIntegration:
    """Test UI panel integration"""
    
    def test_geometry_panel_create(self, qapp):
        """Test creating geometry panel"""
        panel = GeometryPanel()
        assert panel is not None
        
        params = panel.get_parameters()
        assert 'wheelbase' in params
    
    def test_modes_panel_create(self, qapp):
        """Test creating modes panel"""
        panel = ModesPanel()
        assert panel is not None
        
        params = panel.get_parameters()
        assert 'simulation_mode' in params
    
    def test_pneumo_panel_create(self, qapp):
        """Test creating pneumatic panel"""
        panel = PneumoPanel()
        assert panel is not None
        
        params = panel.get_parameters()
        assert 'thermo_mode' in params
    
    def test_panel_parameter_update(self, qapp):
        """Test updating panel parameters"""
        panel = GeometryPanel()
        
        # Track signal emissions
        signal_received = []
        panel.parameter_changed.connect(
            lambda name, val: signal_received.append((name, val))
        )
        
        # Update parameter
        panel.set_parameters({'wheelbase': 3.0})
        
        # Verify signal was emitted
        assert len(signal_received) > 0
