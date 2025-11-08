import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for EnvironmentTab tests",
    exc_type=ImportError,
)

from copy import deepcopy

import src.ui.panels.graphics.environment_tab as environment_tab_module

from src.common.settings_manager import get_settings_manager
from src.ui.environment_schema import (
    ENVIRONMENT_SLIDER_RANGE_DEFAULTS,
    validate_environment_settings,
)
from src.ui.panels.graphics.environment_tab import EnvironmentTab


def test_environment_tab_preserves_default_radius(qapp):
    manager = get_settings_manager()
    env_settings = manager.get("graphics.environment")
    assert env_settings, "Expected environment settings in current profile"

    validated = validate_environment_settings(env_settings)

    tab = EnvironmentTab()
    tab.set_state(validated)

    state = tab.get_state()

    assert state["ao_radius"] == pytest.approx(validated["ao_radius"])


def test_environment_tab_applies_custom_slider_ranges(qapp, monkeypatch):
    base_manager = get_settings_manager()
    custom_ranges = {
        key: {
            "min": value.minimum,
            "max": value.maximum,
            "step": value.step,
        }
        for key, value in ENVIRONMENT_SLIDER_RANGE_DEFAULTS.items()
    }
    custom_ranges["ibl_intensity"] = {"min": 0.5, "max": 1.5, "step": 0.1}

    class _StubManager:
        def __init__(self, base, ranges):
            self._base = base
            self._ranges = deepcopy(ranges)

        def get(self, path, default=None):
            if path == "graphics.environment_ranges":
                return deepcopy(self._ranges)
            if path == "metadata.environment_slider_ranges":
                return None
            if path == "defaults_snapshot.graphics.environment_ranges":
                return None
            return self._base.get(path, default)

    monkeypatch.setattr(
        environment_tab_module,
        "get_settings_manager",
        lambda: _StubManager(base_manager, custom_ranges),
    )

    warnings: list[str] = []

    def _capture_warning(parent, title, text):
        warnings.append(text)
        return None

    monkeypatch.setattr(environment_tab_module.QMessageBox, "warning", _capture_warning)

    tab = EnvironmentTab()
    slider = tab.get_controls()["ibl.intensity"]

    assert slider._min == pytest.approx(0.5)
    assert slider._max == pytest.approx(1.5)
    assert slider.step_size == pytest.approx(0.1)
    assert not warnings


def test_environment_tab_missing_range_triggers_warning(qapp, monkeypatch):
    base_manager = get_settings_manager()
    partial_ranges = {
        key: {
            "min": value.minimum,
            "max": value.maximum,
            "step": value.step,
        }
        for key, value in ENVIRONMENT_SLIDER_RANGE_DEFAULTS.items()
    }
    partial_ranges.pop("skybox_brightness")

    class _StubManager:
        def __init__(self, base, ranges):
            self._base = base
            self._ranges = deepcopy(ranges)

        def get(self, path, default=None):
            if path == "graphics.environment_ranges":
                return deepcopy(self._ranges)
            return self._base.get(path, default)

    monkeypatch.setattr(
        environment_tab_module,
        "get_settings_manager",
        lambda: _StubManager(base_manager, partial_ranges),
    )

    captured: list[str] = []

    def _capture_warning(parent, title, text):
        captured.append(text)
        return None

    monkeypatch.setattr(environment_tab_module.QMessageBox, "warning", _capture_warning)

    tab = EnvironmentTab()
    slider = tab.get_controls()["ibl.skybox_brightness"]

    default_range = ENVIRONMENT_SLIDER_RANGE_DEFAULTS["skybox_brightness"]
    assert slider._min == pytest.approx(default_range.minimum)
    assert slider._max == pytest.approx(default_range.maximum)
    assert slider.step_size == pytest.approx(default_range.step)
    assert captured
    message = "\n".join(captured)
    assert "skybox_brightness" in message
    assert "Используются значения по умолчанию" in message


def test_environment_tab_uses_metadata_ranges_when_current_missing(qapp, monkeypatch):
    base_manager = get_settings_manager()
    partial_ranges = {
        key: {
            "min": value.minimum,
            "max": value.maximum,
            "step": value.step,
        }
        for key, value in ENVIRONMENT_SLIDER_RANGE_DEFAULTS.items()
    }
    partial_ranges.pop("skybox_brightness")

    metadata_ranges = {
        key: {
            "min": value.minimum,
            "max": value.maximum,
            "step": value.step,
        }
        for key, value in ENVIRONMENT_SLIDER_RANGE_DEFAULTS.items()
    }
    metadata_ranges["skybox_brightness"] = {"min": 0.2, "max": 4.0, "step": 0.2}

    class _StubManager:
        def __init__(self, base, ranges, metadata):
            self._base = base
            self._ranges = deepcopy(ranges)
            self._metadata = deepcopy(metadata)

        def get(self, path, default=None):
            if path == "graphics.environment_ranges":
                return deepcopy(self._ranges)
            if path == "metadata.environment_slider_ranges":
                return deepcopy(self._metadata)
            if path == "defaults_snapshot.graphics.environment_ranges":
                return None
            return self._base.get(path, default)

    monkeypatch.setattr(
        environment_tab_module,
        "get_settings_manager",
        lambda: _StubManager(base_manager, partial_ranges, metadata_ranges),
    )

    captured: list[str] = []

    def _capture_warning(parent, title, text):
        captured.append(text)
        return None

    monkeypatch.setattr(environment_tab_module.QMessageBox, "warning", _capture_warning)

    tab = EnvironmentTab()
    slider = tab.get_controls()["ibl.skybox_brightness"]

    assert slider._min == pytest.approx(0.2)
    assert slider._max == pytest.approx(4.0)
    assert slider.step_size == pytest.approx(0.2)
    assert captured
    message = "\n".join(captured)
    assert "metadata.environment_slider_ranges" in message
    assert "skybox_brightness" in message


def test_environment_tab_applies_metadata_decimals_and_units(qapp, monkeypatch):
    base_manager = get_settings_manager()
    partial_ranges = {
        key: {
            "min": value.minimum,
            "max": value.maximum,
            "step": value.step,
        }
        for key, value in ENVIRONMENT_SLIDER_RANGE_DEFAULTS.items()
    }
    partial_ranges.pop("fog_near")

    metadata_ranges = {
        "fog_near": {
            "min": 0.0,
            "max": 250.0,
            "step": 0.5,
            "decimals": 3,
            "units": "м",
        }
    }

    class _StubManager:
        def __init__(self, base, ranges, metadata):
            self._base = base
            self._ranges = deepcopy(ranges)
            self._metadata = deepcopy(metadata)

        def get(self, path, default=None):
            if path == "graphics.environment_ranges":
                return deepcopy(self._ranges)
            if path == "metadata.environment_slider_ranges":
                return deepcopy(self._metadata)
            if path == "defaults_snapshot.graphics.environment_ranges":
                return None
            return self._base.get(path, default)

    monkeypatch.setattr(
        environment_tab_module,
        "get_settings_manager",
        lambda: _StubManager(base_manager, partial_ranges, metadata_ranges),
    )

    tab = EnvironmentTab()
    slider = tab.get_controls()["fog.near"]

    assert slider._decimals == 3
    assert slider._unit == "м"
    assert slider._min == pytest.approx(0.0)
    assert slider._max == pytest.approx(250.0)
    assert slider.step_size == pytest.approx(0.5)
