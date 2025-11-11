"""Unit tests for the GeometryPanel public API."""

from __future__ import annotations

import math

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for GeometryPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.geometry import GeometryPanel
from src.ui.geometry_schema import GeometrySettings

from ._slider_utils import get_slider_value, nudge_slider


def _get_wheelbase_slider(panel: GeometryPanel):
    if hasattr(panel, "frame_tab"):
        return panel.frame_tab.wheelbase_slider
    return panel.wheelbase_slider


@pytest.mark.gui
def test_get_parameters_returns_copy(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = GeometryPanel()
    qtbot.addWidget(panel)

    snapshot = panel.get_parameters()
    settings = panel.get_geometry_settings()

    assert isinstance(snapshot, dict)
    assert "wheelbase" in snapshot
    assert isinstance(settings, GeometrySettings)
    assert settings.to_config_dict()["wheelbase"] == pytest.approx(
        snapshot["wheelbase"]
    )

    snapshot["wheelbase"] = -123.0

    refreshed = panel.get_parameters()
    assert refreshed["wheelbase"] != snapshot["wheelbase"]
    refreshed_settings = panel.get_geometry_settings()
    assert refreshed_settings.to_config_dict()["wheelbase"] == pytest.approx(
        refreshed["wheelbase"]
    )


@pytest.mark.gui
@pytest.mark.parametrize("delta", [0.05, -0.05])
def test_get_parameters_tracks_slider_updates(
    qtbot: pytestqt.qtbot.QtBot, delta: float
) -> None:
    panel = GeometryPanel()
    qtbot.addWidget(panel)

    slider = _get_wheelbase_slider(panel)
    initial = get_slider_value(slider)
    updated = nudge_slider(slider, delta)
    qtbot.wait(350)

    params = panel.get_parameters()
    settings = panel.get_geometry_settings()
    assert not math.isclose(updated, initial, rel_tol=1e-9, abs_tol=1e-9)
    assert params["wheelbase"] == pytest.approx(get_slider_value(slider))
    assert settings.to_config_dict()["wheelbase"] == pytest.approx(
        get_slider_value(slider)
    )
