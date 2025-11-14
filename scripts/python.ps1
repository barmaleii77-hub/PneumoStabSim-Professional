#!/usr/bin/env pwsh
# Python launcher wrapper for PowerShell to bypass Windows App Execution Aliases

$PYTHON_EXE = "C:\Users\Алексей\AppData\Local\Programs\Python\Python313\python.exe"

if (-not (Test-Path $PYTHON_EXE)) {
    Write-Error "Python 3.13 not found at $PYTHON_EXE"
    Write-Error "Please install Python 3.13 or update the path in python.ps1"
    exit 1
}

& $PYTHON_EXE @args
