@echo off
setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0
if "%PROJECT_ROOT:~-1%"=="\" set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%
set VENV_PATH=%PROJECT_ROOT%\.venv

echo ===============================================
echo  PneumoStabSim Professional - Python 3.13
echo ===============================================

echo Detecting Python 3.13 interpreter...
set PY_CMD=
for %%C in ("py -3.13" python3.13 python3 python) do (
  for /f "delims=" %%I in ('%%C --version 2^>nul') do (
    set PY_CMD=%%C
    goto :found
  )
)
:found
if not defined PY_CMD (
  echo ERROR: Python 3.13 interpreter not found in PATH.
  exit /b 1
)

echo Using interpreter: %PY_CMD%
if not exist "%VENV_PATH%" (
  echo Creating virtual environment at %VENV_PATH%
  %PY_CMD% -m venv "%VENV_PATH%"
)

call "%VENV_PATH%\Scripts\activate.bat"
if errorlevel 1 exit /b 1

REM --- Upgrade core build tooling ---
python -m pip install --upgrade pip setuptools wheel >nul 2>&1

REM --- Install requirements if files exist (hash‑locked), else skip gracefully ---
if exist "%PROJECT_ROOT%\requirements.txt" (
  if exist "%PROJECT_ROOT%\requirements-compatible.txt" (
    python -m pip install --require-hashes -r "%PROJECT_ROOT%\requirements.txt" -c "%PROJECT_ROOT%\requirements-compatible.txt"
  ) else (
    python -m pip install -r "%PROJECT_ROOT%\requirements.txt"
  )
)
if exist "%PROJECT_ROOT%\requirements-dev.txt" (
  if exist "%PROJECT_ROOT%\requirements-compatible.txt" (
    python -m pip install --require-hashes -r "%PROJECT_ROOT%\requirements-dev.txt" -c "%PROJECT_ROOT%\requirements-compatible.txt"
  ) else (
    python -m pip install -r "%PROJECT_ROOT%\requirements-dev.txt"
  )
)

REM --- Ensure PySide6 QtQuick3D is present (idempotent) ---
python -c "import PySide6.QtQuick3D" 2>nul || python -m pip install --upgrade "PySide6==6.10.*"

REM --- Optional one‑shot environment setup script ---
if exist "%PROJECT_ROOT%\setup_environment.py" (
  python "%PROJECT_ROOT%\setup_environment.py" || echo WARNING: setup_environment.py failed
)

echo.
if defined PSS_NONINTERACTIVE (
  echo Environment ready (non-interactive).
  exit /b 0
) else (
  echo Environment ready. Run "deactivate" to exit.
  cmd /k
)
