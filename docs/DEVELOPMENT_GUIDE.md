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

> **Linux-only dependency note**: установите системные пакеты Mesa software GL (`xvfb`, `xauth`, `dbus-x11`, `mesa-utils`, `mesa-utils-extra`, `libosmesa6(-dev)`, `libglu1-mesa(-dev)`, `libegl1-mesa(-dev)`, `libgles2-mesa(-dev)`, `libgbm1`, `libdrm2`, `libxcb-*`, `libvulkan1`, `mesa-vulkan-drivers`) чтобы локальная среда совпадала с CI.

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
   `requirements.lock`. Цель `make uv-sync` теперь вызывает `uv sync --frozen --extra dev`,
   поэтому dev-зависимости для тестов и UI автоматически подтягиваются.
   ```bash
   make uv-sync
   ```
5. **Verify the Qt toolchain** – confirms PySide6 6.10, plugin directories, and
   Qt Quick 3D bindings are reachable from the active shell.
   ```bash
   python -m tools.environment.verify_qt_setup
   ```
6. **Run the quality gate** – executes Ruff, mypy, pytest, and qmllint via the
   helper runner and writes consolidated logs (`ruff_format.log`, `ruff_check.log`,
   `mypy.log`, `pytest.log`, `qmllint.log`, and `verify_status.json`) to
   `reports/quality/`. В состав команды входит `make monitor-shader-logs`,
   которая анализирует `reports/shaders/*.log` и собирает сводку в
   `reports/tests/shader_logs_summary.json`.
   ```bash
   make check
   ```
   На Linux используйте `bash scripts/xvfb_wrapper.sh make check`, чтобы Qt Quick 3D
   и QtCharts работали в виртуальном дисплее, аналогично CI.
   После успешного прогона проверьте `reports/tests/shader_logs_summary.json` — там
   перечислены предупреждения Qt Shader Baker и найденные fallback-шейдеры.
   To capture an extended launch trace (mirroring CI), run the autonomous
   wrapper. It persists a timestamped Markdown log and JSON status record that
   can be attached to issues or inspected after failures.
   ```bash
   make autonomous-check
   ```
   Use `make uv-run CMD="..."` (or `uv run -- ...`) to execute ad-hoc commands
   inside the managed environment.

## 2. IDE integration

### Visual Studio Code

1. Run `python setup_vscode.py` from the project root. The bootstrapper ensures
   the `.vscode/` directory exists, validates JSON configuration, refreshes the
   recommended extensions list, and wires Python import paths so IntelliSense
   resolves modules under `src/`, `tests/`, and `tools/` without manual tweaks.
2. Open `PneumoStabSim.code-workspace`. The workspace pins the interpreter to
   the uv-managed `.venv` and exposes tasks for `ruff`, `pytest`, and `qmllint`.
3. Accept the recommended extensions when prompted (Python, Qt Tools, GitHub
   Copilot, Ruff, Jupyter, PowerShell, etc.). The list mirrors the
   `setup_vscode.py` bootstrap to keep all developers aligned.
4. Launch configurations:
   - **App: PneumoStabSim (Qt 6.10)** – invokes `python -m src.app_runner` with
     Qt environment variables.
   - **Tests: Smoke suite** – runs `pytest -k smoke` using uv.
   - **Diagnostics: QML asset scan** – runs `python tools/ci_tasks.py qml-lint`.
5. Format on save delegates to `ruff`; ensure "Python › Formatting: Provider"
   is set to "None" so the Ruff extension owns formatting.

### Visual Studio 2022 (Python workload)

> ⚠️ Поддержка проектов Visual Studio снята. Рекомендуемые IDE — VS Code и PyCharm,
> которые используют `uv` и `Makefile` задачи из этого руководства.

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

- Run both `python -m tools.ci_tasks verify` **and** `make autonomous-check`
  before pushing or opening a pull request. The `verify` command provides the
  fast inner loop, while `make autonomous-check` stores the aggregated results
  under `reports/quality/` (including `autonomous_check_latest.log` and the
  JSON status snapshot) so regressions are easy to audit.
