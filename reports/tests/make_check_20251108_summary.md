# Make Check Run — 2025-11-08 16:24 UTC

- **Command:** `make check`
- **Outcome:** ❌ Failed during unit test stage (`pytest tests/unit`) with 10 failing tests and 14 skipped tests.
- **Key failures:**
  - Structlog JSON payload assertions (`tests/unit/diagnostics/logging/test_structlog_json_events.py`, `test_unicode_output.py`).
  - Runtime kinematics lever geometry integration (`tests/unit/runtime/test_physics_steps.py` multiple scenarios failing due to missing `LeverGeom.angle_to_displacement`).
  - Receiver volume logging keyword mismatch (`tests/unit/runtime/test_receiver_volume_updates.py::test_set_receiver_volume_updates_pneumatic_and_gas_network`).
  - Version string mismatch in master plan (`tests/unit/test_version_consistency.py::test_release_version_is_in_sync_with_documentation`).
- **Artifacts:**
  - Full console log: `reports/tests/make_check_20251108_162420.log`.
  - Pytest JUnit report: `reports/tests/unit.xml` (overwritten with latest results).
  - Shader diagnostics summary: `reports/tests/shader_logs_summary.json`.
- **Notable warnings:**
  - `qmllint` flagged numerous unqualified accesses and missing signals across telemetry and scene environment controllers.
  - `tools/analyze_logs.py` reported missing `logs/graphics/session_*.jsonl` inputs.

Please reference the linked artifacts for full traceability of the failure context.
