#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Resolve project root from script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location -LiteralPath $ProjectRoot

# Prefer project venv pythonw (no console window)
$VenvPythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$VenvPython  = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Launcher = if (Test-Path -LiteralPath $VenvPythonw) { $VenvPythonw } elseif (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { $null }
if (-not $Launcher) {
  Write-Host ('ERROR: .venv python not found at {0} or {1}' -f $VenvPythonw, $VenvPython) -ForegroundColor Red
  Write-Host 'Create venv: py -3.13 -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt' -ForegroundColor Yellow
  exit 1
}

# GUI launch environment (force GPU, not headless)
Remove-Item Env:PSS_HEADLESS -ErrorAction SilentlyContinue
if ($env:QT_QPA_PLATFORM -eq 'offscreen') { Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue }
$env:QT_QPA_PLATFORM = 'windows'
$env:QSG_RHI_BACKEND = 'd3d11'
$env:QT_QUICK_CONTROLS_STYLE = if ($env:QT_QUICK_CONTROLS_STYLE) { $env:QT_QUICK_CONTROLS_STYLE } else { 'Basic' }
$env:PSS_QML_SCENE = 'realism'

# Start app in a separate window without showing a console
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $Launcher
$psi.Arguments = 'app.py'
$psi.WorkingDirectory = $ProjectRoot
$psi.UseShellExecute = $true
$psi.WindowStyle = 'Hidden'
$psi.CreateNoWindow = $true

$proc = [System.Diagnostics.Process]::Start($psi)
if ($null -eq $proc) {
  Write-Host 'ERROR: Failed to start application' -ForegroundColor Red
  exit 1
}

Write-Host ('PneumoStabSim launched (PID={0})' -f $proc.Id) -ForegroundColor Green
Write-Host 'Console window suppressed (pythonw). Close the app window to exit it.' -ForegroundColor Gray

# Brief tail of startup log (if present)
Start-Sleep -Seconds 1
$logPath = Join-Path $ProjectRoot 'logs\startup.log'
if (Test-Path -LiteralPath $logPath) {
  Write-Host ('--- startup.log (tail) ---') -ForegroundColor DarkGray
  Get-Content -LiteralPath $logPath -Tail 6 | Write-Host
}
