"""Integration test validating EnvironmentTab ↔ QML synchronisation."""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

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


def _create_simulation_root(
    context_overrides: dict[str, Any] | None = None,
) -> tuple[QQmlEngine, QQmlComponent, QObject]:
    engine = QQmlEngine()
    qml_root = Path("assets/qml").resolve()
    engine.addImportPath(str(qml_root))

    if context_overrides:
        context = engine.rootContext()
        for key, value in context_overrides.items():
            context.setContextProperty(str(key), value)

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
        assert not bool(root.property("reflectionProbeDefaultsWarningIssued"))
        assert root.property("reflectionProbeMissingKeys") == []
        state = tab.get_state()
        state["fog_enabled"] = not state["fog_enabled"]
        state["fog_density"] = 0.35
        state["ibl_enabled"] = True
        state["skybox_enabled"] = True
        state["ibl_bind_to_camera"] = True
        state["reflection_enabled"] = not state["reflection_enabled"]
        state["reflection_padding_m"] = float(state["reflection_padding_m"]) + 0.05
        state["reflection_quality"] = "low"
        state["reflection_refresh_mode"] = "firstframe"
        state["reflection_time_slicing"] = "allfacesatonce"

        ok = QMetaObject.invokeMethod(
            root, "applyEnvironmentUpdates", Q_ARG("QVariant", state)
        )
        assert ok, "applyEnvironmentUpdates invocation failed"
        qapp.processEvents()

        scene_environment = root.findChild(QObject, "sceneEnvironment")
        assert scene_environment is not None, "sceneEnvironment controller missing"

        assert scene_environment.property("fogEnabled") == state["fog_enabled"]

        fog_object = scene_environment.property("fog")
        assert isinstance(fog_object, QObject), "sceneEnvironment.fog object missing"

        assert math.isclose(
            float(fog_object.property("density")),
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

        reflection_payload = {
            "reflectionProbe": {
                "enabled": state["reflection_enabled"],
                "padding": state["reflection_padding_m"],
                "quality": state["reflection_quality"],
                "refreshMode": state["reflection_refresh_mode"],
                "timeSlicing": state["reflection_time_slicing"],
            }
        }

        ok = QMetaObject.invokeMethod(
            root, "apply3DUpdates", Q_ARG("QVariant", reflection_payload)
        )
        assert ok, "apply3DUpdates invocation failed"
        qapp.processEvents()

        assembly = root.property("sceneSuspensionAssembly")
        assert isinstance(assembly, QObject), "SuspensionAssembly alias missing"
        assert (
            bool(assembly.property("reflectionProbeEnabled"))
            == state["reflection_enabled"]
        )
        assert math.isclose(
            float(assembly.property("reflectionProbePaddingM")),
            float(state["reflection_padding_m"]),
            rel_tol=1e-6,
            abs_tol=1e-6,
        )

        probe = assembly.property("reflectionProbe")
        assert isinstance(probe, QObject), "ReflectionProbe object unavailable"
        assert int(assembly.property("reflectionProbeQualityValue")) == int(
            probe.property("quality")
        )
        assert int(assembly.property("reflectionProbeRefreshModeValue")) == int(
            probe.property("refreshMode")
        )
        assert int(assembly.property("reflectionProbeTimeSlicingValue")) == int(
            probe.property("timeSlicing")
        )
        enabled_index = probe.metaObject().indexOfProperty("enabled")
        assert enabled_index >= 0, "ReflectionProbe.enabled property unavailable"
        assert bool(probe.property("enabled")) == bool(state["reflection_enabled"])
        assert bool(probe.property("visible")) == bool(state["reflection_enabled"])
    finally:
        tab.deleteLater()
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_environment_update_disables_probe_visibility(qapp) -> None:
    engine, component, root = _create_simulation_root()

    try:
        state: dict[str, Any] = {"reflection_enabled": False}

        ok = QMetaObject.invokeMethod(
            root, "applyEnvironmentUpdates", Q_ARG("QVariant", state)
        )
        assert ok, "applyEnvironmentUpdates invocation failed"
        qapp.processEvents()

        scene_environment = root.findChild(QObject, "sceneEnvironment")
        assert scene_environment is not None, "sceneEnvironment controller missing"
        assert bool(scene_environment.property("reflectionProbeEnabled")) is False

        assembly = root.property("sceneSuspensionAssembly")
        assert isinstance(assembly, QObject), "SuspensionAssembly alias missing"

        probe = assembly.property("reflectionProbe")
        assert isinstance(probe, QObject), "ReflectionProbe object unavailable"
        enabled_index = probe.metaObject().indexOfProperty("enabled")
        assert enabled_index >= 0, "ReflectionProbe.enabled property unavailable"
        assert bool(probe.property("enabled")) is False
        assert bool(probe.property("visible")) is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_reflection_probe_disabled_when_settings_false(qapp) -> None:
    overrides = {
        "initialReflectionProbeSettings": {
            "enabled": False,
            "padding_m": 0.15,
            "quality": "veryhigh",
            "refresh_mode": "everyframe",
            "time_slicing": "individualfaces",
        }
    }
    engine, component, root = _create_simulation_root(overrides)

    try:
        assembly = root.property("sceneSuspensionAssembly")
        assert isinstance(assembly, QObject), "SuspensionAssembly alias missing"
        assert not bool(assembly.property("reflectionProbeEnabled"))

        probe = assembly.property("reflectionProbe")
        assert isinstance(probe, QObject), "ReflectionProbe object unavailable"
        enabled_index = probe.metaObject().indexOfProperty("enabled")
        assert enabled_index >= 0, "ReflectionProbe.enabled property unavailable"
        assert bool(probe.property("enabled")) is False
        assert bool(probe.property("visible")) is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_reflection_probe_disabled_when_scene_settings_false(qapp) -> None:
    overrides = {
        "initialSceneSettings": {
            "graphics": {
                "reflection_probe": {
                    "enabled": False,
                },
            },
        }
    }
    engine, component, root = _create_simulation_root(overrides)

    try:
        assembly = root.property("sceneSuspensionAssembly")
        assert isinstance(assembly, QObject), "SuspensionAssembly alias missing"
        assert not bool(assembly.property("reflectionProbeEnabled"))

        probe = assembly.property("reflectionProbe")
        assert isinstance(probe, QObject), "ReflectionProbe object unavailable"
        enabled_index = probe.metaObject().indexOfProperty("enabled")
        assert enabled_index >= 0, "ReflectionProbe.enabled property unavailable"
        assert bool(probe.property("enabled")) is False
        assert bool(probe.property("visible")) is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_reflection_probe_disabled_when_environment_settings_false(qapp) -> None:
    overrides = {
        "initialSceneSettings": {
            "graphics": {"environment": {"reflection_enabled": False}},
        },
    }
    engine, component, root = _create_simulation_root(overrides)

    try:
        assert bool(root.property("reflectionProbeEnabled")) is False
        assembly = root.property("sceneSuspensionAssembly")
        assert isinstance(assembly, QObject), "SuspensionAssembly alias missing"
        assert not bool(assembly.property("reflectionProbeEnabled"))

        probe = assembly.property("reflectionProbe")
        assert isinstance(probe, QObject), "ReflectionProbe object unavailable"
        enabled_index = probe.metaObject().indexOfProperty("enabled")
        assert enabled_index >= 0, "ReflectionProbe.enabled property unavailable"
        assert bool(probe.property("enabled")) is False
        assert bool(probe.property("visible")) is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_reflection_probe_defaults_missing_keys_emits_warning(qapp) -> None:
    overrides = {"initialReflectionProbeSettings": {"enabled": True}}
    engine, component, root = _create_simulation_root(overrides)

    try:
        assert bool(root.property("reflectionProbeDefaultsWarningIssued"))
        missing = root.property("reflectionProbeMissingKeys")
        assert isinstance(missing, list)
        assert set(missing) >= {"padding_m", "quality", "refresh_mode", "time_slicing"}

        assembly = root.property("sceneSuspensionAssembly")
        assert isinstance(assembly, QObject), "SuspensionAssembly alias missing"
        assert math.isclose(
            float(assembly.property("reflectionProbePaddingM")),
            0.15,
            rel_tol=1e-6,
            abs_tol=1e-6,
        )
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_environment_defaults_disable_reflection_probe_visibility(qapp) -> None:
    overrides = {
        "initialSceneSettings": {
            "graphics": {
                "environment": {
                    "reflection_enabled": False,
                    "reflection_padding_m": 0.2,
                }
            }
        }
    }
    engine, component, root = _create_simulation_root(overrides)

    try:
        assembly = root.property("sceneSuspensionAssembly")
        assert isinstance(assembly, QObject), "SuspensionAssembly alias missing"
        assert bool(assembly.property("reflectionProbeEnabled")) is False

        probe = assembly.property("reflectionProbe")
        assert isinstance(probe, QObject), "ReflectionProbe object unavailable"
        enabled_index = probe.metaObject().indexOfProperty("enabled")
        assert enabled_index >= 0, "ReflectionProbe.enabled property unavailable"
        assert bool(probe.property("enabled")) is False
        assert bool(probe.property("visible")) is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_reflection_probe_missing_keys_propagated_from_python(qapp) -> None:
    overrides = {
        "initialReflectionProbeSettings": {
            "enabled": True,
            "padding_m": 0.25,
            "quality": "veryhigh",
            "refresh_mode": "everyframe",
            "time_slicing": "individualfaces",
        },
        "initialReflectionProbeMissingKeys": ["quality", "time_slicing"],
    }
    engine, component, root = _create_simulation_root(overrides)

    try:
        assert bool(root.property("reflectionProbeDefaultsWarningIssued"))
        missing = root.property("reflectionProbeMissingKeys")
        assert isinstance(missing, list)
        assert set(missing) >= {"quality", "time_slicing"}
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
