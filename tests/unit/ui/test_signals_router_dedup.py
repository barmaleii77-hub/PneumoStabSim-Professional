"""Regression tests covering SignalsRouter deduplication logic."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from src.ui.main_window_pkg import signals_router


class _BridgeStub:
    invoke_calls: list[tuple[str, dict[str, Any]]] = []
    queue_calls: list[tuple[str, dict[str, Any]]] = []
    logs: list[tuple[str, dict[str, Any], bool]] = []
    invoke_result: bool = False

    @staticmethod
    def invoke_qml_function(window, name: str, payload: dict[str, Any]) -> bool:
        _BridgeStub.invoke_calls.append((name, dict(payload)))
        return _BridgeStub.invoke_result

    @staticmethod
    def queue_update(_window, category: str, payload: dict[str, Any]) -> None:
        if not payload:
            return
        _BridgeStub.queue_calls.append((category, dict(payload)))

    @staticmethod
    def _log_graphics_change(
        _window, category: str, payload: dict[str, Any], applied: bool
    ) -> None:
        _BridgeStub.logs.append((category, dict(payload), applied))


class _WindowStub:
    def __init__(self) -> None:
        self.saved_updates: list[tuple[str, dict[str, Any]]] = []

    def _apply_settings_update(self, key: str, params: dict[str, Any]) -> None:
        self.saved_updates.append((key, dict(params)))


@pytest.fixture(autouse=True)
def _patch_qml_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    _BridgeStub.invoke_calls.clear()
    _BridgeStub.queue_calls.clear()
    _BridgeStub.logs.clear()
    _BridgeStub.invoke_result = False
    monkeypatch.setattr(signals_router, "QMLBridge", _BridgeStub)


def test_quality_updates_queue_only_once_for_duplicates() -> None:
    window = _WindowStub()
    params: dict[str, Any] = {"taa_enabled": True, "fxaa_enabled": False}

    signals_router.SignalsRouter.handle_quality_changed(window, dict(params))
    signals_router.SignalsRouter.handle_quality_changed(window, dict(params))

    assert len(_BridgeStub.invoke_calls) == 1
    assert len(_BridgeStub.queue_calls) == 1


def test_lighting_updates_invoke_only_once_for_duplicates() -> None:
    window = _WindowStub()
    _BridgeStub.invoke_result = True
    params: dict[str, Any] = {"exposure": 1.5, "temperature": 6500}

    signals_router.SignalsRouter.handle_lighting_changed(window, dict(params))
    signals_router.SignalsRouter.handle_lighting_changed(window, dict(params))

    assert len(_BridgeStub.invoke_calls) == 1
    assert not _BridgeStub.queue_calls
