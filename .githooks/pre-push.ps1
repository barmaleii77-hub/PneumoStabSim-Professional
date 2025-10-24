#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Resolve repository root
$root = git rev-parse --show-toplevel
Set-Location $root

Write-Host "[pre-push] Running repository quality gate (PowerShell)" -ForegroundColor Cyan

try {
    if (Get-Command make -ErrorAction SilentlyContinue) {
        & make check
    }
    else {
        Write-Host "[pre-push] 'make' not found. Using python -m tools.ci_tasks verify" -ForegroundColor Yellow
        & python -m tools.ci_tasks verify
    }
}
catch {
    Write-Error "[pre-push] Quality gate failed: $($_.Exception.Message)"
    exit 1
}
