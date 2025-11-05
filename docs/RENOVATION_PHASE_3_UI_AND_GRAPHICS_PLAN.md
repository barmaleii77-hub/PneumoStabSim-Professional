# Renovation Phase 3 – UI and Graphics Plan

## Objectives
- Deliver a cohesive Qt Quick 3D interface with ergonomic controls and comprehensive parameter exposure.
- Align rendering pipeline for consistent lighting, material fidelity, and animation performance.
- Build diagnostics tooling to visualize pipeline state and performance metrics in real time.

## Entry Criteria
- Architecture refactor merged with stable APIs.
- Baseline performance metrics from Phase 0 available for comparison.
- Design mock-ups for panels and overlays approved.

## Work Breakdown Structure
1. **Camera & Scene Interaction**
   - Implement configurable orbit controller with presets stored in settings.
   - Restrict auto-fit behaviour to double-click interactions; add regression tests.
   - Provide camera state HUD for debugging (position, distance, damping).
2. **Material & Lighting Fidelity**
   - Audit material definitions; normalize IOR, transmittance, and attenuation per design specs.
   - Align skybox orientation by standardizing cube map transforms; add automated validation script.
   - Integrate HDR tonemapping presets accessible from UI.
3. **Panel Modernization**
   - Build modular panels with reusable layout primitives (grid, collapsible sections).
   - Implement preset manager (save/load, reset to defaults) with undo/redo support.
   - Add contextual tooltips and inline documentation linking to docs.
4. **Animation & Performance**
   - Replace legacy animation loops with `NumberAnimation` or `Animator` classes tuned for smooth playback.
   - Integrate GPU profiler overlay toggled via diagnostics panel.
   - Run performance regression tests comparing against Phase 0 baselines.
5. **Accessibility & Localization**
   - Generate English/Russian translation files; set up Qt Linguist pipeline.
   - Ensure high-contrast theme option and keyboard navigation coverage.

## Deliverables
- Refined QML component library with documentation in `docs/ui/`.
- Performance report highlighting frame time improvements and resolved rendering bugs.
- Translation packs and accessibility checklist signed off by QA.

## Exit Criteria
- UI review sign-off by product/design stakeholders.
- Performance metrics meet or exceed baseline targets (frame time, memory usage).
- No unresolved critical UI/graphics defects logged in issue tracker.

## Milestones & Timeline
- **Sprint 14:** Finalise orbit controller presets, land instrumentation for camera
  HUD, and update settings schema bindings.
- **Sprint 15:** Complete material/lighting audits with automated validation
  scripts and baseline HDR comparisons stored under `reports/performance/`.
- **Sprint 16:** Ship modular panel refactor with preset manager MVP and
  regression tests.
- **Sprint 17:** Integrate diagnostics overlays (profiler, performance HUD) and
  run regression benchmarks vs Phase 0 baselines.
- **Sprint 18:** Accessibility and localisation hardening, documentation pass,
  and exit review readiness.

## Dependencies
- Stable service container APIs from Phase 2 to expose settings and diagnostics
  hooks.
- Updated settings control matrix and schema exports for binding validation.
- Asset pipeline availability for HDR and material reference files.

## Risk Register
| Risk | Impact | Probability | Mitigation |
| --- | --- | --- | --- |
| Orbit controller tuning stalls due to missing device profiles | High | Medium | Capture per-device telemetry early, reuse engineering presets stored in `config/orbit_presets.json`. |
| Material audits blocked by HDR asset licensing | Medium | Low | Coordinate with art pipeline lead; ensure legal review before importing new HDR files. |
| Panel refactor introduces regression in settings sync | High | Medium | Leverage pytest-qt integration tests and trace logging before merging. |

## Metrics & Evidence
- Frame time (<16.7 ms target) recorded via Qt profiler exports in
  `reports/performance/ui_phase3_*.json`.
- Automated Qt Quick profiler runs via `make profile-render` with
  complementary HTML summaries and CI threshold checks documented in
  `docs/performance.md`. Baseline envelopes are stored in
  `reports/performance/baselines/` and validated with `make profile-validate`.
- UI regression screenshots stored under `tests/ui/screenshots/` with diff
  approvals.
- Accessibility checklist reviewed using `tools/accessibility/audit_qml.py` with
  sign-off captured in `docs/ui/accessibility_log.md`.

## RACI Snapshot
- **Responsible:** UI lead, graphics engineer.
- **Accountable:** Design lead.
- **Consulted:** Tech lead, QA lead.
- **Informed:** Product representative, support lead.

## Execution Log
Track panel completion status, performance runs, and localization updates here.

### 2025-09-06 – Camera HUD diagnostics overlay
- Implemented `CameraStateHud.qml` overlay with live camera metrics toggled via Ctrl+H.
- Bound the HUD visibility to `diagnostics.camera_hud` settings and exposed defaults through the QML context payload.

### 2025-09-18 – Material calibration and HDR validation
- Re-tuned glass and metal presets in `config/baseline/materials.json` using calibrated IOR and attenuation references.
- Automated skybox alignment validation via `tools/graphics/validate_hdr_orientation.py`, exporting the inaugural
  report to `reports/performance/hdr_orientation.md` for design review sign-off.

### 2025-09-24 – Modular panel MVP landed
- Delivered the first iteration of the preset-aware panel stack under `assets/qml/panels/` with shared layout primitives.
- Introduced `SettingsSyncController` bindings to surface change telemetry in the diagnostics overlay and documented
  the workflow in `docs/ui/panel_modernization_report.md`.

### 2025-10-20 – Static load equilibrium for suspension visuals
- Normalised rigid-body static wheel loads so the scene holds a neutral pose without drift.
- Added regression tests validating the equilibrium to keep render diagnostics reliable.

### 2025-11-05 – Training preset bridge regression coverage
- Captured Phase 3 UI coverage gaps in `reports/tests/ui_phase3_test_gap_analysis_20251105.md`, aligning
  outstanding checklist items with the existing automation inventory.
- Added pytest-qt scenarios validating `TrainingPresetBridge` signal/slot wiring and the
  `TrainingPanel.qml` interactions against scenario metadata from `tests/scenarios/`.
- Introduced reusable fixtures for isolated settings/service setup and a simulation harness,
  and published `make check` evidence in `reports/tests/make_check_20251105.md`.

### 2025-11-12 – Shader profile validation automation
- Added `tools/validate_shaders.py` to assert that every desktop effect has matching `_fallback`,
  `_fallback_es`, and `_es` profiles with the expected GLSL `#version` directives.
- Integrated the validator into `make check` so CI fails when GLES variants are missing and
  passes once the corresponding shader files are restored.

### 2025-11-18 – Performance profiling automation
- Extended `tools/performance_monitor.py` with CPU time and optional GPU metrics plus HTML report export.
- Added `tools/performance_gate.py` and Make targets (`profile-render`, `profile-validate`) to standardise
  Qt Quick profiling workflows.
- Wired the new gate into `.github/workflows/ci.yml` so PRs fail when metrics breach the Phase 3 baseline envelope.

