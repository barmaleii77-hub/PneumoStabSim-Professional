# Codex & Copilot Prompt Blueprint for PneumoStabSim Professional

This blueprint assembles the canonical requirements for large language model coding assistants working on PneumoStabSim Professional. Embed these directives verbatim in Codex or GitHub Copilot chat prompts to ensure generated code aligns with our architecture, logging, and configuration policies.

## 1. Agent Configuration
- Always operate within the active feature branch rebased on `develop`.
- Enforce Conventional Commits using the `type(scope): summary` pattern.
- Treat `config/app_settings.json` and `docs/RENOVATION_MASTER_PLAN.md` as single sources of truth for runtime tunables and roadmap context.
- Use Python 3.13 through the `uv` environment: run commands via `make uv-run CMD="…"`.
- Prefer the `SettingsManager` and related abstractions in `src/core/settings_service.py` instead of manual file IO.

## 2. Parameter Management Strategy
- Declare every adjustable value in `config/app_settings.json` with accompanying schema updates in `config/schemas/app_settings.schema.json`.
- Load parameters exclusively through the settings service. Do not introduce new `@dataclass` defaults or inline constants that duplicate configuration values.
- Surface each parameter in the UI module that owns it (e.g., graphics, simulation, diagnostics). Use descriptive names consistent with the master plan’s terminology.

## 3. Validation Workflow
- Validate modified settings with `make check-config`, which verifies JSON schema compliance and regenerates any derived artefacts.
- For Python modules, run `make check` to execute `ruff`, `mypy`, `pytest`, and `qmllint` gates.
- Ensure every new validator emits actionable error messages routed through the diagnostics overlay defined in `src/diagnostics`.

## 4. Logging & Telemetry Requirements
- Instrument new code paths with `structlog` JSON logs, tagging entries with the owning module (e.g., `ui.graphics`, `simulation.stability`).
- Forward critical events to the telemetry matrix documented in `docs/TRACING_EXECUTION_LOG.md`.
- When integrating with Qt/QML, ensure signals forward context strings rather than raw enums to improve observability.

## 5. Eliminating Magic Numbers
- Move repeated numeric literals into dedicated constants modules such as `src/simulation/constants.py` or the relevant UI settings registry.
- Document the provenance of each constant with inline comments referencing logs, experiments, or plan checklists.
- If a literal originates from configuration, refactor the code to fetch it from the settings service instead.

## 6. Module-Specific Prompt Hooks
- **Graphics Module** (`src/ui/graphics/`): maintain explicit bindings between sliders and Qt Quick properties. Respect any range metadata defined in configuration.
- **Simulation Module** (`src/simulation/`): preserve numerical stability helpers and guard divisions with epsilon values stored in `constants.py`.
- **Diagnostics Module** (`src/diagnostics/`): ensure new logging adapters register with the global telemetry router and include correlation IDs.
- **Tools & Scripts** (`tools/`): keep CLI interfaces idempotent; expose dry-run flags and avoid modifying settings files implicitly.

## 7. Prompt Usage Example
```text
You are assisting with PneumoStabSim Professional. Follow the agent configuration, parameter management, validation, logging, magic number, and module-specific policies defined in docs/CODEX_COPILOT_PROMPT.md. Use Python 3.13 via make uv-run, rely on SettingsManager for configuration, instrument with structlog, and update app_settings.json plus its schema for new tunables.
```

Embed this snippet at the top of every Codex or Copilot session to align completions with project standards.
