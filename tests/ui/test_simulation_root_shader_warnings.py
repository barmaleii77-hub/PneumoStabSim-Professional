"""Regression coverage for SimulationRoot shader warning bridging."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtQuick3D",
    reason="PySide6 QtQuick3D module is required to instantiate SimulationRoot",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtQml",
    reason="PySide6 QtQml module is required for SimulationRoot tests",
    exc_type=ImportError,
)

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine


os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")


class _DummyBridge(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.register_calls: list[tuple[object, object]] = []
        self.clear_calls: list[object] = []

    @Slot(object, object)
    def registerShaderWarning(self, effect_id: object, message: object) -> None:  # noqa: N802 - QML slot name
        self.register_calls.append((effect_id, message))

    @Slot(object)
    def clearShaderWarning(self, effect_id: object) -> None:  # noqa: N802 - QML slot name
        self.clear_calls.append(effect_id)


class _DummyPostEffects(QObject):
    effectCompilationError = Signal(object, object, object)
    effectCompilationRecovered = Signal(object, object)


def _create_simulation_root() -> tuple[QQmlEngine, QQmlComponent, QObject]:
    engine = QQmlEngine()
    qml_root = Path("assets/qml").resolve()
    engine.addImportPath(str(qml_root))

    component = QQmlComponent(engine)
    root_path = qml_root / "PneumoStabSim" / "SimulationRoot.qml"
    component.loadUrl(QUrl.fromLocalFile(str(root_path)))

    if component.isError():  # pragma: no cover - diagnostic guard
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load SimulationRoot.qml: {messages}")

    root = component.create()
    assert root is not None, "Expected SimulationRoot to instantiate"
    return engine, component, root


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_shader_warning_handlers_route_through_bridge(qapp) -> None:
    engine, component, root = _create_simulation_root()
    bridge = _DummyBridge()
    post_effects = _DummyPostEffects()

    try:
        root.setProperty("sceneBridge", bridge)
        root.setProperty("postEffects", post_effects)
        qapp.processEvents()

        post_effects.effectCompilationError.emit("fog", True, "compile failed")
        qapp.processEvents()
        assert bridge.register_calls == [("fog", "compile failed")]

        post_effects.effectCompilationRecovered.emit("fog", False)
        qapp.processEvents()
        assert bridge.clear_calls == ["fog"]
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
