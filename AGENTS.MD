# PneumoStabSim Professional • Agent Operations Manual

This document defines the default configuration, workflows, and etiquette for
automated or human agents collaborating on the renovation programme. It is
intentionally prescriptive: follow it unless the current task or system
instructions explicitly override a rule.

---

## 1. Canonical References

- **Master plan**: [`docs/RENOVATION_MASTER_PLAN.md`](docs/RENOVATION_MASTER_PLAN.md)
- **Phase playbooks**:
  - [`Phase 0`](docs/RENOVATION_PHASE_0_DISCOVERY_PLAN.md)
  - [`Phase 1`](docs/RENOVATION_PHASE_1_ENVIRONMENT_AND_CI_PLAN.md)
  - [`Phase 2`](docs/RENOVATION_PHASE_2_ARCHITECTURE_AND_SETTINGS_PLAN.md)
  - [`Phase 3`](docs/RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md)
  - [`Phase 4`](docs/RENOVATION_PHASE_4_TESTING_PACKAGING_CLEANUP_PLAN.md)
  - [`Phase 5`](docs/RENOVATION_PHASE_5_STABILIZATION_PLAN.md)
- **Settings architecture**: [`docs/SETTINGS_ARCHITECTURE.md`](docs/SETTINGS_ARCHITECTURE.md)
- **Assistant guidance**: [`docs/ai_assistants.md`](docs/ai_assistants.md)
- **Environment variables matrix**: [`docs/ENV_VARS_MATRIX.md`](docs/ENV_VARS_MATRIX.md)
- **Release quality matrix**: [`docs/RELEASE_QUALITY_MATRIX.md`](docs/RELEASE_QUALITY_MATRIX.md)

Before modifying code or configuration, review the relevant phase document and
ensure the master plan accurately reflects the intended scope.

---

## 2. Environment & Toolchain Defaults

