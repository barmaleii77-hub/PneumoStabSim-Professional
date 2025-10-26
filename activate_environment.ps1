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

$pythonHelper = Join-Path $projectRoot 'tools' 'powershell' 'python_environment.ps1'
if (Test-Path $pythonHelper) {
    . $pythonHelper
} else {
    Write-Verbose "[env] Python helper '$pythonHelper' not found; falling back to default interpreter discovery."
}

$preferredPython = $null
if (Get-Command Get-PreferredPython -ErrorAction SilentlyContinue) {
    $preferredPython = Get-PreferredPython
    if ($preferredPython) {
        Write-Host "[env] Preferred Python: $($preferredPython.Version) ($($preferredPython.Path))" -ForegroundColor Cyan
    } else {
        Write-Host "[env] Could not determine preferred Python interpreter" -ForegroundColor Yellow
    }
}

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

if ($preferredPython -and (Get-Command Get-PythonVersionFromExecutable -ErrorAction SilentlyContinue)) {
    $venvPython = Join-Path $venvPath 'Scripts' 'python.exe'
    if (Test-Path $venvPython) {
        $venvVersion = Get-PythonVersionFromExecutable -Executable $venvPython
        if ($venvVersion -and $venvVersion -lt $preferredPython.Version) {
            Write-Host "[env] Existing .venv uses Python $venvVersion – recreating with $($preferredPython.Version)" -ForegroundColor Yellow
            try {
                Remove-Item -Recurse -Force $venvPath
            } catch {
                Write-Error "[env] Failed to remove outdated .venv: $_"
                return
            }
        }
    }
}

if (-not (Test-Path $venvPath)) {
    Write-Host "[env] .venv not found – bootstrapping via uv" -ForegroundColor Yellow
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
        if ($preferredPython) {
            $env:UV_PYTHON = $preferredPython.Path
            Write-Host "[env] Using UV_PYTHON=$($preferredPython.Path)" -ForegroundColor Cyan
        }

        Push-Location $projectRoot
        try {
            & $uv.Source sync
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "[env] uv is not available, falling back to python -m venv" -ForegroundColor Yellow
        $pythonExecutable = if ($preferredPython) { $preferredPython.Path } else { 'python' }
        & $pythonExecutable '-m' 'venv' $venvPath
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
