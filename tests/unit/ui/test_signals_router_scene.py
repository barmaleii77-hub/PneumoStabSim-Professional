from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from src.ui.main_window_pkg import signals_router
from src.ui.environment_schema import validate_scene_settings


class _StubBridge:
    calls: list[tuple[str, dict[str, Any]]] = []
    queue_calls: list[tuple[str, dict[str, Any]]] = []
    logs: list[tuple[str, dict[str, Any], bool]] = []
    invoke_result: bool = True

    @staticmethod
    def invoke_qml_function(window, name: str, payload: dict[str, Any]) -> bool:
        _StubBridge.calls.append((name, dict(payload)))
        return _StubBridge.invoke_result

    @staticmethod
    def queue_update(_window, category: str, payload: dict[str, Any]) -> None:
        if payload:
            _StubBridge.queue_calls.append((category, dict(payload)))

    @staticmethod
    def _log_graphics_change(
        window, category: str, payload: dict[str, Any], applied: bool
    ) -> None:
        _StubBridge.logs.append((category, dict(payload), applied))


class _StubLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, tuple[Any, ...]]] = []

    def warning(self, message: str, *args: Any, **_kwargs: Any) -> None:
        self.records.append(("warning", (message, *args)))


class _StubWindow:
    def __init__(self) -> None:
        self.logger = _StubLogger()
        self.saved_updates: list[tuple[str, dict[str, Any]]] = []

    def _apply_settings_update(self, path: str, payload: dict[str, Any]) -> None:
        self.saved_updates.append((path, dict(payload)))


@pytest.fixture(autouse=True)
def _patch_qml_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    _StubBridge.calls.clear()
    _StubBridge.queue_calls.clear()
    _StubBridge.logs.clear()
    _StubBridge.invoke_result = True
    monkeypatch.setattr(signals_router, "QMLBridge", _StubBridge)


def _scene_payload() -> dict[str, Any]:
    return {
        "scale_factor": 2.5,
        "exposure": 3.75,
        "default_clear_color": "#ABCDEF",
        "model_base_color": "#123456",
        "model_roughness": 0.35,
        "model_metalness": 0.8,
    }


def _effects_payload() -> dict[str, Any]:
    return {
        "bloom": {"enabled": True, "intensity": 0.6},
        "tonemap_mode": "aces",
        "tonemap_enabled": True,
        "motion_blur": True,
        "motion_blur_amount": 0.2,
    }


def test_handle_scene_changed_invokes_qml_bridge() -> None:
    window = _StubWindow()
    params = _scene_payload()

    signals_router.SignalsRouter.handle_scene_changed(window, params)

    expected = validate_scene_settings(_scene_payload())

    assert _StubBridge.calls == [("applySceneUpdates", expected)]
    assert not _StubBridge.queue_calls

    assert window.saved_updates == [("graphics.scene", expected)]
    assert _StubBridge.logs == [("scene", expected, True)]


def test_handle_scene_changed_queues_on_invoke_failure() -> None:
    window = _StubWindow()
    params = _scene_payload()

    _StubBridge.invoke_result = False
    try:
        signals_router.SignalsRouter.handle_scene_changed(window, params)
    finally:
        _StubBridge.invoke_result = True

    expected = validate_scene_settings(_scene_payload())

    assert _StubBridge.calls == [("applySceneUpdates", expected)]
    assert _StubBridge.queue_calls == [("scene", expected)]
    assert window.saved_updates == [("graphics.scene", expected)]
    assert _StubBridge.logs == [("scene", expected, False)]


def test_handle_effects_changed_invokes_qml_bridge() -> None:
    window = _StubWindow()
    params = _effects_payload()

    signals_router.SignalsRouter.handle_effects_changed(window, params)

    expected = _effects_payload()

    assert _StubBridge.calls == [("applyEffectsUpdates", expected)]
    assert not _StubBridge.queue_calls
    assert window.saved_updates == [("graphics.effects", expected)]
    assert _StubBridge.logs == [("effects", expected, True)]


def test_handle_effects_changed_queues_on_invoke_failure() -> None:
    window = _StubWindow()
    params = _effects_payload()

    _StubBridge.invoke_result = False
    try:
        signals_router.SignalsRouter.handle_effects_changed(window, params)
    finally:
        _StubBridge.invoke_result = True

    expected = _effects_payload()

    assert _StubBridge.calls == [("applyEffectsUpdates", expected)]
    assert _StubBridge.queue_calls == [("effects", expected)]
    assert window.saved_updates == [("graphics.effects", expected)]
    assert _StubBridge.logs == [("effects", expected, False)]


def test_handle_scene_changed_logs_validation_error() -> None:
    window = _StubWindow()
    invalid_payload = {"scale_factor": 1.0}

    signals_router.SignalsRouter.handle_scene_changed(window, invalid_payload)

    assert not _StubBridge.calls
    assert not _StubBridge.queue_calls
    assert not window.saved_updates
    assert window.logger.records
    level, args = window.logger.records[-1]
    assert level == "warning"
    assert "Invalid scene payload" in args[0]
