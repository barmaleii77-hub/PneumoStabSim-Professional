"""Behavioural tests for :class:`TrainingPresetBridge`."""

from __future__ import annotations

import math

import pytest

pytest.importorskip("pytestqt")
pytest.importorskip("PySide6.QtTest")

from PySide6.QtTest import QSignalSpy

from tests.scenarios import SCENARIO_INDEX


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

    presets_spy = QSignalSpy(training_preset_bridge.presetsChanged)
    active_spy = QSignalSpy(training_preset_bridge.activePresetChanged)
    selected_spy = QSignalSpy(training_preset_bridge.selectedPresetChanged)

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

    active_spy = QSignalSpy(training_preset_bridge.activePresetChanged)
    selected_spy = QSignalSpy(training_preset_bridge.selectedPresetChanged)

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
