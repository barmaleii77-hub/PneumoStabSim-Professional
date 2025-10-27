# ============================================================================
# PneumoStabSim Professional - Complete PATH Setup Script
# Скрипт для настройки всех путей проекта (Python, Qt, System)
# ============================================================================
# NOTE: This file intentionally includes a UTF-8 BOM so legacy Windows PowerShell versions interpret the Unicode characters below correctly.

param(
    [switch]$Force,
    [switch]$Verbose,
    [switch]$SystemWide,
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$VerbosePreference = if ($Verbose) { 'Continue' } else { 'SilentlyContinue' }

# ============================================================================
# CONFIGURATION
# ============================================================================

$ProjectRoot = $PSScriptRoot
$SrcPath = Join-Path $ProjectRoot "src"
$TestsPath = Join-Path $ProjectRoot "tests"
$ScriptsPath = Join-Path $ProjectRoot "scripts"
$AssetsPath = Join-Path $ProjectRoot "assets"
$ConfigPath = Join-Path $ProjectRoot "config"
$LogsPath = Join-Path $ProjectRoot "logs"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Write-Section {
    param([string]$Title)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Test-PathExists {
  param([string]$Path, [string]$Description)

    if (Test-Path $Path) {
        Write-Success "$Description exists: $Path"
        return $true
    } else {
        Write-Warning "$Description not found: $Path"
        return $false
    }
}

function Get-PythonExecutable {
    $pythonCommands = @('py', 'python3', 'python')

    foreach ($cmd in $pythonCommands) {
        try {
            $version = & $cmd --version 2>&1
         if ($LASTEXITCODE -eq 0) {
 Write-Success "Found Python: $cmd ($version)"
                return $cmd
       }
        } catch {
            continue
        }
    }

    Write-Error "Python not found in PATH"
    return $null
}

function Get-QtPaths {
    param([string]$PythonCmd)

    $script = @'
from PySide6.QtCore import QLibraryInfo
import json

paths = {
    "qml": str(QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)),
    "plugins": str(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)),
    "libraries": str(QLibraryInfo.path(QLibraryInfo.LibraryPath.LibrariesPath)),
    "binaries": str(QLibraryInfo.path(QLibraryInfo.LibraryPath.BinariesPath))
}

print(json.dumps(paths))
'@

    try {
     $result = & $PythonCmd -c $script 2>&1
        if ($LASTEXITCODE -eq 0) {
      return $result | ConvertFrom-Json
        }
    } catch {
   Write-Warning "Failed to get Qt paths: $_"
    }

    return $null
}

# ============================================================================
# PATH SETUP FUNCTIONS
# ============================================================================

function Set-PythonPath {
    Write-Section "Python PYTHONPATH Setup"

    $pythonPath = @(
 $ProjectRoot,
      $SrcPath,
        $TestsPath,
        $ScriptsPath
    ) -join ";"

    Write-Info "Setting PYTHONPATH..."
    $env:PYTHONPATH = $pythonPath

    Write-Success "PYTHONPATH configured:"
    $pythonPath.Split(';') | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor Gray
    }

    return $pythonPath
}

function Set-QtEnvironment {
    param($QtPaths)

 Write-Section "Qt Environment Setup"

    # Qt QML/Plugin paths
 if ($QtPaths) {
        Write-Info "Setting Qt paths..."

        $env:QML2_IMPORT_PATH = $QtPaths.qml
        $env:QML_IMPORT_PATH = $QtPaths.qml
     $env:QT_PLUGIN_PATH = $QtPaths.plugins
      $env:QT_QML_IMPORT_PATH = $QtPaths.qml

        Write-Success "QML Import Path: $($QtPaths.qml)"
   Write-Success "Plugin Path: $($QtPaths.plugins)"
}

    # Qt Graphics Backend
    $env:QSG_RHI_BACKEND = "d3d11"
    Write-Success "Graphics Backend: Direct3D 11"

    # Qt Logging
    $env:QT_LOGGING_RULES = "js.debug=true;qt.qml.debug=true"
    $env:QSG_INFO = "1"
    Write-Success "Qt Logging enabled"

    # Qt High DPI
    $env:QT_ENABLE_HIGHDPI_SCALING = "1"
    $env:QT_SCALE_FACTOR_ROUNDING_POLICY = "PassThrough"
    Write-Success "High DPI scaling configured"
}

function Set-ProjectPaths {
    Write-Section "Project Paths Setup"

    $env:PROJECT_ROOT = $ProjectRoot
    $env:SOURCE_DIR = $SrcPath
    $env:TESTS_DIR = $TestsPath
    $env:SCRIPTS_DIR = $ScriptsPath
    $env:ASSETS_DIR = $AssetsPath
    $env:CONFIG_DIR = $ConfigPath
    $env:LOGS_DIR = $LogsPath

    Write-Success "Project paths configured"

    # Verify critical paths
    $criticalPaths = @{
        "Source" = $SrcPath
        "Assets" = $AssetsPath
        "Config" = $ConfigPath
    }

    foreach ($key in $criticalPaths.Keys) {
        Test-PathExists -Path $criticalPaths[$key] -Description $key | Out-Null
    }
}

