# Renovation Dependency Tracker

This log captures dependency governance updates that affect the PneumoStabSim
Professional renovation programme. Each entry should highlight the impacted
tooling, lockfiles, and CI workflows so that Phase 1 environment owners can
trace when and why the dependency graph changed.

| Date       | Change summary | Notes |
| ---------- | -------------- | ----- |
| 2025-11-09 | Migrated uv dev extras to `[dependency-groups.dev]`, added `types-PySide6`, and confirmed NumPy/SciPy stay on the validated 2.3.x/1.16.x series. | Updated `pyproject.toml`, `uv.lock`, and all exported lockfiles. CI workflows (`ci.yml`, `ci-cd.yml`, `nightly.yml`) now run `uv pip check` and surface the results in job summaries. |

