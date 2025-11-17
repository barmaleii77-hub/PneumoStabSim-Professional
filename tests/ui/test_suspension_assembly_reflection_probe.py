from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtQml",
    reason="PySide6 QtQml module is required for SuspensionAssembly tests",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtQuick3D",
    reason="PySide6 QtQuick3D module is required for SuspensionAssembly tests",
    exc_type=ImportError,
)

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

SUSPENSION_PATH = Path("assets/qml/scene/SuspensionAssembly.qml").resolve()
SHARED_MATERIALS_PATH = Path("assets/qml/scene/SharedMaterials.qml").resolve()


def _create_shared_materials(engine: QQmlEngine) -> tuple[QQmlComponent, QObject]:
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(SHARED_MATERIALS_PATH)))
    assert component.isReady(), str(component.errors())

    shared_materials = component.create()
    assert shared_materials is not None, "SharedMaterials failed to instantiate"

    return component, shared_materials


def _create_world_root(engine: QQmlEngine) -> tuple[QQmlComponent, QObject]:
    component = QQmlComponent(engine)
    component.setData(
        b"import QtQuick3D 6.10; Node { objectName: 'testWorldRoot' }", QUrl()
    )
    assert component.isReady(), str(component.errors())

    world_root = component.create()
    assert world_root is not None, "World root Node failed to instantiate"

    return component, world_root


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_reflection_probe_visibility_tracks_enabled_flag(qapp) -> None:
    engine = QQmlEngine()
    engine.addImportPath(str(Path("assets/qml").resolve()))

    shared_component, shared_materials = _create_shared_materials(engine)
    world_component, world_root = _create_world_root(engine)

    assembly_component = QQmlComponent(engine, QUrl.fromLocalFile(str(SUSPENSION_PATH)))
    assert assembly_component.isReady(), str(assembly_component.errors())

    assembly = assembly_component.createWithInitialProperties(
        {
            "worldRoot": world_root,
            "geometryState": {},
            "sharedMaterials": shared_materials,
            "materialsDefaults": {},
            "geometryDefaults": {},
            "emptyGeometryDefaults": {},
            "reflectionProbeEnabled": False,
        }
    )
    assert assembly is not None, "SuspensionAssembly failed to instantiate"

    try:
        probe = assembly.findChild(QObject, "mainReflectionProbe")
        assert isinstance(probe, QObject), "ReflectionProbe object missing"

        assert bool(probe.property("enabled")) is False
        assert bool(probe.property("visible")) is False

        assembly.setProperty("reflectionProbeEnabled", True)
        qapp.processEvents()

        assert bool(probe.property("enabled")) is True
        assert bool(probe.property("visible")) is True
    finally:
        world_root.deleteLater()
        assembly.deleteLater()
        shared_materials.deleteLater()
        shared_component.deleteLater()
        world_component.deleteLater()
        assembly_component.deleteLater()
        engine.deleteLater()
