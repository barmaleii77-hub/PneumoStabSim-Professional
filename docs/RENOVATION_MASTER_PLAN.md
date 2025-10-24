# PneumoStabSim Professional Modernization Blueprint

## 1. Objectives and Guiding Principles
- Deliver a production-grade Qt 6.10 + Python 3.13 application with predictable, debuggable behaviour and zero hidden fallbacks.
- Remove legacy artefacts (unused scripts, configs, obsolete solutions) while preserving reproducibility through reproducible environment pinning and configuration-as-code.
- Provide traceable, bi-directional signal/slot mapping between Python back-end and QML front-end, with exhaustive logging and validation.
- Guarantee best visual fidelity: glass material correctness, HDR skybox alignment, animation smoothness, and ergonomic orbit controls without scale drift.

## 2. Repository Hygiene & Source Control
1. **Branch Policy**
- Archive or delete stale branches after verifying merged status; enforce `main` + `develop` (integration) + short-lived feature branches.
   - Add `.github/workflows/branch-audit.yml` to detect long-lived branches (>30 days) and notify maintainers.
2. **Git Attributes & Encoding**
   - Extend `.gitattributes` to enforce UTF-8 w/ BOM prevention and normalized line endings for `.qml`, `.py`, `.ps1`, `.bat`, `.cs`, `.sln`.
   - Configure `*.ps1` as text with PowerShell CRLF hints, `*.qml`/`*.py` as LF.
3. **Large Binary/Asset Management**
   - Audit `assets/` for outdated HDR/mesh duplicates via `scripts/cleanup_duplicates.py` and store reference snapshot in `docs/assets_inventory.md`.
   - Introduce Git LFS only if assets exceed 100 MB; otherwise, compress and optimize textures.
4. **Commit Standards**
   - Adopt Conventional Commits; enforce through Husky-like pre-commit hook (Python-based) invoked cross-platform.

## 3. Environment & Dependency Strategy
1. **Python Tooling**
   - Adopt `uv` for virtual env management (fast Python 3.13 resolution) while keeping `venv` fallback for Windows.
   - Maintain `requirements.lock` (hash-locked) generated via `pip-tools` to guarantee deterministic installs.
   - Provide `pyproject.toml` `[tool.uv]` section for Python 3.13 constraint.
2. **Qt 6.10 Toolchain**
   - Use `aqtinstall` in `tools/setup_qt.py` to download PySide6 6.10 and Qt Quick 3D runtime packages with integrity verification.
   - Configure `QT_PLUGIN_PATH` and `QML2_IMPORT_PATH` via cross-platform launcher scripts (`activate_environment.(ps1|sh)` updates) ensuring consistent runtime.
3. **Node & Front-end Tooling**
   - Only install Node (LTS) if QML build pipeline requires shader pre-processing; document optional dependency.
4. **IDEs & Assistants**
   - Provide settings for VS Code Insiders, Visual Studio with Qt Tools, GitHub Copilot, and GPT-based assistants via:
     - `.vscode/settings.json` (per-workspace) + `PneumoStabSim.code-workspace` refresh
     - `visualstudio/.vsconfig` for required workloads
     - `docs/ai_assistants.md` summarizing instructions and privacy considerations.
5. **Shell Compatibility**
 - Harmonize PowerShell scripts to use UTF-8 w/ BOM, set `Set-StrictMode -Version Latest`, and avoid double-escaping of quotes.
   - For Bash, adopt `set -Eeuo pipefail` and ensure locale export `LC_ALL=C.UTF-8`.

## 4. Configuration & Settings Management
1. **Unified Settings File**
   - Implement `config/settings_schema.json` with JSON Schema; include defaults tuned for maximum quality.
   - Develop `src/core/settings_manager.py` to load/save with validation, ensuring atomic writes and backup file (`.bak`).
   - Integrate with QML through context properties + `Qt.labs.settings` for persistence.
2. **Environment Variables**
   - Provide `.env` template with Qt paths, logging levels, telemetry toggles; load via `python-dotenv` in `app.py`.
3. **Multi-platform Paths**
   - Standardize path resolution using `pathlib` + `QStandardPaths`; avoid hardcoded separators.
4. **Logging & Diagnostics**
   - Add structured logging (`structlog`) with JSON + human-friendly console outputs.
   - Provide `logs/` rotation policy and integrate into Git ignore.

## 5. Application Architecture Refinement
1. **Module Structure**
   - Reorganize `src/` into domains: `core/`, `ui/`, `graphics/`, `simulation/`, `infrastructure/`.
 - Introduce `__all__` exports and typed interfaces; enforce mypy + pyright parity.
2. **Dependency Injection**
   - Create lightweight container to manage services (settings, event bus, physics engine) for clarity.
3. **Signal/Slot Mapping**
   - Centralize QML bridge within `src/ui/qml_bridge.py` with automatic registration from declarative metadata (`qml_bridge.yaml`).
   - Provide instrumentation to trace signal direction, accessible via diagnostics overlay.
4. **Simulation Core**
   - Evaluate physics modules for "magic numbers"; replace with named constants in `src/simulation/constants.py` referencing docs.
   - Implement deterministic update loop decoupled from render tick, with delta-time smoothing.
5. **Error Handling**
   - Replace blanket try/except with explicit failure handling; propagate errors to UI overlay + logs.
   - Provide crash handler capturing Qt warnings via `QLoggingCategory` redirection.

