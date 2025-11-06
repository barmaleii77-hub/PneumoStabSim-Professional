"""Integration-style tests for the graphics signal router."""

from __future__ import annotations

import logging
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Dict, List, Tuple

import pytest

from src.ui.main_window_pkg.signals_router import SignalsRouter
from src.ui.qml_bridge import QMLBridge


class _StubGraphicsLogger:
    def __init__(self) -> None:
        self.changes: List[Tuple[str, Dict[str, Any], bool]] = []

    def log_change(
        self,
        *,
        parameter_name: str,
        old_value: Any,
        new_value: Dict[str, Any],
        category: str,
        panel_state: Dict[str, Any],
        qml_state: Dict[str, Any] | None = None,
        applied_to_qml: bool = False,
        error: str | None = None,
    ) -> SimpleNamespace:
        self.changes.append((category, dict(new_value), bool(applied_to_qml)))
        return SimpleNamespace()

    def mark_category_changes_applied(
        self, category: str, since_timestamp: Any | None = None
    ) -> int:  # pragma: no cover - not used in this test but required by bridge
        return 1


@pytest.fixture()
def stub_graphics_logger(monkeypatch: pytest.MonkeyPatch) -> _StubGraphicsLogger:
    stub = _StubGraphicsLogger()
    module = ModuleType("src.ui.panels.graphics_logger")
    module.get_graphics_logger = lambda: stub  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "src.ui.panels.graphics_logger", module)
    return stub


@pytest.fixture()
def qml_bridge_spy(monkeypatch: pytest.MonkeyPatch) -> List[Tuple[str, Dict[str, Any]]]:
    calls: List[Tuple[str, Dict[str, Any]]] = []

    def fake_invoke(window, method_name, payload=None):
        calls.append((str(method_name), dict(payload or {})))
        return True

    def fake_queue(window, category, payload):  # pragma: no cover - failure path
        raise AssertionError(f"queue_update invoked for {category}: {payload}")

    monkeypatch.setattr(QMLBridge, "invoke_qml_function", fake_invoke)
    monkeypatch.setattr(QMLBridge, "queue_update", fake_queue)
    return calls


class _StubWindow:
    def __init__(self) -> None:
        self.logger = logging.getLogger("tests.integration.signal_router")
        self.event_logger = None
        self._last_camera_payload: Dict[str, Any] | None = None
        self._last_dispatched_payloads: Dict[str, Any] = {}
        self._qml_update_queue: Dict[str, Dict[str, Any]] = {}
        self._applied_updates: List[Tuple[str, Dict[str, Any]]] = []

    def _apply_settings_update(self, path: str, payload: Dict[str, Any]) -> None:
        self._applied_updates.append((path, dict(payload)))

    def normalizeHdrPath(self, value: str) -> str:  # noqa: N802 - Qt naming
        return (value or "").strip()


def test_signal_router_dispatches_direct_updates(
    stub_graphics_logger: _StubGraphicsLogger,
    qml_bridge_spy: List[Tuple[str, Dict[str, Any]]],
) -> None:
    """Applying a mix of graphics changes should map to direct QML calls."""

    window = _StubWindow()

    SignalsRouter.handle_lighting_changed(window, {"exposure": 1.25, "shadows": True})
    SignalsRouter.handle_material_changed(window, {"paint": {"roughness": 0.4}})
    SignalsRouter.handle_environment_changed(
        window,
        {
            "ibl_source": "studio.hdr",
            "reflection_enabled": True,
            "reflection_quality": "ultra",
        },
    )
    SignalsRouter.handle_quality_changed(
        window, {"msaa": 4, "shadows": "high", "taa": "on", "vSync": True}
    )
    SignalsRouter.handle_camera_changed(
        window,
        {
            "position": {"x": 1.0, "y": 2.0, "z": 3.0},
            "rotation": {"x": 0.0, "y": 45.0, "z": 0.0},
        },
    )
    SignalsRouter.handle_effects_changed(
        window, {"bloom": {"enabled": True, "intensity": 0.8}, "tonemap": "aces"}
    )

    invoked_methods = {name for name, _ in qml_bridge_spy}
    assert invoked_methods == {
        "applyLightingUpdates",
        "applyMaterialUpdates",
        "applyEnvironmentUpdates",
        "apply3DUpdates",
        "applyQualityUpdates",
        "applyCameraUpdates",
        "applyEffectsUpdates",
    }

    applied_paths = {path for path, _ in window._applied_updates}
    assert applied_paths == {
        "graphics.lighting",
        "graphics.materials",
        "graphics.environment",
        "graphics.quality",
        "graphics.camera",
        "graphics.effects",
    }

    recorded_categories = {category for category, _, _ in stub_graphics_logger.changes}
    assert recorded_categories == {
        "lighting",
        "materials",
        "environment",
        "threeD",
        "quality",
        "camera",
        "effects",
    }

    dispatched = getattr(window, "_last_dispatched_payloads", {}) or {}
    assert set(dispatched.keys()) == {
        "lighting",
        "materials",
        "environment",
        "threeD",
        "quality",
        "camera",
        "effects",
    }
