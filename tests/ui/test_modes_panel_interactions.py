"""Interactive regression tests for the refactored ModesPanel."""

from __future__ import annotations

import pytest

pytest.importorskip("pytestqt")
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_modes_panel_slider_updates_state_and_signals(qtbot, modes_panel):
    """Changing road excitation sliders should update state and emit signals."""

    with qtbot.waitSignal(
        modes_panel.parameter_changed, timeout=1000
    ) as amplitude_signal:
        modes_panel.road_tab.amplitude_slider.slider.setValue(750)

    param_name, amplitude_value = amplitude_signal.args
    assert param_name == "amplitude"
    assert amplitude_value == pytest.approx(0.15, rel=1e-2)
    params = modes_panel.state_manager.get_parameters()
    assert params["amplitude"] == pytest.approx(amplitude_value, rel=1e-3)

    with qtbot.waitSignal(
        modes_panel.animation_changed, timeout=1000
    ) as animation_signal:
        modes_panel.road_tab.frequency_slider.slider.setValue(500)

    animation_payload = animation_signal.args[0]
    assert animation_payload["frequency"] == pytest.approx(5.1, rel=1e-3)
    assert modes_panel.state_manager.get_parameters()["frequency"] == pytest.approx(
        5.1, rel=1e-3
    )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_modes_panel_control_buttons_manage_simulation_state(qtbot, modes_panel):
    """Control buttons should emit commands and update UI lockouts."""

    control_tab = modes_panel.control_tab
    commands: list[str] = []
    modes_panel.simulation_control.connect(commands.append)

    qtbot.mouseClick(control_tab.start_button, Qt.LeftButton)
    qtbot.wait(10)
    assert commands and commands[-1] == "start"
    assert control_tab.status_label.text() == "▶ Запущено"
    assert not control_tab.start_button.isEnabled()
    assert not modes_panel.physics_tab.include_pneumatics_check.isEnabled()

    qtbot.mouseClick(control_tab.pause_button, Qt.LeftButton)
    qtbot.wait(10)
    assert commands[-1] == "pause"
    assert control_tab.status_label.text() == "⏸ Пауза"
    assert control_tab.start_button.isEnabled()
    assert modes_panel.physics_tab.include_pneumatics_check.isEnabled()

    qtbot.mouseClick(control_tab.reset_button, Qt.LeftButton)
    qtbot.wait(10)
    assert commands[-1] == "reset"
    assert control_tab.status_label.text() == "🔄 Сброс..."


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_modes_panel_invalid_parameters_trigger_validation_errors(modes_panel):
    """Out-of-range parameters must be reported by the validator."""

    modes_panel.state_manager.update_parameter("amplitude", 0.5)
    modes_panel.state_manager.update_parameter("frequency", 25.0)

    errors = modes_panel.validate_state()
    assert any("Амплитуда вне диапазона" in err for err in errors)
    assert any("Частота вне диапазона" in err for err in errors)


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_modes_panel_physics_toggle_emits_activation(qtbot, modes_panel):
    """Toggling pneumatics should propagate stabilizer activation state."""

    physics_tab = modes_panel.physics_tab

    with qtbot.waitSignal(
        modes_panel.physics_options_changed, timeout=1000
    ) as disabled_signal:
        physics_tab.include_pneumatics_check.setChecked(False)

    options_payload = disabled_signal.args[0]
    assert not options_payload["include_pneumatics"]
    assert not modes_panel.state_manager.get_physics_options()["include_pneumatics"]

    with qtbot.waitSignal(
        modes_panel.physics_options_changed, timeout=1000
    ) as enabled_signal:
        physics_tab.include_pneumatics_check.setChecked(True)

    options_payload_enabled = enabled_signal.args[0]
    assert options_payload_enabled["include_pneumatics"]
    assert modes_panel.state_manager.get_physics_options()["include_pneumatics"]


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_modes_panel_smoothing_toggle_blocks_controls(qtbot, modes_panel):
    """Smoothing controls should disable when smoothing is turned off."""

    road_tab = modes_panel.road_tab
    assert road_tab.smoothing_duration_slider.isEnabled()

    with qtbot.waitSignal(modes_panel.parameter_changed, timeout=1000):
        road_tab.smoothing_checkbox.setChecked(False)

    assert not road_tab.smoothing_duration_slider.isEnabled()
    assert not road_tab.smoothing_angle_slider.isEnabled()
    assert not road_tab.smoothing_piston_slider.isEnabled()

    with qtbot.waitSignal(modes_panel.parameter_changed, timeout=1000):
        road_tab.smoothing_checkbox.setChecked(True)

    assert road_tab.smoothing_duration_slider.isEnabled()
    assert road_tab.smoothing_angle_slider.isEnabled()
    assert road_tab.smoothing_piston_slider.isEnabled()
