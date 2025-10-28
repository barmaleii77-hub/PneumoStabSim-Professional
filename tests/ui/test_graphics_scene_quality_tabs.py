import math

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for graphics tab tests",
    exc_type=ImportError,
)

from src.ui.panels.graphics.panel_graphics_refactored import GraphicsPanel
from src.ui.panels.graphics.quality_tab import QualityTab
from src.ui.panels.graphics.scene_tab import SceneTab


@pytest.mark.gui
def test_quality_tab_shadow_resolution_numeric(qapp):
    tab = QualityTab()

    initial_state = tab.get_state()
    assert isinstance(initial_state["shadows"]["resolution"], int)

    tab.set_state({"shadows": {"resolution": 2048}})

    updated_state = tab.get_state()
    assert updated_state["shadows"]["resolution"] == 2048
    assert isinstance(updated_state["shadows"]["resolution"], int)


@pytest.mark.gui
def test_scene_tab_roundtrip_preserves_types(qapp):
    tab = SceneTab()

    payload = {
        "scale_factor": 2.5,
        "exposure": 4.0,
        "default_clear_color": "#ABCDEF",
        "model_base_color": "#123456",
        "model_roughness": 0.35,
        "model_metalness": 0.9,
    }

    tab.set_state(payload)
    state = tab.get_state()

    assert math.isclose(state["scale_factor"], 2.5, rel_tol=1e-6)
    assert math.isclose(state["exposure"], 4.0, rel_tol=1e-6)
    assert state["default_clear_color"] == "#abcdef"
    assert state["model_base_color"] == "#123456"
    assert math.isclose(state["model_roughness"], 0.35, rel_tol=1e-6)
    assert math.isclose(state["model_metalness"], 0.9, rel_tol=1e-6)


@pytest.mark.gui
def test_graphics_panel_collect_state_includes_scene(qapp):
    panel = GraphicsPanel()

    try:
        baseline_scene = panel.scene_tab.get_state()
        collected = panel.collect_state()
        assert collected["scene"] == baseline_scene

        updated_scene = dict(baseline_scene)
        updated_scene["scale_factor"] = min(baseline_scene["scale_factor"] + 0.5, 5.0)
        panel.scene_tab.set_state(updated_scene)

        refreshed = panel.collect_state()
        assert refreshed["scene"] == panel.scene_tab.get_state()
    finally:
        panel.deleteLater()
