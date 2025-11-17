from __future__ import annotations

import pytest

from src.road import scenarios


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    scenarios.resolve_preset_name.cache_clear()
    scenarios._preset_name_index.cache_clear()  # type: ignore[attr-defined]


def test_resolve_preset_name_normalizes_and_caches() -> None:
    cache_info_before = scenarios.resolve_preset_name.cache_info()

    assert scenarios.resolve_preset_name("  TEST_SINE  ") == "test_sine"
    assert scenarios.resolve_preset_name("  TEST_SINE  ") == "test_sine"

    cache_info_after = scenarios.resolve_preset_name.cache_info()
    assert cache_info_after.hits > cache_info_before.hits
    assert cache_info_after.currsize >= 1


def test_resolve_preset_name_supports_aliases() -> None:
    assert scenarios.resolve_preset_name("Standard") == "urban_50kmh"
    assert scenarios.resolve_preset_name("тест пневматики") == "test_sine"


def test_get_preset_by_name_handles_invalid_tokens() -> None:
    assert scenarios.get_preset_by_name(None) is None
    assert scenarios.get_preset_by_name("") is None
    assert scenarios.get_preset_by_name(object()) is None  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "name",
    ["urban_50kmh", "URBAN_50KMH", "  urban_50kmh  "],
)
def test_get_preset_by_name_resolves_normalized_tokens(name: str) -> None:
    preset = scenarios.get_preset_by_name(name)
    assert preset is not None
    assert preset.name == "Urban"
