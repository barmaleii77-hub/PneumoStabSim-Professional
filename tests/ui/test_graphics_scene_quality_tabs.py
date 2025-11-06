import math

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for graphics tab tests",
    exc_type=ImportError,
)

from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QComboBox

from src.ui.panels.graphics import environment_tab as environment_tab_module
from src.common.logging_widgets import LoggingCheckBox
from src.ui.panels.graphics.environment_tab import EnvironmentTab
from src.ui.panels.graphics.effects_tab import EffectsTab
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
def test_graphics_panel_color_toggle_sync(qapp):
    panel = GraphicsPanel()

    try:
        toggle = panel._color_adjustments_toggle
        assert isinstance(toggle, LoggingCheckBox)

        effects_tab = panel.effects_tab
        assert effects_tab is not None

        color_checkbox = effects_tab._controls["color.enabled"]
        assert isinstance(color_checkbox, LoggingCheckBox)

        toggle.setChecked(False)
        assert color_checkbox.isChecked() is False
        state_after_toggle = effects_tab.get_state()
        assert state_after_toggle["color_adjustments_enabled"] is False
        assert state_after_toggle["color_adjustments_active"] is False

        color_checkbox.setChecked(True)
        assert toggle.isChecked() is True
        state_after_enable = effects_tab.get_state()
        assert state_after_enable["color_adjustments_enabled"] is True
        assert state_after_enable["color_adjustments_active"] is True
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_graphics_panel_preset_buttons_persist_state(monkeypatch, tmp_path, qapp):
    panel = GraphicsPanel()

    try:
        from PySide6 import QtTest  # type: ignore

        baseline_state = deepcopy(panel.collect_state())
        recorded: dict[str, object] = {}

        def fake_reset_to_defaults() -> dict[str, dict[str, object]]:
            recorded["reset_called"] = True
            return deepcopy(baseline_state)

        def fake_save_defaults(state: dict[str, object]) -> None:
            recorded["save_defaults_called"] = deepcopy(state)

        def fake_save_current(state: dict[str, object]) -> None:
            recorded["save_current_called"] = deepcopy(state)

        panel.settings_service.reset_to_defaults = fake_reset_to_defaults  # type: ignore[assignment]
        panel.settings_service.save_current_as_defaults = fake_save_defaults  # type: ignore[assignment]
        panel.settings_service.save_current = fake_save_current  # type: ignore[assignment]

        def fake_export_report() -> Path:
            report_path = tmp_path / "graphics-analysis.json"
            recorded["analysis_report"] = report_path
            return report_path

        def fake_analyze() -> dict[str, object]:
            analysis = {"status": "ok"}
            recorded["analysis"] = analysis
            return analysis

        panel.graphics_logger.export_analysis_report = fake_export_report  # type: ignore[attr-defined]
        panel.graphics_logger.analyze_qml_sync = fake_analyze  # type: ignore[attr-defined]

        preset_spy = QtTest.QSignalSpy(panel.preset_applied)

        panel.reset_to_defaults()
        assert recorded.get("reset_called") is True
        assert preset_spy.count() >= 1

        panel.save_current_as_defaults()
        saved_state = recorded.get("save_defaults_called")
        assert isinstance(saved_state, dict)
        assert saved_state == panel.collect_state()

        monkeypatch.chdir(tmp_path)
        panel.export_sync_analysis()
        exported_state = recorded.get("save_current_called")
        assert isinstance(exported_state, dict)
        assert exported_state == panel.collect_state()

        export_dir = tmp_path / "reports" / "graphics"
        assert export_dir.exists()
        exported = list(export_dir.glob("graphics-preset-*.json"))
        assert exported, "Exported preset file not found"
    finally:
        panel.deleteLater()


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


@pytest.mark.gui
def test_effects_tab_color_adjustments_toggle(qapp):
    tab = EffectsTab()

    try:
        checkbox = tab._controls["color.enabled"]
        assert isinstance(checkbox, LoggingCheckBox)

        sliders = [
            tab._controls["color.brightness"],
            tab._controls["color.contrast"],
            tab._controls["color.saturation"],
        ]

        # Disable adjustments and verify sliders follow
        checkbox.setChecked(False)
        for slider in sliders:
            assert not slider.isEnabled()

        checkbox.setChecked(True)
        for slider in sliders:
            assert slider.isEnabled()

        state = tab.get_state()
        assert state["color_adjustments_enabled"] is True
        assert state["color_adjustments_active"] is True
    finally:
        tab.deleteLater()


@pytest.mark.gui
def test_quality_presets_emit_without_qt_warnings(qapp):
    tab = QualityTab()

    warnings: list[tuple[QtMsgType, str]] = []

    def message_handler(msg_type, _context, message):  # pragma: no cover - Qt callback
        if msg_type in (
            QtMsgType.QtWarningMsg,
            QtMsgType.QtCriticalMsg,
            QtMsgType.QtFatalMsg,
        ):
            warnings.append((msg_type, message))

    previous_handler = qInstallMessageHandler(message_handler)

    try:
        combo = tab._controls["quality.preset"]
        assert isinstance(combo, QComboBox)

        for preset in ("ultra", "high", "medium", "low"):
            index = combo.findData(preset)
            assert index >= 0, f"Preset {preset} not found"
            combo.setCurrentIndex(index)
            qapp.processEvents()

        assert warnings == []
    finally:
        qInstallMessageHandler(previous_handler)
        tab.deleteLater()
