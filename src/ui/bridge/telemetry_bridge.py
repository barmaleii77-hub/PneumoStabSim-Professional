"""Qt bridge streaming telemetry snapshots to QML charts."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, List
from collections.abc import Iterable, Mapping, Sequence

from PySide6.QtCore import QObject, Property, Signal, Slot

from src.pneumo.enums import Line
from src.runtime.state import StateSnapshot

MetricExtractor = Callable[[StateSnapshot], float]


@dataclass(frozen=True)
class MetricDescriptor:
    """Describe a telemetry metric exposed to QML."""

    id: str
    label: str
    unit: str
    category: str
    color: str
    range_hint: Sequence[float] | None = None

    def as_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "id": self.id,
            "label": self.label,
            "unit": self.unit,
            "category": self.category,
            "color": self.color,
        }
        if self.range_hint is not None:
            payload["rangeHint"] = list(self.range_hint)
        return payload


def _line_pressure(line: Line) -> MetricExtractor:
    def extractor(snapshot: StateSnapshot) -> float:
        state = snapshot.lines.get(line)
        return float(state.pressure if state is not None else 0.0)

    return extractor


def _frame_attr(name: str) -> MetricExtractor:
    def extractor(snapshot: StateSnapshot) -> float:
        return float(getattr(snapshot.frame, name, 0.0))

    return extractor


def _total_inflow(snapshot: StateSnapshot) -> float:
    return float(sum(line.flow_atmo for line in snapshot.lines.values()))


def _total_outflow(snapshot: StateSnapshot) -> float:
    return float(sum(line.flow_tank for line in snapshot.lines.values()))


def _tank_relief(snapshot: StateSnapshot) -> float:
    tank = snapshot.tank
    return float(tank.flow_min + tank.flow_stiff + tank.flow_safety)


_DEFAULT_METRICS: Sequence[MetricDescriptor] = (
    MetricDescriptor(
        id="pressure.a1",
        label="A1",
        unit="Pa",
        category="pressure",
        color="#ff6464",
        range_hint=(100_000.0, 200_000.0),
    ),
    MetricDescriptor(
        id="pressure.b1",
        label="B1",
        unit="Pa",
        category="pressure",
        color="#64ff64",
        range_hint=(100_000.0, 200_000.0),
    ),
    MetricDescriptor(
        id="pressure.a2",
        label="A2",
        unit="Pa",
        category="pressure",
        color="#6464ff",
        range_hint=(100_000.0, 200_000.0),
    ),
    MetricDescriptor(
        id="pressure.b2",
        label="B2",
        unit="Pa",
        category="pressure",
        color="#ffff64",
        range_hint=(100_000.0, 200_000.0),
    ),
    MetricDescriptor(
        id="pressure.tank",
        label="Tank",
        unit="Pa",
        category="pressure",
        color="#ff64ff",
        range_hint=(100_000.0, 200_000.0),
    ),
    MetricDescriptor(
        id="frame.heave",
        label="Heave",
        unit="m",
        category="frame",
        color="#ff8c64",
        range_hint=(-0.2, 0.2),
    ),
    MetricDescriptor(
        id="frame.roll",
        label="Roll",
        unit="rad",
        category="frame",
        color="#64ffbc",
        range_hint=(-0.2, 0.2),
    ),
    MetricDescriptor(
        id="frame.pitch",
        label="Pitch",
        unit="rad",
        category="frame",
        color="#64c8ff",
        range_hint=(-0.2, 0.2),
    ),
    MetricDescriptor(
        id="flow.inflow",
        label="Inflow",
        unit="kg/s",
        category="flow",
        color="#64ff64",
        range_hint=(-0.002, 0.002),
    ),
    MetricDescriptor(
        id="flow.outflow",
        label="Outflow",
        unit="kg/s",
        category="flow",
        color="#ff6464",
        range_hint=(-0.002, 0.002),
    ),
    MetricDescriptor(
        id="flow.tank_relief",
        label="Tank relief",
        unit="kg/s",
        category="flow",
        color="#ffff64",
        range_hint=(-0.002, 0.002),
    ),
)

_DEFAULT_EXTRACTORS: Mapping[str, MetricExtractor] = {
    "pressure.a1": _line_pressure(Line.A1),
    "pressure.b1": _line_pressure(Line.B1),
    "pressure.a2": _line_pressure(Line.A2),
    "pressure.b2": _line_pressure(Line.B2),
    "pressure.tank": lambda snapshot: float(snapshot.tank.pressure),
    "frame.heave": _frame_attr("heave"),
    "frame.roll": _frame_attr("roll"),
    "frame.pitch": _frame_attr("pitch"),
    "flow.inflow": _total_inflow,
    "flow.outflow": _total_outflow,
    "flow.tank_relief": _tank_relief,
}


class TelemetryDataBridge(QObject):
    """Expose buffered telemetry metrics to QML charts."""

    metricsChanged = Signal()
    sampleAppended = Signal("QVariantMap")
    streamReset = Signal()
    pausedChanged = Signal()
    updateIntervalChanged = Signal()
    activeMetricsChanged = Signal()

    def __init__(
        self,
        *,
        max_samples: int = 2048,
        metrics: Sequence[MetricDescriptor] | None = None,
        extractors: Mapping[str, MetricExtractor] | None = None,
    ) -> None:
        super().__init__()
        if max_samples < 10:
            raise ValueError("max_samples must be at least 10")
        self._max_samples = int(max_samples)
        self._descriptors: tuple[MetricDescriptor, ...] = tuple(
            metrics or _DEFAULT_METRICS
        )
        self._extractors: Mapping[str, MetricExtractor] = (
            extractors or _DEFAULT_EXTRACTORS
        )
        self._buffers: dict[str, deque[float]] = {
            descriptor.id: deque(maxlen=self._max_samples)
            for descriptor in self._descriptors
        }
        self._time_buffer: deque[float] = deque(maxlen=self._max_samples)
        self._active_metrics: tuple[str, ...] = tuple(
            descriptor.id for descriptor in self._descriptors[:3]
        )
        self._update_interval = 1
        self._skip_counter = 0
        self._paused = False
        self._oldest_timestamp: float | None = None
        self._latest_timestamp: float | None = None

    # ------------------------------------------------------------------ properties
    @Property("QVariantList", notify=metricsChanged)
    def metricCatalog(self) -> list[dict[str, object]]:
        return [descriptor.as_payload() for descriptor in self._descriptors]

    @Property("QStringList", notify=activeMetricsChanged)
    def activeMetrics(self) -> list[str]:
        return list(self._active_metrics)

    @Property(int, notify=updateIntervalChanged)
    def updateInterval(self) -> int:
        return self._update_interval

    @Property(bool, notify=pausedChanged)
    def paused(self) -> bool:
        return self._paused

    @Property(int, constant=True)
    def maxSamples(self) -> int:
        return self._max_samples

    # ------------------------------------------------------------------ mutators
    @Slot("QStringList")
    def setActiveMetrics(self, metric_ids: Iterable[str]) -> None:
        normalized: list[str] = []
        seen = set()
        for metric_id in metric_ids:
            key = str(metric_id)
            if key not in self._buffers or key in seen:
                continue
            normalized.append(key)
            seen.add(key)
        new_active = tuple(normalized)
        if new_active == self._active_metrics:
            return
        self._active_metrics = new_active
        self.activeMetricsChanged.emit()

    @Slot(int)
    def setUpdateInterval(self, interval: int) -> None:
        value = int(interval) if interval and interval > 0 else 1
        if value == self._update_interval:
            return
        self._update_interval = value
        self._skip_counter = 0
        self.updateIntervalChanged.emit()

    @Slot(bool)
    def setPaused(self, paused: bool) -> None:
        flag = bool(paused)
        if flag == self._paused:
            return
        self._paused = flag
        self.pausedChanged.emit()

    @Slot()
    def togglePaused(self) -> None:
        self.setPaused(not self._paused)

    @Slot()
    def resetStream(self) -> None:
        self._time_buffer.clear()
        for buffer in self._buffers.values():
            buffer.clear()
        self._skip_counter = 0
        self._oldest_timestamp = None
        self._latest_timestamp = None
        self.streamReset.emit()

    # ------------------------------------------------------------------ data flow
    def push_snapshot(self, snapshot: StateSnapshot) -> None:
        if self._paused:
            return
        self._skip_counter += 1
        if self._skip_counter < self._update_interval:
            return
        self._skip_counter = 0

        timestamp = float(snapshot.simulation_time)
        values: dict[str, float] = {}
        for metric_id, extractor in self._extractors.items():
            try:
                value = float(extractor(snapshot))
            except Exception:
                continue
            buffer = self._buffers.get(metric_id)
            if buffer is None:
                buffer = deque(maxlen=self._max_samples)
                self._buffers[metric_id] = buffer
            buffer.append(value)
            values[metric_id] = value

        if not values:
            return

        self._time_buffer.append(timestamp)
        if self._oldest_timestamp is None:
            self._oldest_timestamp = timestamp
        self._latest_timestamp = timestamp

        active_values = {
            metric_id: values[metric_id]
            for metric_id in self._active_metrics
            if metric_id in values
        }
        if not active_values:
            return

        payload = {
            "timestamp": timestamp,
            "values": active_values,
            "oldestTimestamp": float(self._oldest_timestamp or timestamp),
            "latestTimestamp": float(self._latest_timestamp or timestamp),
        }
        self.sampleAppended.emit(payload)

    @Slot("QStringList", result="QVariantMap")
    def exportSeries(self, metric_ids: Iterable[str]) -> dict[str, object]:
        metrics = [str(metric_id) for metric_id in metric_ids if metric_id]
        if not metrics:
            return {
                "series": {},
                "oldestTimestamp": float(self._oldest_timestamp or 0.0),
                "latestTimestamp": float(self._latest_timestamp or 0.0),
            }

        time_points = list(self._time_buffer)
        series_payload: dict[str, list[dict[str, float]]] = {}

        for metric_id in metrics:
            buffer = self._buffers.get(metric_id)
            if not buffer:
                continue
            values = list(buffer)
            if not values:
                continue
            times = time_points
            if len(values) < len(time_points):
                times = time_points[-len(values) :]
            elif len(values) > len(time_points) and time_points:
                values = values[-len(time_points) :]
                times = time_points
            series_payload[metric_id] = [
                {"timestamp": float(t), "value": float(v)}
                for t, v in zip(times, values)
            ]

        return {
            "series": series_payload,
            "oldestTimestamp": float(self._oldest_timestamp or 0.0),
            "latestTimestamp": float(self._latest_timestamp or 0.0),
        }


__all__ = ["TelemetryDataBridge", "MetricDescriptor"]
