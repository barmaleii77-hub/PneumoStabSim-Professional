"""Regression tests for the legacy :class:`PneumoPanel` API."""

from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for PneumoPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.panel_pneumo_legacy import PneumoPanel


@pytest.mark.gui
def test_get_parameters_returns_copy(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = PneumoPanel()
    qtbot.addWidget(panel)

    snapshot = panel.get_parameters()

    assert isinstance(snapshot, dict)
    assert snapshot == panel.parameters

    snapshot["receiver_volume"] = -1.0

    refreshed = panel.get_parameters()

    assert refreshed["receiver_volume"] != snapshot["receiver_volume"]
    assert refreshed["receiver_volume"] == panel.parameters["receiver_volume"]


@pytest.mark.gui
def test_get_parameters_tracks_ui_changes(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = PneumoPanel()
    qtbot.addWidget(panel)

    # Ensure the manual volume mode is active to reflect knob changes
    panel.volume_mode_combo.setCurrentIndex(0)
    qtbot.wait(20)

    initial = float(panel.manual_volume_knob.value())
    new_value = min(panel.manual_volume_knob.maximum(), initial + 0.005)
    if new_value == initial:
        new_value = max(panel.manual_volume_knob.minimum(), initial - 0.005)

    panel.manual_volume_knob.setValue(new_value)
    qtbot.wait(20)

    refreshed = panel.get_parameters()

    assert refreshed["volume_mode"] == "MANUAL"
    assert refreshed["receiver_volume"] == pytest.approx(new_value)
