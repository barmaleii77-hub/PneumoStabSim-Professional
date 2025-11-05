# Telemetry Audit (2025-11-05)

This audit reviews the current telemetry capture pipeline and stored artefacts.

## Repository structure

- **Event capture** – Implemented in `src/telemetry/tracker.py`. The module
  provides a thread-safe router that stores telemetry in JSON Lines files under
  `reports/telemetry/`.
- **Stored artefacts** – At the time of the audit no telemetry files are present.
  The directory has been initialised so downstream tooling can rely on a stable
  location.

## Findings

1. **Schema discovery** – The tracker emits dictionaries with `channel`,
   `event`, `timestamp`, and `payload`. Validation logic now lives in
   `src/telemetry/schema.py`, ensuring every consumer enforces identical rules
   and attaches the `telemetry_event_v1` schema version automatically.
2. **Concurrency guarantees** – `TelemetryRouter` continues to guard writes with
   an `RLock`; no race conditions were observed. Documentation now highlights
   JSON Lines ordering semantics for downstream replay.
3. **Operational gaps** – The repository previously lacked a reusable exporter
   or ETL utility. The refreshed `tools/telemetry_exporter.py` consolidates JSON
   and Parquet exports and produces enriched aggregate reports for analytics.

## Actions taken

- Defined a stable event schema (`telemetry_event_v1`) with validation helpers
  in `src/telemetry/schema.py`, re-used by both runtime tracking and analytics
  tooling.
- Enhanced `tools/telemetry_exporter.py` to convert telemetry archives to
  compact JSON or (optionally) Apache Parquet and to publish richer aggregate
  statistics (channel, schema, and per-event breakdowns).
- Provisioned an ETL entry point (`make telemetry-etl`) that materialises
  aggregate dashboards under `reports/analytics/`, including schema and event
  inventories for observability.

## Next steps

- Deploy the exporter as a scheduled job to gather telemetry snapshots.
- Capture anonymised session identifiers when the runtime exposes them so that
  retention policies can be enforced downstream.
