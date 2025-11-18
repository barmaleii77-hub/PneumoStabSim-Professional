from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.settings_models import dump_settings
from src.core.settings_service import SettingsService

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "settings" / "app_settings.schema.json"


def test_settings_service_rehydrates_environment_ranges_from_metadata(
    tmp_path: Path,
) -> None:
    baseline = json.loads(
        (REPO_ROOT / "config" / "app_settings.json").read_text(encoding="utf-8")
    )

    baseline["current"]["graphics"].pop("environment_ranges", None)
    baseline["defaults_snapshot"]["graphics"].pop("environment_ranges", None)
    baseline["metadata"]["environment_slider_ranges"] = {
        "ibl_intensity": {
            "min": -2.0,
            "max": 12.0,
            "step": 0.5,
            "decimals": None,
            "units": "ev",
        },
        "fog_density": {
            "min": 0.0,
            "max": 8.0,
            "step": 0.25,
            "decimals": 3,
            "units": "abs",
        },
    }

    settings_path = tmp_path / "app_settings.json"
    settings_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    service = SettingsService(settings_path=settings_path, schema_path=SCHEMA_PATH)
    settings = service.load()
    payload = dump_settings(settings)

    ranges = payload["current"]["graphics"]["environment_ranges"]
    assert ranges["ibl_intensity"]["min"] == pytest.approx(-2.0)
    assert ranges["ibl_intensity"]["max"] == pytest.approx(12.0)
    assert ranges["ibl_intensity"]["step"] == pytest.approx(0.5)
    assert ranges["ibl_intensity"].get("decimals") is None
    assert ranges["ibl_intensity"]["units"] == "ev"

    assert ranges["fog_density"]["min"] == pytest.approx(0.0)
    assert ranges["fog_density"]["max"] == pytest.approx(8.0)
    assert ranges["fog_density"]["step"] == pytest.approx(0.25)
    assert ranges["fog_density"]["decimals"] == 3
    assert ranges["fog_density"]["units"] == "abs"

    meta_ranges = payload["metadata"].get("environment_slider_ranges", {})
    assert meta_ranges["ibl_intensity"].get("decimals") is None
    assert meta_ranges["fog_density"]["decimals"] == 3


def test_settings_service_backfills_missing_environment_ranges_from_defaults(
    tmp_path: Path,
) -> None:
    baseline = json.loads(
        (REPO_ROOT / "config" / "app_settings.json").read_text(encoding="utf-8")
    )

    current_ranges = baseline["current"]["graphics"]["environment_ranges"]
    defaults_ranges = baseline["defaults_snapshot"]["graphics"]["environment_ranges"]

    # Имитируем частично утерянную секцию: оставляем только ключ освещения и меняем
    # диапазон, чтобы убедиться, что он не перетирается.
    preserved_key = "ibl_intensity"
    preserved_original = current_ranges[preserved_key]["max"]
    current_ranges[preserved_key]["max"] = preserved_original + 1.0

    removed_keys = ["fog_density", "ao_softness"]
    for key in removed_keys:
        current_ranges.pop(key, None)

    settings_path = tmp_path / "app_settings.json"
    settings_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    service = SettingsService(settings_path=settings_path, schema_path=SCHEMA_PATH)
    payload = dump_settings(service.load())
    ranges = payload["current"]["graphics"]["environment_ranges"]

    # Удалённые ключи должны восстановиться из defaults_snapshot
    for key in removed_keys:
        assert key in ranges
        assert ranges[key] == defaults_ranges[key]

    # Существующие значения не перезаписываются
    assert ranges[preserved_key]["max"] == preserved_original + 1.0


def test_settings_service_prefers_metadata_when_defaults_lack_range(
    tmp_path: Path,
) -> None:
    baseline = json.loads(
        (REPO_ROOT / "config" / "app_settings.json").read_text(encoding="utf-8")
    )

    target_key = "probe_horizon"
    replacement_range = {"min": -2.0, "max": 2.0, "step": 0.25}

    baseline["defaults_snapshot"]["graphics"]["environment_ranges"].pop(
        target_key, None
    )
    baseline["current"]["graphics"]["environment_ranges"].pop(target_key, None)
    baseline.setdefault("metadata", {}).setdefault("environment_slider_ranges", {})[
        target_key
    ] = replacement_range

    settings_path = tmp_path / "app_settings.json"
    settings_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    service = SettingsService(settings_path=settings_path, schema_path=SCHEMA_PATH)
    payload = dump_settings(service.load())

    ranges = payload["current"]["graphics"]["environment_ranges"]
    assert ranges[target_key] == replacement_range
