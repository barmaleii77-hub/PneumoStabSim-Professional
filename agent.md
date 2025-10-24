# Modernization Agent Configuration

This document captures the standing instructions, environment defaults, and navigation aids for contributors working on the PneumoStabSim Professional renovation initiative.

## Mission Context
- Primary reference: [`docs/RENOVATION_MASTER_PLAN.md`](docs/RENOVATION_MASTER_PLAN.md)
- Modernization goal: deliver a Qt 6.10 + Python 3.13 production application with predictable behaviour, reproducible environments, and fully instrumented UI-to-core pathways.

## Operating Principles
1. **Branch Discipline** – Work happens on short-lived feature branches rebased onto `develop`. Merge to `main` only after stabilization sign-off.
2. **Conventional Commits** – Commit messages follow `<type>(scope): summary` format.
3. **Quality Gates** – Every change must pass `ruff`, `mypy`, `pyright`, `qmllint`, and `pytest`. Run the aggregate command `make check-all` when available; otherwise execute individual tools.
4. **Documentation First** – Update relevant plan documents before or alongside code changes to keep the blueprint synchronized.

## Detailed Phase Playbooks
Refer to the phase-specific plans for actionable steps, owners, and metrics:
- Phase 0 – Discovery: [`docs/RENOVATION_PHASE_0_DISCOVERY_PLAN.md`](docs/RENOVATION_PHASE_0_DISCOVERY_PLAN.md)
- Phase 1 – Environment & CI: [`docs/RENOVATION_PHASE_1_ENVIRONMENT_AND_CI_PLAN.md`](docs/RENOVATION_PHASE_1_ENVIRONMENT_AND_CI_PLAN.md)
- Phase 2 – Architecture & Settings: [`docs/RENOVATION_PHASE_2_ARCHITECTURE_AND_SETTINGS_PLAN.md`](docs/RENOVATION_PHASE_2_ARCHITECTURE_AND_SETTINGS_PLAN.md)
- Phase 3 – UI & Graphics Enhancements: [`docs/RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md`](docs/RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md)
- Phase 4 – Testing, Packaging & Cleanup: [`docs/RENOVATION_PHASE_4_TESTING_PACKAGING_CLEANUP_PLAN.md`](docs/RENOVATION_PHASE_4_TESTING_PACKAGING_CLEANUP_PLAN.md)
- Phase 5 – Stabilization: [`docs/RENOVATION_PHASE_5_STABILIZATION_PLAN.md`](docs/RENOVATION_PHASE_5_STABILIZATION_PLAN.md)

## Tooling & Environment Settings
- **Python**: 3.13 pinned via `uv`; fallback `venv` supported for Windows scripting compatibility.
- **Qt/PySide6**: Install using `tools/setup_qt.py` which validates checksums and configures `QT_PLUGIN_PATH` and `QML2_IMPORT_PATH`.
- **Logging**: Default to `structlog` with JSON outputs; ensure console-friendly renderer enabled for development.
- **Configuration**: Use `config/settings_schema.json` as the source of truth. Apply migrations with `python -m src.tools.settings_migrate` when schema changes.

## Review Checklist
Before opening a pull request:
- [ ] Plans updated with scope-specific notes and execution log entries.
- [ ] Tests and linters executed locally with passing status.
- [ ] Release notes or documentation adjustments captured if behaviour changes.
- [ ] Risks or follow-up tasks documented in the relevant phase plan.

Maintain this file as the authoritative instruction set for agents collaborating on the renovation project.
