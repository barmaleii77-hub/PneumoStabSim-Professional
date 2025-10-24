# PneumoStabSim Professional Modernization Blueprint

The master plan is the authoritative roadmap for delivering a production-ready
Python 3.13 + Qt 6.10 application with uncompromising visual fidelity and a
predictable developer workflow. It reflects the current repository layout,
identifies gaps, and prescribes step-by-step actions that align with industry
best practices for scientific visualisation software.

> **How to read this document**
>
> Each section is organised into a concise status summary followed by an
> actionable checklist. The status entries reference concrete files and
> directories in this repository. The action lists should be treated as living
> backlogs – mark items complete in the phase-specific plans located in the
> `docs/RENOVATION_PHASE_*.md` files and keep this master plan synchronised with
> reality after every milestone.

---

## 0. Baseline Snapshot

| Area | Current Baseline (January 2025 snapshot) | Observations |
| --- | --- | --- |
| Application entrypoints | `app.py`, `src/app_runner.py`, legacy launchers in `run*.ps1/.bat` | Multiple entrypoints drift; some scripts still target Qt 6.5 and Python 3.11. |
| Settings | `config/app_settings.json` + helper `src/common/settings_manager.py` and lightweight cache `src/core/settings_service.py` | JSON schema exists but lacks exhaustive validation, and duplicate helper utilities cause divergence. |
| UI/QML bridge | QML assets under `assets/qml` and Python helpers such as `src/ui/qml_host.py`, `src/ui/parameter_slider.py` | Bridge logic is fragmented; signal tracing is manual. |
| Physics & simulation | Domain modules in `src/pneumo`, `src/mechanics`, and legacy namespaced packages `src/PneumoStabSim.*` | Namespaces mix snake_case and PascalCase packages; constant definitions reside in both Python and JSON. |
| Tests & automation | `pytest.ini`, `tests/` folder (Qt smoke tests, settings tests), GitHub workflows missing | Local tooling defined but CI pipelines absent; lint configs (`ruff.toml`, `mypy.ini`) exist yet not wired into automation. |
| Documentation | Extensive markdown reports at repo root, curated plans in `docs/` | Redundant reports clutter root; plans reference historical Qt 6.5 constraints. |

---

## 1. Objectives and Guiding Principles

**Status**

- Primary objective remains delivery of a deterministic Qt Quick 3D application
  with premium materials, correct IBL alignment, and ergonomic camera controls.
- Repository already targets Python 3.13 / Qt 6.10 in `pyproject.toml`, yet
  supporting scripts have not been harmonised.
- Stakeholder-facing «Engineering Charter» опубликован в README и отражает
  пять опорных принципов проекта.

**Action Plan**

1. Lock the definition of "release ready" to five non-negotiable pillars:
   performance, rendering fidelity, configuration determinism, automated
   quality gates, and documentation parity.
2. Mirror these pillars in the phase plans; each deliverable must cite which
   pillar(s) it advances.
3. Publish an "Engineering Charter" excerpt in `README.md` summarising the
   objectives for stakeholders.

---

## 2. Repository Hygiene & Source Control

**Status**

- `.git` history contains numerous documentation-only commits; feature work
  still happens directly on `main`.
- Legacy Visual Studio projects (`PneumoStabSim*.sln`, `.csproj`) remain in the
  root alongside Python packaging metadata.
- Encoding drift persists across PowerShell scripts (BOM vs UTF-8) and QML
  files (LF vs CRLF).
- Branch governance rules are now documented in `.github/CONTRIBUTING.md`,
  establishing `main` for releases, `develop` for integration, and short-lived
  feature branches.

**Action Plan**

1. **Branch Governance**
   - Enforce `main` (releases) and `develop` (integration) with short-lived
     branches. *Status: completed February 2025 via `.github/CONTRIBUTING.md`.*
   - Add a scheduled workflow (`.github/workflows/branch-audit.yml`) that uses
     the GitHub CLI container to flag branches older than 30 days.
     *Status: Implemented March 2025 via a weekly Monday 04:00 UTC run that
     publishes a summary and warnings for stale branches.*
2. **Encoding & Attributes**
   - Expand `.gitattributes` to normalise UTF-8 LF for `.py`, `.qml`, `.json`
     and CRLF hints for `.ps1` while prohibiting BOM usage. Validate using
     `git check-attr` during CI.
   - Run the repository through `tools/encoding_normalizer.py` (to be created)
     to rewrite problematic scripts; confirm Russian-language docs remain UTF-8
     without BOM.
