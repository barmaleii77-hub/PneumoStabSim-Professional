@echo off
rem =============================================================================
rem  PneumoStabSim Professional - Enhanced Quick Launcher (py command)
rem  Automatic environment setup with encoding and compatibility fixes
rem =============================================================================

echo ================================================================
echo  PneumoStabSim Professional - Enhanced Quick Launcher (py)
echo ================================================================

rem Configure terminal encoding first
call fix_terminal.bat 2>nul || (
    rem Fallback terminal configuration if fix_terminal.bat not available
    chcp 65001 >nul 2>&1
    set PYTHONIOENCODING=utf-8
    echo [✓] Basic terminal configuration applied
)

echo.

rem Check if venv exists and works
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Setting up automatically...
    echo.

    rem Run full setup
    if exist "activate_venv.bat" (
        call activate_venv.bat
        if errorlevel 1 (
            echo.
            echo ERROR: Failed to setup virtual environment
            echo Try running: activate_venv.bat manually
            pause
            exit /b 1
        )
    ) else (
        echo ERROR: Setup script not found
        echo Please ensure you're in the correct project directory
        pause
        exit /b 1
    )
) else (
    rem Quick activation of existing venv
    echo Activating existing virtual environment...
    call venv\Scripts\activate.bat

    if "%VIRTUAL_ENV%"=="" (
        echo WARNING: Virtual environment activation may have failed
        echo Trying to continue with py launcher...
    ) else (
        echo [✓] Virtual environment activated: %VIRTUAL_ENV%
    )

    rem Set critical environment variables
    set PYTHONPATH=%CD%;%CD%\src
    set QSG_RHI_BACKEND=opengl
    set QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true

    rem Enhanced encoding settings (don't set PYTHONUTF8 for Python 3.13)
    set PYTHONIOENCODING=utf-8
    set PYTHONLEGACYWINDOWSFSENCODING=utf-8
)

echo.
echo ================================================================
echo Starting PneumoStabSim Professional with py launcher...
echo ================================================================

rem Enhanced error checking using py command
echo Checking Python availability with py launcher...
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python py launcher not available
    echo.
    echo Troubleshooting steps:
    echo 1. Install Python from python.org (includes py launcher)
    echo 2. Check if virtual environment is properly activated
    echo 3. Run: quick_diagnostic.bat for detailed analysis
    echo 4. Reinstall virtual environment: activate_venv.bat
    echo.
    pause
    exit /b 1
)

rem Show which Python version py launcher will use
echo Python version detected:
py --version

rem Check critical imports
echo Testing critical imports...
py -c "import sys, os; sys.path.insert(0, '.'); sys.path.insert(0, 'src')" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Python path configuration may have issues
)

py -c "import numpy, scipy, PySide6" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Some required packages may be missing
    echo This might cause application startup issues
    echo.
    echo Quick fix: Run activate_venv.bat to reinstall packages
    echo.
)

rem Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found
    echo Please ensure you're in the correct project directory
    pause
    exit /b 1
)

echo.
echo [✓] Environment checks passed
echo [✓] Starting application with py launcher and parameters: %*
echo.

rem Run the application with enhanced error handling using py command
py app.py %*

rem Capture exit code
set APP_EXIT_CODE=%ERRORLEVEL%

echo.
echo ================================================================

rem Handle different exit codes (FIXED - removed problematic else)
if %APP_EXIT_CODE% equ 0 (
    echo [✅] Application completed successfully
    goto :success_exit
)

rem Error handling for non-zero exit codes
if %APP_EXIT_CODE% equ 1 (
    echo [!] Application exited with error code %APP_EXIT_CODE%
    echo.
    echo Common solutions:
    echo 1. Check terminal encoding: fix_terminal.bat
    echo 2. Reinstall packages: activate_venv.bat
    echo 3. Run diagnostics: quick_diagnostic.bat
    echo 4. Check logs in logs/ directory
    goto :error_exit
)

if %APP_EXIT_CODE% equ -1073741510 (
    echo [!] Application crashed (Access Violation)
    echo This might be related to graphics drivers or Qt installation
    echo.
    echo Try running with: py app.py --safe-mode
    goto :error_exit
)

if %APP_EXIT_CODE% equ 3221225477 (
    echo [!] Application crashed (segmentation fault equivalent)
    echo This might be related to OpenGL or graphics drivers
    echo.
    echo Try running with: py app.py --legacy
    goto :error_exit
)

rem Default error case
echo [!] Application exited with code %APP_EXIT_CODE%
echo Check logs/ directory for detailed error information
goto :error_exit

:error_exit
rem Only pause on error in interactive mode
if /i not "%1"=="--no-pause" (
    echo.
    echo Press any key to continue...
    pause >nul
)
exit /b %APP_EXIT_CODE%

:success_exit
rem Success path - no additional messages needed
exit /b 0
