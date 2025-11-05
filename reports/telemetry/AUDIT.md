# Telemetry Audit (2025-03-07)

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
   `event`, `timestamp`, and `payload`. The schema version was previously
   implicit; analytics tooling now records it explicitly so consumers can evolve
   safely.
2. **Concurrency guarantees** – `TelemetryRouter` already guards writes with an
   `RLock`; no race conditions were observed. Documentation should emphasise
   JSON Lines ordering semantics.
3. **Operational gaps** – The project lacked an exporter/ETL utility, making it
   difficult to ingest telemetry into analytics pipelines or external storage.

## Actions taken

- Defined a stable event schema (`telemetry_event_v1`) with validation helpers
  used by the exporter and analytics pipeline.
- Added `tools/telemetry_exporter.py` to convert telemetry archives to compact
  JSON or (optionally) Apache Parquet.
- Provisioned an ETL entry point (`make telemetry-etl`) that materialises
  aggregate dashboards under `reports/analytics/`.

## Next steps

- Deploy the exporter as a scheduled job to gather telemetry snapshots.
- Capture anonymised session identifiers when the runtime exposes them so that
  retention policies can be enforced downstream.
