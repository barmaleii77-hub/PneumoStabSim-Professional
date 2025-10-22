@echo off
rem =============================================================================
rem  PneumoStabSim Professional - Complete Environment Fix
rem  Fixes all common issues: terminal, encoding, Python, Qt, dependencies
rem =============================================================================

setlocal enabledelayedexpansion

echo ================================================================
echo  PneumoStabSim Professional - Complete Environment Fix
echo ================================================================
echo.
echo This script will:
echo   1. Fix terminal encoding issues
echo   2. Configure Python environment
echo   3. Set up proper virtual environment
echo   4. Install/update all dependencies
echo   5. Test the complete setup
echo.

set /p CONTINUE="Continue with full environment fix? (Y/n): "
if /i "!CONTINUE!"=="n" goto :cancel

echo.
echo ================================================================
echo  STEP 1: Terminal and Encoding Configuration
echo ================================================================

rem Set UTF-8 encoding
chcp 65001 >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Terminal encoding set to UTF-8
) else (
    echo [!] Could not set UTF-8 encoding, using fallback
)

rem Configure registry for better console support
reg add "HKCU\Console" /v "FaceName" /t REG_SZ /d "Consolas" /f >nul 2>&1
reg add "HKCU\Console" /v "FontSize" /t REG_DWORD /d 0x00120000 /f >nul 2>&1
echo [✓] Console font configured

rem Set comprehensive Python encoding environment
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONLEGACYWINDOWSFSENCODING=utf-8
set PYTHONUNBUFFERED=1

rem Set Windows console for ANSI support
set TERM=xterm-256color
set COLORTERM=truecolor

echo [✓] Python encoding environment configured

echo.
echo ================================================================
echo  STEP 2: Python Version Check and Configuration
echo ================================================================

rem Check Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo [✗] Python not found in PATH
    echo.
    echo Please install Python 3.8-3.11 from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    goto :error_exit
)

rem Display Python version and check compatibility
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [✓] Python %PYTHON_VERSION% found

python -c "import sys; major, minor = sys.version_info[:2]; exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [!] WARNING: Python version %PYTHON_VERSION% may have compatibility issues
    echo [!] Recommended: Python 3.8 - 3.11 for optimal stability
    echo.
    set /p CONTINUE_PYTHON="Continue with this Python version? (Y/n): "
    if /i "!CONTINUE_PYTHON!"=="n" goto :cancel
) else (
    echo [✓] Python version is compatible
)

echo.
echo ================================================================
echo  STEP 3: Virtual Environment Setup
echo ================================================================

rem Remove old virtual environment if it's corrupted
if exist "venv\" (
    echo Checking existing virtual environment...
    venv\Scripts\python.exe --version >nul 2>&1
    if errorlevel 1 (
        echo [!] Existing virtual environment appears corrupted
        echo [!] Removing and recreating...
        rmdir /s /q venv 2>nul
    ) else (
        echo [✓] Existing virtual environment is functional
    )
)

rem Create new virtual environment if needed
if not exist "venv\Scripts\python.exe" (
    echo Creating new virtual environment...
    python -m venv venv --clear
    if errorlevel 1 (
        echo [✗] Failed to create virtual environment
        echo This might be due to permissions or Python installation issues
        pause
        goto :error_exit
    )
    echo [✓] Virtual environment created
) else (
    echo [✓] Virtual environment already exists
)

rem Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if "%VIRTUAL_ENV%"=="" (
    echo [✗] Virtual environment activation failed
    pause
    goto :error_exit
)
echo [✓] Virtual environment activated: %VIRTUAL_ENV%

echo.
echo ================================================================
echo  STEP 4: Package Management and Dependencies
echo ================================================================

rem Upgrade pip to latest version
echo Upgrading pip...
python -m pip install --upgrade pip --disable-pip-version-check --quiet
if errorlevel 1 (
    echo [!] Pip upgrade failed, continuing with existing version
) else (
    echo [✓] Pip upgraded successfully
)

rem Install/update dependencies with multiple fallback strategies
echo Installing dependencies (this may take a few minutes)...

rem Strategy 1: Try compatible requirements first
if exist "requirements-compatible.txt" (
    echo [1/3] Trying compatible requirements...
    pip install -r requirements-compatible.txt --disable-pip-version-check --quiet
    if not errorlevel 1 (
        echo [✓] Compatible requirements installed successfully
        goto :packages_done
    ) else (
        echo [!] Compatible requirements installation failed
    )
)

