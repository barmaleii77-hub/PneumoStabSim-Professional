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

GOTO :help

:autonomous
SHIFT
python -m tools.autonomous_check %*
GOTO :eof

:autonomous_trace
SHIFT
python -m tools.autonomous_check --launch-trace %*
GOTO :eof

:verify
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
REM Прямой fallback (обходит повреждённый pytest.exe launcher). Использует текущий интерпретатор.
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
REM Use Ruff formatter via python to preserve virtualenv
python -m ruff format app.py src tests tools
GOTO :eof

:security
python -m tools.ci_tasks security
GOTO :eof

:perf_check
SHIFT
REM Collect baseline performance metrics (default scenario)
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
uv run --locked -- python -c "import yaml; print(yaml.__version__)"
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

:launcher
REM Запуск интерактивного лаунчера (pythonw, если доступен)
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
ECHO   autonomous-check [--args]    ^| autonomous-check-trace
ECHO   verify ^| check ^| lint ^| typecheck ^| qml-lint ^| format
ECHO   test ^| test-unit ^| test-integration ^| test-ui
ECHO   pytest-direct  (fallback: python -m pytest)
ECHO   security ^| perf-check ^| settings-migrate
ECHO.
ECHO Utilities:
ECHO   sanitize ^| trace-launch ^| analyze-logs
ECHO   uv-sync ^| uv-run CMD ^| run [app args]
ECHO   cipilot-env ^| launcher
EXIT /B 0
