from copy import deepcopy
from pathlib import Path

import pytest

from src.common.settings_manager import SettingsManager
from src.ui.panels.graphics.panel_graphics_settings_manager import (
    GraphicsSettingsError,
    GraphicsSettingsService,
)


SETTINGS_PATH = Path("config/app_settings.json")


@pytest.fixture()
def graphics_service() -> GraphicsSettingsService:
    manager = SettingsManager(settings_file=SETTINGS_PATH)
    return GraphicsSettingsService(settings_manager=manager)


def test_ensure_valid_state_rejects_unknown_keys(
    graphics_service: GraphicsSettingsService,
) -> None:
    state = deepcopy(graphics_service._baseline_current)
    state["camera"]["unexpected"] = 42
    with pytest.raises(GraphicsSettingsError):
        graphics_service.ensure_valid_state(state)


def test_coerce_state_drops_unknown_keys_when_allow_missing(
    graphics_service: GraphicsSettingsService,
) -> None:
    raw_state = deepcopy(graphics_service._baseline_current)
    raw_state["environment"]["mystery"] = 1
    normalized = graphics_service._coerce_state(
        raw_state,
        baseline=graphics_service._baseline_current,
        allow_missing=True,
        source="unit-test",
    )
    assert "mystery" not in normalized["environment"]
