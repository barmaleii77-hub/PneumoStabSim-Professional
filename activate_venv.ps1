# PneumoStabSim Professional - one-click environment activation (Windows)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $projectRoot ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating .venv with Python 3.13" -ForegroundColor Cyan
    py -3.13 -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment interpreter missing" -ForegroundColor Red
  exit 1
}

& $venvPython -m pip install --upgrade pip setuptools wheel
& $venvPython -m pip install --require-hashes -r (Join-Path $projectRoot "requirements.txt") -c (Join-Path $projectRoot "requirements-compatible.txt")
if (Test-Path (Join-Path $projectRoot "requirements-dev.txt")) {
    & $venvPython -m pip install --require-hashes -r (Join-Path $projectRoot "requirements-dev.txt") -c (Join-Path $projectRoot "requirements-compatible.txt")
}

& $venvPython (Join-Path $projectRoot "setup_environment.py")

& (Join-Path $venvPath "Scripts\Activate.ps1")
