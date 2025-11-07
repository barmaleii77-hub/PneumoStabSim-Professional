"""pytest-qt coverage for :class:`GraphicsPanel` bridge payloads."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for GraphicsPanel tests",
    exc_type=ImportError,
)

from PySide6.QtCore import QObject

from src.ui.panels.graphics.panel_graphics_refactored import GraphicsPanel
from src.ui.main_window_pkg import signals_router
from src.ui.qml_bridge import QMLBridge as RealBridge


class _BridgeStub:
    invoke_result: bool = False
    invoke_calls: list[tuple[str, dict[str, Any]]] = []
    queue_calls: list[tuple[str, dict[str, Any]]] = []
    logs: list[tuple[str, dict[str, Any], bool]] = []

    @staticmethod
    def invoke_qml_function(
        _window: object, name: str, payload: dict[str, Any]
    ) -> bool:
        _BridgeStub.invoke_calls.append((name, dict(payload)))
        return _BridgeStub.invoke_result

    @staticmethod
    def queue_update(_window: object, category: str, payload: dict[str, Any]) -> None:
        if not payload:
            return
        _BridgeStub.queue_calls.append((category, dict(payload)))

    @staticmethod
    def _log_graphics_change(
        _window: object, category: str, payload: dict[str, Any], applied: bool
    ) -> None:
        _BridgeStub.logs.append((category, dict(payload), applied))


class _WindowStub(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._qml_update_queue: dict[str, dict[str, Any]] = {}
        self._last_dispatched_payloads: dict[str, dict[str, Any]] = {}
        self.settings_applied: list[tuple[str, dict[str, Any]]] = []

    def _apply_settings_update(self, path: str, params: dict[str, Any]) -> None:
        self.settings_applied.append((path, dict(params)))


@pytest.mark.gui
def test_graphics_panel_lighting_payload_hits_queue(
    qtbot: pytestqt.qtbot.QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate user edits and assert lighting payload respects bridge schema."""

    monkeypatch.setattr(signals_router, "QMLBridge", _BridgeStub)
    _BridgeStub.invoke_calls.clear()
    _BridgeStub.queue_calls.clear()
    _BridgeStub.logs.clear()
    _BridgeStub.invoke_result = False

    panel = GraphicsPanel()
    qtbot.addWidget(panel)

    window = _WindowStub()
    panel.lighting_changed.connect(
        lambda payload: signals_router.SignalsRouter.handle_lighting_changed(
            window, payload
        )
    )

    qtbot.wait(200)
    _BridgeStub.queue_calls.clear()

    brightness = panel.lighting_tab.get_controls()["key.brightness"]
    brightness._spin.setFocus()
    qtbot.wait(50)
    brightness._spin.setValue(brightness._spin.value() + brightness._spin.singleStep())
    qtbot.wait(250)

    assert _BridgeStub.queue_calls, "GraphicsPanel lighting change was not queued"

    category, payload = _BridgeStub.queue_calls[-1]
    assert category == "lighting"
    assert category in RealBridge.describe_routes()
    assert "key" in payload and "brightness" in payload["key"]
    assert payload["key"]["brightness"] == pytest.approx(brightness.value())
