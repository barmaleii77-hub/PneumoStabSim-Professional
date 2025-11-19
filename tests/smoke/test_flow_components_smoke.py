import pytest
from PySide6.QtGui import QColor

from PySide6.QtCore import QObject

from tests.qml.test_simulation_panel_bindings import (
    _as_mapping,
    _color_tuple,
    _load_simulation_panel,
)


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_full_flow_network_visuals(qapp) -> None:
    engine, component, root, panel = _load_simulation_panel()

    try:
        payload = {
            "flowNetwork": {
                "maxLineIntensity": 1.0,
                "masterIsolationOpen": True,
                "lines": {
                    "a1": {
                        "direction": "intake",
                        "netFlow": 0.32,
                        "flowIntensity": 0.8,
                        "animationSpeed": 0.75,
                        "valves": {"atmosphereOpen": False, "tankOpen": True},
                    },
                    "a2": {
                        "direction": "intake",
                        "netFlow": 0.08,
                        "flowIntensity": 0.25,
                        "animationSpeed": 0.35,
                        "valves": {"atmosphereOpen": True, "tankOpen": False},
                    },
                    "b1": {
                        "direction": "exhaust",
                        "netFlow": -0.12,
                        "flowIntensity": 0.5,
                        "animationSpeed": 0.55,
                        "valves": {"atmosphereOpen": False, "tankOpen": True},
                    },
                    "b2": {
                        "direction": "exhaust",
                        "netFlow": -0.04,
                        "flowIntensity": 0.1,
                        "animationSpeed": 0.2,
                        "valves": {"atmosphereOpen": False, "tankOpen": False},
                    },
                },
                "receiver": {
                    "pressures": {
                        "a1": 130_000.0,
                        "a2": 100_000.0,
                        "b1": 118_000.0,
                        "b2": 95_000.0,
                    },
                    "tankPressure": 115_000.0,
                    "minPressure": 90_000.0,
                    "maxPressure": 140_000.0,
                    "thresholds": [
                        {"value": 90_000.0, "label": "Min", "color": "#2c7be5"},
                        {"value": 115_000.0, "label": "Tank", "color": "#55d37a"},
                        {"value": 140_000.0, "label": "High", "color": "#e05752"},
                    ],
                },
            }
        }

        assert panel.setProperty("flowTelemetry", payload) is True
        qapp.processEvents()

        flow_model = panel.property("flowArrowsModel")
        assert flow_model is not None
        assert flow_model.rowCount() == 4

        def _unwrap(val):
            try:
                if hasattr(val, "toVariant"):
                    return val.toVariant()
            except Exception:
                pass
            return val

        def _row(model, idx: int):
            entry = model.get(idx)
            keys = [
                "label",
                "pressureRatio",
                "pressure",
                "animationSpeed",
                "flow",
                "intensity",
                "direction",
            ]
            out = {}
            for k in keys:
                try:
                    out[k] = _unwrap(entry.property(k))
                except Exception:
                    pass
            return out

        arrow_a1 = _row(flow_model, 0)
        arrow_b2 = _row(flow_model, 3)
        assert arrow_a1["label"] == "A1" and arrow_b2["label"] == "B2"
        assert arrow_a1["pressureRatio"] > 0.7
        assert arrow_b2["pressureRatio"] < 0.2

        reservoir = panel.findChild(QObject, "reservoirView")
        assert reservoir is not None
        fluid = reservoir.findChild(QObject, "reservoirFluid")
        assert fluid is not None
        fluid_color = fluid.property("color")
        panel_stops = _as_mapping(panel.property("pressureGradientStops"))
        assert isinstance(panel_stops, list) and len(panel_stops) >= 2
        stop_color_raw = panel_stops[1]["color"]
        stop_color = (
            QColor(stop_color_raw)
            if isinstance(stop_color_raw, str)
            else stop_color_raw
        )
        assert _color_tuple(fluid_color) == _color_tuple(stop_color)

        sphere_a1 = reservoir.findChild(QObject, "lineSphere-A1")
        sphere_b2 = reservoir.findChild(QObject, "lineSphere-B2")
        assert sphere_a1 is not None and sphere_b2 is not None
        assert sphere_a1.property("y") < sphere_b2.property("y")

        valve_a1 = reservoir.findChild(QObject, "valveIcon-A1")
        valve_b2 = reservoir.findChild(QObject, "valveIcon-B2")
        assert valve_a1 is not None and valve_b2 is not None
        open_color = reservoir.property("valveOpenColor")
        closed_color = reservoir.property("valveClosedColor")
        assert _color_tuple(valve_a1.property("color")) == _color_tuple(open_color)
        assert _color_tuple(valve_b2.property("color")) == _color_tuple(closed_color)

        scale = panel.findChild(QObject, "pressureScale")
        assert scale is not None
        scale_gradient = _as_mapping(scale.property("gradientStops"))
        labels = [entry["label"] for entry in scale_gradient]
        assert {"Min", "Tank", "High"}.issubset(set(labels))
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
