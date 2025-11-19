import math
import math

import pytest

pytest.importorskip("PySide6.QtWidgets")

from src.common.settings_manager import get_settings_manager
from src.ui.panels_accordion import (
    AdvancedPanelAccordion,
    RoadPanelAccordion,
    SimulationPanelAccordion,
)


@pytest.fixture()
def settings_snapshot():
    settings = get_settings_manager()
    keys = [
        "current.simulation.physics_dt",
        "current.simulation.sim_speed",
        "current.modes.sim_type",
        "current.pneumatic.thermo_mode",
        "current.modes.amplitude",
        "current.modes.phase",
        "current.modes.mode_preset",
        "current.modes.profile_avg_speed",
        "current.modes.road_mode",
        "current.physics.suspension.spring_constant",
        "current.physics.suspension.damper_coefficient",
        "current.physics.suspension.dead_zone_percent",
        "current.pneumatic.atmo_temp",
        "current.graphics.quality.frame_rate_limit",
        "current.graphics.quality.render_scale",
        "current.graphics.quality.shadows.filter",
    ]
    snapshot = {key: settings.get(key) for key in keys}
    yield settings, snapshot
    for key, value in snapshot.items():
        settings.set(key, value, auto_save=False)


@pytest.mark.qtbot
def test_simulation_panel_updates_settings(qtbot, settings_snapshot):
    settings, _ = settings_snapshot
    panel = SimulationPanelAccordion()
    qtbot.addWidget(panel)

    new_dt = 0.0025
    panel.time_step.set_value(new_dt)
    qtbot.wait(10)
    assert math.isclose(
        float(settings.get("current.simulation.physics_dt")), new_dt, rel_tol=1e-6
    )

    panel.sim_mode_combo.setCurrentText("Kinematics")
    qtbot.wait(10)
    assert settings.get("current.modes.sim_type") == "KINEMATICS"

    panel.thermo_combo.setCurrentText("Adiabatic")
    qtbot.wait(10)
    assert settings.get("current.pneumatic.thermo_mode") == "ADIABATIC"


@pytest.mark.qtbot
def test_simulation_panel_validation_snapshot(qtbot, settings_snapshot):
    settings, _ = settings_snapshot
    settings.set("current.simulation.physics_dt", -1.0, auto_save=False)
    panel = SimulationPanelAccordion()
    qtbot.addWidget(panel)

    assert panel.validationState["physics_dt"] is False

    panel.time_step.set_value(0.0015)
    qtbot.wait(10)
    assert panel.validationState["physics_dt"] is True


@pytest.mark.qtbot
def test_road_panel_binds_manual_and_profile(qtbot, settings_snapshot):
    settings, _ = settings_snapshot
    panel = RoadPanelAccordion()
    qtbot.addWidget(panel)

    panel._on_mode_changed("Manual (Sine)")
    panel.amplitude.set_value(0.075)
    qtbot.wait(10)
    assert math.isclose(
        float(settings.get("current.modes.amplitude")), 0.075, rel_tol=1e-6
    )
    assert settings.get("current.modes.road_mode") == "manual"
    assert panel._manual_section.isVisible()

    panel._on_mode_changed("Road Profile")
    panel.profile_type_combo.setCurrentText("Off-Road")
    qtbot.wait(10)
    assert settings.get("current.modes.mode_preset") == "off_road"
    assert settings.get("current.modes.road_mode") == "profile"
    assert panel._profile_section.isVisible()

    panel.avg_speed.set_value(65.0)
    qtbot.wait(10)
    assert math.isclose(
        float(settings.get("current.modes.profile_avg_speed")), 65.0, rel_tol=1e-6
    )


@pytest.mark.qtbot
def test_road_panel_validation_snapshot(qtbot, settings_snapshot):
    settings, _ = settings_snapshot
    settings.set("current.modes.amplitude", 0.5, auto_save=False)
    settings.set("current.modes.profile_avg_speed", 500.0, auto_save=False)
    panel = RoadPanelAccordion()
    qtbot.addWidget(panel)

    assert panel.validationState["amplitude"] is False
    assert panel.validationState["avg_speed"] is False

    panel.amplitude.set_value(0.05)
    panel.avg_speed.set_value(80.0)
    qtbot.wait(10)

    assert panel.validationState["amplitude"] is True
    assert panel.validationState["avg_speed"] is True


@pytest.mark.qtbot
def test_advanced_panel_propagates_to_settings(qtbot, settings_snapshot):
    settings, _ = settings_snapshot
    panel = AdvancedPanelAccordion()
    qtbot.addWidget(panel)

    panel.spring_stiffness.set_value(75000.0)
    panel.target_fps.set_value(90.0)
    panel.atmospheric_temp.set_value(35.0)
    qtbot.wait(10)

    assert math.isclose(
        float(settings.get("current.physics.suspension.spring_constant")),
        75000.0,
        rel_tol=1e-6,
    )
    assert math.isclose(
        float(settings.get("current.graphics.quality.frame_rate_limit")),
        90.0,
        rel_tol=1e-6,
    )
    assert math.isclose(
        float(settings.get("current.pneumatic.atmo_temp")), 35.0, rel_tol=1e-6
    )


@pytest.mark.qtbot
def test_advanced_panel_validation_snapshot(qtbot, settings_snapshot):
    settings, _ = settings_snapshot
    settings.set("current.graphics.quality.render_scale", -2.0, auto_save=False)
    settings.set(
        "current.physics.suspension.damper_coefficient", 999999.0, auto_save=False
    )

    panel = AdvancedPanelAccordion()
    qtbot.addWidget(panel)

    assert panel.validationState["render_scale"] is False
    assert panel.validationState["damper_coeff"] is False

    panel.aa_quality.set_value(1.1)
    panel.damper_coeff.set_value(2500.0)
    qtbot.wait(10)

    assert panel.validationState["render_scale"] is True
    assert panel.validationState["damper_coeff"] is True
