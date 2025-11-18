from __future__ import annotations

import os

import pytest

from tests.helpers import SignalListener


@pytest.mark.headless
@pytest.mark.usefixtures("headless_env", "headless_qt_modules")
def test_training_bridge_emits_signals_on_apply_headless(headless_qtbot, training_preset_bridge):
    from tests._qt_headless import HEADLESS_FLAG
    from tests.helpers import SignalListener

    assert os.environ.get(HEADLESS_FLAG) == "1"

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
    headless_qtbot.waitUntil(lambda: presets_spy.count() >= 1, timeout=1000)

    assert training_preset_bridge.applyPreset(target_id)

    selected = training_preset_bridge.selectedPresetSnapshot()
    assert training_preset_bridge.activePresetId == target_id
    assert selected.get("id") == target_id
    assert selected.get("metadata", {}).get("scenarioId", "")
    assert active_spy.count() in (0, 1)
    assert selected_spy.count() in (0, 1)


@pytest.mark.headless
@pytest.mark.usefixtures("headless_env", "headless_qt_modules")
def test_training_bridge_detects_settings_drift_headless(
    headless_qtbot, training_preset_bridge, settings_manager
):
    preset_id = training_preset_bridge.defaultPresetId()
    assert training_preset_bridge.applyPreset(preset_id)

    active_spy = SignalListener(training_preset_bridge.activePresetChanged)
    selected_spy = SignalListener(training_preset_bridge.selectedPresetChanged)

    settings_manager.set("current.simulation.physics_dt", 0.123456, auto_save=False)

    headless_qtbot.waitUntil(lambda: active_spy.count() >= 1, timeout=1000)
    headless_qtbot.waitUntil(lambda: selected_spy.count() >= 1, timeout=1000)

    assert training_preset_bridge.activePresetId == ""
    assert training_preset_bridge.selectedPresetSnapshot() == {}


@pytest.mark.headless
@pytest.mark.usefixtures("headless_env", "headless_qt_modules")
def test_training_bridge_plays_nicely_with_simulation_headless(
    simulation_harness, training_preset_bridge
):
    preset_id = training_preset_bridge.defaultPresetId()
    assert training_preset_bridge.applyPreset(preset_id)

    metrics = simulation_harness(runtime_ms=25)
    assert metrics["runtime_ms"] == 25
