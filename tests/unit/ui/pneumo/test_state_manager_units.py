"""Unit tests for pneumatic state manager unit conversions."""

from __future__ import annotations

import pytest

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
        ({"cv_atmo_dp": 0.02, "cv_atmo_dia": 3.0}, {"cv_atmo_dp": 0.02, "cv_atmo_dia": 3.0}),
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
