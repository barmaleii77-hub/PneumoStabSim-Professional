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
$env:PSS_ENV_PRESET = $LogPreset
$profileScript = python -m tools.env_profiles --preset $LogPreset --format powershell --no-header
if ($LASTEXITCODE -ne 0) {
    throw "Failed to resolve environment preset $LogPreset"
}
if ($profileScript) {
    Invoke-Expression $profileScript
}
Write-Host "ℹ️ Logging preset: $LogPreset" -ForegroundColor Cyan
python "$PSScriptRoot/app.py" @Args
