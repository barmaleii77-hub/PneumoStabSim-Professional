"""Persistence and validation tests for :mod:`src.core.settings_service`."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from src.core.settings_service import SettingsService, SettingsValidationError
from src.infrastructure.container import get_default_container
from src.infrastructure.event_bus import EVENT_BUS_TOKEN, EventBus

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = REPO_ROOT / "config" / "app_settings.json"
SCHEMA_PATH = REPO_ROOT / "config" / "schemas" / "app_settings.schema.json"

with SETTINGS_PATH.open("r", encoding="utf-8") as stream:
    _BASE_SETTINGS_PAYLOAD: dict[str, Any] = json.load(stream)


@pytest.fixture()
def settings_payload() -> dict[str, Any]:
    """Return a deep copy of the baseline settings payload for test isolation."""

    return deepcopy(_BASE_SETTINGS_PAYLOAD)


@pytest.fixture()
def settings_file(tmp_path: Path, settings_payload: dict[str, Any]) -> Path:
    """Write the baseline payload to a temporary settings file."""

    target = tmp_path / "app_settings.json"
    target.write_text(
        json.dumps(settings_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target


@pytest.fixture()
def event_bus_override() -> EventBus:
    """Provide an isolated :class:`EventBus` override for published events."""

    container = get_default_container()
    bus = EventBus()
    with container.override(EVENT_BUS_TOKEN, bus):
        yield bus
    container.reset(EVENT_BUS_TOKEN)


def test_load_uses_cache_until_explicit_reload(settings_file: Path) -> None:
    service = SettingsService(settings_path=settings_file, schema_path=SCHEMA_PATH)

    cached = service.load()
    assert (
        cached["metadata"]["units_version"]
        == _BASE_SETTINGS_PAYLOAD["metadata"]["units_version"]
    )

    mutated = deepcopy(cached)
    mutated["metadata"]["version"] = "9.9.9"
    settings_file.write_text(
        json.dumps(mutated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    assert service.load()["metadata"]["version"] != "9.9.9"

    refreshed = service.load(use_cache=False)
    assert refreshed["metadata"]["version"] == "9.9.9"


def test_save_persists_changes_and_emits_event(
    settings_file: Path, event_bus_override: EventBus
) -> None:
    service = SettingsService(settings_path=settings_file, schema_path=SCHEMA_PATH)
    captured: list[dict[str, Any]] = []
    event_bus_override.subscribe(
        "settings.updated", lambda payload: captured.append(dict(payload))
    )

    payload = service.load()
    timestamp = datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")
    payload["metadata"]["last_modified"] = timestamp

    service.save(payload, metadata={"reason": "unit-test"})

    persisted = json.loads(settings_file.read_text(encoding="utf-8"))
    assert persisted["metadata"]["last_modified"] == timestamp

    assert len(captured) == 1
    event_payload = captured[0]
    assert event_payload["source"] == "settings_service"
    assert event_payload["reason"] == "unit-test"
    assert "timestamp" in event_payload


def test_load_raises_for_invalid_payload(tmp_path: Path) -> None:
    invalid_payload = {
        "metadata": {"units_version": "si_v2"},
        # Missing required "current" and "defaults_snapshot" entries
    }
    settings_file = tmp_path / "app_settings.json"
    settings_file.write_text(
        json.dumps(invalid_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    service = SettingsService(settings_path=settings_file, schema_path=SCHEMA_PATH)

    with pytest.raises(SettingsValidationError) as exc_info:
        service.load(use_cache=False)

    assert "current" in str(exc_info.value)
    assert "defaults_snapshot" in str(exc_info.value)


def test_set_unknown_path_records_audit(settings_file: Path) -> None:
    service = SettingsService(
        settings_path=settings_file, schema_path=SCHEMA_PATH, validate_schema=False
    )

    service.set("current.geometry.unknown_field", 123)

    payload = json.loads(settings_file.read_text(encoding="utf-8"))
    assert payload["current"]["geometry"]["unknown_field"] == 123
    assert service.get_unknown_paths() == ["current.geometry.unknown_field"]


def test_set_unknown_path_fails_schema_validation(settings_file: Path) -> None:
    service = SettingsService(settings_path=settings_file, schema_path=SCHEMA_PATH)

    with pytest.raises(SettingsValidationError):
        service.set("current.geometry.unknown_field", 123)

    assert service.get_unknown_paths() == []


def test_update_unknown_key_records_audit(settings_file: Path) -> None:
    service = SettingsService(
        settings_path=settings_file, schema_path=SCHEMA_PATH, validate_schema=False
    )

    service.update("current.geometry", {"unknown_field": 1})

    payload = json.loads(settings_file.read_text(encoding="utf-8"))
    assert payload["current"]["geometry"]["unknown_field"] == 1
    assert service.get_unknown_paths() == ["current.geometry.unknown_field"]


def test_update_unknown_key_validation_failure_does_not_record(
    settings_file: Path,
) -> None:
    service = SettingsService(settings_path=settings_file, schema_path=SCHEMA_PATH)

    with pytest.raises(SettingsValidationError):
        service.update("current.geometry", {"unknown_field": 1})

    assert service.get_unknown_paths() == []


def test_defaults_snapshot_materials_include_ids() -> None:
    defaults_graphics = _BASE_SETTINGS_PAYLOAD["defaults_snapshot"]["graphics"]
    current_graphics = _BASE_SETTINGS_PAYLOAD["current"]["graphics"]

    defaults_materials = defaults_graphics["materials"]
    current_materials = current_graphics["materials"]

    assert set(defaults_materials) == set(current_materials)

    for material_id, material_payload in defaults_materials.items():
        assert material_payload["id"] == material_id
        assert current_materials[material_id]["id"] == material_id

    assert defaults_graphics["quality"]["mesh"] == current_graphics["quality"]["mesh"]


def test_validate_detects_material_key_mismatch(
    settings_payload: dict[str, Any],
) -> None:
    defaults = settings_payload["defaults_snapshot"]["graphics"]["materials"]
    defaults.pop("tail_rod")

    service = SettingsService(schema_path=SCHEMA_PATH)

    with pytest.raises(SettingsValidationError) as exc:
        service.validate(settings_payload)

    assert "missing in defaults_snapshot" in str(exc.value)


def test_validate_rejects_legacy_tail_alias(settings_payload: dict[str, Any]) -> None:
    defaults = settings_payload["defaults_snapshot"]["graphics"]["materials"]
    current = settings_payload["current"]["graphics"]["materials"]

    defaults["tail"] = defaults.pop("tail_rod")
    current["tail"] = current.pop("tail_rod")

    service = SettingsService(schema_path=SCHEMA_PATH)

    with pytest.raises(SettingsValidationError) as exc:
        service.validate(settings_payload)

    assert "legacy graphics material keys" in str(exc.value)


def test_validate_rejects_material_id_mismatch(
    settings_payload: dict[str, Any],
) -> None:
    materials = settings_payload["current"]["graphics"]["materials"]
    materials["frame"]["id"] = "FRAME"

    service = SettingsService(schema_path=SCHEMA_PATH)

    with pytest.raises(SettingsValidationError) as exc:
        service.validate(settings_payload)

    assert "frame has id 'FRAME'" in str(exc.value)
