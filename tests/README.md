# PneumoStabSim Test Suite

This guide documents the structure of the automated tests, platform-specific
workflows, and the remediation plan for stabilising Windows test runs.

## Directory layout

```
tests/
├── bootstrap/               # Provisioning helpers used by CI smoke runs
├── config/                  # Shared configuration payloads consumed by fixtures
├── helpers/                 # Utility modules reused by multiple suites
├── integration/             # Python↔QML integration flows and bridge checks
├── physics/                 # Physics engine regression cases and fixtures
├── pneumo/                  # Pneumatic subsystem behaviour tests
├── qml/                     # QML snapshots, bindings, and regression harnesses
├── quality/                 # Quality gates (lint/typecheck) verification hooks
├── scenarios/               # JSON/YAML scenarios for simulation-driven tests
├── simulation/              # Simulation loop and telemetry validation
├── smoke/                   # Minimal environment verification for CI sanity
├── system/                  # End-to-end orchestration and launch validations
├── ui/                      # Qt widgets, panel controllers, and state sync
├── unit/                    # Pure unit tests covering isolated modules
└── tools/                   # Harnesses invoked by pytest and task runner
```

Fixtures live in `tests/conftest.py`, and Qt-specific headless defaults are
centralised in `tests/_qt_headless.py`.

## Environment prerequisites

1. **Synchronise Python dependencies**
   - Linux/macOS (`make` available): `make uv-sync`
   - Windows / make-less shells: `python -m tools.task_runner uv-sync`
2. **Install Qt runtime** (only when missing): `python tools/setup_qt.py --qt-version 6.10.0`
3. **Verify graphics backend** (см. подробности в `docs/ENVIRONMENT_SETUP.md`)
   - GPU mode: ensure `PSS_HEADLESS` is unset and `QSG_RHI_BACKEND=d3d11` on Windows.
   - Headless mode: set `PSS_HEADLESS=1` or use the pytest `--pss-headless` flag to
     apply the defaults defined in `tests/_qt_headless.py`.
    - Vulkan smoke: export `QSG_RHI_BACKEND=vulkan` и `VK_ICD_FILENAMES=<путь>` из
      таблицы headless/Vulkan в `docs/ENVIRONMENT_SETUP.md`.

Cross-platform provisioning and optional automated runs are also available through
`python -m tools.cross_platform_test_prep --use-uv [--run-tests]`, which installs
OS prerequisites and executes pytest with the correct Qt overrides.

## Running the test suites

### Aggregated quality gate

- Linux/macOS: `make check`
- Windows / make-less shells: `python -m tools.task_runner check`

The aggregated gate performs linting, type checks, shader validation, environment
verification, and smoke/integration pytest sweeps.

### Pytest entry points

| Scope            | Linux/macOS (`make`) | Windows (`python -m tools.task_runner …`) |
| ---------------- | -------------------- | ----------------------------------------- |
| Full CI parity   | `make test-local`    | `python -m tools.task_runner test`        |
| Unit tests       | `make test-unit`     | `python -m tools.task_runner test-unit`   |
| Integration flow | `make test-integration` | `python -m tools.task_runner test-integration` |
| UI/Qt suite      | `make test-ui`       | `python -m tools.task_runner test-ui`     |

For manual Windows executions that need fine-grained control over Qt variables,
use `.\scripts\run_tests_ci.ps1 -Target tests\ui` (PowerShell). The script applies
D3D11 defaults when `PSS_HEADLESS` is unset and records console output under
`reports/tests/` for later inspection.

### Direct pytest usage

When calling pytest manually, prefer the `-p pytestqt.plugin` flag to ensure the
Qt plugin loads even when `PYTEST_DISABLE_PLUGIN_AUTOLOAD` is set. Example:

```powershell
# PowerShell 7+
$env:PSS_HEADLESS = '1'
python -m pytest -p pytestqt.plugin tests/ui
```

Artifacts such as `pytest_console.txt` and environment captures are stored in
`reports/tests/`. Keep these under version control only when referenced by a
tracking document.

## Writing and extending tests

- Reuse fixtures from `tests/conftest.py` for settings management, simulation
  seeds, and Qt application bootstrapping.
- Shared helpers in `tests/helpers/` provide assertions for telemetry snapshots
  and graphics payload comparisons.
- Scenario-driven suites under `tests/scenarios/` and `tests/simulation/` rely on
  JSON/YAML payloads; validate new schemas against `schemas/` before committing.
- Prefer `pytest.mark.qt_log_level('WARNING')` for noisy Qt modules instead of
  silencing logs globally.
- Record long-running or stateful tests in `tests/system/` with descriptive
  docstrings to aid triage.

## Windows remediation plan

1. **Baseline reproduction** – Run `python -m tools.cross_platform_test_prep --use-uv --run-tests --pytest-args tests/ui`
   on a Windows workstation to collect the failing categories and capture the
   generated `reports/tests/pytest_console.txt` artefact.
2. **Stabilise environment scripts** – Audit `scripts/run_tests_ci.ps1` for missing
   Qt overrides, ensuring GPU (D3D11) defaults apply when `PSS_HEADLESS` is unset
   and that headless executions honour the values from `tests/_qt_headless.py`.
3. **Fix flaky suites** – Prioritise `tests/ui/` and `tests/integration/` flows that
   rely on timing-sensitive Qt operations. Use the per-suite commands listed above
   to iterate quickly while inspecting logs in `reports/tests/`.
4. **Document findings** – Update the Phase 4 testing plan and relevant reports
   under `docs/` with remediation outcomes, linking to captured artefacts for CI
   traceability.

Following this plan keeps Windows parity aligned with Linux runners and ensures
future contributors can reproduce, diagnose, and resolve platform-specific test
failures consistently.
