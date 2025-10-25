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

$venvPath = Join-Path $projectRoot ".venv"
$venvActivate = Join-Path $venvPath "Scripts/Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "[env] .venv not found – bootstrapping via uv" -ForegroundColor Yellow
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
        Push-Location $projectRoot
        try {
            & $uv.Source sync
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "[env] uv is not available, falling back to python -m venv" -ForegroundColor Yellow
        python -m venv $venvPath
        $requirements = Join-Path $projectRoot "requirements.txt"
        if (Test-Path $requirements) {
            & (Join-Path $venvPath "Scripts/python.exe") -m pip install -r $requirements
        }
    }
}

if (Test-Path $venvActivate) {
    if ($env:VIRTUAL_ENV) {
        Write-Host "[env] Virtual environment already active: $env:VIRTUAL_ENV" -ForegroundColor Cyan
    } else {
        & $venvActivate
        Write-Host "[env] Activated .venv" -ForegroundColor Green
    }
} elseif (-not (Test-Path $venvPath)) {
    Write-Host "[env] Virtual environment setup failed" -ForegroundColor Red
} else {
    Write-Host "[env] .venv detected but activation script missing" -ForegroundColor Yellow
}

Write-Host "[env] Qt backend: $env:QSG_RHI_BACKEND (Qt $env:QT_VERSION)" -ForegroundColor Cyan
