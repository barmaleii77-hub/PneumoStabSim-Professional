"""Performance checks for render payload generation and sync."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.pneumo.enums import Line
from src.runtime.state import StateSnapshot
from src.ui.qml_bridge import QMLBridge

REPORT_DIR = Path("reports/performance")


def _build_snapshot() -> StateSnapshot:
    snapshot = StateSnapshot()
    snapshot.simulation_time = 1.2

    line_a1 = snapshot.lines[Line.A1]
    line_a1.flow_atmo = 0.12
    line_a1.flow_tank = 0.08
    line_a1.pressure = 125_000.0
    line_a1.temperature = 301.0

    line_b1 = snapshot.lines[Line.B1]
    line_b1.flow_atmo = 0.06
    line_b1.flow_tank = 0.04
    line_b1.pressure = 123_500.0
    line_b1.temperature = 298.5

    snapshot.tank.pressure = 131_000.0
    snapshot.tank.temperature = 302.5
    snapshot.tank.flow_min = 0.06
    snapshot.tank.relief_min_open = True
    snapshot.tank.flow_stiff = -0.03
    snapshot.tank.relief_stiff_open = True
    snapshot.tank.flow_safety = 0.02
    snapshot.tank.relief_safety_open = False

    snapshot.master_isolation_open = True
    snapshot.frame.heave = 0.15
    snapshot.frame.roll = 0.03
    snapshot.frame.pitch = -0.02
    return snapshot


@pytest.mark.performance
@pytest.mark.slow
def test_snapshot_payload_throughput(tmp_path_factory) -> None:
    snapshot = _build_snapshot()
    iterations = 64

    start = time.perf_counter()
    payloads: list[dict[str, object]] = []
    for _ in range(iterations):
        payloads.append(QMLBridge._snapshot_to_payload(snapshot))
    duration = time.perf_counter() - start

    assert payloads[-1]["threeD"]["flowNetwork"]["lines"], "Flow network payload missing"

    metrics = {
        "iterations": iterations,
        "duration_s": duration,
        "throughput_per_s": iterations / duration if duration else float("inf"),
    }

    report_dir = tmp_path_factory.mktemp("render_sync_reports")
    report_dir_path = Path(report_dir)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "metrics": metrics,
        "report_path": report_dir_path.as_posix(),
    }

    perf_report = report_dir_path / "render_sync_benchmark.json"
    perf_report.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    consolidated = REPORT_DIR / "render_sync_benchmark.json"
    consolidated.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    assert metrics["throughput_per_s"] > 1.0, "Render sync throughput degraded"
