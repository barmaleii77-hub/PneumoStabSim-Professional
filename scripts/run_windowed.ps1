param(
  [switch]$NoQml
)

# Force windowed Qt on Windows and start app with pythonw
$ErrorActionPreference = 'SilentlyContinue'

# Unset headless flags that may come from .env
Remove-Item Env:PSS_HEADLESS -ErrorAction SilentlyContinue
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue

# Prefer D3D11 on Windows for Qt RHI
$env:QSG_RHI_BACKEND = 'd3d11'
if (-not $env:QT_QUICK_CONTROLS_STYLE -or $env:QT_QUICK_CONTROLS_STYLE -eq '') { $env:QT_QUICK_CONTROLS_STYLE = 'Basic' }

# Pick interpreter
$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue)
$python  = (Get-Command python  -ErrorAction SilentlyContinue)

if ($null -ne $pythonw) { $exe = $pythonw.Source } elseif ($null -ne $python) { $exe = $python.Source } else { Write-Error 'Python not found in PATH'; exit 1 }

# Build args
$argsList = @('app.py', '--verbose')
if ($NoQml) { $argsList += '--no-qml' }

# Start detached windowed process
Start-Process -FilePath $exe -ArgumentList $argsList | Out-Null
Write-Host 'Started PneumoStabSim in windowed mode.'
