# Renovation Phase 1 – Environment and CI Plan

## Objectives
- Deliver deterministic development and CI environments for Python 3.13 + Qt 6.10.
- Automate branch governance and enforce coding standards through pipelines and hooks.
- Document end-to-end setup for all supported platforms.

## Entry Criteria
- Phase 0 deliverables accepted.
- Hardware resources for CI runners allocated (Windows + Ubuntu).
- Licensing for Qt and automation tools confirmed.

## Work Breakdown Structure
1. **Dependency Governance**
   - Generate `requirements.lock` via `pip-compile` and commit with hashes.
   - Configure `uv` workflows: add `pyproject.toml` entries, bootstrap scripts in `tools/env/`.
   - Validate installation across Windows, Ubuntu, and macOS (if applicable).
2. **Qt Toolchain Automation**
   - Implement `tools/setup_qt.py` with checksum verification and caching strategy.
   - Update `activate_environment.*` scripts to set `QT_PLUGIN_PATH`, `QML2_IMPORT_PATH`, and telemetry toggles.
   - Produce quickstart guide `docs/setup/qt610_environment.md` summarizing usage.
3. **CI/CD Infrastructure**
   - Add GitHub Actions workflows: `ci.yml` (build + tests), `nightly.yml` (scheduled smoke tests), `branch-audit.yml`.
   - Define secrets management playbook (token rotation, environment protection rules).
   - Configure artifact publishing (build outputs, logs, coverage reports).
4. **Developer Tooling**
   - Refresh `.vscode/` settings, ensuring linting tasks match CI commands.
   - Provide onboarding script `setup_dev.py` that bootstraps environment locally.
   - Document guidelines for AI assistants in `docs/ai_assistants.md`.

## Deliverables
- Locked dependency files and environment automation scripts merged to `develop`.
- CI workflows green on at least one reference branch.
- Updated documentation for setup and tooling, accessible from README.

## Exit Criteria
- Successful dry-run of CI on fork or feature branch with artifacts attached.
- All developers able to reproduce environment using documented steps within 30 minutes.
- Branch audit workflow running and reporting against repository history.

## RACI Snapshot
- **Responsible:** DevOps engineer, build engineer.
- **Accountable:** Engineering manager.
- **Consulted:** Tech lead, QA lead.
- **Informed:** Product representative, support lead.

## Execution Log
Capture notable decisions, blockers, and timings here. Reference PR numbers and CI runs.

- 2025-02-15 – Added `tools/ci_tasks.py` command runner and cleaned up the strict
  mypy target list to unblock Phase 1 automation goals.
- 2025-02-18 – Generated `requirements.lock` with uv to cover base, dev, and docs
  dependencies; deferred performance extras until `numba` publishes Python 3.13
  wheels.
- 2025-03-05 – Introduced scheduled branch audit workflow leveraging the GitHub
  CLI container to post weekly stale-branch reports.
- 2025-04-06 – Published `docs/operations/onboarding_uv.md`, providing Windows,
  Linux, and WSL onboarding transcript aligned with the uv-first environment
  workflow and Phase 1 exit criteria.
