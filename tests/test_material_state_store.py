from __future__ import annotations

from typing import Any

from src.graphics.materials import MaterialStateStore


class _DummySettingsManager:
    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self.data: dict[str, Any] = initial or {}

    def get(self, dotted_path: str, default: Any = None) -> Any:
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


def test_material_state_store_rolls_back_and_persists_previous_state():
    initial_state = {
        "current": {
            "graphics": {
                "materials": {
                    "frame": {"base_color": "#111111", "roughness": 0.25},
                }
            }
        }
    }
    manager = _DummySettingsManager(initial_state)

    store = MaterialStateStore(settings_manager=manager)
    updated = store.apply_updates({"frame": {"roughness": 0.5}}, auto_save=True)

    assert updated["frame"]["roughness"] == 0.5
    previous_snapshot = manager.get("current.graphics.materials_previous")
    assert previous_snapshot["frame"]["roughness"] == 0.25

    rolled_back = store.rollback(auto_save=True)
    assert rolled_back["frame"]["roughness"] == 0.25
    assert manager.get("current.graphics.materials") == rolled_back


def test_material_state_store_tracks_previous_frame_between_updates():
    manager = _DummySettingsManager(
        {
            "current": {
                "graphics": {
                    "materials": {"frame": {"base_color": "#222222", "roughness": 0.1}}
                }
            }
        }
    )
    store = MaterialStateStore(settings_manager=manager)

    store.apply_updates({"frame": {"roughness": 0.3}})
    store.apply_updates({"frame": {"roughness": 0.9}})

    assert store.previous_state["frame"]["roughness"] == 0.3
    assert store.current_state["frame"]["roughness"] == 0.9
