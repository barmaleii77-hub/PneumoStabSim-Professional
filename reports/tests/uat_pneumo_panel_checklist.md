# UAT Checklist — Pneumo Interaction Panel

## Scope
- Refactored pneumatic panel validation flows
- Receiver geometry/volume sync behaviours
- Dialog feedback for validation outcomes

## Environment
- Platform: Linux container (Qt offscreen)
- Build: develop branch snapshot
- Test data: default pneumatic presets via `PanelPresetManager`

## Checklist
1. **Validation button (errors)**
   - [x] With invalid receiver limits, pressing **Проверить** shows critical dialog containing limit hints.
2. **Validation button (warnings)**
   - [x] With only throttle diameters out of range, pressing **Проверить** shows warning dialog and no critical errors.
3. **Manual vs geometric volume modes**
   - [x] Switching modes recalculates volume and updates receiver gauge instantly.
4. **History/undo integration**
   - [x] Undo/redo maintains volume mode and valve options without desync.
5. **Preset persistence**
   - [x] Saving defaults stores snapshot and reloading presets keeps validation state clean.

## Outcome
- All checklist items passed in the current build. Validation dialogs now align with state manager findings and prevent silent failures.
