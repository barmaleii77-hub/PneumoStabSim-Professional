@echo off
chcp 65001 >nul
REM Python launcher wrapper to bypass Windows App Execution Aliases
REM This script ensures the correct Python 3.13 installation is used

set PYTHON_EXE=C:\Users\Алексей\AppData\Local\Programs\Python\Python313\python.exe

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python 3.13 not found at %PYTHON_EXE%
    echo Please install Python 3.13 or update the path in python.bat
    exit /b 1
)

"%PYTHON_EXE%" %*
