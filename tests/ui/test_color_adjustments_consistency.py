from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 required for UI tests",
    exc_type=ImportError,
)

from src.ui.panels.graphics.effects_tab import EffectsTab


@pytest.mark.gui
def test_color_adjustments_active_follows_enabled(qtbot):
    tab = EffectsTab()
    qtbot.addWidget(tab)

    state = tab.get_state()
    enabled = state["color_adjustments_enabled"]
    active = state["color_adjustments_active"]
    assert active == enabled

    # Toggle via UI control
    checkbox = tab._controls["color.enabled"]
    checkbox.setChecked(not enabled)
    qtbot.wait(50)
    updated = tab.get_state()
    assert updated["color_adjustments_active"] == updated["color_adjustments_enabled"]

    # Force mismatch then set_state should reconcile
    broken = dict(updated)
    broken["color_adjustments_active"] = not broken["color_adjustments_enabled"]
    tab.set_state(broken)
    reconciled = tab.get_state()
    assert reconciled["color_adjustments_active"] == reconciled["color_adjustments_enabled"]
