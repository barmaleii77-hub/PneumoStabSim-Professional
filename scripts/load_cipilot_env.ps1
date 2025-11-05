param(
  [string]$EnvFile = '.env.cipilot'
)

$ErrorActionPreference = 'Stop'

# Load .env/.env.cipilot into current process environment
function Set-EnvVarFromLine([string]$line) {
  if (-not $line) { return }
  $trim = $line.Trim()
  if ($trim -eq '' -or $trim.StartsWith('#')) { return }
  if ($trim -match '^(export\s+)?([^=\s]+)=(.*)$') {
    $name = $Matches[2]
    $value = $Matches[3]
    # Strip quotes
    if ($value.StartsWith('"') -and $value.EndsWith('"')) { $value = $value.Trim('"') }
    if ($value.StartsWith("'") -and $value.EndsWith("'")) { $value = $value.Trim("'") }
    [Environment]::SetEnvironmentVariable($name, $value, 'Process')
  }
}

if (Test-Path -LiteralPath $EnvFile) {
  Get-Content -LiteralPath $EnvFile | ForEach-Object { Set-EnvVarFromLine $_ }
  Write-Host "[env] Loaded $EnvFile into process environment"
} elseif (Test-Path -LiteralPath '.env') {
  Get-Content -LiteralPath '.env' | ForEach-Object { Set-EnvVarFromLine $_ }
  Write-Host "[env] Loaded .env into process environment"
} else {
  Write-Host "[env] No env file found (.env.cipilot or .env)"
}

# Ensure Qt related variables via temporary code file to avoid quoting issues
function Get-PythonOutput([string]$code) {
  $tmp = [System.IO.Path]::GetTempFileName()
  Set-Content -LiteralPath $tmp -Value $code -Encoding UTF8
  try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'python'
    $psi.Arguments = "-c `"$([IO.File]::ReadAllText($tmp))`""
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $proc = [System.Diagnostics.Process]::Start($psi)
    $out = $proc.StandardOutput.ReadToEnd().Trim()
    $err = $proc.StandardError.ReadToEnd().Trim()
    $proc.WaitForExit()
    if ($proc.ExitCode -ne 0) { return '' }
    return $out
  } finally {
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
  }
}

if (-not $env:QT_PLUGIN_PATH -or $env:QT_PLUGIN_PATH.Trim() -eq '') {
  $code = 'from PySide6.QtCore import QLibraryInfo as Q; print(Q.path(Q.LibraryPath.PluginsPath))'
  $plugin = Get-PythonOutput $code
  if ($plugin) {
    $env:QT_PLUGIN_PATH = $plugin
    Write-Host "[env] QT_PLUGIN_PATH=$plugin"
  }
}

if (-not $env:QML2_IMPORT_PATH -or $env:QML2_IMPORT_PATH.Trim() -eq '') {
  $assetsQml = (Resolve-Path -LiteralPath 'assets/qml' -ErrorAction SilentlyContinue)
  $code = 'from PySide6.QtCore import QLibraryInfo as Q; print(Q.path(Q.LibraryPath.QmlImportsPath))'
  $qmlLib = Get-PythonOutput $code
  $parts = @()
  if ($assetsQml) {
    $parts += $assetsQml.Path
    $scenePath = Join-Path -Path $assetsQml.Path -ChildPath 'scene'
    if (Test-Path -LiteralPath $scenePath) {
      $parts += (Resolve-Path -LiteralPath $scenePath).Path
    }
  }
  if ($qmlLib) { $parts += $qmlLib }
  if ($parts.Count -gt 0) {
    $joined = [string]::Join(';', $parts)
    $env:QML2_IMPORT_PATH = $joined
    $env:QML_IMPORT_PATH = $joined
    $env:QT_QML_IMPORT_PATH = $joined
    Write-Host "[env] QML2_IMPORT_PATH=$($env:QML2_IMPORT_PATH)"
  }
}

# Run environment verifications
try {
  if (Test-Path -LiteralPath 'tools/environment/verify_qt_setup.py') {
    python tools/environment/verify_qt_setup.py
  }
} catch { Write-Warning $_ }

# Always run app-level env check with report
$report = 'reports/quality/environment_setup_report.md'
python app.py --env-report $report --env-check
Write-Host "[env] Environment report written to $report"

