from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "settings" / "app_settings.schema.json"
SETTINGS_PATH = REPO_ROOT / "config" / "app_settings.json"


def _load_environment_schema_keys() -> set[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    ranges_def = schema["$defs"]["EnvironmentSliderRanges"]
    properties = set(ranges_def["properties"].keys())
    required = set(ranges_def["required"])

    assert properties == required, (
        "Environment slider range schema must require all declared properties"
    )
    return properties


def _load_environment_ranges() -> Tuple[
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
]:
    payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    current = payload["current"]["graphics"]["environment_ranges"]
    defaults = payload["defaults_snapshot"]["graphics"]["environment_ranges"]
    metadata = payload["metadata"]["environment_slider_ranges"]
    return current, defaults, metadata


def test_environment_range_keys_match_schema_definition() -> None:
    schema_keys = _load_environment_schema_keys()
    current, defaults, metadata = _load_environment_ranges()

    for block in (current, defaults, metadata):
        assert set(block.keys()) == schema_keys, (
            "Environment slider ranges drifted from schema definition"
        )


def test_environment_slider_range_shapes_match_schema_contract() -> None:
    _, _, metadata = _load_environment_ranges()

    for slider in metadata.values():
        assert set(slider.keys()).issuperset({"min", "max", "step"})
        assert slider["step"] > 0
        if "decimals" in slider:
            assert slider["decimals"] >= 0
        if "units" in slider:
            assert slider["units"]
