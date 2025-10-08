@echo off
rem =============================================================================
rem  PneumoStabSim Professional - Terminal & Encoding Configuration
rem  Fixes: Terminal encoding, Python version compatibility, Unicode issues
rem =============================================================================

echo Configuring terminal environment for PneumoStabSim Professional...
echo.

rem Set UTF-8 encoding for current session
chcp 65001 >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Terminal encoding set to UTF-8 ^(65001^)
) else (
    echo [!] Warning: Could not set UTF-8 encoding
)

rem Set console properties for better Unicode support
reg add "HKCU\Console" /v "FaceName" /t REG_SZ /d "Consolas" /f >nul 2>&1
reg add "HKCU\Console" /v "FontSize" /t REG_DWORD /d 0x00120000 /f >nul 2>&1

rem Set environment variables for Python Unicode support
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSFSENCODING=utf-8
set PYTHONUTF8=1

rem Set Windows console mode for ANSI support
set TERM=xterm-256color
set COLORTERM=truecolor

rem Configure Qt for better text rendering
set QT_LOGGING_RULES=qt.qpa.fonts.debug=false
set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
set QT_FONT_DPI=96

echo [✓] Python encoding variables configured
echo [✓] Console properties updated
echo [✓] Qt text rendering optimized
echo.

rem Check Python version compatibility
python -c "import sys; major, minor = sys.version_info[:2]; print(f'Python {major}.{minor} detected'); exit(0 if (3, 8) <= (major, minor) <= (3, 11) else 1)" 2>nul
if %errorlevel% neq 0 (
    echo [!] WARNING: Python version compatibility issue detected
    echo     Recommended Python versions: 3.8 - 3.11
    echo     Current version may cause issues with some packages
    echo.
)

rem Test Unicode support
python -c "print('🔧 Unicode test: ✅ ❌ ⚠️ 🎯 📊')" 2>nul
if %errorlevel% equ 0 (
    echo [✓] Unicode support test passed
) else (
    echo [!] Unicode support test failed - using fallback encoding
    set PYTHONIOENCODING=utf-8:replace
)

echo.
echo Terminal configuration completed.
echo ============================================================================