- **Python**: 3.13 (managed via [`uv`](https://github.com/astral-sh/uv)).
  - Run `make uv-sync` to materialise the environment; `make uv-run CMD="..."`
    executes commands within the virtualenv.
- **Platform matrix**: _Always_ match the host to the assistant in use.
  - Visual Studio / VS Code Copilot sessions run on **Windows desktop**.
  - Codex / terminal-first assistants operate on **Linux** (the container
    image is the source of truth).
  - Every automation script must begin by detecting `platform.system()` and log
    the detected OS to avoid cross-platform misconfiguration.
  - Before executing build or test commands, re-run dependency installation for
    the active platform (`make uv-sync` on Linux containers, `scripts/setup_dev.py`
    on Windows desktops) so that agents never rely on stale environments.
- **Qt / PySide**: 6.10 installed by `python tools/setup_qt.py`.
  - Launch scripts (`activate_environment.sh`, `.ps1`) export `QT_PLUGIN_PATH`,
    `QML2_IMPORT_PATH`, and set `QT_QUICK_CONTROLS_STYLE=Basic`.
- **Linters & formatters**: `ruff`, `mypy`, `qmllint` (QML), optional
  `clang-format` for C++ interop.
- **Testing**: `pytest` (with `pytest-qt`) and scenario runners under `tests/`.
- **Unified test entrypoint**: run `python scripts/testing_entrypoint.py` from the
  repo root to sync dependencies and execute the standard verification suite.
- **Logging**: Use `structlog` JSON logger configured in `src/diagnostics`.
- **Configuration**: `config/app_settings.json` validated against
  `schemas/settings/app_settings.schema.json`; prefer using `src/core/settings_service.py`
  or `SettingsManager` abstractions instead of raw file IO.

---

## 3. Workflow Expectations

1. **Branch discipline**: create feature branches from `develop`, rebase before
   merging, and keep branches under two weeks unless otherwise approved.
2. **Commit format**: Conventional Commits (`type(scope): summary`). When
   multiple scopes apply, prefer the most specific module (e.g.
   `feat(ui-graphics): add orbit inertia slider`).
3. **Quality gates**: prior to every commit or PR, run `make check` (aggregates
   `ruff`, `mypy`, `pytest`, `qmllint`). Record command output for traceability.
4. **Documentation first**: if the change impacts architecture, tooling, or
   user-facing behaviour, update the master plan or relevant phase playbook in
   the same branch.
5. **Traceability**: link code changes to plan checklist items using inline
   comments or PR descriptions referencing the relevant section.
6. **Coverage threshold**: honour `COVERAGE_MIN_PERCENT` (see `docs/ENV_VARS_MATRIX.md`).
   Commits reducing coverage below the threshold must include remediation steps.

---

## 4. Coding Conventions & Safety Nets

- **Error handling**: avoid blanket `except Exception`; bubble up errors to the
  diagnostics overlay and logs.
- **Magic numbers**: centralise constants in `config/` or dedicated modules such
  as `src/simulation/constants.py`. Document provenance in comments.
- **UI bindings**: ensure each QML control has a single, clearly named signal
  connected to a Python slot. Use the bridge utilities defined in the master
  plan (`config/qml_bridge.yaml`).
- **Internationalisation**: maintain Russian and English translations under
  `assets/i18n/`. Update `.ts` files whenever UI text changes.
- **Performance**: profile with `tools/performance_monitor.py` when adjusting
  animations or rendering parameters. Attach the `.json` or `.prof` report to
  the relevant documentation if regressions occur.
- **HDR path logging**: all HDR path resolutions append JSON events (`asset_lookup`) to
  `logs/ibl/ibl_events.jsonl` (единый файл) for traceability (status: ok|missing|remote|empty).

---

## 5. Automation & CI Integration

- **Pre-commit**: install via `pre-commit install --hook-type pre-commit --hook-type pre-push`.
- **GitHub Actions**: keep workflows in `.github/workflows/` aligned with the
  master plan (CI, nightly, release). Update badges in `README.md` when pipelines
  change.
- **Runner autostart**: enable background watchdog `tools/run_tests_after_exit.py`
  when developing locally to ensure tests rerun after modifications.
- **Reporting**: publish test artefacts to `reports/` (e.g. `reports/tests/`,
  `reports/performance/`). Link them from the phase documents when closing
  action items.
- **HDR integrity**: run verification (`hdr-verify` via `make verify`) to ensure
  all manifest entries are present and checksums match before merging feature branches.

---

## 6. Knowledge Sharing & Logs

- Document rationale for significant refactors in `docs/DECISIONS_LOG.md`.
- When triaging rendering or orbit-control issues, capture findings in
  `docs/graphics.md` or `docs/ui/` sub-guides.
- Maintain the telemetry matrix in `docs/TRACING_EXECUTION_LOG.md` to preserve
  end-to-end signal traceability.

---

## 7. When In Doubt

1. Re-read the master plan section relevant to your change.
2. Consult the matching phase document for acceptance criteria.
3. If ambiguity remains, log an issue in GitHub with a link to the plan and the
   decision you propose.

Keep this manual up-to-date. Every time the master plan evolves, verify that
the references and tooling defaults here remain accurate.

---

## 8. Operational Imperatives

The following mandates are encoded in `config/app_settings.json` metadata and
apply to all contributors without exception:

- **No hard-coded defaults**: application code must load every tunable value
  from `config/app_settings.json`. If a new parameter is required, extend the
  settings file and schema first.
- **Graphics transparency**: every parameter that influences rendering quality
  or aesthetics must surface in the UI as a dedicated control. Avoid hidden
  coupling between parameters—one setting, one widget.
- **Settings integrity**: reading the settings file must never mutate it. The
  runtime may only persist changes in direct response to an explicit user
  action.
- **Dependency & testing compliance**: Всегда в обязательном порядке
  устанавливайте все необходимые модули и библиотеки и тестируйте все
  изменения в полном объеме.
- **Coverage gate**: CI enforces `COVERAGE_MIN_PERCENT`; failing the threshold blocks merge.
- **HDR verification**: run HDR manifest integrity checks (`hdr-verify`) before release tagging.
