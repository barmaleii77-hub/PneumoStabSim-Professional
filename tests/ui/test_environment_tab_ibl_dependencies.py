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
