from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.core.settings_defaults import load_default_settings_payload
from src.core.settings_models import dump_settings
from src.core.settings_service import SettingsService, SettingsValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "settings" / "app_settings.schema.json"


@pytest.fixture()
def settings_payload() -> dict:
    return deepcopy(load_default_settings_payload())


@pytest.fixture()
def settings_file(tmp_path: Path, settings_payload: dict) -> Path:
    target = tmp_path / "app_settings.json"
    target.write_text(json.dumps(settings_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


@pytest.mark.parametrize(
    "metadata_key",
    [
        "geometry_accordion_fields",
        "pneumatic_volume_accordion_fields",
        "pneumatic_pressure_accordion_fields",
        "pneumatic_valve_accordion_fields",
        "simulation_panel_fields",
        "road_panel_fields",
        "advanced_panel_fields",
    ],
)
def test_accordion_metadata_round_trip(metadata_key: str, settings_file: Path) -> None:
    service = SettingsService(settings_path=settings_file, schema_path=SCHEMA_PATH)

    settings = service.load(use_cache=False)
    metadata = dump_settings(settings)["metadata"]
    entries = metadata.get(metadata_key)

    assert isinstance(entries, list) and entries, metadata_key
    assert all({"key", "label", "unit", "settings_path"} <= set(entry) for entry in entries)


@pytest.mark.parametrize(
    "metadata_key",
    [
        "pneumatic_pressure_accordion_fields",
        "simulation_panel_fields",
    ],
)
def test_accordion_metadata_requires_settings_path(metadata_key: str, settings_payload: dict, tmp_path: Path) -> None:
    metadata = settings_payload.setdefault("metadata", {})
    entries = metadata.get(metadata_key)
    assert entries, f"Missing baseline for {metadata_key}"
    broken = deepcopy(entries)
    broken[0].pop("settings_path", None)
    metadata[metadata_key] = broken

    target = tmp_path / "app_settings.json"
    target.write_text(json.dumps(settings_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    service = SettingsService(settings_path=target, schema_path=SCHEMA_PATH)

    with pytest.raises(SettingsValidationError):
        service.load(use_cache=False)
