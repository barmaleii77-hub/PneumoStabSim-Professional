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

