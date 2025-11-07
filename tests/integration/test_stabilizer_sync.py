"""Integration coverage for the stabilizer synchronisation ACK flow."""

from __future__ import annotations

import logging
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Dict, List, Tuple

import pytest

from src.ui.main_window_pkg.state_sync import StateSync
from src.ui.qml_bridge import QMLBridge


class _FakeStatusBar:
    def __init__(self) -> None:
        self.messages: list[tuple[str, int]] = []

    def showMessage(self, message: str, timeout: int) -> None:  # noqa: N802 - Qt style
        self.messages.append((message, timeout))


class _FakeQmlRoot:
    def __init__(self) -> None:
        self.properties: dict[str, Any] = {}

    def setProperty(self, name: str, value: Any) -> bool:  # noqa: N802 - Qt style
        self.properties[name] = value
        return True


class _FakeGraphicsPanel:
    def __init__(self) -> None:
        self.state: dict[str, dict[str, Any]] = {
            "lighting": {"exposure": 1.0, "shadowsEnabled": True},
            "environment": {"ibl_source": "studio.hdr"},
            "scene": {
                "scale_factor": 1.0,
                "exposure": 1.5,
                "default_clear_color": "#1b1f27",
                "model_base_color": "#9ea4ab",
                "model_roughness": 0.35,
                "model_metalness": 0.9,
            },
            "quality": {"shading": "high", "anisotropy": 8},
            "effects": {"bloom": {"enabled": True, "intensity": 0.75}},
        }

    def collect_state(self) -> dict[str, dict[str, Any]]:
        return self.state


class _FakeGraphicsLogger:
    def __init__(self) -> None:
        self.log_change_calls: list[dict[str, Any]] = []
        self.mark_calls: list[tuple[str, Any]] = []

    def log_change(
        self,
        *,
        parameter_name: str,
        old_value: Any,
        new_value: Any,
        category: str,
        panel_state: dict[str, Any],
        qml_state: dict[str, Any] | None = None,
        applied_to_qml: bool = False,
        error: str | None = None,
    ) -> SimpleNamespace:
        self.log_change_calls.append(
            {
                "parameter_name": parameter_name,
                "category": category,
                "payload": new_value,
                "panel_state": panel_state,
                "qml_state": qml_state,
                "applied_to_qml": applied_to_qml,
                "error": error,
            }
        )
        return SimpleNamespace()

    def mark_category_changes_applied(
        self, category: str, since_timestamp: Any | None = None
    ) -> int:
        self.mark_calls.append((category, since_timestamp))
        return 1


class _FakeWindow:
    def __init__(self) -> None:
        self.logger = logging.getLogger("tests.integration.stabilizer_sync")
        self.graphics_panel = _FakeGraphicsPanel()
        self._qml_root_object = _FakeQmlRoot()
        self._last_batched_updates: dict[str, Any] | None = None
        self.status_bar = _FakeStatusBar()
        self._suppress_qml_feedback = False


@pytest.fixture()
def fake_window(monkeypatch: pytest.MonkeyPatch) -> _FakeWindow:
    window = _FakeWindow()
    fake_logger = _FakeGraphicsLogger()
    stub_module = ModuleType("src.ui.panels.graphics_logger")
    stub_module.get_graphics_logger = lambda: fake_logger  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "src.ui.panels.graphics_logger", stub_module)
    window._fake_logger = fake_logger  # type: ignore[attr-defined]
    return window


def test_stabilizer_ack_flow_completes_with_full_success(
    fake_window: _FakeWindow,
) -> None:
    """Full sync → batch ACK should mark every category applied."""

    initial_state = fake_window.graphics_panel.collect_state()

    StateSync.initial_full_sync(fake_window)

    assert fake_window._last_batched_updates == initial_state
    assert fake_window._qml_root_object.properties[
        "pendingPythonUpdates"
    ] == QMLBridge._prepare_for_qml(initial_state)

    summary = {"timestamp": "2025-05-05T12:00:00Z"}
    QMLBridge.handle_qml_ack(fake_window, summary)

    assert fake_window._last_batched_updates is None

    logger: _FakeGraphicsLogger = fake_window._fake_logger  # type: ignore[attr-defined]
    categories = {call["category"] for call in logger.log_change_calls}
    assert categories == set(initial_state.keys())
    assert all(call["applied_to_qml"] for call in logger.log_change_calls)

    marked_categories = {category for category, _ in logger.mark_calls}
    assert marked_categories == set(initial_state.keys())
    assert all(ts == summary["timestamp"] for _, ts in logger.mark_calls)

    assert fake_window.status_bar.messages[-1] == ("Обновления применены в сцене", 1500)
