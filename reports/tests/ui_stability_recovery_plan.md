# UI stability recovery plan (QML/graphics)

## Context
The latest `scripts/testing_entrypoint.py` run still reports failing UI cases related to QML property mismatches, Python↔QML bridge safety checks, and formatting blockers. Existing diagnostics in `reports/tests/test_failures_20251118.md` highlight the recurring themes (missing `fogDensity`/`ssaoEnabled` properties, unsafe `SignalInstance.receivers` access, and `ruff format` violations).

## Objectives
- Restore QML scene loading by aligning `SceneEnvironmentController` bindings with available properties.
- Harden bridge-side signal dispatch without using unsupported PySide6 APIs.
- Clear formatting blockers so `make check` proceeds to execution.
- Validate fixes across Linux (offscreen, software rendering) and Windows (desktop) matrices.

## Action plan
1. **QML property alignment**
   - Audit `assets/qml/main.qml` bindings for `fogDensity` and `ssaoEnabled`.
   - If missing on the controller, add properties to `assets/qml/effects/SceneEnvironmentController.qml` backed by existing fog/SSAO defaults.
   - Re-run `qmllint` and UI smoke tests to confirm successful load without fallback activation.

2. **Signal safety in bridge**
   - Replace `SignalInstance.receivers` checks with a supported guard (e.g., `typeof signal === "function"` and optional try/catch around `connect`/`emit`).
   - Add structured logging in `src/ui/main_window.py` (or the relevant bridge module) for missing handlers instead of raising.
   - Cover the change with a focused pytest case in `tests/` that simulates missing receivers.

3. **Formatting & linting**
   - Run `ruff format tests/test_ibl_logger.py` to satisfy the formatter gate.
   - Execute `make check` (Linux) and `python scripts/testing_entrypoint.py` with Windows flags to ensure cross-platform compliance.

4. **Regression validation**
   - Capture updated results in `reports/tests` (pytest JUnit, qmllint logs, entrypoint log with `[entrypoint] Test pipeline completed successfully`).
   - Verify settings schema integrity and IBL manifest via `make verify` if touched.

## Dependencies & environment
- Python 3.13 via `uv`; ensure `make uv-sync` succeeds before running checks.
- Qt Quick 6.10 with software backend (`QT_QPA_PLATFORM=offscreen`, `QT_QUICK_BACKEND=software`, `LIBGL_ALWAYS_SOFTWARE=1`).
- On Windows hosts, mirror the entrypoint through `python -m tools.ci_tasks verify` after `scripts/setup_dev.py`.

## Exit criteria
- `make check` passes on Linux container.
- `scripts/testing_entrypoint.py` ends with green state on both platforms.
- No skipped/xfail regressions remain; all previously failing UI tests are addressed.
