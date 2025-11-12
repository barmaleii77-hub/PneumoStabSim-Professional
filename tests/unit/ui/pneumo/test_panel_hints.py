"""UI hint behaviour for pneumatic panel components."""

from __future__ import annotations

import pytest
import pytestqt

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for PneumoPanel hint tests",
    exc_type=ImportError,
)

from src.ui.panels.pneumo.receiver_tab import ReceiverTab
from src.ui.panels.pneumo.pressures_tab import PressuresTab
from src.ui.panels.pneumo.state_manager import PneumoStateManager
from tests.unit.ui.pneumo.test_state_manager_units import DummySettings


@pytest.mark.gui
def test_receiver_tab_shows_hint_when_volume_clamped(
    qtbot: pytestqt.qtbot.QtBot,
) -> None:
    manager = PneumoStateManager(settings_manager=DummySettings())
    tab = ReceiverTab(manager)
    qtbot.addWidget(tab)

    manager.set_manual_volume(5.0)
    tab.update_from_state()

    assert tab.volume_hint_label.isVisible()
    assert "скорректирован" in tab.volume_hint_label.text()

    manager.set_manual_volume(0.05)
    tab.update_from_state()

    assert not tab.volume_hint_label.isVisible()


@pytest.mark.gui
def test_pressures_tab_reports_relief_adjustments(
    qtbot: pytestqt.qtbot.QtBot,
) -> None:
    manager = PneumoStateManager(settings_manager=DummySettings())
    tab = PressuresTab(manager)
    qtbot.addWidget(tab)

    manager.set_relief_pressure("relief_min_pressure", 60.0)
    tab.update_from_state()

    assert tab.hint_label.isVisible()
    assert "скорректирован" in tab.hint_label.text()

    manager.set_relief_pressure("relief_min_pressure", 3.0)
    tab.update_from_state()

    assert not tab.hint_label.isVisible()
