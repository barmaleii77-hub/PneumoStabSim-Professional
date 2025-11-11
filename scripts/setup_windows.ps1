[CmdletBinding()]
param(
    [switch]$SkipUvSync
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

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python must be installed before running setup_windows.ps1"
}

if (-not $SkipUvSync) {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-SetupLog "Synchronising Python environment via uv"
        uv sync --extra dev
    } else {
        Write-SetupLog "uv not found; using pip fallback"
        python -m pip install --upgrade pip
        python -m pip install -r requirements-dev.txt
    }
}

Write-SetupLog "Installing mandatory Qt/PySide6 wheels"
$qtPackages = @(
    'PySide6>=6.10,<7',
    'PySide6-Addons>=6.10,<7',
    'PySide6-Essentials>=6.10,<7',
    'shiboken6>=6.10,<7',
    'PyOpenGL==3.1.10',
    'PyOpenGL-accelerate==3.1.10'
)

foreach ($package in $qtPackages) {
    Write-SetupLog "Ensuring package $package"
    python -m pip install --upgrade --no-cache-dir $package
}

Write-SetupLog "Exporting headless Qt defaults"
$envContent = @(
    'QT_QPA_PLATFORM=offscreen',
    'QT_QUICK_BACKEND=rhi',
    'QSG_RHI_BACKEND=d3d11',
    'QT_OPENGL=software'
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
