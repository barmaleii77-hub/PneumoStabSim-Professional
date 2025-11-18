"""Integration coverage for the refactored modes panel UI and validation flows."""

from __future__ import annotations

import os

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 widgets require Qt libraries that must be available",
    exc_type=ImportError,
)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.ui.panels.modes.panel_modes_refactored import ModesPanel


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_modes_panel_emits_control_and_mode_signals(qapp) -> None:
    """Control tab commands should toggle UI state and surface mode changes."""

    panel = ModesPanel()

    commands: list[str] = []
    mode_events: list[tuple[str, str]] = []
    physics_updates: list[dict] = []

    panel.simulation_control.connect(commands.append)
    panel.mode_changed.connect(lambda kind, value: mode_events.append((kind, value)))
    panel.physics_options_changed.connect(
        lambda payload: physics_updates.append(payload)
    )

    panel.control_tab.start_button.click()
    panel.control_tab.pause_button.click()

    panel.simulation_tab.dynamics_radio.setChecked(True)
    qapp.processEvents()
    panel.simulation_tab._on_sim_type_changed()

    panel.simulation_tab.adiabatic_radio.setChecked(True)
    qapp.processEvents()
    panel.simulation_tab._on_thermo_changed()

    panel.physics_tab.include_pneumatics_check.setChecked(False)
    qapp.processEvents()

    assert commands == ["start", "pause"], "Control tab should emit lifecycle commands"
    assert panel.control_tab.start_button.isEnabled()
    assert not panel.control_tab.pause_button.isEnabled()
    assert any(
        kind == "sim_type" and value == "DYNAMICS" for kind, value in mode_events
    )
    assert any(
        kind == "thermo_mode" and value == "ADIABATIC" for kind, value in mode_events
    )
    physics_state = panel.state_manager.get_physics_options()
    assert physics_state.get("include_pneumatics") is False
    assert (
        physics_updates == [] or physics_updates[-1].get("include_pneumatics") is False
    )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_modes_panel_validation_reports_out_of_range_state(qapp) -> None:
    """Manual parameter edits should be validated and reflected in the UI state."""

    panel = ModesPanel()

    panel.state_manager.update_parameter("amplitude", 0.35)
    panel.state_manager.update_parameter("frequency", 14.0)
    panel.state_manager.update_parameter("phase", -5.0)
    panel.state_manager.update_parameter("smoothing_duration_ms", 1200.0)

    panel.road_tab._apply_current_state()

    errors = panel.validate_state()

    assert any("Амплитуда вне диапазона" in message for message in errors)
    assert any("Частота вне диапазона" in message for message in errors)
    assert any("Фаза" in message for message in errors)
    assert any("сглаживания" in message for message in errors)

    assert panel.road_tab.amplitude_slider.value() <= 0.2
    assert panel.road_tab.smoothing_duration_slider.value() <= 600.0
