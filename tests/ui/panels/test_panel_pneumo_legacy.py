import pytest
import pytestqt

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for pneumatic panel tests",
    exc_type=ImportError,
)

from src.ui.panels.panel_pneumo_legacy import PneumoPanel


@pytest.mark.gui
@pytest.mark.qtbot
def test_pneumo_legacy_get_parameters_tracks_state(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = PneumoPanel()
    qtbot.addWidget(panel)

    snapshot = panel.get_parameters()
    assert isinstance(snapshot, dict)

    snapshot["master_isolation_open"] = not snapshot.get("master_isolation_open", False)
    refreshed = panel.get_parameters()
    assert refreshed.get("master_isolation_open") != snapshot["master_isolation_open"]

    target_state = not panel.master_isolation_check.isChecked()
    panel.master_isolation_check.setChecked(target_state)
    qtbot.wait(50)

    updated = panel.get_parameters()
    assert updated.get("master_isolation_open") == target_state
