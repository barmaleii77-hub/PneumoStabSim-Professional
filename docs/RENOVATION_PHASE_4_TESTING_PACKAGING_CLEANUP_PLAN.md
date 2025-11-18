# Renovation Phase 4 – Testing, Packaging, and Cleanup Plan

## Objectives
- Achieve comprehensive automated test coverage and integrate quality gates into CI.
- Produce reproducible distributable artifacts for target platforms.
- Remove or archive legacy assets, scripts, and documents while preserving traceability.

## Entry Criteria
- UI and graphics improvements merged with no open P0 defects.
- Testing infrastructure (pytest-qt, mypy, ruff, pyright) configured from Phase 2.
- Packaging toolchain prototypes (PyInstaller/fbs) validated in sandbox.

## Work Breakdown Structure
1. **Test Expansion**
   - Implement missing unit tests for settings manager, service container, and simulation APIs.
   - Add integration suites covering QML bridge (pytest-qt) and CLI entry points.
   - Introduce physics scenario descriptors (`*.test.json`/`*.scene.yaml`) with shared fixtures in `tests/conftest.py` and automate report generation via `tools/run_test_case.py`.
   - Extend graphics/UI regression checks with baseline image comparisons, shader log triage, and pytest-qt workflows that surface indicator states.
   - Configure coverage thresholds (>=85%) enforced in CI.
   - Enforce cross-platform readiness with `tools/cross_platform_test_prep.py` and the `make cross-platform-test` target so Linux и Windows агентов выполняют полный набор без пропусков.
   - Integrate HDR manifest verification into CI via `make hdr-verify`, publishing `reports/quality/hdr_assets_status.json` and `reports/quality/hdr_verify.log` so missing or mismatched assets block releases.
2. **Static Analysis Enforcement**
   - Wire `ruff`, `mypy`, `pyright`, and `qmllint` into pre-commit hooks.
   - Generate baseline reports and track regressions via GitHub Actions artifacts.
3. **Packaging & Distribution**
   - Finalize `scripts/build_release.py` with environment validation and checksum generation.
   - Produce Windows MSI and Linux AppImage artifacts; document signing process if applicable.
   - Draft release checklist in `docs/release/packaging_playbook.md`.
4. **Repository Cleanup**
   - Move archival markdowns into timestamped folders under `archive/` with index file.
   - Remove deprecated solution files (.csproj/.sln) after confirming no longer needed.
     *Status: Clean-up completed December 2025; audit February 2026 reconfirmed no
     tooling depends on `.sln/.csproj/.pyproj`, with `scripts/comprehensive_test.py`
     guarding against regressions.*
   - Consolidate environment scripts and update README references.
5. **Documentation Refresh**
   - Publish MkDocs site updates, including API docs and troubleshooting guides.
   - Ensure diagrams and architecture decision records reference new modules.

### Headless Qt Toggle for Tests and Utilities

- The default Windows workflow now prefers GPU rendering by forcing
  `QSG_RHI_BACKEND=d3d11` whenever `PSS_HEADLESS` is unset. This ensures test and
  application launchers exercise the Direct3D 11 backend unless headless mode is
  explicitly requested.
- Launchers and developer utilities now reuse
  `tools.headless.prepare_launch_environment(...)` so `app.py --test-mode` calls
  inherit the toggle automatically and clean up stale headless overrides.
- Set `PSS_HEADLESS=1` (or pass `--pss-headless` to pytest) to enable
  `QT_QPA_PLATFORM=offscreen` and `QT_QUICK_BACKEND=software` overrides.
- Tests that depend on offscreen rendering should use the `@pytest.mark.headless`
  marker; the fixture automatically applies the headless environment for the
  marked scope.
- Windows scripts such as `scripts/run_tests_ci.ps1` and `run.ps1` respect the
  toggle. Example usage:
  - `set PSS_HEADLESS=1; python -m pytest --pss-headless`
  - `set PSS_HEADLESS=1; .\scripts\run_tests_ci.ps1`
  - `Remove-Item Env:PSS_HEADLESS; .\run.ps1` *(restores GPU/D3D11 rendering)*
- CI pipelines set `PSS_HEADLESS=1` only on Linux runners so Windows smoke and
  integration sweeps continue to initialise Qt Quick 3D with
  `use_qml_3d=true`.
- Launch trace fixtures
  (`reports/quality/launch_traces/2026-03-05_windows-gpu.json` and
  `reports/quality/launch_traces/2026-03-05_windows-headless.json`) document the
  environment deltas for both GPU and headless modes.

## Deliverables
- Passing automated test suite with coverage report stored under `docs/reports/`.
- Signed release artifacts uploaded to internal distribution channel.
- Repository cleanup summary recorded in change log.

## Exit Criteria
- CI pipelines blocking merges on failing tests/linters.
- Release artifacts validated via smoke test on each platform.
- Stakeholders approve archive structure and documentation updates.

## Milestones & Timeline
- **Sprint 19:** Expand automated tests and stabilise coverage thresholds with
  CI gating dry run.
- **Sprint 20:** Integrate static analysis enforcement into pre-commit and CI;
  publish baseline quality dashboard.
- **Sprint 21:** Finalise packaging automation, produce signed installers, and
  document release playbook.
