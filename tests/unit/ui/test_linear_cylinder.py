from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtQuick3D",
    reason="PySide6 QtQuick3D module is required for LinearCylinder tests",
    exc_type=ImportError,
)

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QVector3D
from PySide6.QtQml import QQmlComponent, QQmlEngine

from src.ui.custom_geometry import ProceduralCylinderGeometry
from src.ui.qml_registration import register_qml_types


def test_linear_cylinder_uses_procedural_geometry(qtbot) -> None:
    register_qml_types()

    engine = QQmlEngine()
    qml_path = Path("assets/qml/geometry/LinearCylinder.qml").resolve()
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml_path)))

    if component.isError():
        raise RuntimeError(component.errorString())

    start = QVector3D(0.0, 0.0, 0.0)
    end = QVector3D(0.0, 2.0, 0.0)

    instance = component.createWithInitialProperties(
        {
            "startPoint": start,
            "endPoint": end,
            "segments": 12,
            "rings": 1,
        }
    )
    assert instance is not None

    qtbot.wait(0)

    cylinder_model = instance.findChild(QObject, "cylinderModel")
    assert cylinder_model is not None

    geometry = cylinder_model.property("geometry")
    assert isinstance(geometry, ProceduralCylinderGeometry)

    base_vertex_count = geometry.vertex_count
    instance.setProperty("segments", 20)
    qtbot.wait(0)

    assert geometry.vertex_count > base_vertex_count

    base_index_count = geometry.index_count
    instance.setProperty("rings", 4)
    qtbot.wait(0)

    assert geometry.index_count > base_index_count

    instance.deleteLater()
