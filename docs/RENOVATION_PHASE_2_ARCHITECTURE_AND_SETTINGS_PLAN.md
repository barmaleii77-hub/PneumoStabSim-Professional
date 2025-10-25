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
   - Introduce service container in `src/infrastructure/container.py` with typed registration.
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

### 2025-03-01 – Settings schema validation uplift
- Added JSON Schema enforcement to `src/core/settings_service.SettingsService`
  backed by `config/app_settings.schema.json`.
- Extended unit tests to cover invalid payload handling via
  `SettingsValidationError`.

### 2025-04-05 – Settings control matrix automation
- Implemented `tools/settings/export_matrix.py` to derive a Markdown control
  matrix from the schema, defaults snapshot, and UI bindings.
- Generated the first revision of `docs/settings_control_matrix.md`, providing a
  single source of truth for module ownership and widget wiring.

### 2025-07-02 – Service container foundation
- Added `src/infrastructure/container.py` featuring a thread-safe dependency
  injection container with override support for tests.
- Registered the canonical `SettingsService` factory during module import so
  CLI tools and runtime code resolve it through the shared container.
- Drafted the first revision of `docs/architecture/service_container.md` to
  describe lifecycle hooks and override patterns; logging and simulation
  factories will be added in follow-up iterations.

### 2025-07-15 – Event bus + logging integration
- Introduced `src/infrastructure/event_bus.py` and
  `src/infrastructure/logging.py`, registering both services in the global
  container with dedicated tokens.
- Updated `SettingsService` to publish `settings.updated` events with metadata,
  enabling diagnostics panels to react to configuration changes in real time.
- Added unit coverage ensuring subscribers receive instrumentation payloads and
  refreshed the service container guide with usage samples.
