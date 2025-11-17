import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for environment tab stress tests",
    exc_type=ImportError,
)

from src.common.settings_manager import get_settings_manager
from src.ui.panels.graphics.environment_tab import EnvironmentTab


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_environment_tab_handles_hdr_churn_and_extreme_sliders(
    qtbot, tmp_path, settings_manager
):
    settings = get_settings_manager(settings_manager.settings_file)

    hdr_first = tmp_path / "first_probe.exr"
    hdr_second = tmp_path / "second_probe.exr"
    hdr_first.write_bytes(b"hdr")
    hdr_second.write_bytes(b"hdr")

    tab = EnvironmentTab()
    qtbot.addWidget(tab)

    controls = tab.get_controls()
    hdr_widget = controls["ibl.file"]
    hdr_widget.set_resolution_roots([tmp_path])
    hdr_widget.set_items([(hdr_first.name, hdr_first.name)])
    hdr_widget.set_current_data(hdr_first.name, emit=False)
    tab._refresh_hdr_status(hdr_widget.current_path())

    status_label = controls["ibl.status_label"]
    assert status_label.text() == hdr_first.name

    hdr_widget.set_items(
        [
            (hdr_first.stem, hdr_first.name),
            (hdr_second.stem, hdr_second.name),
        ]
    )
    hdr_widget.set_current_data(hdr_second.name, emit=True)
    tab._refresh_hdr_status(hdr_widget.current_path())

    assert hdr_widget.current_path() == hdr_second.name
    assert status_label.text() == hdr_second.name

    hdr_widget.set_items([(hdr_second.stem, hdr_second.name)])
    tab._refresh_hdr_status(hdr_widget.current_path())
    assert hdr_widget.current_path() == hdr_second.name

    intensity_slider = controls["ibl.intensity"]
    intensity_slider.set_value(intensity_slider._min)  # type: ignore[attr-defined]
    intensity_slider.set_value(intensity_slider._max)  # type: ignore[attr-defined]

    blur_slider = controls["skybox.blur"]
    blur_slider.set_value(blur_slider._max)  # type: ignore[attr-defined]

    state = tab.get_state()
    assert state["ibl_intensity"] == pytest.approx(intensity_slider._max)
    assert state["skybox_blur"] == pytest.approx(blur_slider._max)
