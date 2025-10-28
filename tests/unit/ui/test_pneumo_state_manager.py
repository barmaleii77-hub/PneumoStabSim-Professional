import pytest

from src.ui.panels.pneumo.state_manager import PneumoStateManager


class DummySettings:
    def __init__(self, current=None, defaults=None):
        self._current = current or {}
        self._defaults = defaults or {}
        self.saved = {}

    def get(self, path, default=None):
        if path == "current.pneumatic":
            return dict(self._current)
        if path == "defaults_snapshot.pneumatic":
            return dict(self._defaults)
        return default

    def set(self, path, value, auto_save=True):
        self.saved[path] = value


def test_load_respects_pressure_units_in_storage():
    current = {
        "pressure_units": "Па",
        "relief_min_pressure": 250_000.0,
        "cv_atmo_dp": 1_000.0,
    }
    manager = PneumoStateManager(settings_manager=DummySettings(current=current))

    assert manager.get_pressure_units() == "Па"
    assert manager.get_relief_pressure("relief_min_pressure") == pytest.approx(250_000.0)
    assert manager.get_pressure_drop("cv_atmo_dp") == pytest.approx(1_000.0)


def test_switching_pressure_units_converts_values_and_persists_as_pa():
    dummy = DummySettings(
        current={
            "pressure_units": "Па",
            "relief_min_pressure": 250_000.0,
            "cv_atmo_dp": 1_000.0,
        }
    )

    manager = PneumoStateManager(settings_manager=dummy)
    manager.set_pressure_units("бар")

    assert manager.get_pressure_units() == "бар"
    assert manager.get_relief_pressure("relief_min_pressure") == pytest.approx(2.5)
    assert manager.get_pressure_drop("cv_atmo_dp") == pytest.approx(0.01)

    manager.save_state()
    saved = dummy.saved.get("current.pneumatic")
    assert saved is not None
    assert saved["pressure_units"] == "бар"
    assert saved["relief_min_pressure"] == pytest.approx(250_000.0)
    assert saved["cv_atmo_dp"] == pytest.approx(1_000.0)
