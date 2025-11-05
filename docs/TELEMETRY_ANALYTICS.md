# Telemetry Analytics Pipeline

This document summarises the telemetry event schema, exporter tooling, and
standard analytics workflow introduced in March 2025.

## Event schema

Telemetry events are emitted by `src/telemetry/tracker.py` using the
`telemetry_event_v1` schema. Each record is stored as a JSON object on a single
line inside `reports/telemetry/*.jsonl`.

| Field           | Type     | Description |
| --------------- | -------- | ----------- |
| `schema_version`| string   | Schema identifier (`telemetry_event_v1`). |
| `channel`       | string   | Logical channel (`user`, `simulation`, etc.). |
| `event`         | string   | Event name recorded by the application. |
| `timestamp`     | datetime | ISO 8601 timestamp (UTC). |
| `payload`       | object   | Arbitrary metadata supplied by the caller. |

All timestamps are normalised to UTC when ingested. Additional fields can be
introduced in later schema revisions; consumers should gate on the
`schema_version` field.

## Exporter usage

`tools/telemetry_exporter.py` reads the JSON Lines artefacts and can produce
consolidated exports:

```bash
python tools/telemetry_exporter.py export --format json --output reports/analytics/telemetry_events.json
python tools/telemetry_exporter.py export --format parquet --output /tmp/events.parquet  # Requires pyarrow
```

The exporter validates every record and collects diagnostics for malformed
entries. Use `--strict` to abort when encountering invalid payloads.

## Aggregations and ETL

Aggregated metrics (event counts per channel, per name, and by day) are written
to `reports/analytics/telemetry_aggregates.json` via the `aggregate` command:

```bash
python tools/telemetry_exporter.py aggregate --output reports/analytics/telemetry_aggregates.json
```

This command powers the dedicated Makefile target:

```bash
make telemetry-etl
```

Running the target performs a JSON export and refreshes the aggregate report in
one step. The aggregate file includes inventory metadata so downstream notebooks
can detect missing files or parse anomalies quickly.

## Example analysis

The JSON export is optimised for lightweight analysis in tools such as pandas or
DuckDB. Example pandas snippet:

```python
import json
from pathlib import Path

with Path("reports/analytics/telemetry_events.json").open(encoding="utf-8") as handle:
    events = json.load(handle)

user_events = [event for event in events if event["channel"] == "user"]
print(f"User-facing actions recorded: {len(user_events)}")
```

When PyArrow is available the Parquet export allows the same dataset to be
queried efficiently in analytics warehouses.
