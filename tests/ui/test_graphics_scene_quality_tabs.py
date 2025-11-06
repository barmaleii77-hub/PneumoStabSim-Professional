import math
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for graphics tab tests",
    exc_type=ImportError,
)

from src.ui.panels.graphics import environment_tab as environment_tab_module
from src.ui.panels.graphics.environment_tab import EnvironmentTab
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
def test_environment_tab_discovers_hdr_relative_to_project_root(monkeypatch, qapp):
    captured: dict[str, object] = {}

    def fake_discover(search_dirs, *, qml_root):
        captured["search_dirs"] = list(search_dirs)
        captured["qml_root"] = qml_root
        return []

    monkeypatch.setattr(environment_tab_module, "discover_hdr_files", fake_discover)

    tab = EnvironmentTab()
    try:
        project_root = Path(environment_tab_module.__file__).resolve().parents[4]
        expected_dirs = [
            project_root / "assets" / "hdr",
            project_root / "assets" / "hdri",
            project_root / "assets" / "qml" / "assets",
        ]

        assert captured["search_dirs"] == expected_dirs
        assert captured["qml_root"] == project_root / "assets" / "qml"
    finally:
        tab.deleteLater()


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


@pytest.mark.gui
def test_camera_controls_signals(qapp):
    panel = GraphicsPanel()

    try:
        from PySide6 import QtTest  # type: ignore

        spy = QtTest.QSignalSpy(panel.camera_changed)
        camera_tab = panel.camera_tab
        assert camera_tab is not None

        slider = camera_tab._controls["orbit_distance"]
        initial = slider.value()
        slider.set_value(initial + 0.5)

        camera_tab._emit()

        assert spy.count() >= 1
        payload = spy.at(spy.count() - 1)[0]

        assert isinstance(payload, dict)
        assert pytest.approx(slider.value(), rel=1e-3) == payload["orbit_distance"]
    finally:
        panel.deleteLater()