- **Sprint 22:** Execute repository cleanup, archive legacy artefacts, and run
  documentation refresh.

## Dependencies
- Phase 3 UI deliverables to ensure stable surfaces for regression testing.
- Access to signing certificates and secure storage for release credentials.
- Operational agreement on archival taxonomy for legacy documents.

## Risk Register
| Risk | Impact | Probability | Mitigation |
| --- | --- | --- | --- |
| Coverage targets delay merges | High | Medium | Adopt staged thresholds with feature toggles; share dashboard for incremental adoption. |
| Packaging automation blocked by Qt licensing | High | Low | Validate entitlements early with legal and procurement; cache installers to avoid repeated downloads. |
| Cleanup removes needed historical docs | Medium | Medium | Mirror artefacts into `archive/YYYY-MM/` and secure sign-off from documentation lead before deletion. |

## Metrics & Evidence
- Coverage reports exported to `reports/quality/coverage_phase4.json` and linked
  from the master plan.
- Static analysis trend lines tracked in `reports/quality/dashboard.csv`.
- Release artefact checksums stored alongside installers in
  `reports/release/candidate_manifests/`.

## RACI Snapshot
- **Responsible:** QA automation lead, release engineer.
- **Accountable:** Engineering manager.
- **Consulted:** Tech lead, DevOps engineer.
- **Informed:** Support lead, documentation lead.

## Execution Log
Use this section to log coverage milestones, release candidate builds, and cleanup decisions.

### 2025-09-28 – Coverage expansion dry run
- Extended `tests/ui/` suites with new signal propagation cases and enabled provisional 75% coverage gate in `pyproject.toml`.
- Captured the first aggregated coverage report under `reports/quality/coverage_phase4_dry_run.json` for stakeholder review.

### 2025-10-03 – Packaging automation spike
- Assembled the initial `scripts/build_release.py` workflow invoking PyInstaller with Qt plugin caching via `tools/setup_qt.py`.
- Produced unsigned MSI/AppImage artifacts stored in `reports/release/candidate_manifests/2025-10-03/` pending security scan sign-off.

### 2025-10-25 – Redundant file audit baseline
- Executed `python -m tools.audit.redundant_files` to catalogue root-level reports and
  quick-fix scripts for archival triage.
- Published the resulting Markdown and JSON artefacts under
  `reports/cleanup/2025-10-25/` for follow-up actions in the cleanup track.

### 2025-11-05 – Automated physics/UI regression harness
- Finalised hierarchical test layout under `tests/{physics,pneumo,graphics,ui,tools}` with shared fixtures in `tests/conftest.py`.
- Authored JSON/YAML schemas for physics scenarios, added baseline images, and wired CLI utilities (`tools/run_test_case.py`, `tools/collect_qml_errors.py`, `tools/check_shader_logs.py`) to persist artefacts in `reports/tests/`.
- Captured new pytest-qt flows validating indicator feedback and ensured shader/QML diagnostics are harvested for CI publishing.

### 2025-11-08 – Manual make check regression snapshot
- Ran `make check` in the Linux container; execution failed at the unit test stage with 10 failing cases while producing updated coverage metrics.
- Preserved full console output in `reports/tests/make_check_20251108_162420.log` and summarised root causes in `reports/tests/make_check_20251108_summary.md` for triage.
- Shader validation fallback analysis exported to `reports/tests/shader_logs_summary.json`; Pytest JUnit artefact refreshed at `reports/tests/unit.xml`.

### 2025-11-18 – make check rerun with PySide6 QtQuick3D dependencies installed
- Installed missing system libraries (`libgl1`, `libopengl0`, `libxkbcommon0`, `libegl1`) to restore `PySide6.QtQuick3D` imports in the Linux container and reformatted `tests/smoke/test_simulation_flow_ui_smoke.py` with `ruff format`.
- `make check` completed `ruff`, `mypy`, `qmllint`, `bandit`, unit (425) and integration (34) suites successfully; UI/QML batch reported 8 failures (GeometryPanel preset restoration, Canvas animation preview canvas missing, Graphics defaults hydration, two `main.qml` baseline timeouts, PostEffects fallback reset, batch_updates signal exposure, SharedMaterials fallback).
- Coverage combined and published to `reports/quality/coverage.json` (44.11% — 15 090/34 213 lines); JUnit outputs stored at `reports/tests/{unit,integration,ui}.xml` and env preflight in `logs/env_check.json`.

### 2025-12-14 – Visual Studio assets retired
- Удалены `.sln/.csproj/.pyproj` вместе с C# заглушками и Insiders скриптами.
- Обновлены `docs/ENVIRONMENT_SETUP.md` и `docs/DEVELOPMENT_GUIDE.md` с рекомендациями по VS Code/PyCharm.
- `scripts/comprehensive_test.py` теперь проверяет отсутствие legacy артефактов.

### 2026-02-10 – Legacy tooling audit
- Подтверждено, что в репозитории отсутствуют `PneumoStabSim*.sln/.csproj/.pyproj`.
- Проверки `scripts/comprehensive_test.py` и поиск по коду подтверждают отсутствие
  зависимостей от Visual Studio проектов; документация обновлена.
