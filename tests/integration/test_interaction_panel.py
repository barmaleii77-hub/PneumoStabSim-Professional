from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QCoreApplication, QMetaObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIMULATION_PANEL = PROJECT_ROOT / "qml" / "SimulationPanel.qml"


def _load_simulation_panel():
    engine = QQmlEngine()
    engine.addImportPath(str(SIMULATION_PANEL.parent))
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(SIMULATION_PANEL)))
    panel = component.create()
    if component.isError():
        errors = "; ".join(str(error) for error in component.errors())
        pytest.fail(f"Failed to load SimulationPanel.qml: {errors}")
    QCoreApplication.processEvents()
    return panel, component, engine


def _to_variant(value):
    if hasattr(value, "toVariant"):
        return value.toVariant()
    return value


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_interaction_panel_flow_models_normalize_payload():
    panel, component, engine = _load_simulation_panel()

    payload = {
        "lines": {
            "a1": {
                "direction": "intake",
                "netFlow": 0.06,
                "valves": {"atmosphereOpen": True, "tankOpen": False},
                "flows": {"fromAtmosphere": 0.06, "toTank": 0.0},
            },
            "b1": {
                "direction": "exhaust",
                "netFlow": -0.02,
                "valves": {"atmosphereOpen": False, "tankOpen": True},
                "flows": {"fromAtmosphere": 0.0, "toTank": -0.02},
            },
        },
        "maxLineIntensity": 0.08,
        "receiver": {
            "pressures": {"a1": 120_000.0, "b1": 118_500.0},
            "tankPressure": 130_000.0,
            "minPressure": 90_000.0,
            "maxPressure": 150_000.0,
            "thresholds": [
                {"value": 100_000.0, "label": "Low", "color": "#30c9ff"},
                {"value": 140_000.0, "label": "High", "color": "#ff944d"},
            ],
        },
        "masterIsolationOpen": True,
    }

    QMetaObject.invokeMethod(
        panel, "_rebuildFlowModels", Qt.DirectConnection, Q_ARG("QVariant", payload)
    )
    QCoreApplication.processEvents()

    pressure_map = _to_variant(panel.property("linePressureMap")) or {}
    assert pressure_map["A1"] == pytest.approx(120_000.0)
    assert pressure_map["B1"] == pytest.approx(118_500.0)

    intensity_map = _to_variant(panel.property("lineIntensityMap"))
    assert intensity_map["A1"] == pytest.approx(0.75, rel=1e-6)
    assert intensity_map["B1"] == pytest.approx(0.25, rel=1e-6)

    gradient = _to_variant(panel.property("pressureGradientStops")) or []
    assert len(gradient) == 2
    assert panel.property("_hasTelemetryGradient") is True

    flow_state = _to_variant(panel.property("_flowState")) or {}
    assert flow_state.get("masterIsolationOpen") is True

    valve_map = _to_variant(panel.property("lineValveStateMap")) or {}
    assert valve_map["A1"]["atmosphereOpen"] is True
    assert valve_map["B1"]["tankOpen"] is True

    panel.deleteLater()
    component.deleteLater()
    engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_interaction_panel_recovers_from_invalid_ranges():
    panel, component, engine = _load_simulation_panel()

    for prop in (
        "minPressure",
        "maxPressure",
        "userMinPressure",
        "userMaxPressure",
        "atmosphericPressure",
        "reservoirPressure",
        "pressure",
    ):
        panel.setProperty(prop, 100_000.0)
    QCoreApplication.processEvents()
    assert panel.property("hasValidRange") is False

    telemetry = {
        "receiver": {
            "tankPressure": 145_000.0,
            "minPressure": 100_000.0,
            "maxPressure": 155_000.0,
        }
    }

    QMetaObject.invokeMethod(
        panel, "applyFlowTelemetry", Qt.DirectConnection, Q_ARG("QVariant", telemetry)
    )
    QMetaObject.invokeMethod(
        panel, "_rebuildFlowModels", Qt.DirectConnection, Q_ARG("QVariant", telemetry)
    )
    QCoreApplication.processEvents()

    assert panel.property("hasValidRange") is True
    assert panel.property("pressure") == pytest.approx(145_000.0)
    assert panel.property("effectiveMinimum") == pytest.approx(100_000.0)
    assert panel.property("effectiveMaximum") == pytest.approx(155_000.0)

    panel.deleteLater()
    component.deleteLater()
    engine.deleteLater()
