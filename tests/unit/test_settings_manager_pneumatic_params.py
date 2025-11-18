"""Ensure SettingsManager handles new pneumatic parameters."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.common.settings_manager import SettingsManager


PROJECT_SETTINGS = Path(__file__).resolve().parents[2] / "config" / "app_settings.json"


def _write_settings(tmp_path: Path) -> Path:
    payload = json.loads(PROJECT_SETTINGS.read_text(encoding="utf-8"))
    target = tmp_path / "settings.json"
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return target


def test_settings_manager_loads_pneumatic_pressures_and_volumes(tmp_path: Path) -> None:
    settings_path = _write_settings(tmp_path)

    manager = SettingsManager(settings_file=settings_path)

    volumes = manager.get("current.pneumatic.chamber_volumes")
    pressures = manager.get("current.pneumatic.line_pressures")

    assert volumes == {
        "head_m3": pytest.approx(0.0005),
        "rod_m3": pytest.approx(0.0003),
    }
    assert pressures == {
        "a1_pa": pytest.approx(150000.0),
        "b1_pa": pytest.approx(150000.0),
        "a2_pa": pytest.approx(150000.0),
        "b2_pa": pytest.approx(150000.0),
    }
    assert manager.get("current.pneumatic.tank_pressure_pa") == pytest.approx(200000.0)
    assert manager.get("current.pneumatic.relief_pressure_pa") == pytest.approx(
        500000.0
    )


def test_settings_manager_persists_updated_pneumatic_values(tmp_path: Path) -> None:
    settings_path = _write_settings(tmp_path)

    manager = SettingsManager(settings_file=settings_path)
    manager.set("current.pneumatic.line_pressures.a1_pa", 175000.0, auto_save=False)
    manager.set("current.pneumatic.chamber_volumes.head_m3", 0.0006, auto_save=False)
    manager.set("current.pneumatic.tank_pressure_pa", 220000.0, auto_save=False)
    manager.set("current.pneumatic.relief_pressure_pa", 525000.0)

    reloaded = SettingsManager(settings_file=settings_path)

    assert reloaded.get("current.pneumatic.line_pressures.a1_pa") == pytest.approx(
        175000.0
    )
    assert reloaded.get("current.pneumatic.chamber_volumes.head_m3") == pytest.approx(
        0.0006
    )
    assert reloaded.get("current.pneumatic.tank_pressure_pa") == pytest.approx(220000.0)
    assert reloaded.get("current.pneumatic.relief_pressure_pa") == pytest.approx(
        525000.0
    )


def test_settings_manager_hydrates_missing_sim_speed(tmp_path: Path) -> None:
    settings_path = _write_settings(tmp_path)
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    payload["current"]["simulation"].pop("sim_speed", None)
    payload.get("defaults_snapshot", {}).get("simulation", {}).pop("sim_speed", None)
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manager = SettingsManager(settings_file=settings_path)

    assert manager.get("current.simulation.sim_speed") == pytest.approx(1.0)
