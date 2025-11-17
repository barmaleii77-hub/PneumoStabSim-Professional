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
