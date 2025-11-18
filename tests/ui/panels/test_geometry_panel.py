"""Unit tests for the GeometryPanel public API."""

from __future__ import annotations

import math
from importlib import import_module

import pytest

from src.ui.geometry_schema import GeometrySettings
from src.ui.panels import panel_geometry

from ._slider_utils import get_slider_value, nudge_slider

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for GeometryPanel tests",
    exc_type=ImportError,
)

PANEL_TARGETS = (
    pytest.param("src.ui.panels.geometry", id="refactored"),
    pytest.param("src.ui.panels.panel_geometry", id="legacy"),
)


@pytest.fixture(params=PANEL_TARGETS)
def geometry_panel(request, qtbot: pytestqt.qtbot.QtBot):
    module = import_module(request.param)
    GeometryPanel = module.GeometryPanel
    panel = GeometryPanel()
    qtbot.addWidget(panel)
    return panel


def _get_wheelbase_slider(panel):
    if hasattr(panel, "frame_tab"):
        return panel.frame_tab.wheelbase_slider
    return panel.wheelbase_slider


@pytest.mark.gui
def test_get_parameters_returns_copy(
    geometry_panel, qtbot: pytestqt.qtbot.QtBot
) -> None:
    panel = geometry_panel

    snapshot = panel.get_parameters()
    settings = panel.get_geometry_settings()

    assert isinstance(snapshot, dict)
    assert "wheelbase" in snapshot
    assert isinstance(settings, GeometrySettings)
    settings_payload = settings.to_config_dict()
    assert settings_payload.items() <= snapshot.items()

    snapshot["wheelbase"] = -123.0

    refreshed = panel.get_parameters()
    assert refreshed["wheelbase"] != snapshot["wheelbase"]
    refreshed_settings = panel.get_geometry_settings()
    assert refreshed_settings.to_config_dict().items() <= refreshed.items()


@pytest.mark.gui
def test_collect_state_tracks_current_ui(
    geometry_panel, qtbot: pytestqt.qtbot.QtBot
) -> None:
    panel = geometry_panel

    assert hasattr(panel, "collect_state"), "collect_state() must be implemented"

    initial = panel.collect_state()
    assert isinstance(initial, dict)
    assert "wheelbase" in initial

    slider = _get_wheelbase_slider(panel)
    bumped = nudge_slider(slider, 0.02)
    qtbot.wait(350)

    snapshot = panel.collect_state()
    assert snapshot["wheelbase"] == pytest.approx(bumped)

    snapshot["wheelbase"] = -123.0
    refreshed = panel.collect_state()
    assert refreshed["wheelbase"] != snapshot["wheelbase"]


@pytest.mark.gui
@pytest.mark.parametrize("delta", [0.05, -0.05])
def test_get_parameters_tracks_slider_updates(
    geometry_panel, qtbot: pytestqt.qtbot.QtBot, delta: float
) -> None:
    panel = geometry_panel

    slider = _get_wheelbase_slider(panel)
    initial = get_slider_value(slider)
    updated = nudge_slider(slider, delta)
    qtbot.wait(350)

    params = panel.get_parameters()
    settings = panel.get_geometry_settings().to_config_dict()
    assert not math.isclose(updated, initial, rel_tol=1e-9, abs_tol=1e-9)
    assert settings.items() <= params.items()
    assert params["wheelbase"] == pytest.approx(get_slider_value(slider))


@pytest.mark.gui
def test_startup_subscriber_probe_handles_missing_receivers(
    geometry_panel, qtbot: pytestqt.qtbot.QtBot, monkeypatch
) -> None:
    panel = geometry_panel
    qtbot.addWidget(panel)

    target_module = import_module(panel.__module__)

    class _BrokenMeta:
        @staticmethod
        def fromSignal(_signal):
            raise AttributeError("receivers unavailable")

    monkeypatch.setattr(target_module, "QMetaMethod", _BrokenMeta, raising=False)

    assert panel._verify_geometry_subscribers() is None
    panel._emit_initial()  # should not raise despite probe failure
