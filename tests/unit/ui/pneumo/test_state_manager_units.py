"""Unit tests for pneumatic state manager unit conversions."""

from __future__ import annotations

import pytest

from src.ui.panels.pneumo.defaults import convert_pressure_value
from src.ui.panels.pneumo.state_manager import PneumoStateManager


class DummySettings:
    """Minimal settings stub used to isolate conversion logic."""

    def get(self, _path: str, default=None):
        return default or {}

    def set(self, _path: str, _value):
        # Persisting is irrelevant for unit conversion tests
        return None


@pytest.mark.parametrize(
    "payload, expected",
    [
        (
            {
                "cv_atmo_dp": 0.02 * 100_000.0,
                "cv_atmo_dia": 0.003,
                "pressure_units": "бар",
            },
            {"cv_atmo_dp": 0.02, "cv_atmo_dia": 3.0},
        ),
        (
            {"cv_atmo_dp": 2000.0, "cv_atmo_dia": 0.003},
            {"cv_atmo_dp": 0.02, "cv_atmo_dia": 3.0},
        ),
    ],
)
def test_convert_from_storage_handles_si_and_legacy_units(payload, expected):
    converted = PneumoStateManager._convert_from_storage(payload)
    for key, value in expected.items():
        assert pytest.approx(value, rel=1e-9) == converted[key]


def test_convert_to_storage_scales_pressure_and_diameter():
    payload = {"cv_atmo_dp": 0.02, "cv_atmo_dia": 3.0}
    converted = PneumoStateManager._convert_to_storage(payload)
    assert pytest.approx(0.02 * 100_000.0, rel=1e-9) == converted["cv_atmo_dp"]
    assert pytest.approx(3.0 / 1000.0, rel=1e-9) == converted["cv_atmo_dia"]


def test_export_storage_payload_uses_canonical_units():
    manager = PneumoStateManager(settings_manager=DummySettings())
    manager.set_pressure_drop("cv_atmo_dp", 0.02)
    manager.set_valve_diameter("cv_atmo_dia", 3.0)

    payload = manager.export_storage_payload()
    assert pytest.approx(0.02 * 100_000.0, rel=1e-9) == payload["cv_atmo_dp"]
    assert pytest.approx(3.0 / 1000.0, rel=1e-9) == payload["cv_atmo_dia"]


def test_set_pressure_units_rescales_pressures():
    manager = PneumoStateManager(settings_manager=DummySettings())
    manager.set_relief_pressure("relief_min_pressure", 5.0)

    manager.set_pressure_units("Па")
    expected_pa = convert_pressure_value(5.0, "бар", "Па")
    assert pytest.approx(expected_pa, rel=1e-9) == manager.get_relief_pressure(
        "relief_min_pressure"
    )

    manager.set_pressure_units("кПа")
    expected_kpa = convert_pressure_value(5.0, "бар", "кПа")
    assert pytest.approx(expected_kpa, rel=1e-9) == manager.get_relief_pressure(
        "relief_min_pressure"
    )


def test_set_relief_pressure_honours_current_units():
    manager = PneumoStateManager(settings_manager=DummySettings())
    manager.set_pressure_units("Па")
    manager.set_relief_pressure("relief_min_pressure", 250000.0)

    assert pytest.approx(250000.0, rel=1e-9) == manager.get_relief_pressure(
        "relief_min_pressure"
    )

    manager.set_pressure_units("бар")
    assert pytest.approx(2.5, rel=1e-9) == manager.get_relief_pressure(
        "relief_min_pressure"
    )
