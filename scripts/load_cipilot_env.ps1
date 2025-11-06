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
    if ($value.StartsWith('"') -and $value.EndsWith('"')) { $value = $value.Trim('"') }
    if ($value.StartsWith("'") -and $value.EndsWith("'")) { $value = $value.Trim("'") }
    [Environment]::SetEnvironmentVariable($name, $value, 'Process')
  }
}

# Helper: check if every path in PATH-like var exists
function Test-AllPathsExist([string]$pathList) {
  if (-not $pathList) { return $false }
  $parts = $pathList -split ';'
  foreach ($p in $parts) { if ($p -and -not (Test-Path -LiteralPath $p)) { return $false } }
  return $true
}

# Robust Python inline execution via temp file
function Get-PythonOutput([string]$code) {
  $tmp = [System.IO.Path]::GetTempFileName()
  $py = [System.IO.Path]::ChangeExtension($tmp, '.py')
  try {
    Move-Item -LiteralPath $tmp -Destination $py -Force
    Set-Content -LiteralPath $py -Value $code -Encoding UTF8
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'python'
    $psi.Arguments = "`"$py`""
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
    Remove-Item -LiteralPath $py -Force -ErrorAction SilentlyContinue
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

# Ensure Qt related variables; override if invalid
$plugin = Get-PythonOutput 'from PySide6.QtCore import QLibraryInfo as Q; print(Q.path(Q.LibraryPath.PluginsPath))'
if ($plugin) {
  if (-not $env:QT_PLUGIN_PATH -or -not (Test-Path -LiteralPath $env:QT_PLUGIN_PATH)) {
    $env:QT_PLUGIN_PATH = $plugin
    Write-Host "[env] QT_PLUGIN_PATH=$env:QT_PLUGIN_PATH"
  }
}

$assetsQml = $null
if (Test-Path -LiteralPath 'assets/qml') { $assetsQml = (Resolve-Path -LiteralPath 'assets/qml').Path }
$qmlLib = Get-PythonOutput 'from PySide6.QtCore import QLibraryInfo as Q; print(Q.path(Q.LibraryPath.QmlImportsPath))'
$parts = @()
if ($assetsQml) {
  $parts += $assetsQml
  $scenePath = Join-Path -Path $assetsQml -ChildPath 'scene'
  if (Test-Path -LiteralPath $scenePath) { $parts += (Resolve-Path -LiteralPath $scenePath).Path }
}
if ($qmlLib -and (Test-Path -LiteralPath $qmlLib)) { $parts += $qmlLib }
if ($parts.Count -gt 0) {
  $joined = [string]::Join(';', $parts)
  if (-not (Test-AllPathsExist $env:QML2_IMPORT_PATH)) {
    $env:QML2_IMPORT_PATH = $joined
    $env:QML_IMPORT_PATH = $joined
    $env:QT_QML_IMPORT_PATH = $joined
    Write-Host "[env] QML2_IMPORT_PATH=$($env:QML2_IMPORT_PATH)"
  }
}

# Run environment verifications (non-fatal)
try {
  if (Test-Path -LiteralPath 'tools/environment/verify_qt_setup.py') {
    python tools/environment/verify_qt_setup.py --allow-missing-runtime --report-dir reports/environment | Write-Host
  }
} catch { Write-Warning $_ }

# App-level env report
$report = 'reports/quality/environment_setup_report.md'
$dir = Split-Path -Path $report -Parent
New-Item -ItemType Directory -Force -Path $dir | Out-Null
python app.py --env-report $report --env-check
Write-Host "[env] Environment report written to $report"

