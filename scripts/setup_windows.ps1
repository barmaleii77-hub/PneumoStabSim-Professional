[CmdletBinding()]
param(
    [switch]$SkipUvSync,
    [switch]$SkipSystem
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$platform = [System.Environment]::OSVersion.Platform
Write-Host "[setup_windows] Detected platform: $platform ($([System.Environment]::OSVersion.VersionString))"
if ($platform -ne [System.PlatformID]::Win32NT) {
    throw "setup_windows.ps1 is only supported on Windows hosts"
}

function Write-SetupLog {
    param([string]$Message)
    Write-Host "[setup_windows] $Message"
}

function Invoke-ChocoInstall {
    param(
        [string]$Package
    )

    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-SetupLog "Chocolatey not available; skipping install of $Package"
        return
    }

    try {
        Write-SetupLog "Ensuring Chocolatey package $Package"
        choco install $Package --no-progress -y | Out-Null
    } catch {
        Write-SetupLog "Failed to install $Package via Chocolatey: $_"
    }
}

function Ensure-PythonCommand {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python must be installed before running setup_windows.ps1"
    }
    return $python.Source
}

$pythonPath = Ensure-PythonCommand()
Write-SetupLog "Using Python from $pythonPath"

if (-not $SkipSystem) {
    Invoke-ChocoInstall -Package 'directx'
    Invoke-ChocoInstall -Package 'vcredist140'
} else {
    Write-SetupLog "Skipping Windows system package installation"
}

if (-not $SkipUvSync) {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-SetupLog "Synchronising Python environment via uv"
        uv sync --extra dev
    } else {
        Write-SetupLog "uv not found; using pip fallback"
        & $pythonPath -m pip install --upgrade pip
        & $pythonPath -m pip install -r requirements-dev.txt
    }
} else {
    Write-SetupLog "Skipping uv sync (per flag)"
}

Write-SetupLog "Installing mandatory Qt/PySide6 wheels"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv pip install --upgrade --no-cache-dir `
        'PySide6>=6.10,<7' `
        'PySide6-Addons>=6.10,<7' `
        'PySide6-Essentials>=6.10,<7' `
        'shiboken6>=6.10,<7' `
        'PyOpenGL==3.1.10' `
        'PyOpenGL-accelerate==3.1.10'
} else {
    & $pythonPath -m pip install --upgrade --no-cache-dir `
        'PySide6>=6.10,<7' `
        'PySide6-Addons>=6.10,<7' `
        'PySide6-Essentials>=6.10,<7' `
        'shiboken6>=6.10,<7' `
        'PyOpenGL==3.1.10' `
        'PyOpenGL-accelerate==3.1.10'
}

Write-SetupLog "Exporting headless Qt defaults"
$envContent = @(
    'QT_QPA_PLATFORM=offscreen',
    'QT_QUICK_BACKEND=rhi',
    'QSG_RHI_BACKEND=d3d11',
    'QT_OPENGL=software',
    'QT_LOGGING_RULES=*.debug=false;qt.scenegraph.general=false',
    'PSS_HEADLESS=1'
)

$envFile = $env:GITHUB_ENV
if (-not [string]::IsNullOrWhiteSpace($envFile)) {
    Write-SetupLog "Writing environment variables to $envFile"
    foreach ($line in $envContent) {
        Add-Content -Path $envFile -Value $line
    }
} else {
    Write-SetupLog "Applying environment variables to current session"
    foreach ($line in $envContent) {
        $parts = $line.Split('=')
        [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1], 'Process')
    }
}

Write-SetupLog "Windows environment bootstrap complete"
