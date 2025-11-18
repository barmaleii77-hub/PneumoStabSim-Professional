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
   - Ship a smoke-check helper `tools/environment/verify_qt_setup.py` that validates PySide6 6.10 availability, Qt plugin paths,
     and Quick 3D bindings for CI agents and developer workstations.
   - Produce quickstart guide `docs/setup/qt610_environment.md` summarizing usage.
3. **CI/CD Infrastructure**
   - Add GitHub Actions workflows: `ci.yml` (build + tests), `nightly.yml` (scheduled smoke tests), `branch-audit.yml`.
   - Define secrets management playbook (token rotation, environment protection rules).
   - Configure artifact publishing (build outputs, logs, coverage reports).
   - Integrate the Qt smoke-check helper into `make check` and CI workflows, persisting run logs under `reports/environment/`.
4. **Developer Tooling**
   - Refresh `.vscode/` settings, ensuring linting tasks match CI commands.
   - Provide onboarding script `setup_dev.py` that bootstraps environment locally.
   - Document guidelines for AI assistants in `docs/ai_assistants.md`.
   - Update `docs/DEVELOPMENT_GUIDE.md` to emphasise the uv-first workflow, the Qt smoke-check helper, and `make check` as the
     non-negotiable pre-commit quality gate.

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
  dependencies; performance extras now track `numba 0.62.1`, which ships Python
  3.13-compatible wheels.
- 2025-03-05 – Introduced scheduled branch audit workflow leveraging the GitHub
  CLI container to post weekly stale-branch reports.
- 2025-04-06 – Published `docs/operations/onboarding_uv.md`, providing Windows,
  Linux, and WSL onboarding transcript aligned with the uv-first environment
  workflow and Phase 1 exit criteria.
- 2025-04-08 – Added `tools/environment/verify_qt_setup.py` plus the refreshed
  development guide detailing the make/uv workflow and captured the first Qt
  smoke-check transcript in `reports/environment/qt-smoke.md`.
- 2025-05-05 – Promoted the Qt environment verification to the `make check`
  quality gate and GitHub Actions matrix; reports are now timestamped snapshots
  inside `reports/environment/`.
- 2025-11-08 – `make check` in the Linux container failed: `pytest` reported
  structlog JSON emission regressions, multiple physics step lever geometry
  AttributeErrors, a receiver volume logging TypeError, and a documentation
  version mismatch. Qt shader baking also warned about missing
  `libxkbcommon.so.0`, but the existing Phase 1 environment guidance remains
  accurate; follow-up fixes belong to application code and dependency packaging
  tasks rather than environment documentation updates.
- 2025-11-09 – Added preset-aware environment helpers with Windows-specific RHI
  pinning and promoted `make full_verify` as the CI default to preserve verbose
  launch traces.
- 2025-11-22 – Refreshed `ci-cd.yml` to target `main`/`develop`, reuse uv-synced
  environments across the test/verify/docs jobs, and keep Qt smoke checks
  aligned with the headless matrices.
- 2025-11-24 – Added `make uv-sync-qt` to chain `uv sync` with
  `python tools/setup_qt.py --env-file .qt/qt.env`, exporting
  `QT_PLUGIN_PATH`, `QML2_IMPORT_PATH`, and `QT_QUICK_CONTROLS_STYLE=Basic` for
  Linux/Windows parity. The unified test entrypoint now consumes the generated
  env file before delegating to `make check`/`tools.ci_tasks verify`.
