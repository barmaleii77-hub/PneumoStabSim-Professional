import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for EnvironmentTab tests",
    exc_type=ImportError,
)

from src.common.settings_manager import get_settings_manager
from src.ui.environment_schema import validate_environment_settings
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
