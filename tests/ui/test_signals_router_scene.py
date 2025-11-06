from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Tuple

import pytest

from src.ui.main_window_pkg import signals_router
from src.ui.main_window_pkg.signals_router import SignalsRouter


class _RecordingBridge:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, str, Dict[str, Any]]] = []

    @staticmethod
    def queue_update(window: Any, category: str, payload: Dict[str, Any]) -> None:
        window._queued_updates.append((category, dict(payload)))

    def invoke_qml_function(
        self, window: Any, method_name: str, payload: Dict[str, Any]
    ) -> bool:
        self.calls.append(("invoke", method_name, dict(payload)))
        return True

    @staticmethod
    def _log_graphics_change(
        window: Any, category: str, payload: Dict[str, Any], applied: bool
    ) -> None:
        window._graphics_log.append((category, dict(payload), applied))


@pytest.fixture()
def bridge_stub(monkeypatch: pytest.MonkeyPatch) -> _RecordingBridge:
    stub = _RecordingBridge()
    monkeypatch.setattr(signals_router, "QMLBridge", stub)
    monkeypatch.setattr(signals_router, "QTimer", None)
    monkeypatch.setattr(signals_router, "QObject", None)
    monkeypatch.setitem(SignalsRouter._DEBOUNCE_DELAYS_MS, "effects", 0)
    return stub


def test_effects_updates_invoke_qml_bridge(bridge_stub: _RecordingBridge) -> None:
    window = SimpleNamespace(
        _apply_settings_update=lambda *_args, **_kwargs: None,
        _queued_updates=[],
        _graphics_log=[],
    )

    payload = {"bloom_enabled": True, "motion_blur": False}

    SignalsRouter.handle_effects_changed(window, payload)

    assert any(
        call[0] == "invoke"
        and call[1] == "applyEffectsUpdates"
        and call[2] == payload
        for call in bridge_stub.calls
    ), "Expected effects update to invoke the QML bridge"

    assert not window._queued_updates
