"""Regression tests covering environment settings serialisation."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.settings_models import (
    AppSettings,
    EnvironmentSettings,
    EnvironmentSliderRanges,
    dump_settings,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = REPO_ROOT / "config" / "app_settings.json"


def test_environment_settings_round_trip_includes_all_fields() -> None:
    """Environment settings should serialise/deserialise without losing fields."""

    payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    app_settings = AppSettings.model_validate(payload)
    environment_model = app_settings.current.graphics.environment

    serialised = dump_settings(app_settings)["current"]["graphics"]["environment"]
    expected_keys = set(EnvironmentSettings.model_fields)

    assert set(serialised) == expected_keys
    assert serialised == environment_model.model_dump(mode="python", round_trip=True)

    restored_model = EnvironmentSettings.model_validate(serialised)
    assert restored_model == environment_model

    for alias in (
        "fog_depth_enabled",
        "fog_depth_near",
        "fog_depth_far",
        "fog_depth_curve",
    ):
        assert alias in serialised
        assert serialised[alias] == getattr(environment_model, alias)


def test_environment_slider_ranges_round_trip_preserves_depth_controls() -> None:
    """Slider range metadata must include depth fog controls during round-trip."""

    payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    app_settings = AppSettings.model_validate(payload)

    serialised_metadata = dump_settings(app_settings)["metadata"][
        "environment_slider_ranges"
    ]
    expected_keys = set(EnvironmentSliderRanges.model_fields)

    assert set(serialised_metadata) == expected_keys

    slider_model = app_settings.metadata.environment_slider_ranges
    assert serialised_metadata == slider_model.model_dump(
        mode="python", round_trip=True
    )

    for alias in ("fog_depth_near", "fog_depth_far", "fog_depth_curve"):
        assert alias in serialised_metadata
        assert serialised_metadata[alias] == getattr(slider_model, alias)