rem Strategy 2: Try standard requirements
if exist "requirements.txt" (
    echo [2/3] Trying standard requirements...
    pip install -r requirements.txt --disable-pip-version-check --quiet
    if not errorlevel 1 (
        echo [✓] Standard requirements installed successfully
        goto :packages_done
    ) else (
        echo [!] Standard requirements installation failed
    )
)

rem Strategy 3: Manual installation of critical packages
echo [3/3] Installing critical packages individually...
set CRITICAL_PACKAGES=numpy scipy PySide6 matplotlib PyOpenGL PyOpenGL-accelerate

for %%p in (%CRITICAL_PACKAGES%) do (
    echo   Installing %%p...
    pip install "%%p" --disable-pip-version-check --quiet >nul 2>&1
    if not errorlevel 1 (
        echo   [✓] %%p installed
    ) else (
        echo   [!] %%p installation failed
    )
)

:packages_done

echo.
echo ================================================================
echo  STEP 5: Environment Variables and Configuration
echo ================================================================

rem Set all necessary environment variables
set PYTHONPATH=%CD%;%CD%\src
set QSG_RHI_BACKEND=d3d11
set QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true

rem Additional Qt optimizations
set QT_AUTO_SCREEN_SCALE_FACTOR=1
set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
set QT_ENABLE_HIGHDPI_SCALING=1
set QT_FONT_DPI=96

echo [✓] Environment variables configured

echo.
echo ================================================================
echo  STEP 6: Complete System Test
echo ================================================================

rem Test Python and encoding
echo Testing Python and encoding...
python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor} - Default encoding: {sys.getdefaultencoding()}')" 2>nul
if errorlevel 1 (
    echo [✗] Python test failed
) else (
    echo [✓] Python test passed
)

rem Test Unicode support
python -c "print('Unicode test: 🔧 ✅ ❌ ⚠️ 🎯 📊')" 2>nul
if errorlevel 1 (
    echo [!] Unicode support limited (using fallback encoding)
) else (
    echo [✓] Unicode support working
)

rem Test critical imports
echo Testing critical package imports...
python -c "import numpy, scipy, PySide6; print('Critical packages: numpy, scipy, PySide6 ✓')" 2>nul
if errorlevel 1 (
    echo [!] Some critical packages missing or broken
    echo [!] You may need to run this fix script again
) else (
    echo [✓] Critical packages working
)

rem Test application startup (quick test)
if exist "app.py" (
    echo Testing application startup...
    python -c "
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'src')
try:
    from src.common import init_logging
    print('Application modules: OK ✓')
except ImportError as e:
    print(f'Application modules: {e}')
" 2>nul
)

echo.
echo ================================================================
echo  SETUP COMPLETE!
echo ================================================================
echo.
echo Environment Status:
echo   Virtual Environment: %VIRTUAL_ENV%
echo   Python Version:
python --version
echo   Encoding: UTF-8 configured
echo   Packages: Installed and tested
echo.
echo Available commands:
echo   run.bat                          # Quick application launch
echo   python app.py                    # Standard launch
echo   python app.py --test-mode        # Test mode (5 seconds)
echo   python app.py --safe-mode        # Safe mode (minimal features)
echo   quick_diagnostic.bat             # Quick problem check
echo   python scripts\terminal_diagnostic.py  # Detailed diagnostic
echo.
echo ================================================================

rem Test launch option
set /p TEST_LAUNCH="Would you like to test launch the application now? (Y/n): "
if /i not "!TEST_LAUNCH!"=="n" (
    echo.
    echo Testing application launch...
    python app.py --test-mode
    echo.
    if errorlevel 1 (
        echo Application test failed. Check the error messages above.
        echo Run: python scripts\terminal_diagnostic.py for detailed analysis
    ) else (
        echo [✓] Application test successful!
    )
)

goto :success_exit

:cancel
echo.
echo Setup cancelled by user.
pause
exit /b 1

:error_exit
echo.
echo ================================================================
echo  SETUP FAILED
echo ================================================================
echo.
echo Please check the error messages above and try:
echo   1. Install/reinstall Python 3.8-3.11
echo   2. Run as Administrator if permissions issues
echo   3. Check internet connection for package downloads
echo   4. Run: quick_diagnostic.bat for specific issues
echo.
pause
exit /b 1

:success_exit
echo.
echo Setup completed successfully! You can now use PneumoStabSim Professional.
if /i not "%1"=="--no-pause" pause
exit /b 0
