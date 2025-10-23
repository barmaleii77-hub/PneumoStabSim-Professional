"""Unit tests for QMLBridge failure handling and logging."""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.common.event_logger import EventLogger, EventType, get_event_logger
from src.runtime.state import StateSnapshot

MODULE_PATH = (
 Path(__file__).resolve().parents[2]
 / "src"
 / "ui"
 / "main_window"
 / "qml_bridge.py"
)
spec = importlib.util.spec_from_file_location(
 "test_support.qml_bridge",
 MODULE_PATH,
)
qml_bridge = importlib.util.module_from_spec(spec)
if spec.loader is None: # pragma: no cover - defensive branch
 raise RuntimeError("Failed to load qml_bridge module for testing")
sys.modules.setdefault("test_support.qml_bridge", qml_bridge)
spec.loader.exec_module(qml_bridge)

QMLBridge = qml_bridge.QMLBridge
QMLUpdateResult = qml_bridge.QMLUpdateResult


class DummyStatusBar:
 """Test double for QStatusBar."""

 def __init__(self) -> None:
  self.messages: list[tuple[str, int]] = []

 def showMessage(self, message: str, timeout: int) -> None: # noqa: N802 - Qt style
  self.messages.append((message, timeout))


class DummyTimer:
 """Minimal timer stub used to satisfy QMLBridge expectations."""

 def __init__(self) -> None:
  self.started: list[int] = []

 def start(self, interval: int) -> None:
  self.started.append(interval)


class FailingRootObject:
 """QML root object stub that simulates property assignment failure."""

 def __init__(self, exception: Exception) -> None:
  self._exception = exception

 def setProperty(self, name: str, value: object) -> None: # noqa: N802 - Qt style
  raise self._exception


class _LogCaptureHandler(logging.Handler):
 """Lightweight logging handler to capture bridge errors."""

 def __init__(self) -> None:
  super().__init__(level=logging.NOTSET)
  self.records: list[logging.LogRecord] = []

 def emit(self, record: logging.LogRecord) -> None: # pragma: no cover - trivial
  self.records.append(record)


@pytest.fixture
def event_logger() -> EventLogger:
 """Provide a clean EventLogger instance for every test."""

 logger = get_event_logger()
 logger.events.clear()
 yield logger
 logger.events.clear()


def _make_window(event_logger, root_object) -> SimpleNamespace:
 """Create a simplified window stub for bridge operations."""

 return SimpleNamespace(
  _qml_root_object=root_object,
  _qml_update_queue={},
  _qml_flush_timer=DummyTimer(),
  _last_batched_updates=None,
  status_bar=DummyStatusBar(),
  event_logger=event_logger,
  _suppress_qml_failure_dialog=True,
  is_simulation_running=False,
 )


def _collect_failure_events(logger) -> list[dict]:
 return [
  event
  for event in logger.events
  if event["event_type"] == EventType.QML_UPDATE_FAILURE.name
 ]


def test_push_batched_updates_failure_logs_and_records_event(event_logger):
 window = _make_window(event_logger, FailingRootObject(RuntimeError("reject")))

 handler = _LogCaptureHandler()
 bridge_logger = QMLBridge.logger
 previous_level = bridge_logger.level
 bridge_logger.setLevel(logging.ERROR)
 bridge_logger.addHandler(handler)
 try:
  result = QMLBridge._push_batched_updates(
   window,
   {"geometry": {"param":1}},
   detailed=True,
  )
 finally:
  bridge_logger.removeHandler(handler)
  bridge_logger.setLevel(previous_level)

 assert isinstance(result, QMLUpdateResult)
 assert not result.success
 assert "reject" in (result.error or "")
 assert any(
 "Failed to push batched updates" in record.getMessage()
 for record in handler.records
 )

 failure_events = _collect_failure_events(event_logger)
 assert failure_events
 assert failure_events[0]["action"] == "flush_updates"
 assert "stacktrace" in failure_events[0]["metadata"]


def test_flush_updates_notifies_status_bar_on_failure(monkeypatch, event_logger):
 window = _make_window(event_logger, FailingRootObject(RuntimeError("reject")))
 window._qml_update_queue = {"geometry": {"param":42}}

 monkeypatch.setattr(QMLBridge, "invoke_qml_function", lambda *_, **__: False)

 QMLBridge.flush_updates(window)

 failure_events = _collect_failure_events(event_logger)
 assert failure_events
 assert failure_events[0]["action"] == "flush_updates"

 status_messages = [message for message, _ in window.status_bar.messages]
 assert status_messages
 assert any("QML не принял пакет обновлений" in message for message in status_messages)


def test_set_simulation_state_failure_logs_and_notifies(event_logger):
 window = _make_window(event_logger, FailingRootObject(RuntimeError("sim error")))

 snapshot = StateSnapshot()

 handler = _LogCaptureHandler()
 bridge_logger = QMLBridge.logger
 previous_level = bridge_logger.level
 bridge_logger.setLevel(logging.ERROR)
 bridge_logger.addHandler(handler)
 try:
  success = QMLBridge.set_simulation_state(window, snapshot)
 finally:
  bridge_logger.removeHandler(handler)
  bridge_logger.setLevel(previous_level)

 assert not success
 assert any(
 "Failed to push simulation state to QML" in record.getMessage()
 for record in handler.records
 )

 failure_events = _collect_failure_events(event_logger)
 assert failure_events
 assert failure_events[0]["action"] == "set_simulation_state"
 assert "stacktrace" in failure_events[0]["metadata"]

 status_messages = [message for message, _ in window.status_bar.messages]
 assert status_messages
 assert any("QML не принял состояние симуляции" in message for message in status_messages)
