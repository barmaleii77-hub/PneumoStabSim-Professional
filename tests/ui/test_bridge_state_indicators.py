"""Tests for the BridgeIndicatorsPanel embedded in SimulationRoot.qml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import pytest

pytest.importorskip(
    "PySide6.QtQuick3D",
    reason="PySide6 QtQuick3D module is required to instantiate SimulationRoot",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtQml",
    reason="PySide6 QtQml module is required for SimulationRoot tests",
    exc_type=ImportError,
)

from PySide6.QtCore import QObject, Property, Signal, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine


os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")


def _create_simulation_root() -> tuple[QQmlEngine, QQmlComponent, QObject]:
    engine = QQmlEngine()
    qml_root = Path("assets/qml").resolve()
    engine.addImportPath(str(qml_root))

    component = QQmlComponent(engine)
    root_path = qml_root / "PneumoStabSim" / "SimulationRoot.qml"
    component.loadUrl(QUrl.fromLocalFile(str(root_path)))

    if component.isError():  # pragma: no cover - defensive guard
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load SimulationRoot.qml: {messages}")

    root = component.create()
    assert root is not None, "SimulationRoot should instantiate successfully"
    return engine, component, root


class _DummyBridge(QObject):
    """Minimal SceneBridge stand-in exposing geometry/simulation payloads."""

    updatesDispatched = Signal("QVariantMap")
    geometryChanged = Signal("QVariantMap")
    simulationChanged = Signal("QVariantMap")

    def __init__(self) -> None:
        super().__init__()
        self._geometry: Dict[str, Any] = {}
        self._simulation: Dict[str, Any] = {}

    @Property("QVariantMap")
    def geometry(self) -> Dict[str, Any]:  # pragma: no cover - accessed from QML
        return dict(self._geometry)

    @Property("QVariantMap")
    def simulation(self) -> Dict[str, Any]:  # pragma: no cover - accessed from QML
        return dict(self._simulation)

    def prime_state(
        self,
        geometry: Dict[str, Any],
        simulation: Dict[str, Any],
    ) -> None:
        self._geometry = dict(geometry)
        self._simulation = dict(simulation)

    def push_updates(
        self,
        *,
        geometry: Dict[str, Any] | None = None,
        simulation: Dict[str, Any] | None = None,
    ) -> None:
        updates: Dict[str, Dict[str, Any]] = {}
        if geometry is not None:
            self._geometry = dict(geometry)
            self.geometryChanged.emit(dict(geometry))
            updates["geometry"] = dict(geometry)
        if simulation is not None:
            self._simulation = dict(simulation)
            self.simulationChanged.emit(dict(simulation))
            updates["simulation"] = dict(simulation)
        if updates:
            self.updatesDispatched.emit(updates)


def _example_geometry_state() -> Dict[str, Any]:
    return {
        "controlArms": {"frontLeft": 1.0},
        "knuckles": {"frontRight": 1.0},
        "linkages": {"rearLeft": 1.0},
    }


def _example_simulation_state() -> Dict[str, Any]:
    return {
        "levers": {"front_left": 1.2, "front_right": -0.8},
        "pistons": {"front_left": 0.05, "front_right": 0.04},
        "aggregates": {
            "stepNumber": 5,
            "simulationTime": 0.125,
            "physicsStepTime": 0.002,
            "integrationSteps": 3,
            "integrationFailures": 0,
            "kineticEnergy": 12.0,
            "potentialEnergy": 4.0,
            "pneumaticEnergy": 1.5,
            "totalFlowIn": 0.2,
            "totalFlowOut": 0.1,
            "netFlow": 0.1,
        },
        "frame": {"heave": 0.0},
        "tank": {"pressure": 0.0},
    }


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_bridge_indicators_reflect_scene_bridge_snapshot(qapp) -> None:
    engine, component, root = _create_simulation_root()
    bridge = _DummyBridge()
    bridge.prime_state(_example_geometry_state(), _example_simulation_state())

    try:
        root.setProperty("sceneBridge", bridge)
        qapp.processEvents()

        geometry_indicator = root.property("geometryIndicatorItem")
        simulation_indicator = root.property("simulationIndicatorItem")

        assert geometry_indicator.property("active") is True
        assert geometry_indicator.property("warning") is False
        assert geometry_indicator.property("detailText") == "3 параметров"

        assert simulation_indicator.property("active") is True
        assert simulation_indicator.property("warning") is False
        assert (
            simulation_indicator.property("detailText")
            == "Рычаги: 2 • Поршни: 2"
        )
        assert (
            simulation_indicator.property("secondaryText")
            == "Шаг 5 • Время 0.125 с"
        )

        bridge.push_updates(simulation=_example_simulation_state())
        qapp.processEvents()

        assert root.property("sceneBridgeDispatchCount") == 1
        assert geometry_indicator.property("pulse") is True
        assert simulation_indicator.property("pulse") is True
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_bridge_indicators_show_warning_when_bridge_missing(qapp) -> None:
    engine, component, root = _create_simulation_root()
    bridge = _DummyBridge()
    bridge.prime_state(_example_geometry_state(), _example_simulation_state())

    try:
        root.setProperty("sceneBridge", bridge)
        qapp.processEvents()

        root.setProperty("sceneBridge", None)
        qapp.processEvents()

        geometry_indicator = root.property("geometryIndicatorItem")
        simulation_indicator = root.property("simulationIndicatorItem")

        assert geometry_indicator.property("active") is False
        assert geometry_indicator.property("warning") is True
        assert (
            geometry_indicator.property("detailText")
            == "Ожидание данных от SceneBridge"
        )
        assert geometry_indicator.property("secondaryText") == "Bridge недоступен"

        assert simulation_indicator.property("active") is False
        assert simulation_indicator.property("warning") is True
        assert simulation_indicator.property("detailText") == "Нет активного снапшота"
        assert simulation_indicator.property("secondaryText") == "Bridge недоступен"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
