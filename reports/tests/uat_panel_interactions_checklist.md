# UAT checklist — Geometry panel interactions and validation

## Scope
- Geometry options tab interactions (presets, validation, interference toggles)
- Visualisation sync feedback for manual QA during panel review

## Pre-requisites
- Application launched with access to geometry panel
- Default settings loaded; ensure no pending overrides in `config/app_settings.json`

## Scenarios
1. **Run validation with conflicting geometry**
   - Open **Геометрия → Опции**.
   - Intentionally set rod diameters so that they exceed cylinder limits.
   - Click **Проверить**.
   - ✅ Expect critical dialog referencing hydraulic and geometric conflicts.
   - ✅ `validate_requested` emitted in logs and validation hints updated.

2. **Toggle interference checks**
   - Ensure **Проверять пересечения геометрии** is unchecked.
   - Enable the toggle.
   - ✅ Info dialog confirms interference checking enabled.
   - ✅ Warning dialog surfaces near-limit rod diameter guidance.
   - ✅ Geometry payload synced to preview without crashes.

3. **Preset application feedback**
   - Select each preset in the combo box sequentially.
   - ✅ Panel fields refresh without stale values.
   - ✅ Validation still passes with info dialog when no issues remain.

4. **Reset to defaults flow**
   - Modify any option, then click **Сбросить**.
   - Confirm when prompted.
   - ✅ All options revert to defaults; interference toggle returns to default state.
   - ✅ No validation errors triggered immediately after reset.

## Observed results (2025-03-18)
- Validation dialogs align with expectation for conflicting setups.
- Interference toggle triggers real-time validation and warning presentation.
- Preset changes persist via sync controller without regression in UI state.

## Follow-ups
- Capture screenshots for presets once updated HDR assets arrive.
- Add headless preset smoke tests once new presets are published.
