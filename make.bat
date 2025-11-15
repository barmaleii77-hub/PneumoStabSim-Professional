@echo off
REM Windows-friendly wrapper for common project tasks
REM Usage: make <target> [extra args]

IF "%~1"=="" GOTO :help

IF /I "%~1"=="autonomous-check" GOTO :autonomous
IF /I "%~1"=="verify" GOTO :verify
IF /I "%~1"=="check" GOTO :check
IF /I "%~1"=="test" GOTO :test
IF /I "%~1"=="lint" GOTO :lint
IF /I "%~1"=="typecheck" GOTO :typecheck
IF /I "%~1"=="qml-lint" GOTO :qmllint
IF /I "%~1"=="sanitize" GOTO :sanitize
IF /I "%~1"=="cipilot-env" GOTO :cipilot

GOTO :help

:autonomous
SHIFT
python -m tools.autonomous_check %*
GOTO :eof

:verify
SHIFT
python -m tools.autonomous_check --task verify --launch-trace %*
GOTO :eof

:check
SHIFT
python -m tools.autonomous_check --task verify %*
GOTO :eof

:test
SHIFT
python -m tools.autonomous_check --task test %*
GOTO :eof

:lint
SHIFT
python -m tools.autonomous_check --task lint %*
GOTO :eof

:typecheck
SHIFT
python -m tools.autonomous_check --task typecheck %*
GOTO :eof

:qmllint
SHIFT
python -m tools.autonomous_check --task qml-lint %*
GOTO :eof

:sanitize
python -m tools.project_sanitize --report-history 5
GOTO :eof

:cipilot
SHIFT
PowerShell -ExecutionPolicy Bypass -File scripts\load_cipilot_env.ps1 %*
GOTO :eof

:help
ECHO Usage: make [autonomous-check^|verify^|check^|test^|lint^|typecheck^|qml-lint^|sanitize^|cipilot-env] [extra args]
EXIT /B 0
