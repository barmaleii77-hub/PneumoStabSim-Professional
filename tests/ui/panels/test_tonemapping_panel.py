"""Unit tests for :class:`TonemappingPanel` state accessors."""

from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for TonemappingPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.tonemapping_panel import TonemappingPanel


@pytest.mark.gui
def test_get_parameters_tracks_active_preset(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = TonemappingPanel()
    qtbot.addWidget(panel)

    snapshot = panel.get_parameters()
    assert "active_preset" in snapshot
    assert "effects" in snapshot and isinstance(snapshot["effects"], dict)

    combo = panel._combo  # noqa: SLF001 - test helper access
    if combo is None or combo.count() <= 1:
        pytest.skip("No tonemapping presets available for selection")

    combo.setCurrentIndex(1)
    qtbot.wait(50)

    updated = panel.get_parameters()
    expected_id = str(combo.currentData() or "")
    assert updated["active_preset"] == expected_id

    updated["effects"]["tonemap_mode"] = "custom_marker"
    refreshed = panel.get_parameters()
    assert refreshed["effects"].get("tonemap_mode") != "custom_marker"
