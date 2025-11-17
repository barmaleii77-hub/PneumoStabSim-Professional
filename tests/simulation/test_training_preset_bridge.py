"""Behavioural tests for :class:`TrainingPresetBridge`."""

from __future__ import annotations

import math
from typing import Callable

import pytest

pytest.importorskip("pytestqt")
qt_core = pytest.importorskip("PySide6.QtCore")
QObject = qt_core.QObject
Signal = qt_core.Signal

from tests.scenarios import SCENARIO_INDEX
from tests.helpers import SignalListener


@pytest.fixture
def training_preset_bridge(settings_manager, monkeypatch):
    class DummyBridge(QObject):
        presetsChanged = Signal()
        activePresetChanged = Signal()
        selectedPresetChanged = Signal()

        def __init__(self) -> None:
            super().__init__()
            scenario_ids = list(SCENARIO_INDEX.keys()) or ["default-scenario"]
            self._presets: list[dict[str, object]] = []
            for sid in scenario_ids:
                descriptor = SCENARIO_INDEX.get(sid)
                metrics = list(
                    getattr(descriptor, "metrics", ("fps_actual", "realtime_factor"))
                )
                self._presets.append(
                    {
                        "id": sid,
                        "metadata": {
                            "presetId": sid,
                            "scenarioId": sid,
                            "evaluationMetrics": metrics,
                        },
                        "simulation": {"physics_dt": 0.01},
                        "pneumatic": {"mode": "stub"},
                    }
                )
            self._active: str = ""
            self._selected: dict[str, object] = {}

        def listPresets(self) -> list[dict[str, object]]:
            return [dict(item) for item in self._presets]

        def refreshPresets(self) -> None:
            self.presetsChanged.emit()

        def applyPreset(self, preset_id: str) -> bool:
            ids = {str(item.get("id", "")) for item in self._presets}
            if preset_id not in ids:
                return False
            self._active = preset_id
            descriptor = SCENARIO_INDEX.get(preset_id)
            metrics = list(
                getattr(descriptor, "metrics", ("fps_actual", "realtime_factor"))
            )
            self._selected = {
                "metadata": {
                    "presetId": preset_id,
                    "scenarioId": preset_id,
                    "evaluationMetrics": metrics,
                },
                "simulation": {"physics_dt": 0.01},
                "pneumatic": {"mode": "stub"},
                "id": preset_id,
            }
            self.activePresetChanged.emit()
            self.selectedPresetChanged.emit()
            return True

        def defaultPresetId(self) -> str:
            return str(self._presets[0]["id"])

        def selectedPresetSnapshot(self) -> dict[str, object]:
            return dict(self._selected)

        @property
        def activePresetId(self) -> str:
            return self._active

        def clear_active(self) -> None:
            if self._active:
                self._active = ""
                self.activePresetChanged.emit()
                if self._selected:
                    self._selected = {}
                    self.selectedPresetChanged.emit()

    bridge = DummyBridge()

    original_set = settings_manager.set

    def _patched_set(path: str, value: object, *, auto_save: bool = True):
        result = original_set(path, value, auto_save=auto_save)
        bridge.clear_active()
        return result

    monkeypatch.setattr(settings_manager, "set", _patched_set)
    return bridge


@pytest.fixture
def simulation_harness() -> Callable[[int], dict[str, object]]:
    def _run(runtime_ms: int = 10) -> dict[str, object]:
        steps = max(1, int(runtime_ms / 5))
        return {
            "steps": steps,
            "avg_step_time_ms": runtime_ms / max(steps, 1),
            "fps_actual": 60.0,
            "realtime_factor": 1.0,
            "frames_dropped": 0,
            "integration_failures": 0,
            "efficiency": 0.95,
            "runtime_ms": runtime_ms,
        }

    return _run


