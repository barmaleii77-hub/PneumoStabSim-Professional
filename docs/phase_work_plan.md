# Phase 3 UI & Graphics Execution Plan

## Context and Constraints
- Follow the master roadmap commitments in `docs/RENOVATION_MASTER_PLAN.md`, especially the five release pillars (performance, rendering fidelity, configuration determinism, automated quality gates, documentation parity) and the repository hygiene rules (branch governance, encoding normalisation, Conventional Commits, `make check` as the default pre-commit gate).
- Phase 3 focuses on stabilising the Qt Quick 3D front-end (camera ergonomics, materials, panel modernisation, diagnostics, and accessibility). All deliverables must leave the existing Qt 6.10 + Python 3.13 toolchain untouched, reuse `src/core/settings_service.py`/`src/common/settings_manager.py` abstractions, and avoid introducing new ad-hoc entrypoints.
- UI changes must maintain dual-language support (assets under `assets/i18n/`) and surface every graphics-impacting parameter through the modular panels per the transparency mandate.

## Phase Objectives Recap
- **Camera & Scene Interaction:** configurable orbit controller presets, constrained auto-fit behaviour, and a diagnostics HUD exposing live camera metrics.
- **Material & Lighting Fidelity:** audited material definitions, standardised skybox orientation, HDR tonemapping presets with automated validation.
- **Panel Modernisation:** reusable layout primitives, preset manager with undo/redo, contextual guidance wired to documentation.
- **Animation & Performance:** modern Qt animation primitives, GPU profiler overlay, regression benchmarks against Phase 0 baselines.
- **Accessibility & Localisation:** refreshed translation packs, high-contrast theming, keyboard navigation coverage.

## Prioritised Subtasks & Acceptance Checks
| Priority | Work Item | Key Modules / Assets | Acceptance & Tests |
| --- | --- | --- | --- |
| P0 | Finalise orbit controller presets and HUD bindings, ensuring settings persistence and HUD toggle wiring. | `src/ui/scene_bridge.py`, `src/ui/hud.py`, `assets/qml/controls/CameraStateHud.qml`, `config/orbit_presets.json`, `src/core/settings_service.py` | `make check`; `pytest tests/ui/test_qml_bridge.py::test_camera_hud_context`; targeted smoke: `pytest tests/ui/test_graphics_scene_quality_tabs.py::test_camera_controls_signals`; update diagnostics snapshot in `reports/ui/camera_hud.md`. |
| P0 | Skybox alignment & material audit automation; enforce tonemapping presets surfaced via panels. | `tools/render_checks/validate_hdr_orientation.py`, `assets/qml/panels/lighting`, `config/baseline/materials.json`, `src/ui/panels/lighting` | `make check`; `pytest tests/ui/test_environment_tab_ibl_dependencies.py`; regenerate validation artefact `reports/performance/hdr_orientation.md`; store updated preset screenshots under `tests/ui/screenshots/`. |
| P1 | Modular panel preset manager with undo/redo and settings sync telemetry. | `src/ui/panels`, `src/ui/panels_accordion.py`, `assets/qml/panels/`, `src/common/settings_manager.py`, `src/core/settings_service.py` | `make check`; `pytest tests/ui/test_signals_router_connections.py`; `pytest tests/settings/test_persistence.py`; document workflow in `docs/ui/panel_modernization_report.md`. |
| P1 | Animation loop modernisation and GPU profiler overlay toggle integrated into diagnostics panel. | `assets/qml/animations/`, `src/ui/qml_host.py`, `tools/performance_monitor.py`, `src/diagnostics` | `make check`; `pytest tests/ui/test_effect_shaders.py::test_profiler_toggle_available`; run `python tools/performance_monitor.py --scenario phase3` and archive results in `reports/performance/ui_phase3_profile.json`. |
| P2 | Accessibility and localisation hardening (high-contrast theme, keyboard nav, i18n sync). | `assets/qml/themes/`, `assets/i18n/`, `tools/accessibility/audit_qml.py`, `src/ui/widgets` | `make check`; `pytest tests/ui/test_main_qml_structure.py::test_accessibility_attributes`; run `python tools/accessibility/audit_qml.py --report reports/ui/accessibility_audit.md`; refresh `.ts` packs via `make qmllint` + `lrelease` workflow. |

## Execution Sequence
1. **Stabilise camera interaction stack (P0):** align presets, HUD, and persistence first to unblock downstream diagnostics and usability reviews.
2. **Close rendering fidelity gaps (P0):** iterate on HDR alignment and materials with automated checks to lock the visual baseline before panel polish.
3. **Deliver preset-aware panel UX (P1):** refactor panels once the camera/material baselines hold, ensuring telemetry hooks and undo/redo readiness.
4. **Upgrade animation & diagnostics stack (P1):** modern animations and GPU profiler overlay rely on stable panel toggles and settings instrumentation.
5. **Complete accessibility & localisation pass (P2):** run once UI behaviours are final to avoid re-translating evolving copy.

## Tooling & Test Cadence
- Default gate: `make check` (aggregates `ruff`, `mypy`, `pytest`, `qmllint`). Execute before every commit and capture logs in `reports/tests/phase3_<date>.log`.
- Scenario-specific runners:
  - Camera & panel UI: `pytest tests/ui/test_qml_bridge.py tests/ui/test_signals_router_connections.py`.
  - Settings persistence: `pytest tests/settings/test_persistence.py`.
  - Performance baselines: `python tools/performance_monitor.py --scenario phase3`.
  - Accessibility audit: `python tools/accessibility/audit_qml.py --report reports/ui/accessibility_audit.md`.
- QML validation: `make qmllint` when modifying `assets/qml/` or `src/ui/qml` to keep schema compliance.

## Expected Artefacts & Documentation Updates
- Updated diagnostics snapshots in `reports/ui/` (camera HUD, accessibility audit) and performance profiles under `reports/performance/`.
- Refreshed translation packs in `assets/i18n/` plus change log entries in `docs/ui/accessibility_log.md` and `docs/ui/panel_modernization_report.md`.
- Continuous updates to this plan and `docs/RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md` to reflect completed checkpoints and remaining risks.
