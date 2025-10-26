# Wrapper script to maintain backwards compatibility with CI expectations
# Invokes the root-level activate_environment.ps1 so that tools relying on
# scripts/activate_environment.ps1 continue to function.

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootScript = Join-Path (Split-Path $scriptDir -Parent) 'activate_environment.ps1'

if (-not (Test-Path $rootScript)) {
    Write-Error "activate_environment.ps1 not found at $rootScript"
    exit 1
}

& $rootScript @args
