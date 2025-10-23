"""Signal tracing service for diagnostics and QML overlays."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from .qt_compat import Property, QObject, Signal, Slot

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SignalTraceConfig:
 """Configuration parameters for :class:`SignalTraceService`."""

 def __init__(self):
 self.enabled = False
 self.overlay_enabled = False
 self.include = ("*",)
 self.exclude = ()
 self.history_limit =200

 @classmethod
 def from_dict(cls, data: Dict[str, Any] | None) -> "SignalTraceConfig":
 if not isinstance(data, dict):
 return cls()
 include = tuple(str(item) for item in data.get("include", ("*",)))
 exclude = tuple(str(item) for item in data.get("exclude", ()))
 return cls(
 enabled=bool(data.get("enabled", False)),
 overlay_enabled=bool(
 data.get("overlayEnabled", data.get("overlay_enabled", False))
 ),
 include=include or ("*",),
 exclude=exclude,
 history_limit=int(data.get("historyLimit", data.get("history_limit",200))),
 )

 def to_dict(self) -> Dict[str, Any]:
 return {
 "enabled": self.enabled,
 "overlayEnabled": self.overlay_enabled,
 "include": list(self.include),
 "exclude": list(self.exclude),
 "historyLimit": self.history_limit,
 }

class SignalTraceService(QObject):
 """Collects signal emissions and exposes them to QML for diagnostics."""

 traceUpdated = Signal(object)

 def __init__(self) -> None:
 super().__init__()
 self._config = SignalTraceConfig()
 self._subscriptions: Dict[str, Dict[str, Any]] = {}
 self._history: List[Dict[str, Any]] = []
 self._lock = Lock()
 self._log_path = Path("logs") / "signal_trace.jsonl"

 @Slot(str, str, str, result=bool)
 def registerSubscription(self, signal_name: str, subscriber: str, source: str = "qml") -> bool:
 """Register a listener for diagnostic purposes."""
 with self._lock:
 entry = self._subscriptions.setdefault(
 signal_name,
 {
 "listeners": {},
 "last_value": None,
 "last_timestamp": None,
 },
 )
 listeners = entry["listeners"]
 listeners[subscriber] = {
 "source": source,
 "updated_at": datetime.utcnow().isoformat(),
 }
 self._notify_listeners()
 return True

 @Slot(str, object, str, result=bool)
 def recordObservation(self, signal_name: str, payload: Any, source: str = "qml") -> bool:
 """Record an observation from QML subscribers."""
 self.record_signal(signal_name, payload, source=source)
 return True

 def record_signal(self, signal_name: str, payload: Any, *, source: str = "python") -> None:
 """Record a signal emission and optionally persist to the trace log."""
 sanitized_payload = self._sanitize(payload)
 timestamp = datetime.utcnow().isoformat()
 with self._lock:
 entry = self._subscriptions.setdefault(
 signal_name,
 {
 "listeners": {},
 "last_value": None,
 "last_timestamp": None,
 },
 )
 entry["last_value"] = sanitized_payload
 entry["last_timestamp"] = timestamp

 self._history.append(
 {
 "timestamp": timestamp,
 "signal": signal_name,
 "payload": sanitized_payload,
 "source": source,
 }
 )
 if len(self._history) > self._config.history_limit:
 del self._history[: -self._config.history_limit]

 if self._config.enabled and self._passes_filters(signal_name):
 self._append_to_log(
 {
 "timestamp": timestamp,
 "signal": signal_name,
 "payload": sanitized_payload,
 "source": source,
 }
 )

 self._notify_listeners()

 def update_config(self, config: SignalTraceConfig) -> None:
 self._config = config
 if self._config.enabled:
 try:
 self._log_path.parent.mkdir(parents=True, exist_ok=True)
 except Exception as exc: # pragma: no cover - IO errors rare
 LOGGER.warning("Failed to create signal trace log directory: %s", exc)
 self._notify_listeners()

 def update_from_settings(self, data: Dict[str, Any] | None) -> None:
 self.update_config(SignalTraceConfig.from_dict(data))

 @Property("QVariant", notify=traceUpdated)
 def subscriptions(self) -> List[Dict[str, Any]]:
 with self._lock:
 return [
 self._subscription_summary(signal, data)
 for signal, data in sorted(self._subscriptions.items())
 ]

 @Property("QVariant", notify=traceUpdated)
 def latestValues(self) -> Dict[str, Any]:
 with self._lock:
 return {
 signal: data.get("last_value")
 for signal, data in self._subscriptions.items()
 if data.get("last_value") is not None
 }

 @Property(bool, notify=traceUpdated)
 def overlayEnabled(self) -> bool:
 return self._config.overlay_enabled

 @Property(bool, notify=traceUpdated)
 def tracingEnabled(self) -> bool:
 return self._config.enabled

 def _notify_listeners(self) -> None:
 snapshot = {
 "subscriptions": self.subscriptions,
 "latestValues": self.latestValues,
 "config": self._config.to_dict(),
 }
 self.traceUpdated.emit(snapshot)

 def _passes_filters(self, signal_name: str) -> bool:
 include_match = any(fnmatch(signal_name, pattern) for pattern in self._config.include)
 exclude_match = any(fnmatch(signal_name, pattern) for pattern in self._config.exclude)
 return include_match and not exclude_match

 def _append_to_log(self, entry: Dict[str, Any]) -> None:
 try:
 self._log_path.parent.mkdir(parents=True, exist_ok=True)
 with self._log_path.open("a", encoding="utf-8") as handle:
 json.dump(entry, handle, ensure_ascii=False)
 handle.write("\n")
 except Exception as exc: # pragma: no cover - logging must never crash
 LOGGER.warning("Failed to append signal trace entry: %s", exc)

 def _sanitize(self, value: Any) -> Any:
 try:
 json.dumps(value)
 return value
 except TypeError:
 if isinstance(value, dict):
 return {str(key): self._sanitize(sub_value) for key, sub_value in value.items()}
 if isinstance(value, (list, tuple, set)):
 return [self._sanitize(item) for item in value]
 return repr(value)

 def _subscription_summary(self, signal_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
 listeners = data.get("listeners", {})
 return {
 "signal": signal_name,
 "listenerCount": len(listeners),
 "listeners": [
 {"name": name, **info} for name, info in sorted(listeners.items())
 ],
 "lastTimestamp": data.get("last_timestamp"),
 "lastValue": data.get("last_value"),
 }

_signal_trace_service: Optional[SignalTraceService] = None

def get_signal_trace_service() -> SignalTraceService:
 global _signal_trace_service
 if _signal_trace_service is None:
 _signal_trace_service = SignalTraceService()
 return _signal_trace_service

def _reset_signal_trace_service_for_tests() -> None:
 global _signal_trace_service
 _signal_trace_service = None

__all__ = [
 "SignalTraceConfig",
 "SignalTraceService",
 "get_signal_trace_service",
 "_reset_signal_trace_service_for_tests",
]
