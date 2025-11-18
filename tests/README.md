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

1. **Synchronise Python dependencies** (каждый прогон вызывает
   `tools.cross_platform_test_prep`, поэтому шаг можно выполнять через него):
   - Linux/macOS (`make` available): `make cross-platform-prep`
   - Windows / make-less shells: `python -m tools.task_runner cross-platform-prep`
2. **Install Qt runtime** (только при первом запуске либо после обновления
   версии): `python tools/setup_qt.py --qt-version 6.10.0`
3. **Verify graphics backend** (см. подробности в `docs/ENVIRONMENT_SETUP.md`)
   - GPU mode: ensure `PSS_HEADLESS` is unset and `QSG_RHI_BACKEND=d3d11` on Windows.
   - Headless mode: set `PSS_HEADLESS=1` or use the pytest `--pss-headless` flag to
     apply the defaults defined in `tests/_qt_headless.py`.
    - Vulkan smoke: export `QSG_RHI_BACKEND=vulkan` и `VK_ICD_FILENAMES=<путь>` из
      таблицы headless/Vulkan в `docs/ENVIRONMENT_SETUP.md`.

Cross-platform provisioning и запуск автотестов теперь выполняются единым
скриптом `tools.cross_platform_test_prep.py`. Он устанавливает системные Qt-
зависимости, синхронизирует Python окружение (`uv sync --extra dev`), проверяет
импорты `PySide6`/`pytest-qt` и по флагу `--run-tests` запускает `pytest` с
необходимыми headless-параметрами. Для типовых сценариев используйте цели
`make cross-platform-prep` / `make cross-platform-test` или их аналоги в
`python -m tools.task_runner ...` на Windows.

> ℹ️ Модульные и UI-тесты больше не пропускаются при отсутствии Qt-зависимостей.
> `pytest.importorskip("PySide6…")` в тестах теперь вызывает `pytest.fail` с
> подсказкой перезапустить `python -m tools.cross_platform_test_prep --use-uv
> --run-tests`. Это гарантирует единое покрытие на Linux и Windows и помогает
> выявлять ошибки настройки сразу после изменения кода.

Начиная с текущей ревизии, любой пропущенный тест приводит к завершению `pytest`
с ошибкой. Это сделано для того, чтобы непрерывная проверка качества не могла
случайно скрыть проблемы конфигурации. Если требуется временно признать
пропуски (например, при диагностике несовместимого драйвера на Windows),
передайте `--allow-skips` или выставьте `PSS_ALLOW_SKIPPED_TESTS=1`. При первом
же стабильном прогоне флаг следует убрать, а в CI потребуется осмысленный
`CI_SKIP_REASON`. Для ожидаемых пропусков (например, ручных предпросмотров в
headless-среде) используйте маркер в сообщении причины `[pytest-skip-ok]`.

## Running the test suites

### Aggregated quality gate

- Linux/macOS: `make check`
- Windows / make-less shells: `python -m tools.task_runner check`

The aggregated gate performs linting, type checks, shader validation, environment
verification, and smoke/integration pytest sweeps. После каждого изменения кода
запускайте `make cross-platform-test` (или `python -m tools.task_runner
cross-platform-test`) чтобы зафиксировать полный Linux/Windows прогон.

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
- New tests must run on Linux and Windows. Do not mark them as `skip`/`xfail`
  unless the line is annotated with `# pytest-skip-ok` and the CI job sets
  `CI_SKIP_REASON` alongside `PSS_ALLOW_SKIPPED_TESTS=1`.

The manual Canvas preview in `tests/ui/test_canvas_animation_preview.py` is only
meant for interactive Windows/Desktop runs. Automated pipelines now export
`PSS_HEADLESS=1` when invoking `make check` or `scripts/testing_entrypoint.py`,
so this preview case is skipped explicitly on headless backends while the
animation regression test continues to run.

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
