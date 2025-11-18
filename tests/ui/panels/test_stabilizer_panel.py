"""Tests for the StabilizerPanel widget API."""

from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for StabilizerPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.stabilizer_panel import StabilizerPanel


@pytest.mark.gui
def test_stabilizer_panel_get_parameters_reflects_spinbox(
    qtbot: pytestqt.qtbot.QtBot,
) -> None:
    panel = StabilizerPanel()
    qtbot.addWidget(panel)

    qtbot.wait(50)

    step = panel._spinbox.singleStep()
    panel._spinbox.setValue(panel._spinbox.value() + step)

    snapshot = panel.get_parameters()
    assert snapshot["diagonal_coupling_dia"] == pytest.approx(panel._spinbox.value())

    snapshot["diagonal_coupling_dia"] = 0.0
    refreshed = panel.get_parameters()
    assert refreshed["diagonal_coupling_dia"] == pytest.approx(panel._spinbox.value())


@pytest.mark.gui
def test_collect_state_matches_parameters(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = StabilizerPanel()
    qtbot.addWidget(panel)

    initial = panel.collect_state()
    assert initial == panel.get_parameters()

    initial["diagonal_coupling_dia"] = 0.1234
    refreshed = panel.collect_state()
    assert refreshed["diagonal_coupling_dia"] != 0.1234
