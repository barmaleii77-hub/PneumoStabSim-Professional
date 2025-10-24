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

## RACI Snapshot
- **Responsible:** QA automation lead, release engineer.
- **Accountable:** Engineering manager.
- **Consulted:** Tech lead, DevOps engineer.
- **Informed:** Support lead, documentation lead.

## Execution Log
Use this section to log coverage milestones, release candidate builds, and cleanup decisions.
