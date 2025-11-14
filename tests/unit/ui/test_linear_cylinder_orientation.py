from __future__ import annotations

import math
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtQuick3D",
    reason="PySide6 QtQuick3D module is required for LinearCylinder orientation tests",
    exc_type=ImportError,
)

from PySide6.QtCore import QUrl
from PySide6.QtGui import QVector3D
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtGui import QQuaternion

from src.ui.qml_registration import register_qml_types


def _load_instance(start: QVector3D, end: QVector3D):
    register_qml_types()
    engine = QQmlEngine()
    qml_path = Path("assets/qml/geometry/LinearCylinder.qml").resolve()
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml_path)))
    if component.isError():  # pragma: no cover - diagnostic
        raise RuntimeError(component.errorString())
    instance = component.createWithInitialProperties(
        {
            "startPoint": start,
            "endPoint": end,
            "segments": 8,
            "rings": 1,
        }
    )
    assert instance is not None
    return engine, component, instance


def _rotation_matches(instance, expected_dir: QVector3D) -> bool:
    cylinder_model = instance.findChild(type(instance), "cylinderModel")
    assert cylinder_model is not None
    quat: QQuaternion = cylinder_model.property("rotation")
    # Rotate local +Y (0,1,0) and compare направление
    local_y = QVector3D(0.0, 1.0, 0.0)
    rotated = quat.rotatedVector(local_y)

    # Нормализуем оба
    def _norm(v: QVector3D) -> QVector3D:
        length = math.sqrt(v.x() * v.x() + v.y() * v.y() + v.z() * v.z())
        if length < 1e-9:
            return QVector3D(0.0, 0.0, 0.0)
        return QVector3D(v.x() / length, v.y() / length, v.z() / length)

    rd = _norm(rotated)
    ed = _norm(expected_dir)
    return (
        math.isclose(rd.x(), ed.x(), abs_tol=1e-4)
        and math.isclose(rd.y(), ed.y(), abs_tol=1e-4)
        and math.isclose(rd.z(), ed.z(), abs_tol=1e-4)
    )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
@pytest.mark.parametrize(
    "start,end,expected",
    [
        (
            QVector3D(0, 0, 0),
            QVector3D(0, 2, 0),
            QVector3D(0, 1, 0),
        ),  # along +Y (identity)
        (QVector3D(0, 0, 0), QVector3D(2, 0, 0), QVector3D(1, 0, 0)),  # along +X
        (QVector3D(0, 0, 0), QVector3D(-2, 0, 0), QVector3D(-1, 0, 0)),  # along -X
        (QVector3D(0, 0, 0), QVector3D(0, 0, 2), QVector3D(0, 0, 1)),  # along +Z
        (QVector3D(0, 0, 0), QVector3D(0, 0, -2), QVector3D(0, 0, -1)),  # along -Z
        (QVector3D(0, 0, 0), QVector3D(1, 1, 1), QVector3D(1, 1, 1)),  # diagonal
    ],
)
def test_linear_cylinder_orientation(start, end, expected, qtbot) -> None:
    engine, component, instance = _load_instance(start, end)
    try:
        qtbot.wait(0)
        assert _rotation_matches(instance, expected), (
            f"Quaternion rotation does not align local +Y with expected direction: {expected}"
        )
    finally:
        instance.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_linear_cylinder_zero_length_identity(qtbot) -> None:
    start = QVector3D(1.0, 1.0, 1.0)
    end = QVector3D(1.0, 1.0, 1.0)  # zero length
    engine, component, instance = _load_instance(start, end)
    try:
        qtbot.wait(0)
        cylinder_model = instance.findChild(type(instance), "cylinderModel")
        assert cylinder_model is not None
        quat: QQuaternion = cylinder_model.property("rotation")
        # Identity quaternion rotates +Y to +Y
        rotated = quat.rotatedVector(QVector3D(0, 1, 0))
        assert math.isclose(rotated.x(), 0.0, abs_tol=1e-5)
        assert math.isclose(rotated.y(), 1.0, abs_tol=1e-5)
        assert math.isclose(rotated.z(), 0.0, abs_tol=1e-5)
    finally:
        instance.deleteLater()
        component.deleteLater()
        engine.deleteLater()
