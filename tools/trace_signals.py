#!/usr/bin/env python3
"""Diagnostic utility for inspecting signal trace logs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, List
from collections.abc import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect logs/signal_trace.jsonl entries"
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("logs/signal_trace.jsonl"),
        help="Path to the signal trace log file",
    )
    parser.add_argument(
        "--signal", help="Filter by signal name (supports substring matching)"
    )
    parser.add_argument("--source", help="Filter by source label")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of entries to display (0 = unlimited)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print aggregated counts per signal instead of detailed entries",
    )
    parser.add_argument(
        "--since",
        help="Only include entries after this ISO timestamp (YYYY-MM-DD or full ISO format)",
    )
    return parser.parse_args()


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if len(value) == 10:
            return datetime.fromisoformat(value)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        raise SystemExit(f"Invalid --since timestamp: {value}")


def iter_entries(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Signal trace log not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON line in {path}: {exc}") from exc


def format_payload(payload: Any, *, max_len: int = 160) -> str:
    try:
        text = json.dumps(payload, ensure_ascii=False)
    except TypeError:
        text = repr(payload)
    if max_len and len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def print_entries(entries: list[dict[str, Any]], limit: int) -> None:
    if limit > 0:
        entries = entries[-limit:]
    for entry in entries:
        timestamp = entry.get("timestamp", "?")
        signal = entry.get("signal", "?")
        source = entry.get("source", "?")
        payload = format_payload(entry.get("payload"))
        print(f"{timestamp} {signal} [{source}] -> {payload}")


def print_summary(entries: Iterable[dict[str, Any]]) -> None:
    counter = Counter(entry.get("signal", "?") for entry in entries)
    for signal, count in counter.most_common():
        print(f"{signal:<40} {count:>6}")


def main() -> None:
    args = parse_args()
    since_ts = parse_timestamp(args.since)

    filtered: list[dict[str, Any]] = []
    for entry in iter_entries(args.file):
        if args.signal and args.signal not in entry.get("signal", ""):
            continue
        if args.source and args.source != entry.get("source"):
            continue
        if since_ts:
            try:
                entry_ts = datetime.fromisoformat(
                    entry.get("timestamp", "").replace("Z", "+00:00")
                )
            except Exception:
                continue
            if entry_ts < since_ts:
                continue
        filtered.append(entry)

    if args.summary:
        print_summary(filtered)
    else:
        print_entries(filtered, args.limit)


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()
