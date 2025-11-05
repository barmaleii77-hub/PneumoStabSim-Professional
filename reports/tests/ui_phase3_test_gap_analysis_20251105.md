# Phase 3 UI & Graphics Test Coverage – Gap Analysis (2025-11-05)

## Scope & Method
- Reviewed existing automated tests under `tests/ui/`, `tests/system/`, `tests/integration/`, and related helpers.
- Cross-referenced coverage against the Phase 3 checklists in `docs/RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md`.
- Focused on training preset panels, camera/scene interactions, panel modernization workflows, and diagnostics overlays.

## Current Coverage Snapshot
- **Training presets**: Only scenario-level assertions in `tests/scenarios/test_training_presets.py`. No direct QML bridge verification.
- **Graphics panels**: Multiple structural tests exist (`test_graphics_scene_quality_tabs.py`, `test_environment_tab_ibl_dependencies.py`, etc.), but none exercise user flows through preset-driven panels.
- **Simulation integration**: `tests/simulation/` directory absent; simulation flows indirectly tested via settings utilities only.
- **Diagnostics overlays**: No automated validation for camera HUD, profiler toggles, or diagnostics panel visibility.
- **Accessibility/localisation**: Structural checks for QML files exist, yet no tests assert runtime theme toggles or translation bindings.

## Gap Matrix (vs Phase 3 Checklist)
| Plan Area | Checklist Items | Existing Automation | Identified Gap |
| --- | --- | --- | --- |
| Camera & Scene Interaction | Orbit presets, auto-fit regression tests, camera HUD diagnostics | Structural QML checks only | Need pytest-qt scenarios driving orbit controller bindings and HUD toggles. |
| Material & Lighting Fidelity | HDR preset validation, material audits, tonemapping toggles | Shader fallback/unit tests present | Missing interaction tests validating preset buttons and HDR toggles via bridge/API. |
| Panel Modernization | Modular panels, preset manager, undo/redo, inline docs | No end-to-end preset flow tests | Need Training Panel integration tests exercising `TrainingPresetBridge` + panel QML. |
| Animation & Performance | GPU profiler overlay, animation loop replacements | No automated coverage | Require simulation harness to assert overlay toggles & performance metrics wiring. |
| Accessibility & Localization | High-contrast theme, bilingual strings, keyboard navigation | Static checks for presence of themes | Lacking runtime assertions for theme switching and translation IDs. |

## Immediate Actions
1. **Introduce pytest-qt integration tests** for the training panel, validating bridge signals, scenario metadata alignment, and selection flows.
2. **Establish reusable fixtures** to spin up an isolated settings environment (`SettingsService` + `SettingsManager`) and a light-weight simulation harness to support UI automation.
3. **Document coverage status** in the Phase 3 execution log and attach `make check` artefacts for traceability.

## Follow-up Opportunities
- Extend the simulation harness to cover diagnostics overlay toggles once the GPU profiler bindings stabilise.
- Add keyboard navigation smoke tests for the modular panels after focus-chain refactors are merged.
- Capture HUD regression screenshots under `tests/ui/screenshots/` for orbit controller presets to complete the Phase 3 exit criteria.
