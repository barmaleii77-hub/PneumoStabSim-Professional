"""Regression checks for SettingsService path splitting helpers."""

from __future__ import annotations

from src.core.settings_service import SettingsService


def _clear_path_cache() -> None:
    """Ensure cache state is isolated between tests."""

    SettingsService._split_path.cache_clear()


def test_split_path_caches_results() -> None:
    _clear_path_cache()

    before = SettingsService._split_path.cache_info()
    SettingsService._split_path("current.simulation.physics_dt")
    after_first = SettingsService._split_path.cache_info()
    SettingsService._split_path("current.simulation.physics_dt")
    after_second = SettingsService._split_path.cache_info()

    assert after_first.misses == before.misses + 1
    assert after_second.hits == after_first.hits + 1


def test_split_path_trims_whitespace_and_empty_segments() -> None:
    _clear_path_cache()

    segments = SettingsService._split_path("  current. simulation..physics_dt  ")

    assert segments == ("current", "simulation", "physics_dt")


def test_split_path_returns_empty_tuple_for_blank_values() -> None:
    _clear_path_cache()

    assert SettingsService._split_path("   ") == ()
