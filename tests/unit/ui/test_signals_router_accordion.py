from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.ui.main_window_pkg import signals_router


class _WindowStub:
    def __init__(self) -> None:
        self.applied: list[tuple[str, dict[str, Any]]] = []

    def _apply_settings_update(self, key: str, params: dict[str, Any]) -> None:
        self.applied.append((key, params))


def test_field_commit_builds_nested_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    window = _WindowStub()
    modes_push_calls: list[str] = []
    monkeypatch.setattr(
        signals_router.SignalsRouter,
        "_push_modes_state",
        staticmethod(lambda _window: modes_push_calls.append("modes")),
    )

    signals_router.SignalsRouter.handle_accordion_field_committed(
        window, "modes", "physics.include_springs", True
    )

    assert window.applied == [("modes", {"physics": {"include_springs": True}})]
    assert modes_push_calls == ["modes"]


def test_field_commit_infers_panel_from_key(monkeypatch: pytest.MonkeyPatch) -> None:
    window = _WindowStub()
    simulation_push_calls: list[str] = []
    monkeypatch.setattr(
        signals_router.SignalsRouter,
        "_push_simulation_state",
        staticmethod(lambda _window: simulation_push_calls.append("simulation")),
    )

    signals_router.SignalsRouter.handle_accordion_field_committed(
        window, "", "simulation.physics_dt", 0.0025
    )

    assert window.applied == [("simulation", {"physics_dt": 0.0025})]
    assert simulation_push_calls == ["simulation"]


def test_preset_activation_delegates_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[tuple[object, str]] = []

    def _preset_stub(window: object, preset_id: str) -> None:
        called.append((window, preset_id))

    monkeypatch.setattr(
        signals_router.SignalsRouter,
        "handle_modes_preset_selected",
        staticmethod(_preset_stub),
    )

    sentinel_window = SimpleNamespace()
    signals_router.SignalsRouter.handle_accordion_preset_activated(
        sentinel_window, "modes", "road_profile"
    )

    assert called == [(sentinel_window, "road_profile")]
