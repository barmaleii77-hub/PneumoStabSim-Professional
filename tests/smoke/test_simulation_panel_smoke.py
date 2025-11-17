import pytest
from pathlib import Path

import pytest

from tests.helpers.qt import require_qt_modules

require_qt_modules("PySide6.QtQml", "PySide6.QtQuick")

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent, QQmlEngine

_QML_ROOT = Path("qml").resolve()


def _load_root():
    engine = QQmlEngine()
    engine.addImportPath(str(_QML_ROOT))

    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(_QML_ROOT / "SimulationRoot.qml")))
    if component.isError():
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load SimulationRoot.qml: {messages}")

    root = component.create()
    assert root is not None

    panel = root.findChild(QObject, "simulationPanel")
    assert panel is not None

    return engine, component, root, panel


@pytest.mark.gui
@pytest.mark.smoke
@pytest.mark.usefixtures("qapp")
def test_simulation_panel_accepts_simulation_snapshot(qapp) -> None:
    engine, component, root, panel = _load_root()

    try:
        telemetry = {
            "atmosphericPressure": 95_000.0,
            "gradientStops": [
                {"value": 90_000.0, "label": "low", "color": "#3a6fbf"},
                {"value": 110_000.0, "label": "target", "color": "#f2c94c"},
                {"value": 130_000.0, "label": "high", "color": "#d96b3b"},
            ],
            "pressureMarkers": [
                {"value": 90_000.0, "label": "min"},
                {"value": 110_000.0, "label": "tank"},
            ],
            "masterIsolationOpen": True,
            "lines": {
                "a1": {
                    "direction": "intake",
                    "netFlow": 0.35,
                    "flowIntensity": 0.5,
                    "animationSpeed": 0.8,
                    "valves": {"atmosphereOpen": True, "tankOpen": False},
                },
                "b1": {
                    "direction": "exhaust",
                    "netFlow": -0.15,
                    "valves": {"atmosphereOpen": False, "tankOpen": True},
                },
            },
            "linePressures": {"a1": 115_000.0, "b1": 98_000.0},
            "receiver": {
                "pressures": {"a1": 115_000.0, "b1": 98_000.0},
                "tankPressure": 108_000.0,
                "minPressure": 85_000.0,
                "maxPressure": 135_000.0,
            },
        }

        assert panel.setProperty("flowTelemetry", telemetry) is True
        qapp.processEvents()

        scale = root.findChild(QObject, "pressureScale")
        assert scale is not None
        assert scale.property("atmosphericPressure") == pytest.approx(95_000.0)
        gradient_value = scale.property("gradientStops")
        gradient = gradient_value.toVariant() if hasattr(gradient_value, "toVariant") else gradient_value
        assert gradient[0]["label"] == "low"
        assert gradient[-1]["label"] == "high"

        markers_value = scale.property("markers")
        markers = markers_value.toVariant() if hasattr(markers_value, "toVariant") else markers_value
        assert markers[0]["label"] == "min"
        tank_marker = markers[1]
        assert tank_marker["label"] == "tank"
        assert tank_marker["color"].alphaF() > 0.0

        reservoir = root.findChild(QObject, "reservoirView")
        assert reservoir is not None
        assert reservoir.property("pressure") == pytest.approx(108_000.0)
        line_pressures_value = reservoir.property("linePressures")
        line_pressures = (
            line_pressures_value.toVariant()
            if hasattr(line_pressures_value, "toVariant")
            else line_pressures_value
        )
        assert line_pressures["A1"] == pytest.approx(115_000.0)

        valve_states_value = reservoir.property("lineValveStates")
        valve_states = (
            valve_states_value.toVariant()
            if hasattr(valve_states_value, "toVariant")
            else valve_states_value
        )
        assert valve_states["A1"]["atmosphereOpen"] is True
        assert valve_states["B1"]["tankOpen"] is True

        intensity_map_value = panel.property("lineIntensityMap")
        intensity_map = (
            intensity_map_value.toVariant()
            if hasattr(intensity_map_value, "toVariant")
            else intensity_map_value
        )
        assert intensity_map["A1"] >= 0.5

        fluid = reservoir.findChild(QObject, "reservoirFluid")
        assert fluid is not None
        fluid_color: QColor = fluid.property("color")
        assert isinstance(fluid_color, QColor)
        assert fluid_color.alphaF() > 0.0
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
