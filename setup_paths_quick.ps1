# =============================================================================
# PneumoStabSim Professional - PATH Setup (Simplified)
# Quick PATH configuration for all environments
# =============================================================================

param(
    [switch]$VerifyOnly
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " PneumoStabSim - PATH Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ProjectRoot = $PSScriptRoot
$SrcPath = Join-Path $ProjectRoot "src"
$TestsPath = Join-Path $ProjectRoot "tests"
$ScriptsPath = Join-Path $ProjectRoot "scripts"
$AssetsPath = Join-Path $ProjectRoot "assets"
$ConfigPath = Join-Path $ProjectRoot "config"

# Setup PYTHONPATH
Write-Host "Setting up PYTHONPATH..." -ForegroundColor Yellow
$pythonPath = @($ProjectRoot, $SrcPath, $TestsPath, $ScriptsPath) -join ";"
$env:PYTHONPATH = $pythonPath
Write-Host "  ✅ PYTHONPATH configured" -ForegroundColor Green

# Setup Qt environment
Write-Host "`nConfiguring Qt environment..." -ForegroundColor Yellow
$env:QSG_RHI_BACKEND = "d3d11"
$env:QT_LOGGING_RULES = "js.debug=true;qt.qml.debug=true"
$env:QSG_INFO = "1"
$env:QT_ENABLE_HIGHDPI_SCALING = "1"
Write-Host "  ✅ Qt environment configured" -ForegroundColor Green

# Setup Python environment
Write-Host "`nConfiguring Python environment..." -ForegroundColor Yellow
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONOPTIMIZE = "1"
Write-Host "  ✅ Python environment configured" -ForegroundColor Green

# Create .env file
if (-not $VerifyOnly) {
Write-Host "`nCreating .env file..." -ForegroundColor Yellow
    $envContent = @"
# PneumoStabSim Professional Environment
# Last updated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

PYTHONPATH=$pythonPath
PYTHONIOENCODING=utf-8
PYTHONUNBUFFERED=1
PYTHONOPTIMIZE=1

QSG_RHI_BACKEND=d3d11
QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true
QSG_INFO=1
QT_ENABLE_HIGHDPI_SCALING=1

PROJECT_ROOT=$ProjectRoot
SOURCE_DIR=$SrcPath
TESTS_DIR=$TestsPath
SCRIPTS_DIR=$ScriptsPath
ASSETS_DIR=$AssetsPath
CONFIG_DIR=$ConfigPath

LANG=ru_RU.UTF-8
COPILOT_LANGUAGE=ru

DEVELOPMENT_MODE=true
DEBUG_ENABLED=true
"@

    $envFile = Join-Path $ProjectRoot ".env"
    $envContent | Out-File -FilePath $envFile -Encoding utf8 -Force
    Write-Host "  ✅ .env file created" -ForegroundColor Green
}

# Verification
Write-Host "`nVerifying installation..." -ForegroundColor Yellow

# Test Python
try {
    $pythonVersion = py --version 2>&1
    Write-Host "  ✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Python not found" -ForegroundColor Yellow
}

# Test PySide6
try {
    py -c "import PySide6" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
     Write-Host "  ✅ PySide6 installed" -ForegroundColor Green
    } else {
      Write-Host "  ⚠️  PySide6 not found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  PySide6 not found" -ForegroundColor Yellow
}

# Test project structure
$structureOk = $true
foreach ($path in @($SrcPath, $AssetsPath, $ConfigPath)) {
    if (Test-Path $path) {
        Write-Host "  ✅ $(Split-Path $path -Leaf) directory exists" -ForegroundColor Green
    } else {
  Write-Host "  ⚠️  $(Split-Path $path -Leaf) directory missing" -ForegroundColor Yellow
 $structureOk = $false
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($structureOk) {
    Write-Host " ✅ Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "`nNext steps:"
    Write-Host "  1. Activate:. .\activate_environment.ps1" -ForegroundColor White
    Write-Host "  2. Run app:   py app.py`n" -ForegroundColor White
} else {
    Write-Host " ⚠️  Setup Complete with Warnings" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "`nSome paths are missing. Check the warnings above.`n"
}
