# Quality Dashboard Aggregation

The renovation master plan requires daily aggregation of automated quality
signals (linting, type checks, tests, coverage).  This document describes the
`tools.quality.report_metrics` helper and the expected data pipeline feeding the
CSV dashboard stored in `reports/quality/dashboard.csv`.

## Data Sources

Each metrics snapshot is described by a JSON document with the following
contract:

```json
{
  "timestamp": "2025-10-30T12:30:45Z",
  "lint": {"duration_seconds": 12.4, "issues": 0},
  "typecheck": {"duration_seconds": 18.1, "errors": 0},
  "pytest": {"duration_seconds": 95.0, "tests": 142, "failures": 0, "flaky": 1},
  "coverage": {"percent": 79.6}
}
```

- `timestamp` **must** be an ISO 8601 string (UTC recommended). Duplicate
  timestamps are ignored to prevent accidental replays.
- Nested objects are flattened using underscore-separated keys, producing
  columns like `lint_duration_seconds` and `pytest_failures`.
- Arrays or complex values are JSON-encoded before being stored in the CSV.

## CLI Usage

The aggregator accepts one or more input files.  Each file can contain either a
single metrics dictionary or a list of dictionaries.  Invoke the helper via the
Makefile or directly with Python:

```bash
python -m tools.quality.report_metrics \
  --input reports/quality/2025-10-30.json \
  --input reports/quality/2025-10-31.json \
  --output reports/quality/dashboard.csv
```

When the destination CSV already exists the command appends new rows and
expands the header to include any previously unseen metrics.  Historical rows
are padded with empty values so downstream analytics can rely on a stable
schema.

## Automation Hook

- Schedule the CLI from the nightly CI workflow after `make check` finishes.
- Store raw JSON snapshots under `reports/quality/<YYYY-MM-DD>.json` so the
  aggregator can be rerun for audit purposes.
- Use the generated CSV as the data source for dashboards or notebooks tracking
  lint duration, mypy errors, flaky tests, and coverage trends.

## Next Steps

- Wire the script into the `nightly.yml` workflow (Phase 4 deliverable).
- Generate visualisations in the upcoming engineering health report and link
  them back to this document for traceability.
