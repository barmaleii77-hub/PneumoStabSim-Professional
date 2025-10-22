@echo off
echo ================================================================
echo  PneumoStabSim Professional - Environment Status
echo ================================================================
echo.

rem Check if virtual environment exists
if exist "venv\Scripts\python.exe" (
    echo [✓] Virtual environment: EXISTS

    rem Check if currently activated
    if "%VIRTUAL_ENV%"=="" (
        echo [!] Virtual environment: NOT ACTIVATED
        echo.
        echo To activate, run: activate_venv.bat
    ) else (
        echo [✓] Virtual environment: ACTIVATED
        echo     Path: %VIRTUAL_ENV%
    )

    echo.
    echo Python version:
    venv\Scripts\python.exe --version

    echo.
    echo Installed packages:
    venv\Scripts\pip.exe list --format=freeze | findstr /C:"numpy" /C:"scipy" /C:"PySide6" /C:"matplotlib" /C:"PyOpenGL"

) else (
    echo [✗] Virtual environment: NOT FOUND
    echo.
    echo To create, run: activate_venv.bat
)

echo.
rem Check project files
echo Project structure:
if exist "app.py" (
    echo [✓] app.py
) else (
    echo [✗] app.py - MISSING
)

if exist "requirements.txt" (
    echo [✓] requirements.txt
) else (
    echo [✗] requirements.txt - MISSING
)

if exist "src\" (
    echo [✓] src/ directory
) else (
    echo [✗] src/ directory - MISSING
)

echo.
rem Check .NET project
if exist "PneumoStabSim-Professional.sln" (
    echo [✓] .NET solution file
    dotnet --version >nul 2>&1
    if errorlevel 1 (
        echo [!] .NET SDK: NOT FOUND
    ) else (
        echo [✓] .NET SDK: AVAILABLE
        dotnet --version
    )
) else (
    echo [✗] .NET solution - MISSING
)

echo.
echo ================================================================
