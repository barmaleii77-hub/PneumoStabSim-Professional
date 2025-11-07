"""Unit tests for pneumatic state manager unit conversions."""

from __future__ import annotations

import logging

import pytest

from src.ui.panels.pneumo.defaults import PRESSURE_DROP_LIMITS, convert_pressure_value
from src.ui.panels.pneumo.state_manager import PneumoStateManager


class DummySettings:
    """Minimal settings stub used to isolate conversion logic."""

    def __init__(self, values=None, *, units_version: str = "si_v2") -> None:
        self._values = {}
        self._units_version = units_version
        if values:
            for path, value in values.items():
                self.set(path, value, auto_save=False)

    def _resolve(self, path: str, create: bool = False):
        parts = path.split(".")
        node = self._values
        for index, part in enumerate(parts[:-1]):
            next_node = node.get(part)
            if next_node is None:
                if not create:
                    return None, parts[-1]
                next_node = {}
                node[part] = next_node
            if not isinstance(next_node, dict):
                if not create:
                    return None, parts[-1]
                next_node = {}
                node[part] = next_node
            node = next_node
        return node, parts[-1]

    def get(self, path: str, default=None):
        container, leaf = self._resolve(path)
        if container is None:
            return default
        return container.get(leaf, default)

    def set(self, path: str, value, auto_save: bool = True):
        container, leaf = self._resolve(path, create=True)
        container[leaf] = value
        return True

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


def test_legacy_payload_normalised_before_save():
    settings = DummySettings(
        {
            "metadata.units_version": "legacy",
            "current.pneumatic": {
                "cv_atmo_dp": "0.02",
                "cv_atmo_dia": "3.0",
                "pressure_units": "бар",
            },
            "defaults_snapshot.pneumatic": {},
        },
        units_version="legacy",
    )

    manager = PneumoStateManager(settings_manager=settings)

    storage = manager.export_storage_payload()
    assert pytest.approx(0.02 * 100_000.0, rel=1e-9) == storage["cv_atmo_dp"]
    assert pytest.approx(3.0 / 1000.0, rel=1e-9) == storage["cv_atmo_dia"]

    assert settings.get("metadata.pneumo_units_normalised") is True

    storage_again = manager.export_storage_payload()
    assert storage_again == storage


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


def test_set_pressure_drop_outside_limits_logs_and_clamps(caplog):
    manager = PneumoStateManager(settings_manager=DummySettings())

    caplog.set_level(logging.WARNING)
    manager.set_pressure_drop("cv_atmo_dp", 5.0)

    assert pytest.approx(
        PRESSURE_DROP_LIMITS["max"], rel=1e-9
    ) == manager.get_pressure_drop("cv_atmo_dp")
    assert any(
        "pressure_drop.cv_atmo_dp" in record.message for record in caplog.records
    ), "Expected clamp warning for cv_atmo_dp"


def test_relief_min_pressure_exceeding_stiff_is_reduced(caplog):
    manager = PneumoStateManager(settings_manager=DummySettings())

    caplog.set_level(logging.WARNING)
    manager.set_relief_pressure("relief_min_pressure", 60.0)

    stiff_value = manager.get_relief_pressure("relief_stiff_pressure")
    assert pytest.approx(stiff_value, rel=1e-9) == manager.get_relief_pressure(
        "relief_min_pressure"
    )
    assert any(
        "relief_pressure.relief_min_pressure" in record.message
        and "relief_stiff_pressure" in record.message
        for record in caplog.records
    ), "Expected warning about exceeding stiff relief pressure"


def test_relief_stiff_pressure_respects_bounds(caplog):
    manager = PneumoStateManager(settings_manager=DummySettings())

    caplog.set_level(logging.WARNING)
    manager.set_relief_pressure("relief_stiff_pressure", 0.5)

    min_value = manager.get_relief_pressure("relief_min_pressure")
    assert pytest.approx(min_value, rel=1e-9) == manager.get_relief_pressure(
        "relief_stiff_pressure"
    )
    assert any(
        "relief_pressure.relief_stiff_pressure" in record.message
        and "relief_min_pressure" in record.message
        for record in caplog.records
    ), "Expected warning about falling below relief_min_pressure"


def test_relief_safety_pressure_not_below_active_bounds(caplog):
    manager = PneumoStateManager(settings_manager=DummySettings())

    caplog.set_level(logging.WARNING)
    manager.set_relief_pressure("relief_safety_pressure", 5.0)

    stiff_value = manager.get_relief_pressure("relief_stiff_pressure")
    assert pytest.approx(stiff_value, rel=1e-9) == manager.get_relief_pressure(
        "relief_safety_pressure"
    )
    assert any(
        "relief_pressure.relief_safety_pressure" in record.message
        and "max(relief_min_pressure, relief_stiff_pressure)" in record.message
        for record in caplog.records
    ), "Expected warning about safety pressure falling below dependent bounds"
