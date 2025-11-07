"""Telemetry tracking for user actions and simulation events.

The tracker writes JSON Lines artefacts to ``reports/telemetry`` so that
diagnostics tooling can ingest structured histories without parsing ad-hoc log
messages.  Each call records an event dictionary with a timestamp, event name,
and arbitrary payload provided by the caller.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from collections.abc import Mapping

from src.diagnostics.logger_factory import LoggerProtocol, get_logger
from src.telemetry.schema import EVENT_SCHEMA_VERSION, TelemetryRecord


__all__ = [
    "EVENT_SCHEMA_VERSION",
    "TelemetryRouter",
    "TelemetryTracker",
    "get_tracker",
    "track_simulation_event",
    "track_user_action",
]


_DEFAULT_BASE_DIR = Path("reports/telemetry")
_USER_ACTIONS_FILE = "user_actions.jsonl"
_SIMULATION_EVENTS_FILE = "simulation_events.jsonl"


class TelemetryRouter:
    """Persist telemetry records as JSON lines."""

    def __init__(
        self,
        base_dir: Path | str = _DEFAULT_BASE_DIR,
        *,
        logger: LoggerProtocol | None = None,
    ) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logger or get_logger("telemetry.router")
        self._lock = RLock()

    def _append(self, file_name: str, record: TelemetryRecord) -> Path:
        target = self._base_dir / file_name
        payload = json.dumps(record.as_dict(), ensure_ascii=False)
        with self._lock:
            with target.open("a", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")
        self._logger.info(
            "telemetry_record_written",
            channel=record.channel,
            telemetry_event=record.event,
            path=str(target),
        )
        return target

    def route(self, record: TelemetryRecord) -> Path:
        if record.channel == "user":
            return self._append(_USER_ACTIONS_FILE, record)
        if record.channel == "simulation":
            return self._append(_SIMULATION_EVENTS_FILE, record)
        # Generic fallback file keeps unexpected channels separate.
        file_name = f"{record.channel}.jsonl"
        return self._append(file_name, record)


class TelemetryTracker:
    """High level API used by the application to record telemetry events."""

    def __init__(
        self,
        router: TelemetryRouter | None = None,
        *,
        logger: LoggerProtocol | None = None,
    ) -> None:
        self._router = router or TelemetryRouter(logger=logger)
        self._logger = logger or get_logger("telemetry.tracker")

    @staticmethod
    def _build_payload(
        action: str,
        metadata: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"action": action}
        if metadata:
            payload["metadata"] = dict(metadata)
        if context:
            payload["context"] = dict(context)
        return payload

    def _record(self, channel: str, event: str, payload: dict[str, Any]) -> Path:
        record = TelemetryRecord(
            channel=channel,
            event=event,
            timestamp=datetime.now(timezone.utc),
            payload=payload,
        )
        path = self._router.route(record)
        self._logger.info(
            "telemetry_event_recorded",
            channel=channel,
            telemetry_event=event,
            path=str(path),
        )
        return path

    def track_user_action(
        self,
        action: str,
        *,
        metadata: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> Path:
        payload = self._build_payload(action, metadata=metadata, context=context)
        return self._record("user", action, payload)

    def track_simulation_event(
        self,
        event: str,
        *,
        metadata: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> Path:
        payload = self._build_payload(event, metadata=metadata, context=context)
        return self._record("simulation", event, payload)


_DEFAULT_TRACKER: TelemetryTracker | None = None
_TRACKER_LOCK = RLock()


def get_tracker(*, base_dir: Path | str | None = None) -> TelemetryTracker:
    """Return the process-wide telemetry tracker instance."""

    global _DEFAULT_TRACKER
    with _TRACKER_LOCK:
        if _DEFAULT_TRACKER is not None and base_dir is None:
            return _DEFAULT_TRACKER

        router = (
            TelemetryRouter(base_dir=base_dir)
            if base_dir is not None
            else TelemetryRouter()
        )
        tracker = TelemetryTracker(router=router)
        if base_dir is None:
            _DEFAULT_TRACKER = tracker
        return tracker


def track_user_action(
    action: str,
    *,
    metadata: Mapping[str, Any] | None = None,
    context: Mapping[str, Any] | None = None,
) -> Path:
    """Record a user-facing telemetry event."""

    tracker = get_tracker()
    return tracker.track_user_action(action, metadata=metadata, context=context)


def track_simulation_event(
    event: str,
    *,
    metadata: Mapping[str, Any] | None = None,
    context: Mapping[str, Any] | None = None,
) -> Path:
    """Record a simulation telemetry event."""

    tracker = get_tracker()
    return tracker.track_simulation_event(event, metadata=metadata, context=context)
