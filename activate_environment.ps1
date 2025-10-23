# ============================================================================
# PneumoStabSim Professional - Environment Activation Script
# Активация окружения в текущей PowerShell сессии
# ============================================================================

param(
    [string]$PythonVersion,
    [switch]$InstallQt,
    [string]$QtVersion,
    [string]$QtModules,
    [string]$QtOutputDir,
    [string]$QtLogFile,
    [string]$HashFile,
    [string]$HashLogFile,
    [switch]$Setup
)

$ProjectRoot = $PSScriptRoot

# Import .env file if exists
$envFile = Join-Path $ProjectRoot ".env"
if (Test-Path $envFile) {
    Write-Host "📋 Loading environment from .env..." -ForegroundColor Cyan

    Get-Content $envFile | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
  $name = $matches[1].Trim()
      $value = $matches[2].Trim()

   # Remove quotes if present
   $value = $value -replace '^"(.*)"$', '$1'
       $value = $value -replace "^'(.*)'$", '$1'

      Set-Item -Path "env:$name" -Value $value
       Write-Host "  ✅ $name" -ForegroundColor Green
   }
 }

    Write-Host "`n✅ Environment activated!" -ForegroundColor Green
    Write-Host "📦 PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
    Write-Host "🎨 QT Backend: $env:QSG_RHI_BACKEND" -ForegroundColor Gray
    Write-Host "📚 Матрица совместимости: docs/environments.md" -ForegroundColor Gray

} else {
    Write-Host "⚠️  .env file not found. Run setup_all_paths.ps1 first." -ForegroundColor Yellow
}

if ($PythonVersion) {
    $env:PYTHON_VERSION = $PythonVersion
    Write-Host "🔁 PYTHON_VERSION overridden to $PythonVersion" -ForegroundColor Yellow
}

if ($QtVersion) {
    $env:QT_SDK_VERSION = $QtVersion
    Write-Host "🎨 QT_SDK_VERSION overridden to $QtVersion" -ForegroundColor Yellow
}

if ($QtModules) {
    $env:QT_SDK_MODULES = $QtModules
    Write-Host "🎨 QT_SDK_MODULES overridden to $QtModules" -ForegroundColor Yellow
}

if ($QtOutputDir) {
    $env:QT_SDK_ROOT = $QtOutputDir
    Write-Host "📁 QT_SDK_ROOT overridden to $QtOutputDir" -ForegroundColor Yellow
}

if ($QtLogFile) {
    $env:QT_INSTALL_LOG = $QtLogFile
    Write-Host "📝 QT_INSTALL_LOG overridden to $QtLogFile" -ForegroundColor Yellow
}

if ($HashFile) {
    $env:DEPENDENCIES_FILE = $HashFile
    $env:DEPENDENCY_HASHES_ENABLED = 'true'
    Write-Host "🔐 DEPENDENCIES_FILE overridden to $HashFile" -ForegroundColor Yellow
}

if ($HashLogFile) {
    $env:DEPENDENCY_HASH_LOG = $HashLogFile
    Write-Host "📝 DEPENDENCY_HASH_LOG overridden to $HashLogFile" -ForegroundColor Yellow
}

if ($InstallQt.IsPresent) {
    $env:INSTALL_QT_SDK = '1'
}

if ($Setup.IsPresent) {
    $pythonCandidates = @("py", "python3", "python")
    $pythonExe = $null

    foreach ($candidate in $pythonCandidates) {
    try {
   & $candidate --version >$null 2>&1
+ if ($LASTEXITCODE -eq 0) {
+ $pythonExe = $candidate
+       break
+      }
+        } catch {
+        continue
+   }
    }

    if (-not $pythonExe) {
    Write-Host "❌ Python не найден для запуска setup_environment.py" -ForegroundColor Red
   exit 1
    }

    $setupArgs = @("$ProjectRoot/setup_environment.py")

    if ($PythonVersion) {
   $setupArgs += @("--python-version", $PythonVersion)
    }
+if ($InstallQt.IsPresent) {
+   $setupArgs += "--install-qt"
+}
    if ($QtVersion) {
   $setupArgs += @("--qt-version", $QtVersion)
    }
    if ($QtModules) {
    $setupArgs += @("--qt-modules", $QtModules)
    }
    if ($QtOutputDir) {
    $setupArgs += @("--qt-output-dir", $QtOutputDir)
    }
    if ($QtLogFile) {
   $setupArgs += @("--qt-log-file", $QtLogFile)
+}
+    if ($HashFile) {
+   $setupArgs += @("--hash-file", $HashFile)
+    }
+    if ($HashLogFile) {
+    $setupArgs += @("--hash-log-file", $HashLogFile)
+}

    Write-Host "🚀 Running setup_environment.py with overrides..." -ForegroundColor Cyan
    & $pythonExe @setupArgs
}