## 6. QML & UI Modernization
1. **Scene Control**
   - Ensure double-click auto-fit only; disable auto-fit on load.
   - Configure camera orbit via `QtQuick3D.Helpers.OrbitCameraController` tuned for human ergonomics (target distance, acceleration, damping) without scale distortion.
2. **Material Fidelity**
   - Validate glass materials: adjust `ior`, `transmittance`, `attenuationColor`, `specularAmount`.
   - Ensure skybox + IBL share consistent coordinate system by aligning `TextureCube` orientation.
3. **UI Panels**
   - Build modular panel components (`ControlsPanel`, `LightingPanel`, `MaterialsPanel`, `AnimationPanel`, `DiagnosticsPanel`) exposing every available Qt 6.10 property relevant to scene.
   - Provide tooltips, reset-to-default per control, and preset management.
4. **Animation & Performance**
   - Rebuild animations using `NumberAnimation` with easing curves and frame-sync, ensuring >120 FPS on reference hardware.
   - Integrate GPU frame profiler overlay toggled via UI.
5. **Accessibility & Localization**
   - Adopt Qt Internationalization pipeline; maintain Russian + English translation `.ts` files.

## 7. Testing & Quality Gates
1. **Automated Tests**
   - Expand `tests/` to cover: settings I/O, signal wiring, geometry calculations, CLI integration.
   - Use `pytest-qt` for UI signal tests; integrate `pytest-xdist` for parallelism.
2. **Static Analysis**
   - Configure `ruff`, `mypy`, `pyright` (via `npx`) and `qmllint`; enforce via pre-commit and CI.
   - Adopt `clang-format`/`clang-tidy` for C#/C++ interop if any.
3. **Continuous Integration**
   - GitHub Actions matrix: {Windows, Ubuntu} x {Python 3.13}; steps: setup Qt via `aqt`, install deps, run linters, run tests, build artifacts, publish release zip.
   - Add scheduled workflow for nightly integration tests and branch pruning check.
4. **Performance Baselines**
   - Scripted scenario capturing camera orbit, UI toggles, recorded via `src/tools/perf_capture.py`.
   - Compare frame time statistics against baseline using `pytest-benchmark`.

## 8. Deployment & Distribution
1. **Packaging**
   - Use `fbs` or `PyInstaller` with Qt plugin collection; maintain `scripts/build_release.py` for reproducible builds.
   - Generate MSI (Windows) and AppImage (Linux) using GitHub Actions release job.
2. **Configuration Export**
   - Provide user settings export/import via single JSON file with schema validation.
3. **Documentation**
   - Maintain up-to-date docs with MkDocs; host via GitHub Pages with versioned docs.

## 9. Cleanup & Legacy Removal
- Inventory root directory reports; move archival markdowns to `archive/` with timestamped subfolders.
- Remove outdated `.csproj`, `.sln`, `.pyproj` if .NET integration deprecated; otherwise, document cross-language build steps.
- Delete redundant scripts (e.g., duplicates ending `_fix.py` superseded by new modules) after confirming coverage.
- Consolidate environment activation scripts to minimal cross-platform set to avoid drift.

## 10. Execution Roadmap
The roadmap is split into six phases with detailed implementation playbooks. Each phase has a dedicated plan file that captures prerequisites, sprint-level deliverables, and acceptance metrics. The links below point to the living documents that track daily progress and should be reviewed before kicking off the phase.

1. **Phase 0 – Discovery (1 week)**  
   [Detailed plan](RENOVATION_PHASE_0_DISCOVERY_PLAN.md)
2. **Phase 1 – Environment & CI (2 weeks)**  
   [Detailed plan](RENOVATION_PHASE_1_ENVIRONMENT_AND_CI_PLAN.md)
3. **Phase 2 – Architecture & Settings (3 weeks)**  
   [Detailed plan](RENOVATION_PHASE_2_ARCHITECTURE_AND_SETTINGS_PLAN.md)
4. **Phase 3 – UI & Graphics Enhancements (4 weeks)**  
   [Detailed plan](RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md)
5. **Phase 4 – Testing, Packaging & Cleanup (2 weeks)**  
   [Detailed plan](RENOVATION_PHASE_4_TESTING_PACKAGING_CLEANUP_PLAN.md)
6. **Phase 5 – Stabilization (continuous)**  
   [Detailed plan](RENOVATION_PHASE_5_STABILIZATION_PLAN.md)

### Phase Overview Refresh

- **Milestone Gates** – Each phase now concludes with a structured review covering code readiness, documentation parity, and metrics captured in the corresponding detailed plan. Advancement requires explicit sign-off recorded in the phase document.
- **Resource Planning** – The dedicated plans outline cross-functional roles (engineering, QA, design, DevOps) and expected weekly capacity. Adjustments should be logged inline to keep the modernization blueprint synchronized with staffing realities.
- **Risk Tracking** – Major risks, mitigation strategies, and contingency actions are maintained directly within the detailed plan files to keep the high-level roadmap evergreen without overwhelming it with tactical noise.

## 11. Success Criteria
- Application runs on Python 3.13 + Qt 6.10 across Windows/Linux without runtime warnings or missing plugins.
- UI exposes complete scene configuration set; double-click auto-fit works exclusively as requested.
- All tests + linters pass; CI pipelines green on all platforms.
- Repository contains only active assets, scripts, and configurations with clear ownership and documentation.
- Full parameter traceability from UI to simulation core validated through automated integration tests.
