import pytest
import pytestqt

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for panel tests",
    exc_type=ImportError,
)

from src.ui.panels.panel_modes import ModesPanel
from src.ui.panels.panel_road import RoadPanel


@pytest.mark.gui
@pytest.mark.qtbot
def test_modes_panel_get_parameters_reflects_ui_state(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = ModesPanel()
    qtbot.addWidget(panel)

    initial = panel.get_parameters()
    assert isinstance(initial, dict)
    assert "physics" in initial

    panel.include_springs_check.setChecked(
        not panel.include_springs_check.isChecked()
    )
    qtbot.wait(50)

    updated = panel.get_parameters()
    assert updated["physics"].get("include_springs") == panel.include_springs_check.isChecked()

    initial["physics"]["include_springs"] = not updated["physics"].get(
        "include_springs", False
    )
    refreshed = panel.get_parameters()
    assert refreshed["physics"].get("include_springs") == updated["physics"].get(
        "include_springs"
    )


@pytest.mark.gui
@pytest.mark.qtbot
def test_road_panel_get_parameters_after_preset(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = RoadPanel()
    qtbot.addWidget(panel)

    baseline = panel.get_parameters()
    assert isinstance(baseline, dict)
    assert baseline["preset"] == ""
    assert baseline["has_profile"] is False

    panel.preset_combo.setCurrentIndex(1)
    qtbot.wait(50)
    panel._apply_current_preset()
    qtbot.wait(50)

    params = panel.get_parameters()
    assert params["preset"] == "Smooth Highway"
    assert params["has_profile"] is True
    assert params["assignment_enabled"] is True
