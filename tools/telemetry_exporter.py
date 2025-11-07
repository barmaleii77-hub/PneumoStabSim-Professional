"""Utilities to export telemetry archives and build analytics aggregates."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from collections.abc import Iterable, MutableMapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if TYPE_CHECKING:  # pragma: no cover - used for static analysis only.
    from src.telemetry.schema import TelemetryRecord

try:
    from src.telemetry.schema import EVENT_SCHEMA_VERSION, parse_event_dict
except ModuleNotFoundError:
    schema_path = REPO_ROOT / "src" / "telemetry" / "schema.py"
    spec = importlib.util.spec_from_file_location("_telemetry_schema", schema_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        EVENT_SCHEMA_VERSION = getattr(
            module, "EVENT_SCHEMA_VERSION", "telemetry_event_v1"
        )
        parse_event_dict = getattr(module, "parse_event_dict", None)
    else:  # pragma: no cover - fallback when spec resolution fails.
        EVENT_SCHEMA_VERSION = "telemetry_event_v1"
        parse_event_dict = None

try:  # Optional dependency for Parquet exports.
    import pyarrow as pa
    import pyarrow.parquet as pq
except ModuleNotFoundError:  # pragma: no cover - executed when pyarrow is absent.
    pa = None
    pq = None


@dataclass(slots=True)
class NormalizedEvent:
    """Telemetry event normalised for analytics processing."""

    record: TelemetryRecord
    source: Path

    def as_dict(self) -> dict[str, Any]:
        payload = self.record.as_dict()
        payload["source"] = str(self.source)
        return payload


@dataclass(slots=True)
class TelemetryBundle:
    """Container for parsed telemetry events and parsing diagnostics."""

    events: list[NormalizedEvent]
    errors: list[str]
    inventory: dict[str, int]

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def error_count(self) -> int:
        return len(self.errors)


def _read_jsonl(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield stripped


def load_events(source: Path, *, strict: bool = False) -> TelemetryBundle:
    events: list[NormalizedEvent] = []
    errors: list[str] = []
    inventory: MutableMapping[str, int] = defaultdict(int)

    if parse_event_dict is None:  # pragma: no cover - executed in limited envs
        raise RuntimeError(
            "telemetry schema helpers are unavailable; ensure src/telemetry is on PYTHONPATH"
        )

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
                record = parse_event_dict(payload)
            except ValueError as exc:
                message = f"{file_path.name}:{index}: {exc}"
                if strict:
                    raise ValueError(message) from exc
                errors.append(message)
                continue
            events.append(NormalizedEvent(record=record, source=file_path))
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
            "schema_version": [event.record.schema_version for event in bundle.events],
            "channel": [event.record.channel for event in bundle.events],
            "event": [event.record.event for event in bundle.events],
            "timestamp": [event.record.timestamp for event in bundle.events],
            "payload": [
                json.dumps(event.record.payload, ensure_ascii=False)
                for event in bundle.events
            ],
            "source": [str(event.source) for event in bundle.events],
        }
    )
    pq.write_table(table, output)
    return output


def build_aggregates(bundle: TelemetryBundle) -> dict[str, Any]:
    per_channel = Counter(event.record.channel for event in bundle.events)
    per_event = Counter(event.record.event for event in bundle.events)
    per_day = Counter(
        event.record.timestamp.date().isoformat() for event in bundle.events
    )
    per_schema = Counter(event.record.schema_version for event in bundle.events)
    events_by_channel: dict[str, Counter[str]] = defaultdict(Counter)
    for normalised in bundle.events:
        events_by_channel[normalised.record.channel][normalised.record.event] += 1

    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "event_count": bundle.event_count,
        "error_count": bundle.error_count,
        "channels": dict(sorted(per_channel.items())),
        "events": dict(sorted(per_event.items())),
        "daily_counts": dict(sorted(per_day.items())),
        "schema_versions": dict(sorted(per_schema.items())),
        "events_by_channel": {
            channel: dict(sorted(counter.items()))
            for channel, counter in sorted(events_by_channel.items())
        },
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


def main(argv: Sequence[str] | None = None) -> int:
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
