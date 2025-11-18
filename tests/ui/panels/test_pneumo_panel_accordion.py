from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for PneumoPanel accordion tests",
    exc_type=ImportError,
)

from src.ui.panels.pneumo import PneumoPanel


@pytest.mark.gui
def test_pneumo_panel_exposes_accordion_sections(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = PneumoPanel()
    qtbot.addWidget(panel)

    qtbot.wait(250)

    accordion = panel.accordion
    assert {"volumes", "pressures", "valves"}.issubset(accordion.sections)

    volumes_section = accordion.get_section("volumes")
    assert volumes_section.is_expanded()

    content_widget = volumes_section.content_layout.itemAt(0).widget()
    assert content_widget is panel.receiver_tab


@pytest.mark.gui
def test_pneumo_panel_accordion_bindings(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = PneumoPanel()
    qtbot.addWidget(panel)

    emissions: list[dict[str, object]] = []
    panel.pneumatic_updated.connect(lambda payload: emissions.append(dict(payload)))

    qtbot.wait(250)

    knob = panel.receiver_tab.manual_volume_knob
    spinbox = knob.spinbox
    spinbox.setValue(spinbox.value() + spinbox.singleStep())
    qtbot.wait(200)

    assert emissions, "Expected pneumatic_updated to fire after accordion change"
    payload = emissions[-1]
    assert payload.get("receiver_volume") == pytest.approx(
        panel.state_manager.get_manual_volume()
    )
