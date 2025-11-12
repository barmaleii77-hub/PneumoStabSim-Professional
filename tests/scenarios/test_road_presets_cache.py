"""Additional regression tests for cached road preset lookups."""

from __future__ import annotations

import pytest

from src.road import scenarios


def test_get_all_presets_is_cached_singleton() -> None:
    first = scenarios.get_all_presets()
    second = scenarios.get_all_presets()

    assert first is second
    assert "test_sine" in first


def test_preset_catalogue_is_read_only() -> None:
    presets = scenarios.get_all_presets()

    with pytest.raises(TypeError):
        presets["new_preset"] = object()  # type: ignore[index]


def test_get_preset_by_name_uses_cached_catalogue() -> None:
    preset = scenarios.get_preset_by_name("test_sine")

    assert preset is not None
    assert preset.name.lower().startswith("test_")