function Set-PythonEnvironment {
    Write-Section "Python Environment Setup"

    $env:PYTHONIOENCODING = "utf-8"
  $env:PYTHONUNBUFFERED = "1"
    $env:PYTHONOPTIMIZE = "1"
    $env:PYTHONDONTWRITEBYTECODE = "1"

    Write-Success "Python environment configured"
    Write-Info "  - UTF-8 encoding"
    Write-Info "  - Unbuffered output"
    Write-Info "  - Optimized bytecode"
}

function Set-LocaleEnvironment {
  Write-Section "Locale Environment Setup"

    $env:LANG = "ru_RU.UTF-8"
    $env:LC_ALL = "ru_RU.UTF-8"
    $env:COPILOT_LANGUAGE = "ru"

    Write-Success "Russian locale configured"
}

function Set-DevelopmentMode {
 Write-Section "Development Mode Setup"

    $env:DEVELOPMENT_MODE = "true"
    $env:DEBUG_ENABLED = "true"

    Write-Success "Development mode enabled"
}

# ============================================================================
# ENV FILE MANAGEMENT
# ============================================================================

function Update-EnvFile {
param([hashtable]$Paths)

    Write-Section "Updating .env File"

    $envFile = Join-Path $ProjectRoot ".env"

    $envContent = @"
# PneumoStabSim Professional Environment
# Auto-generated by setup_all_paths.ps1
# Last updated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# ============================================================================
# PYTHON PATHS
# ============================================================================
PYTHONPATH=$($Paths.PythonPath)
PYTHONIOENCODING=utf-8
PYTHONUNBUFFERED=1
PYTHONOPTIMIZE=1
PYTHONDONTWRITEBYTECODE=1

# ============================================================================
# QT CONFIGURATION
# ============================================================================
QSG_RHI_BACKEND=d3d11
QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true
QSG_INFO=1
QT_ENABLE_HIGHDPI_SCALING=1
QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough

"@

    if ($Paths.QtPaths) {
        $envContent += @"

# Qt Paths
QML2_IMPORT_PATH=$($Paths.QtPaths.qml)
QML_IMPORT_PATH=$($Paths.QtPaths.qml)
QT_PLUGIN_PATH=$($Paths.QtPaths.plugins)
QT_QML_IMPORT_PATH=$($Paths.QtPaths.qml)

"@
  }

    $envContent += @"

# ============================================================================
# PROJECT PATHS
# ============================================================================
PROJECT_ROOT=$ProjectRoot
SOURCE_DIR=$SrcPath
TESTS_DIR=$TestsPath
SCRIPTS_DIR=$ScriptsPath
ASSETS_DIR=$AssetsPath
CONFIG_DIR=$ConfigPath
LOGS_DIR=$LogsPath

# ============================================================================
# LOCALE
# ============================================================================
LANG=ru_RU.UTF-8
LC_ALL=ru_RU.UTF-8
COPILOT_LANGUAGE=ru

# ============================================================================
# DEVELOPMENT
# ============================================================================
DEVELOPMENT_MODE=true
DEBUG_ENABLED=true

"@

    try {
        $envContent | Out-File -FilePath $envFile -Encoding utf8 -Force
        Write-Success ".env file updated: $envFile"
      return $true
    } catch {
        Write-Error "Failed to update .env file: $_"
        return $false
    }
}

# ============================================================================
# VERIFICATION
# ============================================================================

function Test-PythonImports {
    param([string]$PythonCmd)

    Write-Section "Verifying Python Imports"

    $criticalModules = @(
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtQuick3D',
      'numpy',
'scipy'
    )

    $successCount = 0
    $totalCount = $criticalModules.Count

    foreach ($module in $criticalModules) {
        try {
       $result = & $PythonCmd -c "import $module" 2>&1
            if ($LASTEXITCODE -eq 0) {
  Write-Success "$module"
         $successCount++
 } else {
    Write-Warning "$module (import failed)"
   }
        } catch {
          Write-Warning "$module (error: $_)"
        }
    }

    Write-Info "Import test: $successCount/$totalCount modules successful"
    return ($successCount -eq $totalCount)
}

