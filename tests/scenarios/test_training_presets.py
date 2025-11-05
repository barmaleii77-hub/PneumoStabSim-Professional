from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.common.settings_manager import SettingsManager
from src.simulation.presets import get_default_training_library
from tests.scenarios import SCENARIO_INDEX


def _clone_settings(tmp_path: Path) -> Path:
    source = Path("config/app_settings.json")
    payload = json.loads(source.read_text(encoding="utf-8"))
    target = tmp_path / "app_settings.json"
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return target


def test_default_presets_align_with_scenarios() -> None:
    library = get_default_training_library()
    presets = library.list_presets()
    assert len(presets) >= 4

    scenario_ids = {preset.metadata.scenario_id for preset in presets}
    assert scenario_ids <= set(SCENARIO_INDEX)

    for preset in presets:
        assert preset.simulation["physics_dt"] > 0
        assert preset.metadata.duration_minutes > 0
        assert preset.to_qml_payload()["id"] == preset.id
        descriptor = SCENARIO_INDEX[preset.metadata.scenario_id]
        assert descriptor.difficulty in {preset.metadata.difficulty, "mixed"}
        assert descriptor.label == preset.metadata.scenario_label
        assert descriptor.summary == preset.metadata.scenario_summary
        for metric in preset.metadata.evaluation_metrics:
            assert metric in descriptor.metrics

    assert library.get("endurance_validation") is not None


def test_apply_preset_updates_settings(tmp_path: Path) -> None:
    settings_path = _clone_settings(tmp_path)
    manager = SettingsManager(settings_file=settings_path)
    library = get_default_training_library()

    library.apply(manager, "precision_mode", auto_save=False)
    snapshot = {
        "simulation": manager.get("current.simulation", {}),
        "pneumatic": manager.get("current.pneumatic", {}),
    }
    assert library.resolve_active_id(snapshot) == "precision_mode"
    assert snapshot["simulation"]["physics_dt"] == pytest.approx(0.0005)
    assert snapshot["pneumatic"]["volume_mode"] == "GEOMETRIC"


def test_matches_settings_detects_drift() -> None:
    library = get_default_training_library()
    baseline = library.get("baseline")
    assert baseline is not None

    snapshot = {
        "simulation": dict(baseline.simulation),
        "pneumatic": dict(baseline.pneumatic),
    }
    assert baseline.matches_settings(snapshot)

    drifted = {
        "simulation": dict(baseline.simulation),
        "pneumatic": dict(baseline.pneumatic),
    }
    drifted["simulation"]["physics_dt"] += 0.001
    assert not baseline.matches_settings(drifted)


def test_resolve_active_id_round_trip(tmp_path: Path) -> None:
    settings_path = _clone_settings(tmp_path)
    manager = SettingsManager(settings_file=settings_path)
    library = get_default_training_library()

    library.apply(manager, "rapid_iteration", auto_save=True)
    snapshot = {
        "simulation": manager.get("current.simulation", {}),
        "pneumatic": manager.get("current.pneumatic", {}),
    }
    assert library.resolve_active_id(snapshot) == "rapid_iteration"
