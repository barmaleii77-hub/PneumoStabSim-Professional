@echo off
REM Windows-friendly wrapper for common project tasks
REM Usage: make <target> [extra args]

IF "%~1"=="" GOTO :help

REM Core quality gates
IF /I "%~1"=="autonomous-check" GOTO :autonomous
IF /I "%~1"=="autonomous-check-trace" GOTO :autonomous_trace
IF /I "%~1"=="verify" GOTO :verify
IF /I "%~1"=="check" GOTO :check
IF /I "%~1"=="test" GOTO :test
IF /I "%~1"=="test-unit" GOTO :test_unit
IF /I "%~1"=="test-integration" GOTO :test_integration
IF /I "%~1"=="test-ui" GOTO :test_ui
IF /I "%~1"=="pytest-direct" GOTO :pytest_direct
IF /I "%~1"=="lint" GOTO :lint
IF /I "%~1"=="typecheck" GOTO :typecheck
IF /I "%~1"=="qml-lint" GOTO :qmllint
IF /I "%~1"=="format" GOTO :format
IF /I "%~1"=="security" GOTO :security
IF /I "%~1"=="perf-check" GOTO :perf_check
IF /I "%~1"=="settings-migrate" GOTO :settings_migrate

REM Environment and utilities
IF /I "%~1"=="uv-sync" GOTO :uvsync
IF /I "%~1"=="uv-run" GOTO :uvrun
IF /I "%~1"=="run" GOTO :run
IF /I "%~1"=="trace-launch" GOTO :trace
IF /I "%~1"=="analyze-logs" GOTO :analyze_logs
IF /I "%~1"=="sanitize" GOTO :sanitize
IF /I "%~1"=="cipilot-env" GOTO :cipilot
IF /I "%~1"=="launcher" GOTO :launcher
IF /I "%~1"=="env-check" GOTO :env_check
IF /I "%~1"=="env-report" GOTO :env_report
IF /I "%~1"=="hdr-verify" GOTO :hdr_verify
IF /I "%~1"=="render-diagnostics" GOTO :render_diagnostics
IF /I "%~1"=="smoke-render" GOTO :smoke_render

GOTO :help

:smoke_render
REM Sequential smoke: pytest filter then safe test-mode app launch
SHIFT
SET "PY_ARGS=%*"
IF "%PY_ARGS%"=="" SET "PY_ARGS=-k SimulationRoot -q"
python -m pytest %PY_ARGS%
IF ERRORLEVEL 1 (
  ECHO Pytest failed (skip app launch). Exit code %ERRORLEVEL%.
  GOTO :eof
)
where uv >NUL 2>&1
IF ERRORLEVEL 1 (
  python app.py --safe --test-mode
) ELSE (
  uv run --locked -- python app.py --safe --test-mode
)
GOTO :eof

:render_diagnostics
SHIFT
python -m tools.render_diagnostics %*
GOTO :eof

:autonomous
SHIFT
python -m tools.autonomous_check %*
GOTO :eof

:autonomous_trace
SHIFT
python -m tools.autonomous_check --launch-trace %*
GOTO :eof

:verify
REM --- Extended verification: migrations, audit, HDR verify, receiver smoke, autonomous check ---
python tools/migrations/apply.py --settings config/app_settings.json --migrations config/migrations --in-place --verbose
python tools/migrations/audit_status.py
python tools/verify_hdr_assets.py || echo HDR verify failed
REM Use standalone mode to avoid pytest launcher issues
python tests/receiver/test_b3_integration.py --standalone
python -m tools.autonomous_check --task verify --launch-trace
GOTO :eof

:check
python -m tools.autonomous_check --task verify
GOTO :eof

:test
python -m tools.autonomous_check --task test
GOTO :eof

:test_unit
python -m tools.ci_tasks test-unit
GOTO :eof

:test_integration
python -m tools.ci_tasks test-integration
GOTO :eof

:test_ui
python -m tools.ci_tasks test-ui
GOTO :eof

:pytest_direct
SHIFT
python -m pytest %*
GOTO :eof

:lint
python -m tools.autonomous_check --task lint
GOTO :eof

