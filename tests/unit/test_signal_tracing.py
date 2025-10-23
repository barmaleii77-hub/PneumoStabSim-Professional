# -*- coding: utf-8 -*-
"""Unit-тесты для модуля трассировки Qt-сигналов."""

from __future__ import annotations

from typing import Any, List

import pytest

from src.diagnostics.signal_tracing import (
 HAS_QT,
 MissingSignalError,
 SignalTraceRecord,
 SignalTracer,
 SignalTracerBridge,
 SignalTracingError,
)


class _FakeSignal:
    def __init__(self) -> None:
        self._callbacks: List[Any] = []

    def connect(self, callback: Any) -> None:
        self._callbacks.append(callback)

    def disconnect(self, callback: Any) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def emit(self, *args: Any) -> None:
        for callback in list(self._callbacks):
            callback(*args)


class _FakeQObject:
    def __init__(self, name: str) -> None:
        self._object_name = name
        self.changed = _FakeSignal()

    def objectName(self) -> str:
        return self._object_name


@pytest.mark.unit
class TestSignalTracer:
    def test_records_emitted_signals(self) -> None:
        tracer = SignalTracer(max_records=10)
        source = _FakeQObject("EngineController")
        tracer.attach(source, "changed", alias="sourceChanged")

        source.changed.emit(42, "rpm")

        records = tracer.records
        assert len(records) == 1
        record = records[0]
        assert isinstance(record, SignalTraceRecord)
        assert record.sender == "EngineController"
        assert record.signal == "sourceChanged"
        assert record.args == (42, "rpm")

    def test_missing_signal_detection(self) -> None:
        tracer = SignalTracer(max_records=10)
        source = _FakeQObject("Pump")
        tracer.attach(source, "changed")

        with pytest.raises(MissingSignalError):
            tracer.assert_emitted("changed", min_count=1)

        source.changed.emit()
        tracer.assert_emitted("changed", min_count=1)

    def test_attach_missing_signal_raises(self) -> None:
        tracer = SignalTracer()
        source = _FakeQObject("Controller")

        with pytest.raises(SignalTracingError):
            tracer.attach(source, "notExists")

    def test_sinks_receive_records(self) -> None:
        tracer = SignalTracer()
        source = _FakeQObject("Indicator")
        captured: List[SignalTraceRecord] = []
        tracer.register_sink(captured.append)
        tracer.attach(source, "changed")

        source.changed.emit("ok")

        assert len(captured) == 1
        assert captured[0].args == ("ok",)

    def test_clear_notifies_reset_hooks(self) -> None:
        tracer = SignalTracer()
        was_called: list[bool] = []
        tracer.register_reset_hook(lambda: was_called.append(True))
        source = _FakeQObject("Display")
        tracer.attach(source, "changed")

        source.changed.emit("value")
        tracer.clear()

        assert was_called
        assert tracer.records == ()


@pytest.mark.unit
def test_bridge_requires_qt_environment() -> None:
    tracer = SignalTracer()
    if HAS_QT:
        pytest.skip("PySide6 available in environment; bridge can be instantiated")
    with pytest.raises(SignalTracingError):
        SignalTracerBridge(tracer)
