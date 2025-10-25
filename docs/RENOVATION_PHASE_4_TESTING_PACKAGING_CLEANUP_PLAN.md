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
   - Configure coverage thresholds (>=85%) enforced in CI.
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
   - Consolidate environment scripts and update README references.
5. **Documentation Refresh**
   - Publish MkDocs site updates, including API docs and troubleshooting guides.
   - Ensure diagrams and architecture decision records reference new modules.

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
