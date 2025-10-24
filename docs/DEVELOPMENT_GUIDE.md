# PneumoStabSim – Development Guide

This guide summarises the modernised workflow for contributing to
PneumoStabSim Professional. It reflects the Qt 6.10 / Python 3.13 stack and the
uv-first environment strategy captured in the renovation master plan.

## 1. Environment Setup (uv-first workflow)

### Prerequisites

| Software | Version | Notes |
| --- | --- | --- |
| Git | ≥ 2.45 | Configure credential helper before cloning. |
| Python | 3.13.x | Either system Python or `pyenv` shim. |
| uv | Latest | Installed automatically by `scripts/bootstrap_uv.py`. |
| Qt runtime | 6.10 | Provisioned via `tools/setup_qt.py` and the `activate_environment.*` scripts. |

### Step-by-step onboarding

1. **Clone the repository**
   ```bash
   git clone https://github.com/barmaleii77-hub/PneumoStabSim-Professional.git
   cd PneumoStabSim-Professional
   ```
2. **Bootstrap uv** – installs uv if missing and prepares the managed virtual
   environment cache.
   ```bash
   python scripts/bootstrap_uv.py
   ```
3. **Activate the Qt-aware shell** – export Qt plugin paths before installing
   dependencies.
   ```powershell
   # PowerShell 7 (Windows)
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ./activate_environment.ps1
   ```
   ```bash
   # Bash (Linux or WSL)
   source ./activate_environment.sh
   ```
4. **Synchronise dependencies** – resolves the exact lockfile captured in
   `requirements.lock`.
   ```bash
   make uv-sync
   ```
5. **Verify the Qt toolchain** – confirms PySide6 6.10, plugin directories, and
   Qt Quick 3D bindings are reachable from the active shell.
   ```bash
   python -m tools.environment.verify_qt_setup
   ```
6. **Run the quality gate** – executes Ruff, mypy, pytest, and qmllint via the
   helper runner.
   ```bash
   make check
   ```
   Use `make uv-run CMD="..."` (or `uv run -- ...`) to execute ad-hoc commands
   inside the managed environment.

## 2. IDE integration

### Visual Studio Code

1. Open `PneumoStabSim.code-workspace`. The workspace pins the interpreter to the
   uv-managed `.venv` and wires tasks for `ruff`, `pytest`, and `qmllint`.
2. Accept the recommended extensions (Python, Qt Tools, GitHub Copilot, YAML).
3. Launch configurations:
   - **App: PneumoStabSim (Qt 6.10)** – invokes `python -m src.app_runner` with
     Qt environment variables.
   - **Tests: Smoke suite** – runs `pytest -k smoke` using uv.
   - **Diagnostics: QML asset scan** – runs `python tools/ci_tasks.py qml-lint`.
4. Format on save delegates to `ruff`; ensure "Python › Formatting: Provider"
   is set to "None" so the Ruff extension owns formatting.

### Visual Studio 2022 (Python workload)

1. Load `PneumoStabSim.slnx`. Visual Studio binds to `.venv\\Scripts\\python.exe`
   automatically when the environment has been provisioned.
2. Use the **Debug Targets** drop-down to run the GUI, smoke tests, or QML
   diagnostics. Profiles map to the same commands exposed via the Makefile.
3. Enable Qt tooling (Qt VS Tools extension) to inspect `.qml` assets directly.

## 3. Project structure highlights

- `src/core/` – application services (settings, diagnostics, configuration).
- `src/ui/` – Qt bridges, parameter widgets, diagnostics overlays, and QML glue.
- `src/simulation/` – physics integrators and domain models.
- `assets/qml/` – UI scenes and panel definitions.
- `config/` – baseline settings JSON, schema, and migration descriptors.
- `tools/` – automation helpers including `tools.environment.verify_qt_setup` and
  CI runners under `tools/ci_tasks.py`.
- `tests/` – pytest suites (unit, integration, smoke) and supporting fixtures.

## 4. Quality gates & workflows

- `make check` (or `python -m tools.ci_tasks verify`) must succeed before pushing
  or opening a pull request. The command runs Ruff (format + lint), mypy,
  pytest, and qmllint with repository-configured targets.
- `python -m tools.environment.verify_qt_setup` validates that Qt plugins and
  Qt Quick 3D bindings are discoverable on the current workstation. Capture the
  first successful transcript in `reports/environment/qt-smoke.md`.
- Enable `pre-commit` hooks (`pre-commit install --hook-type pre-commit --hook-type
  pre-push`) to mirror CI behaviour locally.
- Follow Conventional Commit messages (`type(scope): summary`) when committing.

## 5. Troubleshooting & support

- **PySide6 import errors** – rerun `make uv-sync`, then `python tools/setup_qt.py`
  (via `make uv-run`) to reinstall Qt archives.
- **`qmllint` missing** – ensure Qt 6.10 tools are available on `PATH`. The Qt
  setup script downloads the CLI utilities into `.qt/6.10` and the activation
  scripts append them to the shell.
- **CI reproductions** – run `python -m tools.ci_tasks verify` for local parity
  with the CI container workflows.
- Post blockers and environment anomalies in the `#dev-environment` Slack
  channel; link the relevant section of this guide or the renovation master plan
  when requesting assistance.
