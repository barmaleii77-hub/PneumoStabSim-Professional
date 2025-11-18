from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 widgets require Qt libraries that must be available",
    exc_type=ImportError,
)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.ui.panels.graphics.panel_graphics import GraphicsPanel
from src.ui.panels.modes.panel_modes_refactored import ModesPanel

REPORT_PATH = Path("reports/tests/panel_rendering_performance.json")


def _persist_metric(metric: str, payload: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, object] = {}
    if REPORT_PATH.exists():
        try:
            existing = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing[metric] = payload
    REPORT_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")


@pytest.mark.performance
@pytest.mark.usefixtures("qapp")
def test_graphics_panel_collect_state_within_budget(qapp) -> None:
    panel = GraphicsPanel()

    iterations = 12
    start = time.perf_counter()
    snapshot: dict | None = None
    for _ in range(iterations):
        snapshot = panel.collect_state()
    elapsed = time.perf_counter() - start

    assert snapshot is not None
    assert "lighting" in snapshot and "scene" in snapshot

    average_ms = (elapsed / iterations) * 1000.0
    _persist_metric(
        "graphics_collect_state",
        {
            "iterations": iterations,
            "total_seconds": elapsed,
            "average_ms": average_ms,
            "budget_ms": 25.0,
        },
    )

    assert average_ms < 25.0, "GraphicsPanel.collect_state exceeded render budget"


@pytest.mark.performance
@pytest.mark.usefixtures("qapp")
def test_modes_panel_collect_and_validate_within_budget(qapp) -> None:
    panel = ModesPanel()

    panel.state_manager.update_parameter("amplitude", 0.12)
    panel.state_manager.update_parameter("frequency", 1.5)
    panel.state_manager.update_parameter("phase", 0.0)
    panel.state_manager.update_parameter("smoothing_duration_ms", 120.0)

    iterations = 25
    start = time.perf_counter()
    payload: dict | None = None
    errors: list[str] = []
    for idx in range(iterations):
        panel.state_manager.update_parameter(
            "sim_type", "KINEMATICS" if idx % 2 else "DYNAMICS"
        )
        payload = panel.collect_state()
        errors = panel.validate_state()
    elapsed = time.perf_counter() - start

    assert payload is not None and payload.get("physics")
    assert not errors

    average_ms = (elapsed / iterations) * 1000.0
    _persist_metric(
        "modes_collect_and_validate",
        {
            "iterations": iterations,
            "total_seconds": elapsed,
            "average_ms": average_ms,
            "budget_ms": 15.0,
        },
    )

    assert average_ms < 15.0, "ModesPanel collect/validate path exceeded sync budget"
