@echo off
rem =============================================================================
rem  PneumoStabSim Professional - Virtual Environment Setup (Enhanced)
rem  Fixed: Terminal encoding, Python compatibility, Unicode support
rem =============================================================================

rem Configure terminal first
call fix_terminal.bat

echo.
echo ================================================================
echo  PneumoStabSim Professional - Virtual Environment Setup
echo ================================================================
echo.

rem Detect available Python command with preference for supported minors (3.11 -> 3.10 -> 3.9)
set "PYTHON_CMD="
py -3.11 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3.11"
if not defined PYTHON_CMD (
    py -3.10 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.10"
)
if not defined PYTHON_CMD (
    py -3.9 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.9"
)
if not defined PYTHON_CMD (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)
if not defined PYTHON_CMD (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
    python3 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python3"
)
if not defined PYTHON_CMD (
    echo ERROR: Python not found or not working
    echo Please install Python 3.9-3.11 and ensure it's in PATH
    pause
    exit /b 1
)

rem Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    
    rem Detect available Python command with preference for supported minors
    set "PYTHON_CMD="
    rem Try py -3.11
    if not defined PYTHON_CMD (
        py -3.11 -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=py -3.11"
    )
    rem Try py -3.10
    if not defined PYTHON_CMD (
        py -3.10 -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=py -3.10"
    )
    rem Try py -3.9
    if not defined PYTHON_CMD (
        py -3.9 -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=py -3.9"
    )
    rem Generic py -3 as fallback
    if not defined PYTHON_CMD (
        py -3 -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=py -3"
    )
    rem Fallbacks: python, python3
    if not defined PYTHON_CMD (
        python -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
    if not defined PYTHON_CMD (
        python3 -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python3"
    )
    if not defined PYTHON_CMD (
        echo ERROR: Python not found or not working
        echo Please install Python 3.8+ and ensure it's in PATH
        pause
        exit /b 1
    )
    
    rem Check Python version before creating venv (warn outside 3.8-3.13), auto-continue
    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
    if errorlevel 1 (
        echo WARNING: Python version may not be fully compatible (recommended 3.8 - 3.13). Continuing...
    )
    
    %PYTHON_CMD% -m venv venv --clear
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo This might be due to Python version or permissions issues
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
    echo.
)

rem Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

rem Verify activation
if "%VIRTUAL_ENV%"=="" (
    echo ERROR: Virtual environment activation failed
    pause
    exit /b 1
)

rem Upgrade pip with better error handling
echo Upgrading pip...
python -m pip install --upgrade pip --disable-pip-version-check --no-warn-script-location
if errorlevel 1 (
    echo Warning: pip upgrade failed, continuing with existing version
)

rem Install requirements with compatibility fixes
echo Installing project dependencies...
if exist "requirements.txt" (
    echo Installing from requirements.txt...
    
    rem First try normal installation
    pip install -r requirements.txt --disable-pip-version-check --no-warn-script-location
    if errorlevel 1 (
        echo Installation failed, trying with compatibility flags...
        
        rem Try with --force-reinstall for problematic packages
        pip install -r requirements.txt --force-reinstall --no-deps --disable-pip-version-check
        if errorlevel 1 (
            echo Some packages failed to install. Installing critical packages manually...
            
            rem Install critical packages one by one with fallbacks
            echo Installing numpy...
            pip install "numpy>=1.21.0,<2.0.0" --disable-pip-version-check || (
                pip install "numpy==1.24.3" --disable-pip-version-check
            )
            
            echo Installing scipy...
            pip install "scipy>=1.9.0,<2.0.0" --disable-pip-version-check || (
                pip install "scipy==1.10.1" --disable-pip-version-check
            )
            
            echo Installing PySide6...
            pip install "PySide6>=6.4.0,<7.0.0" --disable-pip-version-check || (
                pip install "PySide6==6.6.0" --disable-pip-version-check
            )
            
            echo Installing matplotlib...
            pip install "matplotlib>=3.5.0" --disable-pip-version-check
            
            echo Installing PyOpenGL...
            pip install "PyOpenGL>=3.1.0" "PyOpenGL-accelerate>=3.1.0" --disable-pip-version-check

            echo Installing python-dotenv...
            pip install "python-dotenv>=1.0.0" --disable-pip-version-check
        )
    )
) else (
    echo WARNING: requirements.txt not found, installing basic packages...
    
    rem Install basic packages with version constraints for compatibility
    pip install "numpy>=1.21.0,<2.0.0" "scipy>=1.9.0,<2.0.0" "PySide6>=6.4.0,<7.0.0" "matplotlib>=3.5.0" "PyOpenGL>=3.1.0" "PyOpenGL-accelerate>=3.1.0" "python-dotenv>=1.0.0" --disable-pip-version-check
)

rem Set environment variables for optimal operation
echo Setting environment variables...
set PYTHONPATH=%CD%;%CD%\src
set QSG_RHI_BACKEND=d3d11
set QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true
set PYTHONOPTIMIZE=0
set PYTHONUNBUFFERED=1

rem Additional Python encoding settings
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONLEGACYWINDOWSFSENCODING=utf-8

rem Qt-specific settings for better compatibility
set QT_AUTO_SCREEN_SCALE_FACTOR=1
set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
set QT_ENABLE_HIGHDPI_SCALING=1

echo.
echo ================================================================
echo  Virtual Environment Ready!
echo ================================================================
echo.
echo Environment: %VIRTUAL_ENV%
echo Python version:
python --version
echo Pip version:
pip --version
echo.
echo Installed critical packages:
pip list | findstr /C:"numpy" /C:"scipy" /C:"PySide6" /C:"matplotlib" /C:"PyOpenGL" 2>nul
echo.
echo Unicode test:
python -c "print('🔧 Encoding test: ✅ Success! 🎯')" 2>nul || echo "Unicode support: Limited (fallback mode)"
echo.
echo Available commands:
echo   python app.py                    # Run main application
echo   python app.py --test-mode        # Test mode (auto-close 5s)
echo   python app.py --debug            # Debug mode
echo   python scripts\check_environment.py    # Environment check
echo   python scripts\comprehensive_test.py   # Full project test
echo   deactivate                       # Exit virtual environment
echo.
echo ================================================================
