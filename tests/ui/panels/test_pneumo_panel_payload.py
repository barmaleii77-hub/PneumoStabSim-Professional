"""Bridge payload validation for :class:`PneumoPanel`."""

from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for PneumoPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.pneumo import PneumoPanel
from src.ui.qml_bridge import QMLBridge


@pytest.mark.gui
def test_pneumo_panel_emits_simulation_payload(
    qtbot: pytestqt.qtbot.QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Changing receiver volume should surface simulation payload."""

    captured: list[tuple[str, dict[str, object]]] = []

    def _queue_stub(_window: object, category: str, payload: dict[str, object]) -> None:
        captured.append((category, dict(payload)))

    monkeypatch.setattr(QMLBridge, "queue_update", _queue_stub)

    panel = PneumoPanel()
    qtbot.addWidget(panel)

    panel.pneumatic_updated.connect(
        lambda payload: QMLBridge.queue_update(object(), "simulation", payload)
    )

    qtbot.wait(300)
    captured.clear()

    knob = panel.receiver_tab.manual_volume_knob
    spinbox = knob.spinbox
    spinbox.setFocus()
    qtbot.wait(50)
    spinbox.setValue(spinbox.value() + spinbox.singleStep())
    qtbot.wait(250)

    assert captured, "PneumoPanel did not enqueue any simulation payloads"

    category, payload = captured[-1]
    assert category == "simulation"
    assert category in QMLBridge.describe_routes()

    assert "receiver_volume" in payload
    assert "volume_mode" in payload
    assert payload["volume_mode"] in {"MANUAL", "GEOMETRIC"}
    assert payload["receiver_volume"] == pytest.approx(
        panel.state_manager.get_manual_volume()
    )

    # ensure additional pneumatic metadata (e.g. pressure units) travels along
    assert "pressure_units" in payload