function Test-QtQuick3D {
    param([string]$PythonCmd)

    Write-Section "Verifying QtQuick3D"

    $testScript = @'
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, QLibraryInfo
import sys
import tempfile
import os

# Setup environment
qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
os.environ["QML2_IMPORT_PATH"] = str(qml_path)

# Create app
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

# Test QML
test_qml = """
import QtQuick
import QtQuick3D

Item {
 Component.onCompleted: {
        console.log("QtQuick3D OK")
    }
}
"""

# Create temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.qml', delete=False) as f:
    f.write(test_qml)
    temp_path = f.name

try:
    widget = QQuickWidget()
  engine = widget.engine()
    engine.addImportPath(str(qml_path))
    widget.setSource(QUrl.fromLocalFile(temp_path))

    if widget.status() == QQuickWidget.Status.Error:
        print("ERROR: QtQuick3D import failed")
        sys.exit(1)
    else:
        print("SUCCESS: QtQuick3D working")
        sys.exit(0)
finally:
    os.unlink(temp_path)
'@

  try {
        $result = & $PythonCmd -c $testScript 2>&1
        if ($LASTEXITCODE -eq 0 -and $result -match "SUCCESS") {
        Write-Success "QtQuick3D is working"
            return $true
        } else {
            Write-Warning "QtQuick3D test failed"
 if ($result) {
          Write-Host $result -ForegroundColor Gray
       }
            return $false
      }
    } catch {
        Write-Warning "QtQuick3D test error: $_"
      return $false
    }
}

function Test-ProjectStructure {
    Write-Section "Verifying Project Structure"

    $requiredPaths = @{
    "Source directory" = $SrcPath
        "Assets directory" = $AssetsPath
        "Config directory" = $ConfigPath
  "QML main file" = (Join-Path $AssetsPath "qml\main.qml")
        "App entry point" = (Join-Path $ProjectRoot "app.py")
    }

    $allExist = $true
    foreach ($key in $requiredPaths.Keys) {
        if (-not (Test-PathExists -Path $requiredPaths[$key] -Description $key)) {
            $allExist = $false
    }
    }

    return $allExist
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function Main {
    Write-Host @"

╔════════════════════════════════════════════════════════════════╗
║          ║
║    PneumoStabSim Professional - PATH Setup Tool        ║
║             ║
║        Комплексная настройка всех путей проекта ║
║         ║
╚════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

  # Check if running in verification mode only
    if ($VerifyOnly) {
   Write-Info "Running in verification-only mode"
    }

    # 1. Find Python
    Write-Section "Detecting Python"
    $pythonCmd = Get-PythonExecutable
    if (-not $pythonCmd) {
     Write-Error "Python not found. Please install Python 3.8+ and add to PATH"
        return 1
    }

    # 2. Get Qt paths
    Write-Section "Detecting Qt Installation"
    $qtPaths = Get-QtPaths -PythonCmd $pythonCmd
    if (-not $qtPaths) {
        Write-Warning "Could not detect Qt paths. Continuing with basic setup..."
    } else {
        Write-Success "Qt installation found"
    }

 # 3. Setup environment (skip if verify-only)
    if (-not $VerifyOnly) {
        $pythonPath = Set-PythonPath
        Set-QtEnvironment -QtPaths $qtPaths
 Set-ProjectPaths
 Set-PythonEnvironment
        Set-LocaleEnvironment
        Set-DevelopmentMode

        # 4. Update .env file
  $paths = @{
            PythonPath = $pythonPath
            QtPaths = $qtPaths
        }
        Update-EnvFile -Paths $paths
    }

    # 5. Verification
    Write-Section "Running Verification Tests"

$tests = @{
        "Python imports" = (Test-PythonImports -PythonCmd $pythonCmd)
        "QtQuick3D" = (Test-QtQuick3D -PythonCmd $pythonCmd)
      "Project structure" = (Test-ProjectStructure)
    }

    # Results summary
    Write-Section "Setup Summary"

    $passedTests = ($tests.Values | Where-Object { $_ -eq $true }).Count
    $totalTests = $tests.Count

    foreach ($testName in $tests.Keys) {
        if ($tests[$testName]) {
         Write-Success "$testName"
        } else {
            Write-Warning "$testName (failed)"
        }
    }

    Write-Host "`n" -NoNewline
    Write-Host "Tests passed: $passedTests/$totalTests" -ForegroundColor $(if ($passedTests -eq $totalTests) { 'Green' } else { 'Yellow' })

    # Final instructions
    Write-Section "Next Steps"

    if ($passedTests -eq $totalTests) {
     Write-Success "All paths configured successfully!"
        Write-Info ""
        Write-Info "To run the application:"
        Write-Host "  py app.py" -ForegroundColor White
        Write-Info ""
        Write-Info "To activate environment in current session:"
      Write-Host "  . .\activate_environment.ps1" -ForegroundColor White
      Write-Info ""
   return 0
    } else {
     Write-Warning "Some tests failed. Please review the errors above."
        Write-Info ""
   Write-Info "Try reinstalling dependencies:"
        Write-Host "  pip install -r requirements.txt --force-reinstall" -ForegroundColor White
        Write-Info ""
  return 1
    }
}

# Run main
exit (Main)
