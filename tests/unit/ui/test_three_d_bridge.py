from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.ui.main_window import qml_bridge


class _DummySettings:
    def __init__(self, payload: dict | None = None) -> None:
        self._payload = payload or {}

    def get(self, path: str, default: object = None) -> object:  # pragma: no cover - trivial
        if path == "current.threeD":
            return self._payload
        return default


class _DummyWindow(SimpleNamespace):
    pass


def test_initial_three_d_payload_defaults() -> None:
    payload = qml_bridge.initial_three_d_payload()

    assert payload["camera"]["azimuth"] == pytest.approx(35.0)
    assert set(payload["primitives"].keys()) == {"box", "sphere", "cylinder"}
    assert payload["lighting"]["keyIntensity"] > 0


def test_initial_three_d_payload_merges_settings_and_overrides() -> None:
    settings = _DummySettings({"camera": {"distance": 4.5}, "lighting": {"keyIntensity": 42}})
    payload = qml_bridge.initial_three_d_payload(settings, overrides={"camera": {"azimuth": 12}})

    assert payload["camera"]["distance"] == pytest.approx(4.5)
    assert payload["camera"]["azimuth"] == pytest.approx(12)
    assert payload["lighting"]["keyIntensity"] == pytest.approx(42)


def test_sync_three_d_state_enqueues_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_window = _DummyWindow()
    flushed_payloads: list[dict] = []

    def _fake_flush(window: object) -> None:  # pragma: no cover - simple hook
        flushed_payloads.append(getattr(window, "_qml_update_queue", {}))

    monkeypatch.setattr(qml_bridge.QMLBridge, "flush_updates", _fake_flush)

    payload = qml_bridge.sync_three_d_state(dummy_window, overrides={"lighting": {"rimIntensity": 123}}, flush=True)

    assert "threeD" in getattr(dummy_window, "_qml_update_queue")
    queued_payload = dummy_window._qml_update_queue["threeD"]
    assert queued_payload["lighting"]["rimIntensity"] == 123
    assert payload["lighting"]["rimIntensity"] == 123
    assert flushed_payloads, "flush_updates should be called when flush=True"
