#!/usr/bin/env python3
"""Synthetic effects performance benchmark using the existing performance monitor."""

from __future__ import annotations

import json
import logging
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.performance_monitor import PerformanceMonitor  # noqa: E402

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class EffectScenario:
    """Description of a synthetic effects workload."""

    name: str
    resolution: str
    effects: list[str]
    base_frame_time_ms: float
    effect_overhead_ms: float
    duration_s: float = 6.0
    sample_interval_s: float = 0.5

    @property
    def frame_time_ms(self) -> float:
        return self.base_frame_time_ms + self.effect_overhead_ms

    @property
    def frame_interval(self) -> float:
        return self.frame_time_ms / 1000.0


@dataclass
class ScenarioResult:
    scenario: EffectScenario
    averages: dict[str, float]
    sample_count: int


REPORT_DIR = Path("reports/performance")
REPORT_PATH = REPORT_DIR / "effects_performance_report.json"


def run_scenario(scenario: EffectScenario) -> ScenarioResult:
    """Run a synthetic scenario and capture metrics via PerformanceMonitor."""

    LOGGER.info(
        "Running effects scenario %s at %s with frame budget %.2f ms (+%.2f ms effects)",
        scenario.name,
        scenario.resolution,
        scenario.base_frame_time_ms,
        scenario.effect_overhead_ms,
    )
    monitor = PerformanceMonitor()
    monitor.start_monitoring(interval=scenario.sample_interval_s)
    try:
        deadline = time.time() + scenario.duration_s
        while time.time() < deadline:
            monitor.record_frame()
            time.sleep(scenario.frame_interval)
    finally:
        monitor.stop_monitoring()

    averages = monitor.get_average_metrics()
    return ScenarioResult(
        scenario=scenario,
        averages=averages,
        sample_count=len(monitor.metrics),
    )


def run_all(scenarios: Iterable[EffectScenario]) -> list[ScenarioResult]:
    """Execute all scenarios and persist a JSON report."""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[ScenarioResult] = []
    os_name = platform.system()
    LOGGER.info("Detected platform: %s", os_name)

    for scenario in scenarios:
        results.append(run_scenario(scenario))

    payload = {
        "platform": os_name,
        "scenarios": [
            {
                "name": result.scenario.name,
                "resolution": result.scenario.resolution,
                "effects": result.scenario.effects,
                "frame_time_ms": result.scenario.frame_time_ms,
                "base_frame_time_ms": result.scenario.base_frame_time_ms,
                "effect_overhead_ms": result.scenario.effect_overhead_ms,
                "duration_s": result.scenario.duration_s,
                "sample_interval_s": result.scenario.sample_interval_s,
                "sample_count": result.sample_count,
                "averages": result.averages,
            }
            for result in results
        ],
    }

    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LOGGER.info("Effects performance report written: %s", REPORT_PATH)
    return results


def main() -> int:
    scenarios = [
        EffectScenario(
            name="integrated_gpu_720p",
            resolution="1280x720",
            effects=["hdr_bloom", "lens_flare", "motion_blur"],
            base_frame_time_ms=16.7,
            effect_overhead_ms=9.3,
        ),
        EffectScenario(
            name="workstation_1080p",
            resolution="1920x1080",
            effects=["hdr_bloom", "dof", "chromatic_aberration"],
            base_frame_time_ms=12.0,
            effect_overhead_ms=5.8,
        ),
        EffectScenario(
            name="desktop_1440p",
            resolution="2560x1440",
            effects=["hdr_bloom", "dof", "lens_flare", "vignette"],
            base_frame_time_ms=8.5,
            effect_overhead_ms=3.2,
        ),
    ]

    run_all(scenarios)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
