"""Tests for ensuring StateSync initial synchronisation invokes QML update methods."""

from __future__ import annotations

from collections import OrderedDict
from importlib import import_module

import pytest

from src.ui.main_window_pkg import state_sync


class DummyGraphicsPanel:
    """Stub graphics panel returning a deterministic state snapshot."""

    def __init__(self) -> None:
        self._state = OrderedDict(
            (
                ("geometry", {"frameLength": 2500.0}),
                ("environment", {"ibl_source": "studio.hdr", "fog": {"enabled": True}}),
                ("quality", {"aaPrimaryMode": "ssaa"}),
                ("effects", {"bloomEnabled": True}),
            )
        )

    def collect_state(self) -> OrderedDict[str, dict]:
        return self._state


class DummyWindow:
    def __init__(self) -> None:
        self.graphics_panel = DummyGraphicsPanel()
        self._last_batched_updates = None


@pytest.fixture()
def dummy_bridge(monkeypatch):
    """Provide a stubbed QMLBridge capturing invocations."""

    calls: list[tuple[str, dict]] = []

    class BridgeStub:
        QML_UPDATE_METHODS = {
            "geometry": ("applyGeometryUpdates",),
            "environment": ("applyEnvironmentUpdates",),
            "quality": ("applyQualityUpdates",),
            "effects": ("applyEffectsUpdates",),
        }

        @staticmethod
        def _push_batched_updates(window, state):
            calls.append(("batch", state))
            return False

        @staticmethod
        def invoke_qml_function(window, name, payload):
            calls.append((name, payload))
            return True

        @staticmethod
        def _log_graphics_change(window, category, payload, applied):
            calls.append((f"log:{category}", {"applied": applied}))

    bridge_module = import_module("src.ui.main_window_pkg.qml_bridge")
    monkeypatch.setattr(state_sync, "QMLBridge", BridgeStub, raising=False)
    monkeypatch.setattr(bridge_module, "QMLBridge", BridgeStub, raising=False)
    return calls


def test_initial_full_sync_invokes_all_apply_methods(dummy_bridge):
    """StateSync.initial_full_sync should invoke category apply functions when batch fails."""

    window = DummyWindow()

    state_sync.StateSync.initial_full_sync(window)

    invoked = {name for name, _payload in dummy_bridge if name.startswith("apply")}

    assert {
        "applyGeometryUpdates",
        "applyEnvironmentUpdates",
        "applyQualityUpdates",
        "applyEffectsUpdates",
    }.issubset(invoked)

    assert any(name == "batch" for name, _payload in dummy_bridge)
