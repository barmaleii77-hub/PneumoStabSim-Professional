"""Unit tests for :class:`RoadPanel` parameter snapshots."""

from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for RoadPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.panel_road import RoadPanel


@pytest.mark.gui
def test_get_parameters_reflects_current_profile(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = RoadPanel()
    qtbot.addWidget(panel)

    initial = panel.get_parameters()
    assert initial["csv_path"] == ""
    assert initial["preset"] == ""
    assert initial["available_presets"]

    panel.current_csv_path = "/tmp/example.csv"
    panel.csv_path_label.setText(panel.current_csv_path)
    panel.current_preset = "City Streets"

    snapshot = panel.get_parameters()
    assert snapshot["csv_path"].endswith("example.csv")
    assert snapshot["preset"] == "City Streets"
    assert snapshot["has_profile"] is True

    snapshot["preset"] = "invalid"
    refreshed = panel.get_parameters()
    assert refreshed["preset"] == "City Streets"
