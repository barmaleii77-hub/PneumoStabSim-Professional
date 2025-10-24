# Renovation Phase 2 – Architecture and Settings Plan

## Objectives
- Reorganize the application into coherent modules with enforceable contracts.
- Implement a unified settings system with schema validation and persistence guarantees.
- Establish reliable communication paths between Python back-end and QML front-end.

## Entry Criteria
- Phase 1 tooling merged and stable.
- Architectural stakeholders agree on target module boundaries.
- Prototype settings schema reviewed and approved.

## Work Breakdown Structure
1. **Module Restructuring**
   - Create domain directories (`src/core`, `src/ui`, `src/graphics`, `src/simulation`, `src/infrastructure`).
   - Implement import maps and `__all__` exports to stabilize public APIs.
   - Update namespace package configuration in `pyproject.toml` and adjust tests.
2. **Dependency Injection & Services**
   - Introduce service container in `src/core/container.py` with typed registration.
   - Provide factory methods for settings, logging, event bus, simulation engine.
   - Document lifecycle hooks in `docs/architecture/service_container.md`.
3. **Settings Platform**
   - Finalize `config/settings_schema.json` with validation rules and defaults.
   - Implement `SettingsManager` (load, save, migrate) and CLI for exporting/importing configurations.
   - Integrate with QML via context properties and `Qt.labs.settings` wrappers.
4. **Signal/Slot Alignment**
   - Define `qml_bridge.yaml` metadata for automatic wiring.
   - Implement instrumentation to log every signal with correlation IDs.
   - Add integration tests verifying round-trip updates (pytest-qt).
5. **Logging & Error Handling**
   - Configure `structlog` and fallback to standard logging when unavailable.
   - Capture Qt warnings and surface them through diagnostics overlay.
   - Update exception handling to propagate actionable feedback to UI.

## Deliverables
- Refactored source tree with updated imports and module contracts.
- Settings system in place with migration coverage and regression tests.
- Signal/slot bridge validated through automated tests and trace logs.

## Exit Criteria
- All tests (unit + integration) green after refactor.
- Documentation updated: architecture overview, settings reference, signal map.
- No circular dependencies or mypy/pyright errors in core modules.

## RACI Snapshot
- **Responsible:** Tech lead, senior Python engineer.
- **Accountable:** Principal engineer.
- **Consulted:** UI lead, QA automation lead.
- **Informed:** Product representative, support lead.

## Execution Log
Log architectural decisions, ADR references, and schema revisions here.
