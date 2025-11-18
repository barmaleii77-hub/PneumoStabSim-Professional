import pytest

from PySide6.QtCore import QObject

from tests.qml.test_simulation_panel_bindings import _as_mapping, _load_simulation_panel


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_simulation_root_accepts_nested_flow_network(qapp) -> None:
    engine, component, root, panel = _load_simulation_panel()

    try:
        payload = {
            "flowNetwork": {
                "maxLineIntensity": 0.8,
                "masterIsolationOpen": True,
                "lines": {
                    "a1": {
                        "direction": "intake",
                        "netFlow": 0.12,
                        "flowIntensity": 0.4,
                        "valves": {"atmosphereOpen": True, "tankOpen": False},
                    },
                    "b2": {
                        "direction": "exhaust",
                        "netFlow": -0.06,
                        "flowIntensity": 0.2,
                        "valves": {"atmosphereOpen": False, "tankOpen": True},
                    },
                },
                "receiver": {
                    "pressures": {"a1": 118_000.0, "b2": 102_000.0},
                    "tankPressure": 110_000.0,
                    "minPressure": 90_000.0,
                    "maxPressure": 130_000.0,
                    "thresholds": [
                        {"value": 95_000.0, "label": "Low", "color": "#3a6fbf"},
                        {"value": 110_000.0, "label": "Tank", "color": "#f2c94c"},
                        {"value": 125_000.0, "label": "High", "color": "#d96b3b"},
                    ],
                },
            }
        }

        assert root.setProperty("flowTelemetry", payload) is True
        qapp.processEvents()

        flow_model = panel.property("flowArrowsModel")
        assert flow_model is not None
        assert flow_model.get(0)["label"] == "A1"
        assert flow_model.get(1)["label"] == "B2"

        assert panel.property("masterIsolationValveOpen") is True

        reservoir = panel.findChild(QObject, "reservoirView")
        assert reservoir is not None
        assert reservoir.property("pressure") == pytest.approx(110_000.0, rel=1e-6)

        line_pressures = _as_mapping(reservoir.property("linePressures"))
        assert line_pressures["A1"] == pytest.approx(118_000.0, rel=1e-6)
        assert line_pressures["B2"] == pytest.approx(102_000.0, rel=1e-6)

        arrow_a1 = root.findChild(QObject, "flowArrow-A1")
        assert arrow_a1 is not None
        assert arrow_a1.property("effectivePressureRatio") == pytest.approx(
            0.7, rel=1e-6
        )
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
