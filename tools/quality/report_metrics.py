"""Aggregate quality metrics into a CSV dashboard.

The master plan mandates nightly aggregation of lint, type checking, testing,
and coverage telemetry.  This module provides a simple command line interface
that ingests structured JSON payloads and appends them to
``reports/quality/dashboard.csv`` in a normalized tabular format.  When new
metrics introduce additional fields, the CSV header is automatically expanded
and historical rows are padded with empty values so downstream tooling can rely
on a stable schema.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


Timestamp = str


class MetricsError(RuntimeError):
    """Raised when an input payload cannot be interpreted."""


@dataclass(slots=True)
class MetricsEntry:
    """Normalized representation of a single metrics snapshot."""

    timestamp: Timestamp
    values: dict[str, str]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        dest="inputs",
        action="append",
        required=True,
        help=(
            "Path to a JSON file describing one or more quality metric entries. "
            "Files may contain a dictionary or a list of dictionaries."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/quality/dashboard.csv"),
        help="Destination CSV file (defaults to reports/quality/dashboard.csv).",
    )
    return parser.parse_args(argv)


def load_entries(paths: Sequence[str]) -> list[MetricsEntry]:
    entries: list[MetricsEntry] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise MetricsError(f"Metrics file not found: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MetricsError(f"Invalid JSON in {path}: {exc}") from exc

        if isinstance(payload, Mapping):
            payloads = [payload]
        elif isinstance(payload, Sequence):
            payloads = list(payload)
        else:
            raise MetricsError(
                f"Unsupported payload type in {path}: {type(payload)!r}. "
                "Expected mapping or sequence of mappings.",
            )

        for item in payloads:
            if not isinstance(item, Mapping):
                raise MetricsError(
                    f"Metrics entries in {path} must be mappings. "
                    f"Received {type(item)!r}."
                )
            entries.append(_normalise_entry(dict(item)))
    return entries


def _normalise_entry(entry: dict[str, Any]) -> MetricsEntry:
    try:
        raw_timestamp = entry.pop("timestamp")
    except KeyError as exc:
        raise MetricsError("Metrics entry is missing required 'timestamp'.") from exc

    if not isinstance(raw_timestamp, str):
        raise MetricsError("'timestamp' must be a string in ISO 8601 format.")

    timestamp = _normalise_timestamp(raw_timestamp)

    flattened: dict[str, str] = {"timestamp": timestamp}
    for key, value in entry.items():
        if not isinstance(key, str) or not key:
            raise MetricsError("Metric keys must be non-empty strings.")
        _flatten_value(flattened, key, value)

    values = flattened
    values.pop("timestamp", None)
    return MetricsEntry(timestamp=timestamp, values=values)


def _normalise_timestamp(raw: str) -> Timestamp:
    candidate = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise MetricsError(f"Invalid ISO 8601 timestamp: {raw!r}") from exc
    # Always persist timezone information for downstream aggregators.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def _flatten_value(target: dict[str, str], prefix: str, value: Any) -> None:
    if isinstance(value, Mapping):
        for nested_key, nested_value in value.items():
            if not isinstance(nested_key, str) or not nested_key:
                raise MetricsError("Nested metric keys must be non-empty strings.")
            _flatten_value(target, f"{prefix}_{nested_key}", nested_value)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        serialised = json.dumps(list(value), ensure_ascii=False, sort_keys=True)
    else:
        serialised = _serialise_scalar(value)

    if prefix in target:
        raise MetricsError(f"Duplicate metric key detected: {prefix}")
    target[prefix] = serialised


def _serialise_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    return str(value)


def read_existing_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []

    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames or []
        rows = [
            {key: (value or "") for key, value in row.items() if key is not None}
            for row in reader
        ]
    return rows, fieldnames


def merge_rows(
    existing_rows: list[dict[str, str]],
    new_entries: Sequence[MetricsEntry],
) -> list[dict[str, str]]:
    seen = {row.get("timestamp", "") for row in existing_rows}
    merged = list(existing_rows)
    for entry in new_entries:
        if entry.timestamp in seen:
            continue
        row = {"timestamp": entry.timestamp}
        row.update(entry.values)
        merged.append(row)
        seen.add(entry.timestamp)
    return merged


def determine_columns(rows: Sequence[dict[str, str]]) -> list[str]:
    if not rows:
        return ["timestamp"]

    keys: set[str] = {"timestamp"}
    for row in rows:
        keys.update(row.keys())

    keys.discard("timestamp")
    return ["timestamp", *sorted(keys)]


def write_rows(path: Path, rows: Sequence[dict[str, str]]) -> None:
    if not rows:
        # Nothing to write, but ensure the directory exists.
        path.parent.mkdir(parents=True, exist_ok=True)
        return

    fieldnames = determine_columns(rows)
    normalized_rows = [
        {column: row.get(column, "") for column in fieldnames} for row in rows
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_rows)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    entries = load_entries(args.inputs)
    existing_rows, _ = read_existing_rows(args.output)
    merged_rows = merge_rows(existing_rows, entries)
    write_rows(args.output, merged_rows)

    appended = len(merged_rows) - len(existing_rows)
    print(f"Wrote {appended} entr{'y' if appended == 1 else 'ies'} to {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
