"""Integration coverage for panel interactions and validation flows."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.ui.environment_schema import (
    EnvironmentValidationError,
    validate_environment_settings,
)
from src.ui.panels.graphics.panel_graphics import GraphicsPanel
from src.ui.panels.graphics.panel_graphics_settings_manager import (
    GraphicsSettingsError,
)


@pytest.fixture()
def _panel_with_isolated_settings(tmp_path, monkeypatch, qtbot):
    """Instantiate ``GraphicsPanel`` with a temp settings file."""

    baseline = json.loads(Path("config/app_settings.json").read_text(encoding="utf-8"))
    settings_path = tmp_path / "app_settings.json"
    settings_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setenv("PSS_SETTINGS_FILE", str(settings_path))

    panel = GraphicsPanel()
    qtbot.addWidget(panel)
    return panel


@pytest.mark.gui
@pytest.mark.integration
@pytest.mark.usefixtures("qapp")
def test_graphics_panel_rejects_unknown_and_invalid_payload(_panel_with_isolated_settings):
    panel = _panel_with_isolated_settings
    baseline = panel.collect_state()

    with pytest.raises(GraphicsSettingsError):
        panel.settings_service.ensure_valid_state({**baseline, "unexpected": {}})

    invalid_environment = deepcopy(baseline)
    invalid_environment["environment"]["fog_far"] = (
        invalid_environment["environment"]["fog_near"] - 1.0
    )

    with pytest.raises(EnvironmentValidationError):
        validate_environment_settings(invalid_environment["environment"])

    validated_environment = deepcopy(baseline)
    validated_environment["environment"]["fog_far"] = validated_environment[
        "environment"
    ]["fog_near"]

    validated = panel.settings_service.ensure_valid_state(validated_environment)
    assert validated["environment"]["fog_far"] >= validated["environment"]["fog_near"]


@pytest.mark.gui
@pytest.mark.integration
@pytest.mark.usefixtures("qapp")
def test_graphics_panel_round_trip_applies_validated_payload(_panel_with_isolated_settings):
    panel = _panel_with_isolated_settings
    current_state = panel.collect_state()

    adjusted = deepcopy(current_state)
    adjusted["camera"]["speed"] = 0.35
    adjusted["quality"]["frame_rate_limit"] = 90.0

    validated = panel.settings_service.ensure_valid_state(adjusted)
    panel.settings_service.save_current(validated)

    reloaded = panel.settings_service.load_current()
    assert reloaded["camera"]["speed"] == pytest.approx(0.35)
    assert reloaded["quality"]["frame_rate_limit"] == pytest.approx(90.0)
