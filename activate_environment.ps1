# ============================================================================
# PneumoStabSim Professional - Environment Activation Script
# Активация окружения в текущей PowerShell сессии
# ============================================================================

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $projectRoot ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "[env] .env not found – run setup_environment.py" -ForegroundColor Yellow
    return
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^[A-Za-z_][A-Za-z0-9_]*=') {
        $key, $value = $_.Split('=', 2)
      $env:$key = $value
    }
}

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