:typecheck
python -m tools.autonomous_check --task typecheck
GOTO :eof

:qmllint
python -m tools.autonomous_check --task qml-lint
GOTO :eof

:format
REM Ruff formatter (preserve virtualenv)
python -m ruff format app.py src tests tools
GOTO :eof

:security
python -m tools.ci_tasks security
GOTO :eof

:perf_check
SHIFT
python -m tools.performance_monitor --scenario default %*
GOTO :eof

:settings_migrate
SHIFT
python -m tools.migrations.apply --in-place --verbose %*
GOTO :eof

:uvsync
where uv >NUL 2>&1
IF ERRORLEVEL 1 (
  ECHO Error: 'uv' is not installed. Run "python scripts\bootstrap_uv.py" first.
  GOTO :eof
)
uv sync --frozen --extra dev
REM Print versions (PySide6, Qt, yaml) for sanity check
uv run --locked -- python -c "import PySide6, PySide6.QtCore as QC, yaml; print('PySide6', PySide6.__version__, 'Qt', QC.qVersion(), 'yaml', yaml.__version__)"
GOTO :eof

:uvrun
SHIFT
where uv >NUL 2>&1
IF ERRORLEVEL 1 (
  ECHO Error: 'uv' is not installed. Run "python scripts\bootstrap_uv.py" first.
  GOTO :eof
)
IF "%~1"=="" (
  ECHO Error: command is required. Example: make uv-run pytest -vv
  GOTO :eof
)
uv run --locked -- %*
GOTO :eof

:run
SHIFT
where uv >NUL 2>&1
IF ERRORLEVEL 1 (
  ECHO Error: 'uv' is not installed. Run "python scripts\bootstrap_uv.py" first.
  GOTO :eof
)
uv run --locked -- python app.py %*
GOTO :eof

:trace
SHIFT
python -m tools.trace_launch %*
GOTO :eof

:analyze_logs
SHIFT
python -m tools.ci_tasks analyze-logs %*
GOTO :eof

:sanitize
python -m tools.project_sanitize --report-history 5
GOTO :eof

:cipilot
SHIFT
PowerShell -ExecutionPolicy Bypass -File scripts\load_cipilot_env.ps1 %*
GOTO :eof

:env_check
REM Quick environment diagnostics (does not start full UI)
python app.py --env-check
GOTO :eof

:env_report
SHIFT
REM Save environment report (default path if none supplied)
SET "TARGET=%~1"
IF "%TARGET%"=="" SET "TARGET=reports\quality\env_report.md"
python app.py --env-report="%TARGET%" --env-check
ECHO Report written: %TARGET%
GOTO :eof

:hdr_verify
python tools/verify_hdr_assets.py
GOTO :eof

:launcher
SET "LAUNCHER=scripts\interactive_launcher.py"
IF EXIST .venv\Scripts\pythonw.exe (
  .venv\Scripts\pythonw.exe "%LAUNCHER%"
) ELSE (
  python "%LAUNCHER%"
)
GOTO :eof

:help
ECHO Usage: make ^<target^> [extra args]
ECHO.
ECHO Quality gates:
ECHO   autonomous-check ^| autonomous-check-trace ^| verify ^| check
ECHO   lint ^| typecheck ^| qml-lint ^| format
ECHO   test ^| test-unit ^| test-integration ^| test-ui ^| pytest-direct
ECHO.
ECHO Smoke:
ECHO   smoke-render [pytest args]  ^(pytest + safe UI launch^)
ECHO.
ECHO Render diagnostics:
ECHO   render-diagnostics [--qml-snapshot]
ECHO.
ECHO Environment / diagnostics:
ECHO   uv-sync ^| uv-run CMD ^| cipilot-env ^| env-check ^| env-report [path] ^| hdr-verify
ECHO.
ECHO Utilities:
ECHO   sanitize ^| trace-launch ^| analyze-logs ^| run [app args] ^| launcher
ECHO.
ECHO Examples:
ECHO   make smoke-render -k SimulationRoot -q
ECHO   make render-diagnostics --qml-snapshot
EXIT /B 0
