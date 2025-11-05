"""Utilities to export telemetry archives and build analytics aggregates."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from src.telemetry.tracker import EVENT_SCHEMA_VERSION as _TRACKER_SCHEMA_VERSION
except ModuleNotFoundError:
    _TRACKER_SCHEMA_VERSION = None

EVENT_SCHEMA_VERSION = _TRACKER_SCHEMA_VERSION or "telemetry_event_v1"

try:  # Optional dependency for Parquet exports.
    import pyarrow as pa
    import pyarrow.parquet as pq
except ModuleNotFoundError:  # pragma: no cover - executed when pyarrow is absent.
    pa = None
    pq = None


@dataclass(slots=True)
class NormalizedEvent:
    """Telemetry event normalised for analytics processing."""

    schema_version: str
    channel: str
    event: str
    timestamp: datetime
    payload: Dict[str, Any]
    source: Path

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "channel": self.channel,
            "event": self.event,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "source": str(self.source),
        }


@dataclass(slots=True)
class TelemetryBundle:
    """Container for parsed telemetry events and parsing diagnostics."""

    events: List[NormalizedEvent]
    errors: List[str]
    inventory: Mapping[str, int]

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def error_count(self) -> int:
        return len(self.errors)


def _parse_timestamp(raw: Any) -> datetime:
    if not isinstance(raw, str):
        raise ValueError("timestamp must be an ISO 8601 string")
    candidate = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:  # pragma: no cover - defensive against malformed data.
        raise ValueError(f"invalid timestamp '{raw}': {exc}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _normalize_event(payload: Mapping[str, Any], source: Path) -> NormalizedEvent:
    missing = {
        key
        for key in ("channel", "event", "timestamp", "payload")
        if key not in payload
    }
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")

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

    return NormalizedEvent(
        schema_version=schema_version,
        channel=channel,
        event=event,
        timestamp=timestamp,
        payload=dict(body),
        source=source,
    )


def _read_jsonl(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield stripped


def load_events(source: Path, *, strict: bool = False) -> TelemetryBundle:
    events: List[NormalizedEvent] = []
    errors: List[str] = []
    inventory: MutableMapping[str, int] = defaultdict(int)

    for file_path in sorted(source.glob("*.jsonl")):
        count = 0
        for index, raw_line in enumerate(_read_jsonl(file_path), start=1):
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                message = f"{file_path.name}:{index}: invalid JSON: {exc.msg}"
                if strict:
                    raise ValueError(message) from exc
                errors.append(message)
                continue
            try:
                event = _normalize_event(payload, file_path)
            except ValueError as exc:
                message = f"{file_path.name}:{index}: {exc}"
                if strict:
                    raise ValueError(message) from exc
                errors.append(message)
                continue
            events.append(event)
            count += 1
        inventory[str(file_path)] = count

    return TelemetryBundle(events=events, errors=errors, inventory=dict(inventory))


def export_json(bundle: TelemetryBundle, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(
            [event.as_dict() for event in bundle.events],
            handle,
            ensure_ascii=False,
            indent=2,
        )
        handle.write("\n")
    return output


def export_parquet(bundle: TelemetryBundle, output: Path) -> Path:
    if pa is None or pq is None:
        raise RuntimeError(
            "pyarrow is required for Parquet exports; install pyarrow to continue"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "schema_version": [event.schema_version for event in bundle.events],
            "channel": [event.channel for event in bundle.events],
            "event": [event.event for event in bundle.events],
            "timestamp": [event.timestamp for event in bundle.events],
            "payload": [
                json.dumps(event.payload, ensure_ascii=False) for event in bundle.events
            ],
            "source": [str(event.source) for event in bundle.events],
        }
    )
    pq.write_table(table, output)
    return output


def build_aggregates(bundle: TelemetryBundle) -> Dict[str, Any]:
    per_channel = Counter(event.channel for event in bundle.events)
    per_event = Counter(event.event for event in bundle.events)
    per_day = Counter(event.timestamp.date().isoformat() for event in bundle.events)

    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "event_count": bundle.event_count,
        "error_count": bundle.error_count,
        "channels": dict(sorted(per_channel.items())),
        "events": dict(sorted(per_event.items())),
        "daily_counts": dict(sorted(per_day.items())),
        "source_inventory": bundle.inventory,
        "notes": ["Counts include only successfully parsed records."],
    }


def write_aggregates(bundle: TelemetryBundle, output: Path) -> Path:
    aggregates = build_aggregates(bundle)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(aggregates, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return output


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("reports/telemetry"),
        help="Directory containing telemetry JSONL files (default: reports/telemetry).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Abort on malformed records instead of collecting diagnostics.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser(
        "export", help="Export telemetry events to JSON or Parquet."
    )
    export_parser.add_argument("--format", choices=("json", "parquet"), default="json")
    export_parser.add_argument("--output", type=Path, required=True)

    aggregate_parser = subparsers.add_parser(
        "aggregate", help="Generate aggregate metrics for analytics dashboards."
    )
    aggregate_parser.add_argument("--output", type=Path, required=True)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    bundle = load_events(args.source, strict=args.strict)

    if args.command == "export":
        if args.format == "json":
            export_path = export_json(bundle, args.output)
        else:
            export_path = export_parquet(bundle, args.output)
        print(f"Exported {bundle.event_count} events to {export_path}")
    elif args.command == "aggregate":
        export_path = write_aggregates(bundle, args.output)
        print(f"Wrote aggregates to {export_path}")
    else:  # pragma: no cover - defensive, should never happen due to argparse
        parser.error(f"Unknown command: {args.command}")
        return 2

    if bundle.errors:
        for message in bundle.errors:
            print(f"warning: {message}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
