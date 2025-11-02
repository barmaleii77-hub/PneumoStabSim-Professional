# Runtime Graphics Synchronization Failures — Log Analysis

## Context
- **Target entity**: GitHub Copilot
- **Latest autonomous checks**: `lint`, `mypy`, `qmllint`, `pytest`, and `trace` all pass.
- **Manual scenario run**: exits with code `0`; all batched acknowledgements (`ack`) are visible in the console.
- **Issue scope**: anomalies appear exclusively in runtime logs (`logs/*`) despite healthy preflight checks.

## Observations from Graphics Session Logs
- Session files (`logs/graphics/session_*.jsonl`) consistently report **31–43 events** per run with a sync rate of roughly **72–74 %**, leaving **8–12 events** marked as `failed` or `pending`.
- The failed events concentrate in the **`environment.environment_batch`** and **`threeD.threeD_batch`** categories, with only occasional hits on `lighting`/`quality`. A single `pending` entry usually appears for `unknown.unknown`, representing an early event that never receives `applied_to_qml` before auto-timeout (~5 s).
- **Payload anomalies**:
  - Batched payloads intentionally carry both `ibl_source` and the legacy `iblSource` so that newer Python code and legacy QML handlers remain interoperable. The values still need to be normalised to avoid drift while we clean up duplicate dispatches.
  - Duplicate `environment_batch`/`threeD_batch` payloads are emitted within the same second, signalling redundant dispatch or race conditions in debouncing logic.
- Consequence: High-level handlers still print `✅ QML updated`, but the analytics pipeline marks individual parameter updates as `failed` because the underlying QML work item never succeeds.

## IBL Subsystem Logs
- `logs/ibl/ibl_signals_*.log` hold **1–2 INFO events** without warnings or errors.
- HDR source initialization and swaps complete normally; no correlation with the graphics sync failures.

## System Runtime Log (`logs/run.log`)
- Dozens of repeating shader compilation errors per session (`"ERROR: :47: '' : compilation terminated"`, followed by `"2 compilation errors. No code generated."`). Totals range between **43 and 91 errors** for the monitored runs. The leading line number refers to the generated GLSL; enable `QT_DEBUG_SHADERS=1` to capture the expanded shader source for correlation.
- Error bursts align with the timestamps of `environment`/`threeD` batch processing, meaning shader compilation aborts prevent those batches from applying.
- Recent git history shows modifications around **`assets/qml/effects/FogEffect.qml`** and **`assets/qml/effects/PostEffects.qml`**, aligning with the failures in Qt Quick 3D’s material pipeline.

## Root Cause Assessment
1. **Primary blocker — QML/Shader compilation failures**
   - The graphics engine aborts material compilation, so batched environment and 3D updates cannot finalize, yielding the persistent `failed` statuses in graphics session logs.
2. **Secondary destabilizers — payload drift and duplication**
   - Maintaining both `iblSource` and `ibl_source` is required for compatibility, but the normalisation logic must guarantee that both keys expose the same path while duplicate payloads are eliminated.
   - Duplicate batch payloads suggest the dispatcher replays stale updates, compounding the observed failure count and introducing `pending` entries when acknowledgements race each other.

## Recommended Next Actions
1. **Fix shader compilation regressions**
   - Revisit `FogEffect.qml` and `PostEffects.qml` (and any adjacent Qt Quick 3D materials) to eliminate syntax or compatibility issues introduced in recent commits. Validate with `qmllint` and an instrumented run to ensure `run.log` is clean.
2. **Document and enforce IBL payload normalisation**
   - Keep emitting both keys for compatibility, but ensure the canonical `ibl_source` value propagates to `iblSource` and add validation that rejects divergent pairs.
3. **Debounce or deduplicate batch dispatch**
   - Instrument `environment_batch` and `threeD_batch` producers to ensure each logical change maps to a single dispatch. A monotonic sequence ID in the session log can aid post-run reconciliation.
4. **Strengthen monitoring**
   - Extend the runtime analyzer to cross-link console ACKs with QML-level application results, highlighting cases where a handler reports success while the parameter-level update fails.

Addressing the shader compilation loop should immediately improve the sync rate, while schema cleanup and deduplication will stabilize telemetry and prevent regressions once the compilation errors are resolved.
