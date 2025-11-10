"""Integration test validating EnvironmentTab ↔ QML synchronisation."""

from __future__ import annotations

import math
import os
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for environment sync tests",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtQml",
    reason="PySide6 QtQml module is required for SimulationRoot tests",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtQuick3D",
    reason="PySide6 QtQuick3D module is required to instantiate SimulationRoot",
    exc_type=ImportError,
)

from PySide6.QtCore import QObject, QMetaObject, QUrl, Q_ARG
from PySide6.QtQml import QQmlComponent, QQmlEngine

from src.ui.panels.graphics.environment_tab import EnvironmentTab

os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")


def _create_simulation_root() -> tuple[QQmlEngine, QQmlComponent, QObject]:
    engine = QQmlEngine()
    qml_root = Path("assets/qml").resolve()
    engine.addImportPath(str(qml_root))

    component = QQmlComponent(engine)
    root_path = qml_root / "PneumoStabSim" / "SimulationRoot.qml"
    component.loadUrl(QUrl.fromLocalFile(str(root_path)))

    if component.isError():  # pragma: no cover - defensive guard
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load SimulationRoot.qml: {messages}")

    root = component.create()
    assert root is not None, "Expected SimulationRoot to instantiate"
    return engine, component, root


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_environment_updates_propagate_to_scene_environment(qapp) -> None:
    engine, component, root = _create_simulation_root()
    tab = EnvironmentTab()

    try:
        state = tab.get_state()
        state["fog_enabled"] = not state["fog_enabled"]
        state["fog_density"] = 0.35
        state["ibl_enabled"] = True
        state["skybox_enabled"] = True
        state["ibl_bind_to_camera"] = True

        ok = QMetaObject.invokeMethod(
            root, "applyEnvironmentUpdates", Q_ARG("QVariant", state)
        )
        assert ok, "applyEnvironmentUpdates invocation failed"
        qapp.processEvents()

        scene_environment = root.findChild(QObject, "sceneEnvironment")
        assert scene_environment is not None, "sceneEnvironment controller missing"

        assert scene_environment.property("fogEnabled") == state["fog_enabled"]
        assert math.isclose(
            float(scene_environment.property("fogDensity")),
            float(state["fog_density"]),
            rel_tol=1e-6,
            abs_tol=1e-6,
        )
        assert scene_environment.property("iblLightingEnabled") == state["ibl_enabled"]
        assert scene_environment.property("skyboxToggleFlag") == state["skybox_enabled"]

        environment_state = root.property("environmentState")
        assert isinstance(environment_state, dict)
        assert environment_state.get("fog_enabled") == state["fog_enabled"]
        assert math.isclose(
            float(environment_state.get("fog_density", 0.0)),
            float(state["fog_density"]),
            rel_tol=1e-6,
            abs_tol=1e-6,
        )
        assert environment_state.get("ibl_enabled") == state["ibl_enabled"]
        assert environment_state.get("skybox_enabled") == state["skybox_enabled"]
    finally:
        tab.deleteLater()
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
