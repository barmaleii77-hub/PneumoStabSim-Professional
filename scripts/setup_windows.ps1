<#
.SYNOPSIS
    PneumoStabSim Professional — Windows dependency bootstrap.
.DESCRIPTION
    Installs the packages required to execute Qt-based tests in headless mode.
#>
[CmdletBinding()]
param(
    [string]$Python = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Log {
    param([string]$Message)
    Write-Host "[setup-windows] $Message"
}

Write-Log "Ensuring Chocolatey dependencies"
if (Get-Command choco -ErrorAction SilentlyContinue) {
    choco install -y --no-progress vcredist140 visualstudio2022buildtools qt6-sdk || Write-Log "Chocolatey dependencies already installed"
    choco install -y --no-progress make || Write-Log "GNU Make already installed"
}
else {
    Write-Log "Chocolatey not available; skipping system package installation"
}

Write-Log "Upgrading pip"
& $Python -m pip install --upgrade pip

Write-Log "Installing PySide6 runtime packages"
& $Python -m pip install `
    "PySide6>=6.10,<7" `
    "PySide6-Essentials>=6.10,<7" `
    "PySide6-Addons>=6.10,<7" `
    "PySide6-QtQuick3D>=6.10,<7"

Write-Log "Configuring Qt headless defaults"
$env:QT_QPA_PLATFORM = $env:QT_QPA_PLATFORM -as [string]
if (-not $env:QT_QPA_PLATFORM) {
    $env:QT_QPA_PLATFORM = 'offscreen'
}
$env:QT_QUICK_BACKEND = $env:QT_QUICK_BACKEND -as [string]
if (-not $env:QT_QUICK_BACKEND) {
    $env:QT_QUICK_BACKEND = 'rhi'
}
$env:QSG_RHI_BACKEND = $env:QSG_RHI_BACKEND -as [string]
if (-not $env:QSG_RHI_BACKEND) {
    $env:QSG_RHI_BACKEND = 'd3d11'
}

Write-Log "Setup complete. QT_QPA_PLATFORM=$($env:QT_QPA_PLATFORM)"
