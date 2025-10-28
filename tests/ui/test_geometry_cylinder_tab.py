import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for geometry cylinder tab tests",
    exc_type=ImportError,
)

from src.ui.panels.geometry.cylinder_tab import CylinderTab
from src.ui.panels.geometry.state_manager import GeometryStateManager


@pytest.mark.gui
def test_cylinder_tab_link_toggle_syncs_sliders(qtbot):
    """Ensure linked rod diameters stay synchronised in the UI."""

    state_manager = GeometryStateManager()
    tab = CylinderTab(state_manager)
    qtbot.addWidget(tab)

    # Establish distinct initial values to verify restoration later.
    tab.rod_diameter_front_m_slider.value_spinbox.setValue(0.039)
    tab.rod_diameter_rear_m_slider.value_spinbox.setValue(0.043)
    qtbot.wait(250)

    assert state_manager.get_parameter("rod_diameter_m") == pytest.approx(0.039)
    assert state_manager.get_parameter("rod_diameter_rear_m") == pytest.approx(0.043)

    # Enable linking – rear slider is disabled and mirrors the front value.
    state_manager.set_parameter("link_rod_diameters", True)
    tab.update_from_state()
    tab.update_link_state(True)

    assert not tab.rod_diameter_rear_m_slider.isEnabled()
    assert (
        tab.rod_diameter_rear_m_slider.value()
        == pytest.approx(tab.rod_diameter_front_m_slider.value())
    )

    # Changing the front slider propagates to the rear slider and state manager.
    tab.rod_diameter_front_m_slider.value_spinbox.setValue(0.041)
    qtbot.wait(250)

    assert state_manager.get_parameter("rod_diameter_m") == pytest.approx(0.041)
    assert state_manager.get_parameter("rod_diameter_rear_m") == pytest.approx(0.041)
    assert (
        tab.rod_diameter_rear_m_slider.value()
        == pytest.approx(tab.rod_diameter_front_m_slider.value())
    )

    # Disabling the link restores the original independent values.
    state_manager.set_parameter("link_rod_diameters", False)
    tab.update_from_state()
    tab.update_link_state(False)

    assert tab.rod_diameter_rear_m_slider.isEnabled()
    assert tab.rod_diameter_front_m_slider.value() == pytest.approx(0.039)
    assert tab.rod_diameter_rear_m_slider.value() == pytest.approx(0.043)
