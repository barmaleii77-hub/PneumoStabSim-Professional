# ============================================================================
# FIX POWERSHELL ENCODING - ASCII ONLY VERSION
# No Russian characters to avoid encoding issues
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " POWERSHELL ENCODING FIX" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Check current PowerShell version
Write-Host "`n[1/4] Checking PowerShell version..." -ForegroundColor Yellow
Write-Host "Current version: $($PSVersionTable.PSVersion)" -ForegroundColor White

if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Host "WARNING: PowerShell 5.x detected - recommend updating to PS7+" -ForegroundColor Red
    Write-Host "Download: https://github.com/PowerShell/PowerShell/releases" -ForegroundColor Gray
} else {
    Write-Host "OK: PowerShell 7+ installed" -ForegroundColor Green
}

# 2. Check current encoding
Write-Host "`n[2/4] Checking encoding..." -ForegroundColor Yellow
Write-Host "Console Output Encoding: $([Console]::OutputEncoding.EncodingName)" -ForegroundColor White
Write-Host "Console Input Encoding:  $([Console]::InputEncoding.EncodingName)" -ForegroundColor White

# 3. Fix encoding to UTF-8
Write-Host "`n[3/4] Setting UTF-8 encoding..." -ForegroundColor Yellow
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
   chcp 65001 | Out-Null
    Write-Host "OK: UTF-8 set for current session" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to set UTF-8: $_" -ForegroundColor Red
}

# 4. Setup PowerShell profile
Write-Host "`n[4/4] Setting up PowerShell profile..." -ForegroundColor Yellow
Write-Host "Profile path: $PROFILE" -ForegroundColor White

$profileDir = Split-Path $PROFILE -Parent
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    Write-Host "OK: Created profile directory" -ForegroundColor Green
}

$utfSettings = @'

# UTF-8 ENCODING FIX for PneumoStabSim Professional
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ($Host.Name -eq 'ConsoleHost') {
  chcp 65001 | Out-Null
}

$ProgressPreference = 'SilentlyContinue'
$ErrorView = 'NormalView'

'@

if (Test-Path $PROFILE) {
    $currentProfile = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
    if ($currentProfile -notmatch "UTF-8 ENCODING FIX") {
        Add-Content -Path $PROFILE -Value $utfSettings -Encoding UTF8
        Write-Host "OK: UTF-8 settings added to profile" -ForegroundColor Green
    } else {
  Write-Host "OK: UTF-8 settings already present" -ForegroundColor Green
    }
} else {
    Set-Content -Path $PROFILE -Value $utfSettings -Encoding UTF8
    Write-Host "OK: Profile created with UTF-8 settings" -ForegroundColor Green
}

# Test commands
Write-Host "`nTesting commands..." -ForegroundColor Yellow
$testsOK = 0

try {
    Test-Path . | Out-Null
  Write-Host "OK: Test-Path works" -ForegroundColor Green
    $testsOK++
} catch {
    Write-Host "FAIL: Test-Path failed" -ForegroundColor Red
}

try {
    Get-ChildItem -Path . -ErrorAction Stop | Select-Object -First 1 | Out-Null
    Write-Host "OK: Get-ChildItem works" -ForegroundColor Green
    $testsOK++
} catch {
    Write-Host "FAIL: Get-ChildItem failed" -ForegroundColor Red
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nTests passed: $testsOK/2" -ForegroundColor $(if ($testsOK -eq 2) {"Green"} else {"Yellow"})

Write-Host "`nNEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Restart VS Code (Ctrl+Shift+P -> 'Reload Window')" -ForegroundColor White
Write-Host "2. Or restart terminal (Ctrl+Shift+``)" -ForegroundColor White
Write-Host "3. Check encoding: [Console]::OutputEncoding" -ForegroundColor White
Write-Host "`n========================================" -ForegroundColor Cyan
