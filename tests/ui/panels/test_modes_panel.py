"""Unit tests for :class:`ModesPanel` parameter snapshots."""

from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for ModesPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.panel_modes import ModesPanel


@pytest.mark.gui
def test_get_parameters_returns_copy(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = ModesPanel()
    qtbot.addWidget(panel)

    panel._on_parameter_changed("amplitude", 0.42)  # noqa: SLF001 - signal helper
    panel._on_physics_option_changed("include_springs", True)

    snapshot = panel.get_parameters()
    assert snapshot["amplitude"] == pytest.approx(0.42)
    assert snapshot["physics"]["include_springs"] is True

    snapshot["amplitude"] = -1.0
    snapshot["physics"]["include_springs"] = False

    refreshed = panel.get_parameters()
    assert refreshed["amplitude"] == pytest.approx(0.42)
    assert refreshed["physics"]["include_springs"] is True