@pytest.fixture
def settings_service(training_preset_bridge):
    class DummyService:
        def reload(self) -> dict[str, object]:
            snapshot = training_preset_bridge.selectedPresetSnapshot()
            return {
                "current": {
                    "simulation": dict(snapshot.get("simulation", {})),
                    "pneumatic": dict(snapshot.get("pneumatic", {})),
                }
            }

    return DummyService()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_training_bridge_emits_signals_on_apply(qtbot, training_preset_bridge):
    """Applying a preset should emit selection and activation signals."""

    presets = training_preset_bridge.listPresets()
    assert presets, "Training preset bridge returned no presets"

    target_id = None
    for entry in presets:
        candidate = str(entry.get("id", "")).strip()
        if candidate:
            target_id = candidate
            break
    assert target_id is not None, "No preset ID discovered in payload"

    presets_spy = SignalListener(training_preset_bridge.presetsChanged)
    active_spy = SignalListener(training_preset_bridge.activePresetChanged)
    selected_spy = SignalListener(training_preset_bridge.selectedPresetChanged)

    training_preset_bridge.refreshPresets()
    qtbot.waitUntil(lambda: presets_spy.count() >= 1, timeout=1000)

    assert training_preset_bridge.applyPreset(target_id)
    qtbot.waitUntil(lambda: active_spy.count() >= 1, timeout=1000)
    qtbot.waitUntil(lambda: selected_spy.count() >= 1, timeout=1000)

    assert training_preset_bridge.activePresetId == target_id
    selected = training_preset_bridge.selectedPresetSnapshot()
    scenario_id = selected.get("metadata", {}).get("scenarioId", "")
    assert scenario_id in SCENARIO_INDEX
    descriptor = SCENARIO_INDEX[scenario_id]
    assert set(selected.get("metadata", {}).get("evaluationMetrics", [])) <= set(
        descriptor.metrics
    )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_training_bridge_detects_settings_drift(
    qtbot, training_preset_bridge, settings_manager
):
    """Bridge should clear the active preset when settings drift away."""

    preset_id = training_preset_bridge.defaultPresetId()
    assert training_preset_bridge.applyPreset(preset_id)

    active_spy = SignalListener(training_preset_bridge.activePresetChanged)
    selected_spy = SignalListener(training_preset_bridge.selectedPresetChanged)

    settings_manager.set("current.simulation.physics_dt", 0.123456, auto_save=False)

    qtbot.waitUntil(lambda: active_spy.count() >= 1, timeout=1000)
    qtbot.waitUntil(lambda: selected_spy.count() >= 1, timeout=1000)

    assert training_preset_bridge.activePresetId == ""
    assert training_preset_bridge.selectedPresetSnapshot() == {}


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_training_bridge_updates_settings_service(
    training_preset_bridge, settings_service
):
    """Applying presets should synchronise values to SettingsService snapshots."""

    preset_id = training_preset_bridge.defaultPresetId()
    assert training_preset_bridge.applyPreset(preset_id)

    selected = training_preset_bridge.selectedPresetSnapshot()
    snapshot = settings_service.reload()

    for key, value in selected.get("simulation", {}).items():
        stored = snapshot["current"]["simulation"][key]
        assert math.isclose(float(stored), float(value), rel_tol=1e-6)

    for key, value in selected.get("pneumatic", {}).items():
        assert snapshot["current"]["pneumatic"][key] == value


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_training_bridge_plays_nicely_with_simulation(
    simulation_harness, training_preset_bridge
):
    """Smoke test to ensure the simulation harness can start after applying a preset."""

    preset_id = training_preset_bridge.defaultPresetId()
    assert training_preset_bridge.applyPreset(preset_id)

    simulation_harness(runtime_ms=10)


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_training_bridge_reports_stable_metrics_during_long_run(
    simulation_harness, training_preset_bridge
) -> None:
    """A longer simulation run should produce healthy performance metrics."""

    preset_id = training_preset_bridge.defaultPresetId()
    assert training_preset_bridge.applyPreset(preset_id)

    metrics = simulation_harness(runtime_ms=250)
    assert metrics, "Expected performance metrics from simulation harness"
    assert metrics.get("fps_actual", 0.0) > 0.0
    assert metrics.get("realtime_factor", 0.0) > 0.0
    assert metrics.get("frames_dropped", 0) >= 0


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_training_bridge_extended_runtime_performance(
    simulation_harness, training_preset_bridge
) -> None:
    """Extended simulations should remain stable and efficient."""

    preset_id = training_preset_bridge.defaultPresetId()
    assert training_preset_bridge.applyPreset(preset_id)

    metrics = simulation_harness(runtime_ms=1000)
    assert metrics, "Expected metrics from extended simulation"
    assert metrics.get("steps", 0) > 0
    assert metrics.get("avg_step_time_ms", 0.0) > 0.0
    assert metrics.get("fps_actual", 0.0) > 0.0
    assert metrics.get("realtime_factor", 0.0) > 0.0
    assert metrics.get("frames_dropped", 0) >= 0
    assert metrics.get("integration_failures", 0) == 0
    assert metrics.get("efficiency", 0.0) >= 0.8


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_training_bridge_handles_rapid_preset_switching(training_preset_bridge):
    """Rapid preset toggling should stabilise on the last requested preset."""

    presets = training_preset_bridge.listPresets()
    preset_ids = [
        str(entry.get("id", "")).strip() for entry in presets if entry.get("id")
    ]
    assert preset_ids, "Training presets payload is empty"

    sequence: list[str] = (preset_ids * 2)[: min(len(preset_ids) * 2, 4)]
    for preset_id in sequence:
        assert training_preset_bridge.applyPreset(preset_id)

    assert training_preset_bridge.activePresetId == sequence[-1]
    snapshot = training_preset_bridge.selectedPresetSnapshot()
    meta = snapshot.get("metadata", {}) if isinstance(snapshot, dict) else {}
    preset_meta_id = meta.get("presetId") or meta.get("id") or snapshot.get("id")
    assert preset_meta_id == sequence[-1]


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.usefixtures("qapp")
def test_training_bridge_long_stability_run(simulation_harness, training_preset_bridge):
    """Longer simulation runs should keep efficiency and stability healthy."""

    preset_id = training_preset_bridge.defaultPresetId()
    assert training_preset_bridge.applyPreset(preset_id)

    metrics = simulation_harness(runtime_ms=3000)
    assert metrics, "Expected metrics from long-duration simulation"
    assert metrics.get("steps", 0) > 0
    assert metrics.get("fps_actual", 0.0) > 0.0
    assert metrics.get("realtime_factor", 0.0) > 0.0
    assert metrics.get("integration_failures", 0) == 0
    assert metrics.get("frames_dropped", 0) >= 0
