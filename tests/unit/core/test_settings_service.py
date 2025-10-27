import json
from pathlib import Path
from typing import Any

import pytest

from config import constants as constants_module
from src.core.settings_service import (
    SETTINGS_SERVICE_TOKEN,
    SettingsService,
    SettingsValidationError,
    get_settings_service,
)
from src.infrastructure.container import get_default_container
from src.infrastructure.event_bus import EVENT_BUS_TOKEN, get_event_bus


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROJECT_SETTINGS = PROJECT_ROOT / "config" / "app_settings.json"


@pytest.fixture()
def settings_payload(tmp_path: Path) -> Path:
    data = json.loads(PROJECT_SETTINGS.read_text(encoding="utf-8"))

    # Normalise key values used in assertions
    constants = data["current"]["constants"]
    constants["geometry"]["kinematics"]["track_width_m"] = 2.0
    pneumo = constants["pneumo"]
    pneumo["valves"]["delta_open_pa"] = 123.0
    pneumo["receiver"].update(
        {
            "volume_min_m3": 0.1,
            "volume_max_m3": 0.2,
            "initial_volume_m3": 0.15,
        }
    )
    pneumo["gas"].update(
        {
            "tank_volume_initial_m3": 0.42,
            "tank_pressure_initial_pa": 200_000.0,
            "tank_temperature_initial_k": 285.0,
            "tank_volume_mode": "NO_RECALC",
            "time_step_s": 0.01,
            "total_time_s": 10.0,
        }
    )
    pneumo["master_isolation_open"] = True

    data["defaults_snapshot"] = json.loads(json.dumps(data["current"]))

    settings_file = tmp_path / "app_settings.json"
    settings_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return settings_file


def test_settings_service_get_and_set(settings_payload: Path) -> None:
    service = SettingsService(settings_path=settings_payload)

    assert service.get("current.constants.geometry.kinematics.track_width_m") == 2.0

    service.set("current.constants.geometry.kinematics.track_width_m", 2.5)
    assert service.get("current.constants.geometry.kinematics.track_width_m") == 2.5

    reloaded = json.loads(settings_payload.read_text(encoding="utf-8"))
    assert (
        reloaded["current"]["constants"]["geometry"]["kinematics"]["track_width_m"]
        == 2.5
    )


def test_settings_service_update_merges(settings_payload: Path) -> None:
    service = SettingsService(settings_path=settings_payload)

    service.update(
        "current.constants.geometry.kinematics",
        {"rod_attach_fraction": 0.55},
    )

    payload = service.load()
    assert (
        payload["current"]["constants"]["geometry"]["kinematics"]["rod_attach_fraction"]
        == 0.55
    )


def test_settings_service_emits_event_on_save(settings_payload: Path) -> None:
    container = get_default_container()
    container.reset(EVENT_BUS_TOKEN)
    events: list[dict[str, Any]] = []

    bus = get_event_bus()
    unsubscribe = bus.subscribe(
        "settings.updated", lambda payload: events.append(payload or {})
    )
    try:
        service = SettingsService(settings_path=settings_payload)
        service.set("current.constants.geometry.kinematics.track_width_m", 3.14)
    finally:
        unsubscribe()
        container.reset(EVENT_BUS_TOKEN)

    assert events, "settings.updated event was not published"
    last_event = events[-1]
    assert last_event.get("action") == "set"
    assert (
        last_event.get("path") == "current.constants.geometry.kinematics.track_width_m"
    )
    assert "timestamp" in last_event


def test_constants_accessors_use_settings_service(
    settings_payload: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        constants_module,
        "get_settings_service",
        lambda: SettingsService(settings_path=settings_payload),
    )

    constants_module.refresh_cache()

    valves = constants_module.get_pneumo_valve_constants()
    assert valves["delta_open_pa"] == 123.0

    receiver = constants_module.get_pneumo_receiver_constants()
    assert receiver["initial_volume_m3"] == 0.15

    gas = constants_module.get_pneumo_gas_constants()
    assert gas["total_time_s"] == 10.0

    assert constants_module.get_pneumo_master_isolation_default() is True


def test_settings_service_load_does_not_modify_file(settings_payload: Path) -> None:
    service = SettingsService(settings_path=settings_payload)

    before = settings_payload.read_bytes()
    service.load()
    after = settings_payload.read_bytes()

    assert after == before


def test_settings_service_raises_on_schema_violation(tmp_path: Path) -> None:
    payload = {
        "metadata": {"version": "1.0.0"},  # missing units_version
        "current": {},
        "defaults_snapshot": {},
    }
    settings_file = tmp_path / "invalid.json"
    settings_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    service = SettingsService(settings_path=settings_file)

    with pytest.raises(SettingsValidationError) as exc:
        service.load()

    assert any("metadata.units_version" in error for error in exc.value.errors)


def test_get_settings_service_respects_overrides(
    settings_payload: Path,
) -> None:
    container = get_default_container()
    container.reset(SETTINGS_SERVICE_TOKEN)

    override = SettingsService(settings_path=settings_payload)
    with container.override(SETTINGS_SERVICE_TOKEN, override):
        resolved = get_settings_service()
        assert resolved is override

    container.reset(SETTINGS_SERVICE_TOKEN)
