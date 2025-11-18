"""Integration test to verify geometry defaults are applied to QML scene."""

from __future__ import annotations

from pathlib import Path

import pytest

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine


QML_PATH = Path("assets/qml/main_simple.qml").resolve()


def _load_component_with_geometry_defaults(geometry_defaults: dict[str, float]):
    engine = QQmlEngine()
    engine.addImportPath(str(QML_PATH.parent))

    context = engine.rootContext()
    context.setContextProperty("initialGeometrySettings", geometry_defaults)

    component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML_PATH)))
    assert component.isReady(), str(component.errors())

    root = component.create()
    assert root is not None, "main_simple.qml failed to instantiate"
    return engine, component, root


@pytest.mark.gui
@pytest.mark.usefixtures("qt_runtime_ready")
def test_geometry_defaults_populated_from_settings(settings_manager) -> None:
    geometry_defaults = settings_manager.get_category("geometry") or {}
    engine, component, root = _load_component_with_geometry_defaults(geometry_defaults)

    try:
        assert root.property("userFrameLength") == pytest.approx(
            geometry_defaults["frame_length_m"] * 1000.0, rel=1e-6
        )
        assert root.property("userTrackWidth") == pytest.approx(
            geometry_defaults["track"] * 1000.0, rel=1e-6
        )
        assert root.property("userBeamSize") == pytest.approx(
            geometry_defaults["frame_beam_size_m"] * 1000.0, rel=1e-6
        )
        assert root.property("userFrameHeight") == pytest.approx(
            geometry_defaults["frame_height_m"] * 1000.0, rel=1e-6
        )
        assert root.property("userLeverLength") == pytest.approx(
            geometry_defaults["lever_length"] * 1000.0, rel=1e-6
        )
        assert root.property("userCylinderLength") == pytest.approx(
            geometry_defaults["cylinder_body_length_m"] * 1000.0, rel=1e-6
        )
        assert root.property("userRodPosition") == pytest.approx(
            geometry_defaults["rod_position"], rel=1e-6
        )
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        engine.collectGarbage()
