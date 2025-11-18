from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_sync_module():
    project_root = Path(__file__).resolve().parents[2]
    sync_path = project_root / "src" / "runtime" / "sync.py"
    spec = importlib.util.spec_from_file_location("runtime_sync_module", sync_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_sync = _load_sync_module()
PerformanceMetrics = _sync.PerformanceMetrics
TimingAccumulator = _sync.TimingAccumulator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_FILE = PROJECT_ROOT / "reports" / "performance" / "render_sync_test_report.json"


@pytest.mark.performance
def test_performance_metrics_record_and_report() -> None:
    durations = [0.0012, 0.0008, 0.0015, 0.0020, 0.0010]
    metrics = PerformanceMetrics()

    for duration in durations:
        metrics.update_step_time(duration)
        metrics.update_realtime_factor(sim_dt=0.001, real_dt=duration)

    summary = metrics.get_summary()
    assert summary["steps"] == len(durations)
    assert summary["fps_actual"] > 0
    assert summary["avg_step_time_ms"] > 0

    report_payload = {
        "render_sync": {
            "summary": summary,
            "max_step_ms": metrics.max_step_time * 1000,
            "min_step_ms": metrics.min_step_time * 1000,
            "dt_variance": metrics.dt_variance,
        }
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    assert REPORT_FILE.exists()
    parsed = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
    assert parsed["render_sync"]["summary"]["steps"] == len(durations)


@pytest.mark.performance
def test_timing_accumulator_limits_frame_budget() -> None:
    accumulator = TimingAccumulator(
        target_dt=0.01, max_steps_per_frame=5, max_frame_time=0.05
    )

    accumulator.last_time = accumulator.last_time - 0.2
    steps = accumulator.update()

    assert steps == accumulator.max_steps_per_frame
    assert accumulator.total_real_time <= accumulator.max_frame_time + 1e-6
    assert accumulator.get_interpolation_alpha() >= 0.0

    accumulator.reset()
    assert accumulator.steps_taken == 0
    assert accumulator.total_sim_time == 0.0
