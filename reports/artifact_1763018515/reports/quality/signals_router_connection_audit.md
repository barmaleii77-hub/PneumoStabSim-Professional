# SignalsRouter Connection Audit

## Summary
- Reviewed `SignalsRouter._connect_simulation_signals` to verify that cross-thread
  connections use `Qt.QueuedConnection`.
- Added unit coverage to lock the behaviour and prevent regressions.
- Implemented an integration scenario that exercises the stabilizer
  synchronisation batch ACK flow with a fully queued connection path.
- Executed the full `make check` gate (lint, type-check, QML lint, targeted
  pytest suite) and the new stabilizer integration test.

## Inspection Notes
- `SignalsRouter` now has explicit test coverage ensuring the simulation bus
  connects `state_ready` and `physics_error` handlers with queued delivery.
- `config/qml_bridge.yaml` already requests queued delivery for the QML
  signals that bridge cross-thread acknowledgements.
- `src/runtime/sim_loop.py` and `src/runtime/state.py` continue to use queued
  connections for physics-thread emissions, matching the router behaviour.

## Test Results
| Command | Outcome | Notes |
| --- | --- | --- |
| `make check` | ✅ | Passed lint, type-check, QML lint, and targeted pytest suites. |
| `pytest tests/integration/test_stabilizer_sync.py -vv` | ✅ | Stabilizer synchronisation scenario succeeds with 100% ACK coverage. |

## Follow-up
- The stabilizer synchronisation scenario now runs under
  `tests/integration/test_stabilizer_sync.py`, providing an automated ACK
  validation check.
