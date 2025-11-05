"""Shared telemetry schema definitions and helpers.

This module centralises the canonical telemetry event schema so that the
runtime tracker, command line exporters, and analytics tooling all interpret
records consistently.  Keeping the validation logic in one place prevents the
JSON Lines artefacts from drifting away from the documented contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping

__all__ = [
    "EVENT_SCHEMA_VERSION",
    "TelemetryRecord",
    "parse_event_dict",
]


# ``telemetry_event_v1`` is the first public schema revision.  New versions
# should be introduced by extending the constants below and updating the
# documentation alongside validation helpers.
EVENT_SCHEMA_VERSION = "telemetry_event_v1"

REQUIRED_FIELDS = ("channel", "event", "timestamp", "payload")


@dataclass(slots=True)
class TelemetryRecord:
    """Structured telemetry payload."""

    channel: str
    event: str
    timestamp: datetime
    payload: Dict[str, Any]
    schema_version: str = EVENT_SCHEMA_VERSION

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "channel": self.channel,
            "event": self.event,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }


def _parse_timestamp(raw: Any) -> datetime:
    if not isinstance(raw, str):
        raise ValueError("timestamp must be an ISO 8601 string")
    candidate = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:  # pragma: no cover - defensive guard rail.
        raise ValueError(f"invalid timestamp '{raw}': {exc}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_event_dict(payload: Mapping[str, Any]) -> TelemetryRecord:
    """Validate and normalise a telemetry dictionary.

    Parameters
    ----------
    payload:
        Mapping parsed from the JSON Lines artefact.

    Returns
    -------
    TelemetryRecord
        Normalised record ready for analytics consumption.
    """

    missing = {key for key in REQUIRED_FIELDS if key not in payload}
    if missing:
        missing_keys = ", ".join(sorted(missing))
        raise ValueError(f"missing keys: {missing_keys}")

    channel = payload["channel"]
    event = payload["event"]
    if not isinstance(channel, str):
        raise ValueError("channel must be a string")
    if not isinstance(event, str):
        raise ValueError("event must be a string")

    schema_version = payload.get("schema_version") or EVENT_SCHEMA_VERSION
    if not isinstance(schema_version, str):
        raise ValueError("schema_version must be a string when provided")

    timestamp = _parse_timestamp(payload["timestamp"])

    body = payload["payload"]
    if not isinstance(body, Mapping):
        raise ValueError("payload must be a mapping")

    return TelemetryRecord(
        channel=channel,
        event=event,
        timestamp=timestamp,
        payload=dict(body),
        schema_version=schema_version,
    )
