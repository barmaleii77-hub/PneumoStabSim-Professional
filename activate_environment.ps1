# ============================================================================
# PneumoStabSim Professional - Environment Activation Script
# Активация окружения в текущей PowerShell сессии
# ============================================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    Write-Verbose "[env] Failed to configure console encoding: $_"
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $projectRoot ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "[env] .env not found – run setup_environment.py" -ForegroundColor Yellow
    return
}

Get-Content -Path $envFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()

    if ($line.Length -eq 0 -or $line.StartsWith('#')) {
        return
    }

    $delimiterIndex = $line.IndexOf('=' )
    if ($delimiterIndex -lt 1) {
        return
    }

    $key = $line.Substring(0, $delimiterIndex).Trim()
    $value = $line.Substring($delimiterIndex + 1)
    Set-Item -Path "Env:$key" -Value $value
}

if (-not $env:LANG) { Set-Item -Path Env:LANG -Value 'C.UTF-8' }
if (-not $env:LC_ALL) { Set-Item -Path Env:LC_ALL -Value 'C.UTF-8' }

Write-Host "[env] Variables loaded from .env" -ForegroundColor Cyan
if (Test-Path (Join-Path $projectRoot ".venv/Scripts/Activate.ps1")) {
    if ($env:VIRTUAL_ENV) {
        Write-Host "[env] Virtual environment already active: $env:VIRTUAL_ENV" -ForegroundColor Cyan
    } else {
        & (Join-Path $projectRoot ".venv/Scripts/Activate.ps1")
        Write-Host "[env] Activated .venv" -ForegroundColor Green
    }
} else {
    Write-Host "[env] .venv not found – run setup_environment.py" -ForegroundColor Yellow
}

Write-Host "[env] Qt backend: $env:QSG_RHI_BACKEND (Qt $env:QT_VERSION)" -ForegroundColor Cyan
