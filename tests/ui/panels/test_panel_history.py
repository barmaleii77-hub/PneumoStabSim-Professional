from __future__ import annotations

import math

import pytest

pytest.importorskip("PySide6.QtWidgets")

from src.core.settings_sync_controller import SettingsSyncController
from src.ui.panels.graphics.panel_graphics import GraphicsPanel
from src.ui.panels.geometry.panel_geometry_refactored import GeometryPanel
from src.ui.panels.pneumo.panel_pneumo_refactored import PneumoPanel


def test_settings_sync_controller_history_roundtrip() -> None:
    controller = SettingsSyncController(initial_state={"foo": 1})
    controller.apply_patch({"foo": 2}, description="increment foo")
    assert controller.snapshot()["foo"] == 2

    undo_command = controller.undo()
    assert undo_command is not None
    assert controller.snapshot()["foo"] == 1

    redo_command = controller.redo()
    assert redo_command is not None
    assert controller.snapshot()["foo"] == 2


@pytest.mark.qtbot
def test_graphics_panel_undo_redo(qtbot) -> None:
    panel = GraphicsPanel()
    qtbot.addWidget(panel)
    qtbot.wait(100)

    initial_state = panel.collect_state()
    slider = panel.quality_tab._controls["mesh.cylinder_segments"]._spin  # type: ignore[attr-defined]
    slider.setValue(slider.value() + 4)
    qtbot.wait(50)

    updated_state = panel.collect_state()
    assert (
        updated_state["quality"]["mesh"]["cylinder_segments"]
        != initial_state["quality"]["mesh"]["cylinder_segments"]
    )

    assert panel.undo_last_change()
    qtbot.wait(50)
    reverted_state = panel.collect_state()
    assert (
        reverted_state["quality"]["mesh"]["cylinder_segments"]
        == initial_state["quality"]["mesh"]["cylinder_segments"]
    )

    assert panel.redo_last_change()
    qtbot.wait(50)
    redone_state = panel.collect_state()
    assert (
        redone_state["quality"]["mesh"]["cylinder_segments"]
        == updated_state["quality"]["mesh"]["cylinder_segments"]
    )


@pytest.mark.qtbot
def test_geometry_panel_registered_preset(qtbot) -> None:
    panel = GeometryPanel()
    qtbot.addWidget(panel)
    qtbot.wait(100)

    original = panel.get_parameters()
    assert panel.apply_registered_preset("geometry.compact")
    qtbot.wait(50)
    compact = panel.get_parameters()
    assert math.isclose(compact["frame_length_m"], 5.5, rel_tol=1e-6)
    assert panel.undo_last_change()
    qtbot.wait(50)
    restored = panel.get_parameters()
    assert math.isclose(
        restored["frame_length_m"], original["frame_length_m"], rel_tol=1e-6
    )


@pytest.mark.qtbot
def test_pneumo_panel_tooltips_and_preset(qtbot) -> None:
    panel = PneumoPanel()
    qtbot.addWidget(panel)
    qtbot.wait(100)

    assert "defaults_snapshot" in panel.reset_button.toolTip()

    baseline_units = panel.state_manager.get_state()["pressure_units"]
    assert panel.apply_registered_preset("pneumo.winter")
    qtbot.wait(50)
    winter_state = panel.state_manager.get_state()
    assert winter_state["pressure_units"] == "кПа"
    assert panel.undo_last_change()
    qtbot.wait(50)
    reverted = panel.state_manager.get_state()
    assert reverted["pressure_units"] == baseline_units
