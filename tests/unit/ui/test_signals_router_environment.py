"""Unit tests for environment routing helpers."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip(
    "PySide6.QtCore",
    reason="PySide6 QtCore module is required for signals router environment tests",
    exc_type=ImportError,
)

from src.ui.main_window_pkg import signals_router


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
        if not payload:
            return
        _StubBridge.queue_calls.append((category, dict(payload)))

    @staticmethod
    def _log_graphics_change(
        window, category: str, payload: dict[str, Any], applied: bool
    ) -> None:
        _StubBridge.logs.append((category, dict(payload), applied))


class _StubLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, tuple[Any, ...]]] = []

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
        self.saved_updates: list[tuple[str, dict[str, Any]]] = []

    def normalizeHdrPath(self, value: str) -> str:
        return value.replace("\\", "/")

    def _apply_settings_update(self, key: str, params: dict[str, Any]) -> None:
        self.saved_updates.append((key, dict(params)))


@pytest.fixture(autouse=True)
def _patch_qml_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    _StubBridge.calls.clear()
    _StubBridge.queue_calls.clear()
    _StubBridge.logs.clear()
    _StubBridge.invoke_result = True
    monkeypatch.setattr(signals_router, "QMLBridge", _StubBridge)


def test_handle_environment_changed_normalises_hdr_path() -> None:
    window = _StubWindow()
    params: dict[str, Any] = {
        "iblSource": "assets\\hdr\\studio.hdr",
        "ibl_enabled": True,
    }

    signals_router.SignalsRouter.handle_environment_changed(window, params)

    assert _StubBridge.calls, "invoke_qml_function should be called"
    call_name, payload = _StubBridge.calls[0]
    assert call_name == "applyEnvironmentUpdates"
    assert payload["ibl_source"] == "assets/hdr/studio.hdr"
    assert "iblSource" not in payload

    assert params["ibl_source"] == "assets/hdr/studio.hdr"
    assert "iblSource" not in params

    assert not _StubBridge.queue_calls

    assert window.saved_updates
    _, saved_payload = window.saved_updates[0]
    assert saved_payload["ibl_source"] == "assets/hdr/studio.hdr"
    assert "iblSource" not in saved_payload


def test_handle_environment_changed_prefers_canonical_key_when_both_provided() -> None:
    window = _StubWindow()
    params: dict[str, Any] = {
        "ibl_source": "assets/hdr/canonical.hdr",
        "iblSource": "assets/hdr/legacy.hdr",
        "ibl_enabled": False,
    }

    signals_router.SignalsRouter.handle_environment_changed(window, params)

    assert _StubBridge.calls
    _, payload = _StubBridge.calls[0]
    assert payload["ibl_source"] == "assets/hdr/canonical.hdr"
    assert "iblSource" not in payload

    assert params["ibl_source"] == "assets/hdr/canonical.hdr"
    assert "iblSource" not in params

    saved_payload = window.saved_updates[0][1]
    assert saved_payload["ibl_source"] == "assets/hdr/canonical.hdr"


def test_handle_environment_changed_supports_nested_sections() -> None:
    window = _StubWindow()
    params: dict[str, Any] = {
        "background": {"mode": "color", "color": "#445566", "skybox_enabled": False},
        "ibl": {"enabled": True, "intensity": 1.25, "source": "assets/hdr/nested.hdr"},
        "fog": {"enabled": True, "density": 0.42},
        "ambient_occlusion": {
            "enabled": True,
            "strength": 0.6,
            "radius": 5.0,
            "bias": 0.035,
            "dither": False,
            "sample_rate": 6,
        },
    }

    signals_router.SignalsRouter.handle_environment_changed(window, params)

    assert _StubBridge.calls
    call_name, payload = _StubBridge.calls[-1]
    assert call_name == "applyEnvironmentUpdates"
    assert payload["background_mode"] == "color"
    assert payload["background_color"] == "#445566"
    assert payload["ibl_enabled"] is True
    assert payload["ibl_intensity"] == 1.25
    assert payload["ibl_source"] == "assets/hdr/nested.hdr"
    assert payload["fog_enabled"] is True
    assert payload["fog_density"] == 0.42
    assert payload["ao_strength"] == 0.6
    assert payload["ao_radius"] == 5.0
    assert payload["ao_bias"] == 0.035
    assert payload["ao_sample_rate"] == 6
    assert payload["ao_dither"] is False
    assert "ssao" in payload
    assert payload["ssao"]["intensity"] == 0.6
    assert payload["ssao"]["bias"] == 0.035
    assert payload["ssao"]["dither"] is False

    assert params["ibl_source"] == "assets/hdr/nested.hdr"
    assert params["ao_strength"] == 0.6
    assert params["ssao"]["radius"] == 5.0
    assert params["ao_bias"] == 0.035


def test_environment_change_invoke_failure_queues_payload() -> None:
    window = _StubWindow()
    params: dict[str, Any] = {"iblSource": "assets\\hdr\\queued.hdr"}

    _StubBridge.invoke_result = False
    try:
        signals_router.SignalsRouter.handle_environment_changed(window, params)
    finally:
        _StubBridge.invoke_result = True

    assert _StubBridge.calls
    assert _StubBridge.queue_calls
    category, queued_payload = _StubBridge.queue_calls[0]
    assert category == "environment"
    assert queued_payload["ibl_source"] == "assets/hdr/queued.hdr"
    assert "iblSource" not in queued_payload

    assert params["ibl_source"] == "assets/hdr/queued.hdr"
    assert "iblSource" not in params

    saved_payload = window.saved_updates[0][1]
    assert saved_payload["ibl_source"] == "assets/hdr/queued.hdr"


def test_handle_preset_applied_normalizes_environment_section() -> None:
    window = _StubWindow()
    full_state: dict[str, Any] = {
        "environment": {
            "iblSource": " assets\\hdr\\preset.hdr ",
            "ibl_enabled": True,
        },
        "lighting": {"mode": "studio"},
        "materials": {},
        "quality": {},
        "camera": {},
        "effects": {},
    }

    signals_router.SignalsRouter.handle_preset_applied(window, full_state)

    env_state = full_state["environment"]
    assert env_state["ibl_source"] == "assets/hdr/preset.hdr"
    assert "iblSource" not in env_state

    env_queue_payloads = [
        payload
        for category, payload in _StubBridge.queue_calls
        if category == "environment"
    ]
    assert env_queue_payloads
    queued_payload = env_queue_payloads[-1]
    assert queued_payload["ibl_source"] == "assets/hdr/preset.hdr"
    assert "iblSource" not in queued_payload

    saved_key, saved_payload = window.saved_updates[-1]
    assert saved_key == "graphics"
    assert saved_payload["environment"]["ibl_source"] == "assets/hdr/preset.hdr"


def test_handle_environment_changed_skips_duplicate_payloads() -> None:
    window = _StubWindow()
    base_params: dict[str, Any] = {"iblSource": "assets/hdr/unique.hdr"}

    signals_router.SignalsRouter.handle_environment_changed(window, dict(base_params))
    initial_invoke_calls = len(_StubBridge.calls)

    signals_router.SignalsRouter.handle_environment_changed(window, dict(base_params))

    assert len(_StubBridge.calls) == initial_invoke_calls
    assert not _StubBridge.queue_calls


def test_handle_environment_changed_skips_duplicate_queued_payloads() -> None:
    window = _StubWindow()
    base_params: dict[str, Any] = {"iblSource": "assets\\hdr\\dedupe.hdr"}

    _StubBridge.invoke_result = False
    try:
        signals_router.SignalsRouter.handle_environment_changed(
            window, dict(base_params)
        )
        signals_router.SignalsRouter.handle_environment_changed(
            window, dict(base_params)
        )
    finally:
        _StubBridge.invoke_result = True

    assert len(_StubBridge.calls) == 1
    assert len(_StubBridge.queue_calls) == 1


@pytest.mark.parametrize("raw_value", [None, "   "])
def test_handle_environment_changed_handles_empty_hdr_selection(raw_value: Any) -> None:
    window = _StubWindow()
    params: dict[str, Any] = {"iblSource": raw_value, "ibl_enabled": False}

    signals_router.SignalsRouter.handle_environment_changed(window, params)

    assert _StubBridge.calls
    call_name, payload = _StubBridge.calls[-1]
    assert call_name == "applyEnvironmentUpdates"
    assert payload["ibl_source"] == ""
    assert params["ibl_source"] == ""

    saved_payload = window.saved_updates[-1][1]
    assert saved_payload["ibl_source"] == ""


def test_handle_environment_changed_preserves_extreme_slider_values() -> None:
    window = _StubWindow()
    params: dict[str, Any] = {
        "ibl_source": "assets/hdr/extreme.hdr",
        "ibl_intensity": 4.5,
        "skybox_brightness": 6.0,
        "fog_density": 0.95,
        "fog_near": 0.0,
        "fog_far": 500.0,
    }

    signals_router.SignalsRouter.handle_environment_changed(window, params)

    _, payload = _StubBridge.calls[-1]
    assert payload["ibl_source"] == "assets/hdr/extreme.hdr"
    assert payload["ibl_intensity"] == pytest.approx(4.5)
    assert payload["skybox_brightness"] == pytest.approx(6.0)
    assert payload["fog_density"] == pytest.approx(0.95)
    assert payload["fog_far"] == pytest.approx(500.0)


def test_handle_preset_applied_handles_quick_toggle_sequences() -> None:
    window = _StubWindow()
    first_state: dict[str, Any] = {
        "environment": {"iblSource": "assets/hdr/first.hdr", "ibl_enabled": True},
        "lighting": {"mode": "studio"},
        "materials": {},
        "quality": {},
        "camera": {},
        "effects": {},
    }
    second_state: dict[str, Any] = {
        "environment": {"iblSource": "assets/hdr/second.hdr", "ibl_enabled": True},
        "lighting": {"mode": "studio"},
        "materials": {},
        "quality": {},
        "camera": {},
        "effects": {},
    }

    signals_router.SignalsRouter.handle_preset_applied(window, first_state)
    signals_router.SignalsRouter.handle_preset_applied(window, second_state)
    signals_router.SignalsRouter.handle_preset_applied(window, second_state)

    env_payloads = [
        payload
        for category, payload in _StubBridge.queue_calls
        if category == "environment"
    ]
    assert len(env_payloads) == 2
    assert env_payloads[0]["ibl_source"] == "assets/hdr/first.hdr"
    assert env_payloads[1]["ibl_source"] == "assets/hdr/second.hdr"

    saved_payload = window.saved_updates[-1][1]
    assert saved_payload["environment"]["ibl_source"] == "assets/hdr/second.hdr"
