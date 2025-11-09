#!/usr/bin/env pwsh
param(
    [ValidateSet('normal', 'debug', 'trace')]
    [string]$LogPreset = 'normal',

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)
$ErrorActionPreference = 'Stop'
& "$PSScriptRoot/activate_venv.bat" | Out-Null
$env:PSS_LOG_PRESET = $LogPreset
Write-Host "ℹ️ Logging preset: $LogPreset" -ForegroundColor Cyan
python "$PSScriptRoot/app.py" @Args
