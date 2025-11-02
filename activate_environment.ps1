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

function Normalize-WorkspacePath {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Value
    )

    $adjusted = $Value -replace '/workspace/PneumoStabSim-Professional', $projectRoot
    $adjusted = $adjusted -replace '/', '\\'

    return $adjusted
}

function Get-PathSegments {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Value
    )

    $segments = $Value -split ';'
    if ($segments.Count -eq 1 -and $Value -match ':(?=/)') {
        $segments = $Value -split ':(?=/)'
    }

    return $segments
}

$pathVariables = @{
    'PROJECT_ROOT'     = $false
    'PYTHONPATH'       = $true
    'QT_PLUGIN_PATH'   = $false
    'QML2_IMPORT_PATH' = $false
    'QML_IMPORT_PATH'  = $false
}

foreach ($entry in $pathVariables.GetEnumerator()) {
    $currentValue = (Get-Item -Path "Env:$($entry.Key)" -ErrorAction SilentlyContinue).Value
    if (-not $currentValue) {
        continue
    }

    if ($entry.Value) {
        $segments = Get-PathSegments -Value $currentValue
        $normalized = @()
        foreach ($segment in $segments) {
            if (-not [string]::IsNullOrWhiteSpace($segment)) {
                $normalized += (Normalize-WorkspacePath -Value $segment.Trim())
            }
        }

        $currentValue = $normalized -join ';'
    } else {
        $currentValue = Normalize-WorkspacePath -Value $currentValue
    }

    Set-Item -Path "Env:$($entry.Key)" -Value $currentValue
}

Write-Host "[env] Variables loaded from .env" -ForegroundColor Cyan

$venvPath = Join-Path $projectRoot ".venv"
$venvActivate = Join-Path $venvPath "Scripts/Activate.ps1"

if ($preferredPython -and (Get-Command Get-PythonVersionFromExecutable -ErrorAction SilentlyContinue)) {
    $venvPython = Join-Path $venvPath 'Scripts' 'python.exe'
    if (Test-Path $venvPython) {
        $venvVersion = Get-PythonVersionFromExecutable -Executable $venvPython
        if ($venvVersion -and $venvVersion -lt $preferredPython.Version) {
            $recreateMessage = "[env] Existing .venv uses Python $venvVersion – recreating with $($preferredPython.Version)"
            Write-Host $recreateMessage -ForegroundColor Yellow
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
            $uvExecutable = if ($uv.Path) { $uv.Path } else { $uv.Source }
            & $uvExecutable 'sync'
        } catch {
            Write-Host "[env] uv sync failed: $_" -ForegroundColor Red
            $uv = $null
        } finally {
            Pop-Location
        }
    }

    if (-not $uv) {
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
