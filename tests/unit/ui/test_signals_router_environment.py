"""Unit tests for environment routing helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from src.ui.main_window_pkg import signals_router


class _StubBridge:
    calls: List[Tuple[str, Dict[str, Any]]] = []
    logs: List[Tuple[str, Dict[str, Any], bool]] = []

    @staticmethod
    def invoke_qml_function(window, name: str, payload: Dict[str, Any]) -> bool:
        _StubBridge.calls.append((name, dict(payload)))
        return True

    @staticmethod
    def queue_update(*args, **kwargs) -> None:  # pragma: no cover - should not run
        raise AssertionError("queue_update should not be called when invoke succeeds")

    @staticmethod
    def _log_graphics_change(
        window, category: str, payload: Dict[str, Any], applied: bool
    ) -> None:
        _StubBridge.logs.append((category, dict(payload), applied))


class _StubLogger:
    def __init__(self) -> None:
        self.records: List[Tuple[str, Tuple[Any, ...]]] = []

    def warning(
        self, message: str, *args: Any, **kwargs: Any
    ) -> None:  # pragma: no cover - optional path
        self.records.append(("warning", (message, *args)))

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.records.append(("info", (message, *args)))

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.records.append(("debug", (message, *args)))


class _StubWindow:
    def __init__(self) -> None:
        self.logger = _StubLogger()
        self.saved_updates: List[Tuple[str, Dict[str, Any]]] = []

    def normalizeHdrPath(self, value: str) -> str:
        return value.replace("\\", "/")

    def _apply_settings_update(self, key: str, params: Dict[str, Any]) -> None:
        self.saved_updates.append((key, dict(params)))


@pytest.fixture(autouse=True)
def _patch_qml_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    _StubBridge.calls.clear()
    _StubBridge.logs.clear()
    monkeypatch.setattr(signals_router, "QMLBridge", _StubBridge)


def test_handle_environment_changed_normalises_hdr_path() -> None:
    window = _StubWindow()
    params: Dict[str, Any] = {
        "iblSource": "assets\\hdr\\studio.hdr",
        "ibl_enabled": True,
    }

    signals_router.SignalsRouter.handle_environment_changed(window, params)

    assert _StubBridge.calls, "invoke_qml_function should be called"
    call_name, payload = _StubBridge.calls[0]
    assert call_name == "applyEnvironmentUpdates"
    assert payload["ibl_source"] == "assets/hdr/studio.hdr"
    assert payload["iblSource"] == "assets/hdr/studio.hdr"

    assert params["ibl_source"] == "assets/hdr/studio.hdr"
    # Original key preserved with normalised value for backwards compatibility
    assert params["iblSource"] == "assets/hdr/studio.hdr"

    assert window.saved_updates
    _, saved_payload = window.saved_updates[0]
    assert saved_payload["ibl_source"] == "assets/hdr/studio.hdr"
