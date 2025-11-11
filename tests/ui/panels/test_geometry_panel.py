"""Unit tests for the GeometryPanel public API."""

from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for GeometryPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.geometry import GeometryPanel


def _get_wheelbase_slider(panel: GeometryPanel):
    if hasattr(panel, "frame_tab"):
        return panel.frame_tab.wheelbase_slider
    return panel.wheelbase_slider


@pytest.mark.gui
def test_get_parameters_returns_copy(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = GeometryPanel()
    qtbot.addWidget(panel)

    snapshot = panel.get_parameters()

    assert isinstance(snapshot, dict)
    assert "wheelbase" in snapshot

    snapshot["wheelbase"] = -123.0

    refreshed = panel.get_parameters()
    assert refreshed["wheelbase"] != snapshot["wheelbase"]


@pytest.mark.gui
@pytest.mark.parametrize("delta", [0.05, -0.05])
def test_get_parameters_tracks_slider_updates(
    qtbot: pytestqt.qtbot.QtBot, delta: float
) -> None:
    panel = GeometryPanel()
    qtbot.addWidget(panel)

    slider = _get_wheelbase_slider(panel)
    initial = slider.value()
    target = max(slider.minimum(), min(slider.maximum(), initial + delta))

    slider.value_spinbox.setValue(target)
    qtbot.wait(350)

    params = panel.get_parameters()
    assert params["wheelbase"] == pytest.approx(slider.value())
