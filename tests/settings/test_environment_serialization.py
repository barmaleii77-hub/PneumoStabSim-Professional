"""Regression tests covering environment settings serialisation."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.settings_models import (
    EnvironmentSettings,
    EnvironmentSliderRanges,
    dump_settings,
)
from src.core.settings_service import SettingsService

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = REPO_ROOT / "config" / "app_settings.json"


def test_environment_settings_round_trip_includes_all_fields() -> None:
    """Environment settings should serialise/deserialise without losing fields."""

    # Не валидируем целиком AppSettings из файла настроек, чтобы тест не зависел
    # от несвязанных разделов схемы. Читаем через SettingsService и валидируем
    # только раздел окружения.
    service = SettingsService(settings_path=str(SETTINGS_PATH), validate_schema=False)
    loaded = service.load()
    serialised = dump_settings(loaded)["current"]["graphics"]["environment"]
    environment_model = EnvironmentSettings.model_validate(serialised)

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

    service = SettingsService(settings_path=str(SETTINGS_PATH), validate_schema=False)
    loaded = service.load()
    serialised_metadata = dump_settings(loaded)["metadata"]["environment_slider_ranges"]
    expected_keys = set(EnvironmentSliderRanges.model_fields)

    assert set(serialised_metadata) == expected_keys

    slider_model = EnvironmentSliderRanges.model_validate(serialised_metadata)
    assert serialised_metadata == slider_model.model_dump(
        mode="python", round_trip=True, exclude_none=True
    )

    for alias in ("fog_depth_near", "fog_depth_far", "fog_depth_curve"):
        assert alias in serialised_metadata
        model_entry = getattr(slider_model, alias).model_dump(mode="python", round_trip=True, exclude_none=True)
        assert serialised_metadata[alias] == model_entry
