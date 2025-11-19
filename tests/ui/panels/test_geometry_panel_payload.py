"""End-to-end payload validation for :class:`GeometryPanel`."""

from __future__ import annotations

import math

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for GeometryPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.panel_geometry import GeometryPanel
from src.ui.qml_bridge import QMLBridge

from ._bridge_window_stub import BridgeWindowStub
from ._slider_utils import get_slider_value, nudge_slider


@pytest.mark.gui
@pytest.mark.parametrize(
    "delta",
    [0.05, -0.07],
)
def test_geometry_panel_queues_payload_matches_bridge_schema(
    qtbot: pytestqt.qtbot.QtBot, monkeypatch: pytest.MonkeyPatch, delta: float
) -> None:
    """Ensure geometry slider edits push bridge-ready payloads."""

    captured: list[tuple[str, dict[str, float]]] = []

    def _queue_stub(_window: object, category: str, payload: dict[str, float]) -> None:
        # store shallow copy to avoid subsequent mutation surprises
        captured.append((category, dict(payload)))

    monkeypatch.setattr(QMLBridge, "queue_update", _queue_stub)

    panel = GeometryPanel()
    qtbot.addWidget(panel)

    window = BridgeWindowStub()
    panel.geometry_changed.connect(
        lambda payload: QMLBridge.queue_update(window, "geometry", payload)
    )

    # Allow the deferred initial emission to complete, then ignore it
    qtbot.wait(400)
    captured.clear()

    slider = panel.wheelbase_slider
    initial_value = get_slider_value(slider)
    slider.value_spinbox.setFocus()
    qtbot.wait(50)
    updated_value = nudge_slider(slider, delta)
    qtbot.wait(300)

    assert captured, "GeometryPanel did not enqueue any payloads"

    category, payload = captured[-1]
    assert category == "geometry"
    assert category in QMLBridge.describe_routes()

    required_keys = {
        "frameLength",
        "leverLength",
        "cylinderBodyLength",
        "trackWidth",
        "frameToPivot",
        "rodPosition",
        "boreHead",
        "rodDiameter",
        "rodDiameterRear",
        "pistonRodLength",
        "pistonThickness",
        "rodDiameterM",
        "rodDiameterFrontM",
        "rodDiameterRearM",
        "rod_diameter_front_mm",
        "rod_diameter_rear_mm",
        "rod_diameter_mm",
    }
    missing = required_keys.difference(payload)
    assert not missing, f"Geometry payload missing keys: {sorted(missing)}"

    assert not math.isclose(updated_value, initial_value, rel_tol=1e-9, abs_tol=1e-9)
    assert payload["frameLength"] == pytest.approx(get_slider_value(slider))
    assert payload["rodDiameterFrontM"] == pytest.approx(payload["rodDiameterM"])
    assert payload["rod_diameter_front_mm"] == pytest.approx(
        payload["rodDiameterFrontM"] * 1000.0
    )
    assert payload["rod_diameter_rear_mm"] == pytest.approx(
        payload["rodDiameterRearM"] * 1000.0
    )
