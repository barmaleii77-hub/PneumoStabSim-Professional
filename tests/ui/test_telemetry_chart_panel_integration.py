import os
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip(
    "PySide6.QtCharts",
    reason="PySide6 QtCharts module is required for telemetry panel tests",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtQml",
    reason="PySide6 QtQml module is required for telemetry panel tests",
    exc_type=ImportError,
)

from PySide6.QtCore import Property, QUrl, Signal, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtCore import QObject

os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")

_QML_ROOT = Path("assets/qml").resolve()


class _TelemetryBridgeStub(QObject):
    metricsChanged = Signal()
    activeMetricsChanged = Signal()
    pausedChanged = Signal()
    updateIntervalChanged = Signal()
    sampleAppended = Signal(object)
    streamReset = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._metric_catalog = [
            {
                "id": "pressure",
                "label": "Pressure",
                "unit": "bar",
                "category": "hydraulics",
                "color": "#4ec0ff",
            },
            {
                "id": "flow",
                "label": "Flow",
                "unit": "l/s",
                "category": "hydraulics",
                "color": "#f7b801",
                "rangeHint": [-0.5, 0.5],
            },
        ]
        self._active_metrics = ["pressure"]
        self._paused = False
        self._update_interval = 2
        self._max_samples = 16
        self.set_active_calls: list[list[str]] = []
        self.set_paused_calls: list[bool] = []
        self.update_interval_calls: list[int] = []
        self.reset_count = 0
        self.export_requests: list[list[str]] = []

    @Property("QVariantList", constant=True)
    def metricCatalog(self) -> list[dict[str, Any]]:  # noqa: N802 - Qt property name
        return list(self._metric_catalog)

    @Property("QVariantList", notify=activeMetricsChanged)
    def activeMetrics(self) -> list[str]:  # noqa: N802 - Qt property name
        return list(self._active_metrics)

    @Property(bool, notify=pausedChanged)
    def paused(self) -> bool:  # noqa: N802 - Qt property name
        return self._paused

    @Property(int, notify=updateIntervalChanged)
    def updateInterval(self) -> int:  # noqa: N802 - Qt property name
        return self._update_interval

    @Property(int, constant=True)
    def maxSamples(self) -> int:  # noqa: N802 - Qt property name
        return self._max_samples

    @Slot(bool)
    def setPaused(self, paused: bool) -> None:  # noqa: N802 - Qt slot name
        self._paused = bool(paused)
        self.set_paused_calls.append(self._paused)
        self.pausedChanged.emit()

    @Slot(int)
    def setUpdateInterval(self, interval: int) -> None:  # noqa: N802
        self._update_interval = int(interval)
        self.update_interval_calls.append(self._update_interval)
        self.updateIntervalChanged.emit()

    @Slot()
    def resetStream(self) -> None:  # noqa: N802 - Qt slot name
        self.reset_count += 1
        self.streamReset.emit()

    @Slot("QVariantList")
    def setActiveMetrics(self, metrics: list[Any]) -> None:  # noqa: N802
        self._active_metrics = [str(metric) for metric in metrics]
        self.set_active_calls.append(list(self._active_metrics))
        self.activeMetricsChanged.emit()

    @Slot("QVariantList", result="QVariantMap")
    def exportSeries(self, metrics: list[Any]) -> dict[str, Any]:  # noqa: N802
        ids = [str(metric) for metric in metrics]
        self.export_requests.append(ids)
        series: dict[str, list[dict[str, float]]] = {}
        for index, metric_id in enumerate(ids):
            series[metric_id] = [{"timestamp": float(index), "value": float(index + 1)}]
        latest = float(len(ids)) if ids else 0.0
        return {
            "series": series,
            "oldestTimestamp": 0.0,
            "latestTimestamp": latest,
        }


def _create_telemetry_panel():
    engine = QQmlEngine()
    engine.addImportPath(str(_QML_ROOT))

    component = QQmlComponent(engine)
    panel_path = _QML_ROOT / "components" / "TelemetryChartPanel.qml"
    component.loadUrl(QUrl.fromLocalFile(str(panel_path)))

    if component.isError():  # pragma: no cover - diagnostic guard
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load TelemetryChartPanel.qml: {messages}")

    root = component.create()
    assert root is not None
    return engine, component, root


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_telemetry_chart_panel_syncs_metrics_and_samples(qapp) -> None:
    engine, component, root = _create_telemetry_panel()
    bridge = _TelemetryBridgeStub()

    try:
        root.setProperty("telemetryBridge", bridge)
        qapp.processEvents()

        bridge.metricsChanged.emit()
        bridge.activeMetricsChanged.emit()
        qapp.processEvents()

        assert root.property("visible") is True
        info_by_id = root.property("metricInfoById")
        assert "pressure" in info_by_id
        assert root.property("selectedMetrics") == ["pressure"]

        buffers = root.property("seriesBuffers")
        assert "pressure" in buffers
        assert buffers["pressure"], "expected exportSeries to seed buffers"

        root.addMetric("flow")
        qapp.processEvents()
        assert bridge.set_active_calls[-1] == ["pressure", "flow"]
        assert root.property("selectedMetrics")[-1] == "flow"

        bridge.sampleAppended.emit(
            {"timestamp": 5.0, "values": {"pressure": 0.7, "flow": 0.2}}
        )
        qapp.processEvents()

        buffers = root.property("seriesBuffers")
        assert pytest.approx(buffers["pressure"][-1][1], rel=1e-6) == 0.7
        assert pytest.approx(buffers["flow"][-1][1], rel=1e-6) == 0.2

        bridge.streamReset.emit()
        qapp.processEvents()
        buffers = root.property("seriesBuffers")
        assert all(not series for series in buffers.values())
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