3. **Legacy Asset Rationalisation**
   - Relocate all historical markdown reports into `archive/<YYYY-MM>/` keeping
     README breadcrumbs.
   - Decide whether the .NET solution is still supported. If obsolete, remove
     `.sln`, `.csproj`, `.pyproj`, and document the deprecation in
     `docs/CHANGELOG_MODULAR.md`.
4. **Commit Quality**
   - Configure `pre-commit` with hooks for `ruff`, `mypy`, `qmllint`, and
     Conventional Commits (`commitizen`).
   - Introduce `tools/git/prepare_commit_msg.py` to auto-insert scope hints
     (module derived from modified files).

---

## 3. Environment & Dependency Strategy

**Status**

- `pyproject.toml` pins Python 3.13 and Qt 6.10, but lockfiles are absent.
- Scripts `activate_environment.(sh|ps1)` export Qt-related env vars yet still
  contain quoted paths tailored for Windows PowerShell 5.1.
- `requirements*.txt` duplicates dependency declarations, risking divergence.
- `scripts/bootstrap_uv.py` together with the `uv-sync`/`uv-run` make targets already accelerates local provisioning, but onboarding docs still reference legacy `python -m venv` flows and lack troubleshooting notes.

**Action Plan**

1. **Environment Provisioning**
   - Adopt [`uv`](https://github.com/astral-sh/uv) as the canonical virtual
     environment manager. Create `Makefile` targets (`make uv-sync`,
     `make uv-run CMD=...`) and mirror instructions in `docs/ENVIRONMENT_SETUP.md`.
   - Provide `scripts/bootstrap_uv.py` that installs uv if missing and seeds the
     environment.
   - Refresh `docs/ENVIRONMENT_SETUP.md` and `README.md` quick-start snippets to walk through the bootstrap helper and `make uv-sync`, removing stale venv advice. *(Completed March 2025; both documents now describe the uv-first workflow. Onboarding transcript pending.)*
  - Produce a concise onboarding transcript in `docs/operations/onboarding_uv.md` covering Windows, Linux, and WSL runs so support teams can reuse the same playbook. *Status: Completed April 2025 with cross-platform transcript and troubleshooting table.*
2. **Dependency Locking**
   - Generate a deterministic lockfile (`uv lock` or `pip-compile` producing
     `requirements.lock`) and store it under version control.
   - Consolidate `requirements.txt`, `requirements-dev.txt`, and
     `requirements-compatible.txt` into autogenerated files, referencing the
     lockfile in documentation.
3. **Qt Installation**
   - Rewrite `tools/setup_qt.py` to leverage `aqtinstall` with checksum
     verification and caching under `.qt/`.
   - Update launch scripts to source `QT_PLUGIN_PATH`, `QML2_IMPORT_PATH`, and
     `QT_QUICK_CONTROLS_STYLE` without double-escaping quotes. Validate with
     PowerShell Core 7.4 and Bash.
   - Add a lightweight smoke check (extend `tools/check_ui_utf8.py` or create `tools/environment/verify_qt_setup.py`) that asserts Qt plugin discovery works on CI agents and link it into the `make check` pipeline once stable.
4. **IDE & Assistant Integration**
   - Refresh `PneumoStabSim.code-workspace` with tasks for `ruff`, `pytest`, and
     `qmllint`. Add recommended extensions (Python, Qt Tools, GitHub Copilot).
   - Commit `.vs/VSWorkspaceSettings.json` with Visual Studio Insiders
     configuration enabling Qt plugin, clang-format, and Python workload.
   - Extend `docs/ai_assistants.md` with prompts for GPT-based agents, Copilot,
     and Visual Studio IntelliCode.

---

## 4. Configuration & Settings Management

**Status**

- `config/app_settings.schema.json` defines a JSON Schema but is not enforced
  automatically when saving settings.
- Settings logic is split between `src/common/settings_manager.py` (schema
  aware) and `src/core/settings_service.py` (lightweight cache), leading to
  duplicated behaviour and inconsistent defaults.
- Settings persistence lacks traceability between UI sliders and stored keys.
- JSON-based migration descriptors exist under `config/migrations/` with a
  command-line runner in `src.tools.settings_migrate` keeping track of applied
  upgrades.

**Action Plan**

1. Consolidate settings logic into `src/core/settings_manager.py` that wraps the
   schema-aware loader while exposing async-safe read/write for Qt threads.
2. Implement a `config/migrations/` pipeline driven by migration descriptors
   (YAML/JSON) executed by `python -m src.tools.settings_migrate`. Document the
   workflow in `docs/SETTINGS_ARCHITECTURE.md`.
3. Add end-to-end tests: `tests/settings/test_persistence.py` verifying
   round-trips and schema validation errors.
4. Provide instrumentation hooks – emit Qt signals whenever settings change,
   enabling the UI diagnostics panel to display the last write timestamp and the
   source of change.
5. Ensure settings read/write uses atomic temp files with explicit UTF-8
   encoding and newline normalisation.
6. Publish a generated matrix `docs/settings_control_matrix.md` that maps each
   persisted key to its owning module, validation rules, and UI control. Build a
   helper `tools/settings/export_matrix.py` that derives the document from the
   schema and QML metadata. *Status: completed April 2025 with the automated
   exporter now generating the matrix from the schema and UI sources.*
7. Ship a diagnostics CLI `python -m src.tools.settings_audit` producing
   human-readable diffs between the current runtime configuration and the
   baseline JSON shipped in `config/`. Capture exemplar reports under
   `reports/settings/` to validate the workflow.

---

## 5. Application Architecture Refinement

**Status**

- Mixed namespace strategy: `src/pneumo`, `src/mechanics`, `src/runtime`, and
  legacy `src/PneumoStabSim.*` packages co-exist.
- Service wiring relies on module-level singletons (`get_settings_service`), and
  UI integration uses ad-hoc imports from Python to QML.
- Error handling still features broad `except Exception` clauses in certain
  scripts within `src/bootstrap` and `src/diagnostics`.

**Action Plan**

1. **Modular Boundaries**
   - Reorganise `src/` into first-class domains: `core/`, `ui/`, `graphics/`,
     `simulation/`, `infrastructure/`. Migrate PascalCase packages into
     idiomatic snake_case modules while maintaining import compatibility through
     shim packages until consumers are updated.
2. **Service Composition**
   - Introduce `src/infrastructure/container.py` implementing a declarative
     dependency container (e.g. using `attrs` or `pydantic` for config binding).
   - Register services (settings, event bus, simulation engine, material cache)
     and expose injection helpers for CLI tools and Qt bootstrap.
3. **Signal/Slot Registry**
   - Centralise the QML bridge in `src/ui/qml_bridge.py`. Auto-register signals
     from metadata defined in `config/qml_bridge.yaml`. Provide introspection via
     `qmlBridge.dump_routes()` accessible in the diagnostics overlay.
4. **Simulation Loop**
   - Extract deterministic update loop into `src/simulation/runner.py` with a
     fixed timestep integrator (semi-implicit Euler + smoothing filter). Replace
     ad-hoc timers with orchestrated `QTimer` + worker thread pipeline.
5. **Error Transparency**
   - Remove silent exception swallowing. Surface errors through a
     `src/ui/overlays/error_toast.qml` component, while logging full tracebacks
     via `structlog`. Ensure Qt message handler is wired to Python logging.
6. **Architecture Handbook**
   - Maintain `docs/ARCHITECTURE_MAP.md` with diagrams exported from
     `tools/architecture/derive_diagram.py`. Update it whenever module boundaries
     or public interfaces change to keep onboarding friction low.

---

## 6. QML & UI Modernisation

**Status**

- QML controls are scattered across `assets/qml/panels`, with legacy versions in
  `archive/` and prototypes under `src/ui/*.py` generating QML fragments.
- Auto-fit on first render is still enabled in certain scenes; double-click
  behaviour is inconsistent.
- Material presets for glass and metals exist in JSON but are not exposed in the
  UI.

**Action Plan**

1. **Unified Scene Controller**
   - Configure `QtQuick3D.Helpers.OrbitCameraController` within
     `assets/qml/SceneView.qml` using parameters tested against the baseline
     scene. Ensure inertia, acceleration, and damping produce natural orbiting
     without scaling artefacts. Double-click triggers auto-fit via an explicit
     handler.
2. **Material Fidelity**
   - Audit material definitions in `config/baseline/materials.json`; update
     glass to use physically-correct index of refraction and absorption.
   - Validate skybox orientation and IBL rotation (`src/ui/ibl_logger.py`)
     ensuring consistent coordinate frames for HDR files stored in `assets/hdr`.
3. **UI Panel Architecture**
   - Build modular panels under `assets/qml/panels/` with one-to-one mapping
     between scene parameters and UI controls. Leverage reusable components such
     as `ParameterSlider` and `ToggleButton` from `src/ui/parameter_slider.py`.
   - Implement a `SettingsSyncController` that binds UI controls to
     `SettingsService` changes with signal tracing for debugging.
4. **Performance Tooling**
   - Integrate the Qt Quick profiler overlay toggled via `DiagnosticsPanel`.
   - Ensure animations use `NumberAnimation` and `Animator` elements with target
     framerates logged to `reports/performance/`.
5. **Accessibility & Localisation**
   - Maintain translations in `assets/i18n/` with lrelease-generated `.qm`
     files. Provide script `tools/i18n/update_translations.py` to regenerate.
6. **Design Language Alignment**
   - Establish a miniature design system documenting typography, spacing, and
     colour tokens for engineering teams. Store guidelines in
     `docs/ui/design_language.md` and enforce usage through shared QML style
     primitives in `assets/qml/styles/`.

---

## 7. Testing & Quality Gates

**Status**

- `pytest.ini` configures strict markers but tests do not cover UI extensively.
- Static analysis tools (`ruff`, `mypy`, `qmllint`) are configured yet not wired
  into automation or enforced via pre-commit.
- No CI workflows in `.github/workflows/`.
- `Makefile` already exposes `check`, `lint`, `typecheck`, and `qml-lint` targets backed by `tools/ci_tasks.py`, but adoption is ad-hoc and undocumented for contributors.

**Action Plan**

1. **Test Coverage Expansion**
   - Add behavioural tests in `tests/ui/` using `pytest-qt` to validate signal
     propagation between UI controls and the Python backend.
   - Implement regression tests for simulation math in `tests/simulation/` using
     golden files stored under `tests/data/`.
2. **Quality Gates Automation**
   - Create `make check` aggregating `ruff`, `mypy`, `pytest`, and `qmllint`.
   - Configure GitHub Actions workflows:
     - `ci.yml`: matrix {Ubuntu, Windows} x Python 3.13 running make targets.
     - `nightly.yml`: scheduled pipeline executing long-running simulations and
       encoding audits.
   - Ensure workflows install Qt 6.10 via the scripted setup and cache the
     download.
   - Document the local workflow in `docs/DEVELOPMENT_GUIDE.md`, clarifying that contributors must run `make check` (or `python -m tools.ci_tasks verify`) before submitting changes and offering troubleshooting steps for qmllint/Qt setup.
3. **Pre-Push Runner**
   - Implement `.hooks/pre-push` script invoking `make check`. Document how to
     opt-in on Windows (`.githooks/`) and include instructions in
     `docs/DEVELOPMENT_GUIDE.md`.
4. **Quality Telemetry**
   - Feed code coverage, lint duration, and flaky-test metrics into
     `reports/quality/dashboard.csv`. Automate nightly aggregation via
     `tools/quality/report_metrics.py` and visualise trends in
     `docs/operations/quality_dashboard.md`.

---

## 8. Deployment & Distribution

**Status**

- Packaging scripts exist in `tools/` but rely on older PyInstaller versions.
- No automated release pipeline; manual packaging documented in `QUICK_DEPLOY.md`.

**Action Plan**

1. Modernise packaging with `fbs` or `briefcase` depending on Qt Quick 3D
   support. Prototype using `scripts/package_app.py`.
2. Create GitHub Action `release.yml` triggered on tags: build installers (MSI,
   AppImage), attach artifacts, publish changelog from `CHANGELOG_MODULAR.md`.
3. Provide signed PowerShell scripts for enterprise environments and update
   `docs/QUICK_DEPLOY.md` with new workflows.

---

## 9. Cleanup & Legacy Removal

**Status**

- The repository root houses dozens of historical reports and quick-fix scripts
  that are superseded by the modular architecture.
- Duplicate geometry scripts exist in `src/ui` and `tools/`.

**Action Plan**

1. Perform a structured audit using `tools/audit/redundant_files.py` (to be
   implemented). Generate an actionable report stored in `reports/cleanup/`.
2. Delete superseded scripts (anything ending with `_fix.py` or `_final_report.md`
   once documentation has been migrated). Preserve references in the archive.
3. Ensure `.gitignore` excludes build outputs, logs, and Qt caches.
4. Document removal decisions in `docs/CHANGELOG_MODULAR.md` and phase plans to
   maintain traceability.

---

## 10. Execution Roadmap

**Status**

- Phase plans (`docs/RENOVATION_PHASE_*.md`) exist but need alignment with the
  updated objectives and timelines.

**Action Plan**

1. Refresh each phase document with:
   - **Scope statement** referencing this master plan sections.
   - **Entry criteria** (e.g., required documentation updates, baseline tests).
   - **Exit criteria** with measurable deliverables and links to test evidence in
     `reports/`.
2. Introduce a Kanban-style tracker (`docs/operations/phase_burndown.md`) for
   cross-functional visibility.
3. After every sprint, append a changelog entry summarising progress and update
   the "status" blocks in this master plan.
4. Maintain a rolling six-week milestone schedule in
   `docs/operations/milestones.md`, including planned capacity, dependencies,
   and review checkpoints with stakeholders.

---

## 11. Success Criteria

To declare the renovation complete, every item below must be demonstrably true
with evidence attached in the repository.

1. **Deterministic Runtime** – Application launches via `python -m
   src.app_runner` on Windows and Linux using Python 3.13 without warnings or
   missing Qt plugins.
2. **Complete UI Coverage** – Every scene parameter exposed in
   `config/app_settings.json` has a dedicated UI control with bidirectional
   binding and logging.
3. **Visual Fidelity** – Glass materials, IBL alignment, and orbit camera
   parameters validated using automated visual regression tests stored in
   `tests/ui/screenshots/`.
4. **Automation First** – `make check` and CI pipelines run green; pre-commit
   hooks block non-conforming commits.
5. **Repository Hygiene** – No redundant scripts or stale branches remain; all
   documentation reflects Qt 6.10 / Python 3.13 workflows.

---

## 12. Cross-References & Living Documents

- Detailed execution steps per phase:
  - [`docs/RENOVATION_PHASE_0_DISCOVERY_PLAN.md`](RENOVATION_PHASE_0_DISCOVERY_PLAN.md)
  - [`docs/RENOVATION_PHASE_1_ENVIRONMENT_AND_CI_PLAN.md`](RENOVATION_PHASE_1_ENVIRONMENT_AND_CI_PLAN.md)
  - [`docs/RENOVATION_PHASE_2_ARCHITECTURE_AND_SETTINGS_PLAN.md`](RENOVATION_PHASE_2_ARCHITECTURE_AND_SETTINGS_PLAN.md)
  - [`docs/RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md`](RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md)
  - [`docs/RENOVATION_PHASE_4_TESTING_PACKAGING_CLEANUP_PLAN.md`](RENOVATION_PHASE_4_TESTING_PACKAGING_CLEANUP_PLAN.md)
  - [`docs/RENOVATION_PHASE_5_STABILIZATION_PLAN.md`](RENOVATION_PHASE_5_STABILIZATION_PLAN.md)
- Assistant onboarding and tooling guide: [`docs/ai_assistants.md`](ai_assistants.md)
- Settings architecture primer: [`docs/SETTINGS_ARCHITECTURE.md`](SETTINGS_ARCHITECTURE.md)

Keep this blueprint under version control discipline: update it whenever a
significant architectural, tooling, or process change lands in the repository.

---

## 13. Review Cadence & Governance

**Status**

- Weekly architecture syncs are informal; meeting notes are scattered across
  personal notebooks and ad-hoc chat transcripts.
- Sprint reviews highlight risks, but there is no canonical risk register tied
  to the renovation backlog.

**Action Plan**

1. Codify a governance calendar in `docs/operations/governance.md` outlining
   weekly architecture syncs, bi-weekly sprint reviews, and monthly release
   readiness checkpoints. Attach agendas and expected artefacts.
2. Establish `docs/operations/risk_register.md` curated alongside this master
   plan. Each risk entry must include impact, probability, mitigation owner, and
   cross-references to relevant phase items.
3. Archive decisions from architecture syncs into `docs/DECISIONS_LOG.md` within
   24 hours, tagging affected modules and linking pull requests for auditability.
---

## 14. Immediate Next Steps

**Focus for the next sprint (March 2025)**

1. Publish the refreshed uv onboarding materials and circulate them via `docs/operations/onboarding_uv.md` with links in `README.md`.
2. Draft the Qt setup smoke-check utility (`tools/environment/verify_qt_setup.py`) and capture first-run notes in `reports/environment/qt-smoke.md`.
3. Align contributor documentation by updating `docs/DEVELOPMENT_GUIDE.md` and `docs/RENOVATION_PHASE_1_ENVIRONMENT_AND_CI_PLAN.md` to reference `make check` as mandatory prior to pull requests.
4. Prepare a status update for the governance sync summarising progress on dependency locking and CI workflow design, attaching action items to `docs/operations/governance.md`.
