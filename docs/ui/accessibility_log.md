# Accessibility Hardening Log

## 2025-11-04 – High-contrast palette expansion and shortcut surfacing

- Refreshed the high-contrast palette with clearer outline, selection, and
  danger tones while publishing widget-specific accessibility metadata so
  automation can match colours to control roles.
- Extended the `Knob` and `RangeSlider` widgets to expose explicit semantic
  roles, enumerated keyboard shortcuts, and aggregated descriptions for screen
  readers.
- Localised the new guidance strings (EN/RU) and exported the compiled
  translation packs after validating the updated QML with `qmllint`.
- Captured a new accessibility audit report and verified the targeted widget
  tests to ensure the additional metadata is exercised in CI.

## 2025-03-08 – High-contrast theme and widget metadata refresh

- Added the dedicated `assets/qml/themes/` module with singleton palette and
  metadata files describing the high-contrast theme. The metadata now exposes
  a documented keyboard shortcut (`Ctrl+Alt+H`) and WCAG contrast metrics so it
  can be surfaced by automation and UX documentation.
- Instrumented Python widgets (`Knob`, `RangeSlider`) with explicit accessible
  names, descriptions, and keyboard shortcuts. Screen readers can now announce
  the control purpose, current bounds, and available shortcuts for fine-grained
  adjustments.
- Regenerated localisation strings (EN/RU) covering the new accessibility copy
  to keep the UI bilingual. Shortcut hints, descriptive text, and the theme
  metadata are translated to match existing panel terminology.
- Captured an updated accessibility audit report via
  `python tools/accessibility/audit_qml.py --report reports/ui/accessibility_audit.md`
  and verified the new `tests/ui/test_main_qml_structure.py::test_accessibility_attributes`
  guard.

## Next steps

- Integrate the high-contrast theme toggle into the runtime UI once the settings
  panel refactor lands.
- Extend the audit script to validate custom keyboard navigation handlers inside
  dynamic loaders (panels, dialogs) to ensure parity with manual QA.