- `make check` chains the core quality gate (`python -m tools.ci_tasks verify`)
  with shader validation, localization checks, and Qt environment probes. Use
  this target when you need the exact CI contract on a workstation.
- `python -m tools.environment.verify_qt_setup` validates that Qt plugins and
  Qt Quick 3D bindings are discoverable on the current workstation. Capture the
  first successful transcript in `reports/environment/qt-smoke.md`.
- Enable `pre-commit` hooks (`pre-commit install --hook-type pre-commit --hook-type
  pre-push`) to mirror CI behaviour locally.
- Opt into the repository-provided Git hooks so the pre-push quality gate runs
  automatically:
  - **Unix-like shells** – `git config core.hooksPath .hooks` (this makes Git
    execute `.hooks/pre-push`, which delegates to `make check`).
  - **Windows PowerShell** – copy `.hooks/pre-push` into `.git/hooks/` and use
    `bash` from Git for Windows, or mirror the logic in a PowerShell script (see
    below) and register it with `git config core.hooksPath .githooks`.
  - A reference PowerShell implementation lives at `.githooks/pre-push.ps1` and
    calls `python -m tools.ci_tasks verify` for environments where `make`
    is unavailable.
- Install the optional commit message helper to surface Conventional Commit
  scopes automatically. The script inserts a `# Suggested scopes: ...` comment
  derived from the staged files:
  - **Unix-like shells** – `ln -s ../../tools/git/prepare_commit_msg.py .git/hooks/prepare-commit-msg`
  - **Windows (PowerShell)** – `cmd /c mklink .git\\hooks\\prepare-commit-msg ..\\..\\tools\\git\\prepare_commit_msg.py`
- Follow Conventional Commit messages (`type(scope): summary`) when committing.

## 5. Troubleshooting & support

- **PySide6 import errors** – rerun `make uv-sync`, then `python tools/setup_qt.py`
  (via `make uv-run`) to reinstall Qt archives.
- **`qmllint` missing** – ensure Qt 6.10 tools are available on `PATH`. The Qt
  setup script downloads the CLI utilities into `.qt/6.10` and the activation
  scripts append them to the shell.
- **CI reproductions** – run `make check` to mirror the GitHub Actions jobs. The
  command emits logs in `reports/quality/` which are uploaded as workflow
  artefacts (see the `quality-<os>` bundle on successful or failed runs).
- **Quality gate failures** – inspect the corresponding log in
  `reports/quality/` (`ruff_*.log`, `mypy.log`, `qmllint.log`, `pytest.log`) and
  the aggregated `verify_status.json` summary. These files are bundled in the
  CI artefacts for remote debugging and remain locally after each run.
- **Investigating CI failures** – download the `quality-<os>` artefact from the
  corresponding workflow. It contains the autonomous-check Markdown log,
  `autonomous_check_status.json`, and any Qt environment reports produced by the
  job. Inspect these files before re-running the pipeline.
- Post blockers and environment anomalies in the `#dev-environment` Slack
  channel; link the relevant section of this guide or the renovation master plan
  when requesting assistance.

## 6. Development readiness checklist

Follow this checklist whenever preparing a new workstation or CI runner:

1. **Bootstrap the IDE** – execute `python setup_vscode.py` and reopen
   Visual Studio Code to pick up refreshed launch/tasks configuration and the
   latest extension recommendations.
2. **Verify the Qt toolchain** – run `python -m tools.environment.verify_qt_setup`
   (via `make uv-run`) to confirm PySide6 6.10, plugin paths, and Quick 3D
   bindings resolve correctly.
3. **Run the quality gate** – execute `make check` (or `python -m tools.ci_tasks
   verify`) to ensure Ruff, mypy, pytest, and qmllint all pass locally before
   starting feature work.
4. **Capture the transcript** – stash the first successful command outputs under
   `reports/environment/` for auditability and future troubleshooting.

Completion of these steps signals the workstation is fully ready for active
development, matching the expectations outlined in the renovation master plan.
