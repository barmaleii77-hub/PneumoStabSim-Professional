"""Unit tests for pneumatic state manager unit conversions."""

from __future__ import annotations

import pytest

from src.ui.panels.pneumo.defaults import convert_pressure_value
from src.ui.panels.pneumo.state_manager import PneumoStateManager


class DummySettings:
    """Minimal settings stub used to isolate conversion logic."""

    def __init__(self, values=None, *, units_version: str = "si_v2") -> None:
        self._values = values or {}
        self._units_version = units_version

    def get(self, path: str, default=None):
        return self._values.get(path, default)

    def set(self, path: str, value):
        self._values[path] = value
        return None

    def get_units_version(self, *, normalised: bool = True) -> str:
        if normalised:
            return "si_v2"
        return self._units_version


@pytest.mark.parametrize(
    "payload, units_version, expected",
    [
        (
            {
                "cv_atmo_dp": 0.02 * 100_000.0,
                "cv_atmo_dia": 0.003,
                "pressure_units": "бар",
            },
            "si_v2",
            {"cv_atmo_dp": 0.02, "cv_atmo_dia": 3.0},
        ),
        (
            {"cv_atmo_dp": 0.02, "cv_atmo_dia": 3.0, "pressure_units": "бар"},
            "legacy",
            {"cv_atmo_dp": 0.02, "cv_atmo_dia": 3.0},
        ),
    ],
)
def test_convert_from_storage_handles_si_and_legacy_units(
    payload, units_version, expected
):
    converted = PneumoStateManager._convert_from_storage(
        payload, units_version=units_version
    )
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


def test_load_respects_legacy_units_version():
    settings = DummySettings(
        {
            "current.pneumatic": {
                "cv_atmo_dp": 0.02,
                "cv_atmo_dia": 3.0,
                "pressure_units": "бар",
            },
            "defaults_snapshot.pneumatic": {},
        },
        units_version="legacy",
    )

    manager = PneumoStateManager(settings_manager=settings)

    assert pytest.approx(0.02, rel=1e-9) == manager.get_pressure_drop("cv_atmo_dp")
    assert pytest.approx(3.0, rel=1e-9) == manager.get_valve_diameter("cv_atmo_dia")


def test_load_converts_si_units_to_ui_defaults():
    settings = DummySettings(
        {
            "current.pneumatic": {
                "cv_atmo_dp": 0.02 * 100_000.0,
                "cv_atmo_dia": 0.003,
                "pressure_units": "бар",
            },
            "defaults_snapshot.pneumatic": {},
        },
        units_version="si_v2",
    )

    manager = PneumoStateManager(settings_manager=settings)

    assert pytest.approx(0.02, rel=1e-9) == manager.get_pressure_drop("cv_atmo_dp")
    assert pytest.approx(3.0, rel=1e-9) == manager.get_valve_diameter("cv_atmo_dia")


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
