import os
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtQuick3D",
    reason="PySide6 QtQuick3D module is required for FlowNetwork tests",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtQml",
    reason="PySide6 QtQml module is required for FlowNetwork tests",
    exc_type=ImportError,
)

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")

_QML_ROOT = Path("assets/qml").resolve()


def _create_flow_network():
    engine = QQmlEngine()
    engine.addImportPath(str(_QML_ROOT))

    component = QQmlComponent(engine)
    flow_path = _QML_ROOT / "PneumoStabSim" / "scene" / "FlowNetwork.qml"
    component.loadUrl(QUrl.fromLocalFile(str(flow_path)))

    if component.isError():  # pragma: no cover - diagnostic guard
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load FlowNetwork.qml: {messages}")

    root = component.create()
    assert root is not None
    return engine, component, root


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_flow_network_exposes_scaled_flow_properties(qapp) -> None:
    engine, component, root = _create_flow_network()

    try:
        assert root.property("visible") is False

        payload = {
            "maxLineIntensity": 0.12,
            "maxReliefIntensity": 0.2,
            "lines": {
                "a1": {"flows": {"net": 0.08}},
                "b1": {"flows": {"fromAtmosphere": 0.02, "toTank": 0.05}},
            },
            "relief": {
                "min": {"flow": 0.05},
                "stiff": {"intensity": 0.18, "open": True},
            },
        }

        root.setProperty("flowData", payload)
        qapp.processEvents()

        assert root.property("visible") is True
        assert pytest.approx(root.property("lineFlowCeiling"), rel=1e-6) == 0.12
        assert pytest.approx(root.property("reliefFlowCeiling"), rel=1e-6) == 0.2
        assert root._lineDirection("b1") == "exhaust"
        assert 0 < root._lineSpeedHint("a1") <= 1.0

        arrow_a1 = root.findChild(QObject, "arrowA1")
        assert arrow_a1 is not None
        assert arrow_a1.property("visible") is True
        assert pytest.approx(
            arrow_a1.property("animationSpeedFactor"), rel=1e-6
        ) == pytest.approx(root._lineSpeedHint("a1"), rel=1e-6)
        assert arrow_a1.property("pulseCount") > 0

        relief_min = root.findChild(QObject, "reliefMin")
        assert relief_min is not None
        assert relief_min.property("active") is True
        assert pytest.approx(relief_min.property("intensity"), rel=1e-6) == 0.25

        root.setProperty("flowData", {})
        qapp.processEvents()
        assert root.property("visible") is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
