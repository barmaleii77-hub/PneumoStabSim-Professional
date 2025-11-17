import os
from pathlib import Path

import pytest

from tests.helpers.qt import require_qt_modules

# Инициализируем обязательные Qt модули; при отсутствии произойдёт pytest.fail
require_qt_modules("PySide6.QtQml", "PySide6.QtQuick")

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent, QQmlEngine

os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")

_QML_ROOT = Path("qml").resolve()


def _load_simulation_panel():
    engine = QQmlEngine()
    engine.addImportPath(str(_QML_ROOT))

    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(_QML_ROOT / "SimulationRoot.qml")))

    if component.isError():  # pragma: no cover - diagnostic guard
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load SimulationRoot.qml: {messages}")

    root = component.create()
    assert root is not None

    panel = root.findChild(QObject, "simulationPanel")
    assert panel is not None, (
        "Expected SimulationPanel with objectName 'simulationPanel'"
    )

    return engine, component, root, panel


def _color_tuple(qcolor: QColor) -> tuple[float, float, float, float]:
    return (
        pytest.approx(qcolor.redF(), rel=1e-3),
        pytest.approx(qcolor.greenF(), rel=1e-3),
        pytest.approx(qcolor.blueF(), rel=1e-3),
        pytest.approx(qcolor.alphaF(), rel=1e-3),
    )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_simulation_panel_flow_mappings(qapp) -> None:
    engine, component, root, panel = _load_simulation_panel()

    try:
        payload = {
            "maxLineIntensity": 0.4,
            "masterIsolationOpen": True,
            "lines": {
                "a1": {
                    "direction": "intake",
                    "netFlow": 0.2,
                    "flowIntensity": 0.25,
                    "animationSpeed": 0.65,
                    "valves": {"atmosphereOpen": True, "tankOpen": False},
                },
                "b1": {
                    "direction": "exhaust",
                    "netFlow": -0.1,
                    "flowIntensity": 0.15,
                    "valves": {"atmosphereOpen": False, "tankOpen": True},
                },
            },
            "receiver": {
                "pressures": {"a1": 110_000.0, "b1": 90_000.0},
                "tankPressure": 105_000.0,
                "minPressure": 85_000.0,
                "maxPressure": 125_000.0,
                "thresholds": [
                    {"value": 90_000.0, "label": "Low", "color": "#3a6fbf"},
                    {"value": 105_000.0, "label": "Tank", "color": "#f2c94c"},
                    {"value": 120_000.0, "label": "High", "color": "#d96b3b"},
                ],
            },
            "linePressures": {"a1": 110_000.0, "b1": 90_000.0},
        }

        assert panel.setProperty("flowTelemetry", payload) is True
        qapp.processEvents()

        flow_model_obj = panel.property("flowArrowsModel")
        assert flow_model_obj is not None
        if hasattr(flow_model_obj, "rowCount"):
            count = flow_model_obj.rowCount()
        else:
            count = flow_model_obj.property("count")
        assert count == 2

        first_entry = flow_model_obj.get(0)
        assert first_entry["label"] == "A1"
        assert pytest.approx(first_entry["pressure"], rel=1e-6) == 110_000.0
        assert pytest.approx(first_entry["pressureRatio"], rel=1e-6) == pytest.approx(
            0.625, rel=1e-6
        )
        assert pytest.approx(first_entry["animationSpeed"], rel=1e-6) == pytest.approx(
            0.65, rel=1e-6
        )

        reservoir = panel.findChild(QObject, "reservoirView")
        assert reservoir is not None
        line_pressures = reservoir.property("linePressures")
        assert line_pressures["A1"] == pytest.approx(110_000.0, rel=1e-6)
        assert line_pressures["B1"] == pytest.approx(90_000.0, rel=1e-6)

        line_valves = reservoir.property("lineValveStates")
        assert line_valves["A1"]["atmosphereOpen"] is True
        assert line_valves["B1"]["tankOpen"] is True

        line_intensities = reservoir.property("lineIntensities")
        assert line_intensities["A1"] == pytest.approx(0.625, rel=1e-6)

        gradient_stops = panel.property("pressureGradientStops")
        assert len(gradient_stops) >= 3
        assert gradient_stops[0]["label"] == "Low"
        assert gradient_stops[1]["label"] == "Tank"

        scale = panel.findChild(QObject, "pressureScale")
        assert scale is not None
        scale_gradient = scale.property("gradientStops")
        assert scale_gradient[0]["label"] == "Low"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_reservoir_visuals_follow_pressures(qapp) -> None:
    engine, component, root, panel = _load_simulation_panel()

    try:
        payload = {
            "maxLineIntensity": 0.4,
            "masterIsolationOpen": True,
            "lines": {
                "a1": {
                    "direction": "intake",
                    "netFlow": 0.2,
                    "valves": {"atmosphereOpen": True, "tankOpen": False},
                },
                "b1": {
                    "direction": "exhaust",
                    "netFlow": -0.1,
                    "valves": {"atmosphereOpen": False, "tankOpen": True},
                },
            },
            "receiver": {
                "pressures": {"a1": 110_000.0, "b1": 90_000.0},
                "tankPressure": 105_000.0,
                "minPressure": 85_000.0,
                "maxPressure": 125_000.0,
                "thresholds": [
                    {"value": 90_000.0, "label": "Low", "color": "#3a6fbf"},
                    {"value": 105_000.0, "label": "Tank", "color": "#f2c94c"},
                    {"value": 120_000.0, "label": "High", "color": "#d96b3b"},
                ],
            },
            "linePressures": {"a1": 110_000.0, "b1": 90_000.0},
        }

        assert panel.setProperty("flowTelemetry", payload) is True
        qapp.processEvents()

        reservoir = panel.findChild(QObject, "reservoirView")
        assert reservoir is not None
        fluid = reservoir.findChild(QObject, "reservoirFluid")
        assert fluid is not None
        fluid_color = fluid.property("color")
        assert _color_tuple(fluid_color) == _color_tuple(QColor("#f2c94c"))

        sphere_a1 = reservoir.findChild(QObject, "lineSphere-A1")
        sphere_b1 = reservoir.findChild(QObject, "lineSphere-B1")
        assert sphere_a1 is not None and sphere_b1 is not None
        assert sphere_a1.property("y") < sphere_b1.property("y")

        valve_a1 = reservoir.findChild(QObject, "valveIcon-A1")
        valve_b1 = reservoir.findChild(QObject, "valveIcon-B1")
        assert valve_a1 is not None and valve_b1 is not None
        assert valve_a1.property("color") != valve_b1.property("color")

        arrow_a1 = root.findChild(QObject, "flowArrow-A1")
        assert arrow_a1 is not None
        assert arrow_a1.property("effectivePressureRatio") == pytest.approx(
            0.625, rel=1e-6
        )
        assert arrow_a1.property("minPressure") == pytest.approx(85_000.0, rel=1e-6)
        assert arrow_a1.property("maxPressure") == pytest.approx(125_000.0, rel=1e-6)
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
