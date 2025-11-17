from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for graphics tab tests",
    exc_type=ImportError,
)

from src.ui.panels.graphics.environment_tab import EnvironmentTab


def _is_enabled(widget) -> bool:
    return bool(getattr(widget, "isEnabled", lambda: True)())


@pytest.mark.gui
def test_environment_tab_disables_dependent_controls_on_master_toggles(qapp):
    tab = EnvironmentTab()
    try:
        baseline = tab.get_state()
        baseline["ibl_enabled"] = True
        baseline["skybox_enabled"] = True
        tab.set_state(baseline)

        controls = tab.get_controls()

        assert _is_enabled(controls["ibl.intensity"])
        assert _is_enabled(controls["ibl.probe_horizon"])
        assert _is_enabled(controls["ibl.offset_x"])
        assert _is_enabled(controls["ibl.offset_y"])
        assert _is_enabled(controls["ibl.bind"])
        assert _is_enabled(controls["ibl.skybox_brightness"])
        assert _is_enabled(controls["skybox.blur"])
        assert _is_enabled(controls["ibl.rotation"])

        controls["ibl.enabled"].click()
        qapp.processEvents()

        assert not _is_enabled(controls["ibl.intensity"])
        assert not _is_enabled(controls["ibl.probe_horizon"])
        assert not _is_enabled(controls["ibl.offset_x"])
        assert not _is_enabled(controls["ibl.offset_y"])
        assert not _is_enabled(controls["ibl.bind"])
        assert _is_enabled(controls["ibl.rotation"])

        controls["background.skybox_enabled"].click()
        qapp.processEvents()

        assert not _is_enabled(controls["ibl.skybox_brightness"])
        assert not _is_enabled(controls["skybox.blur"])
        assert not _is_enabled(controls["ibl.rotation"])

        controls["background.skybox_enabled"].click()
        qapp.processEvents()

        assert _is_enabled(controls["ibl.skybox_brightness"])
        assert _is_enabled(controls["skybox.blur"])
        assert _is_enabled(controls["ibl.rotation"])

        controls["ibl.enabled"].click()
        qapp.processEvents()

        assert _is_enabled(controls["ibl.intensity"])
        assert _is_enabled(controls["ibl.probe_horizon"])
        assert _is_enabled(controls["ibl.offset_x"])
        assert _is_enabled(controls["ibl.offset_y"])
        assert _is_enabled(controls["ibl.bind"])
    finally:
        tab.deleteLater()


@pytest.mark.gui
def test_environment_tab_missing_hdr_path_updates_status(
    qapp,
    qtbot,
    monkeypatch: pytest.MonkeyPatch,
):
    tab = EnvironmentTab()
    qtbot.addWidget(tab)
    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.warning",
        lambda *args, **kwargs: None,
    )

    try:
        state = tab.get_state()
        state["ibl_source"] = "missing_hdr.exr"
        tab.set_state(state)

        tab.show()
        qapp.processEvents()

        selector = tab.get_controls()["ibl.file"]
        assert selector.current_path() == "missing_hdr.exr"
        assert selector.is_missing()

        status_label = tab.get_controls()["ibl.status_label"]
        assert status_label.text() == "⚠ файл не найден"
        assert status_label.toolTip() == "missing_hdr.exr"
    finally:
        tab.deleteLater()


@pytest.mark.gui
def test_environment_tab_hdr_add_remove_cycle_updates_status(qapp, tmp_path: Path):
    tab = EnvironmentTab()
    try:
        controls = tab.get_controls()
        hdr_widget = controls["ibl.file"]
        hdr_widget.set_resolution_roots([tmp_path])

        studio_path = tmp_path / "studio.hdr"
        outdoor_path = tmp_path / "outdoor.hdr"
        studio_path.write_text("fake hdr", encoding="utf-8")
        outdoor_path.write_text("fake hdr", encoding="utf-8")

        hdr_widget.set_items(
            [("Studio", studio_path.as_posix()), ("Outdoor", outdoor_path.as_posix())]
        )

        state = tab.get_state()
        state["ibl_source"] = "studio.hdr"
        tab.set_state(state)

        current_path = Path(hdr_widget.current_path())
        assert current_path.name == studio_path.name
        status_label = controls["ibl.status_label"]
        assert status_label.text() == studio_path.name
        assert Path(tab.get_state()["ibl_source"]).name == studio_path.name

        state["ibl_source"] = ""
        tab.set_state(state)

        assert hdr_widget.current_path() == ""
        assert status_label.text() == "—"
        assert tab.get_state()["ibl_source"] == ""
    finally:
        tab.deleteLater()


@pytest.mark.gui
def test_environment_tab_accepts_slider_extremes(qapp):
    tab = EnvironmentTab()
    try:
        state = tab.get_state()
        ranges = tab._slider_ranges

        state["ibl_intensity"] = ranges["ibl_intensity"].minimum
        state["ibl_rotation"] = ranges["ibl_rotation"].maximum
        state["probe_horizon"] = ranges["probe_horizon"].minimum
        state["skybox_blur"] = ranges["skybox_blur"].maximum

        tab.set_state(state)
        updated = tab.get_state()

        assert updated["ibl_intensity"] == pytest.approx(
            ranges["ibl_intensity"].minimum
        )
        assert updated["ibl_rotation"] == pytest.approx(ranges["ibl_rotation"].maximum)
        assert updated["probe_horizon"] == pytest.approx(
            ranges["probe_horizon"].minimum
        )
        assert updated["skybox_blur"] == pytest.approx(ranges["skybox_blur"].maximum)
    finally:
        tab.deleteLater()
