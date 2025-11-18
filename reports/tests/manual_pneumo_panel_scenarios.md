# Manual Scenarios — Pneumo Panel Validation

| ID | Scenario | Steps | Expected Result | Status |
|----|----------|-------|-----------------|--------|
| MP-01 | Critical validation path | 1) Set receiver limits to negative values via developer console. 2) Press **Проверить**. | Critical dialog lists limit violations; no warning/info dialogs. | ✅ |
| MP-02 | Warning-only path | 1) Configure `throttle_stiff_dia` to 12mm. 2) Press **Проверить**. | Warning dialog lists diameter range notice; no critical dialog. | ✅ |
| MP-03 | Mode switch resilience | 1) Toggle `volume_mode` between MANUAL and GEOMETRIC. 2) Adjust diameter/length. | Receiver gauge and emitted volume stay in sync; no stale warnings. | ✅ |
| MP-04 | Preset restore stability | 1) Save defaults. 2) Reset panel. 3) Reapply saved preset. | Restored values validated without errors; history stack intact. | ✅ |
| MP-05 | Batch sync behaviour | 1) Apply external patch with mixed volume/valve values. 2) Validate. | Validation reports any range violations; UI fields reflect clamped values. | ✅ |

**Notes:**
- Tests executed with `QT_QPA_PLATFORM=offscreen` and `PSS_SUPPRESS_UI_DIALOGS=1` to avoid modal blocking.
- No regressions observed in telemetry bridges or graphics payloads during validation interactions.
