from collections.abc import Mapping
from typing import Any

import pytest

from tests.helpers import SignalListener, require_qt_modules

require_qt_modules("PySide6.QtQml")

from src.ui.scene_bridge import SceneBridge  # noqa: E402
from src.ui.services.visualization_service import VisualizationService  # noqa: E402


class _DummySettingsManager:
    def __init__(self, payload: Mapping[str, Any] | None = None) -> None:
        self.data = dict(payload or {})

    def get(self, dotted_path: str, default: Any | None = None) -> Any:
        segments = dotted_path.split(".")
        node: Any = self.data
        for segment in segments:
            if not isinstance(node, dict) or segment not in node:
                return default
            node = node[segment]
        return node

    def set(self, dotted_path: str, value: Any, auto_save: bool = True) -> bool:  # noqa: ARG002
        segments = dotted_path.split(".")
        node: dict[str, Any] = self.data
        for segment in segments[:-1]:
            node = node.setdefault(segment, {})
        node[segments[-1]] = value
        return True


@pytest.fixture()
def materials_settings_manager() -> _DummySettingsManager:
    return _DummySettingsManager(
        {
            "current": {
                "graphics": {
                    "materials": {"frame": {"roughness": 0.5}},
                    "materials_previous": {"frame": {"roughness": 0.25}},
                    "effects": {"bloom_enabled": False},
                }
            }
        }
    )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_scene_bridge_rollback_materials_emits_reset(
    materials_settings_manager: _DummySettingsManager,
) -> None:
    service = VisualizationService(settings_manager=materials_settings_manager)
    bridge = SceneBridge(
        visualization_service=service, settings_manager=materials_settings_manager
    )

    reset_spy = SignalListener(bridge.resetSharedMaterials)
    materials_spy = SignalListener(bridge.materialsChanged)

    rolled_back = bridge.rollback_materials()

    assert rolled_back["frame"]["roughness"] == 0.25
    assert len(reset_spy) == 1
    assert len(materials_spy) >= 1
    assert materials_spy[-1][0]["frame"]["roughness"] == 0.25


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_scene_bridge_undo_post_effects_triggers_signal(
    materials_settings_manager: _DummySettingsManager,
) -> None:
    service = VisualizationService(settings_manager=materials_settings_manager)
    bridge = SceneBridge(
        visualization_service=service, settings_manager=materials_settings_manager
    )

    undo_spy = SignalListener(bridge.undoPostEffects)
    effects_spy = SignalListener(bridge.effectsChanged)

    snapshot = bridge.undo_post_effects()

    assert snapshot.get("bloom_enabled") is False
    assert len(undo_spy) == 1
    assert undo_spy[-1][0].get("bloom_enabled") is False
    assert len(effects_spy) >= 1
    assert effects_spy[-1][0].get("bloom_enabled") is False
