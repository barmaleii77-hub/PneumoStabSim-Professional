# =============================================================================
# Quick Start Setup - PneumoStabSim Professional
# =============================================================================

Write-Host "PneumoStabSim Professional - Quick Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

# Check venv
Write-Host "[2/5] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "OK: Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Update pip
Write-Host "[3/5] Updating pip..." -ForegroundColor Yellow
.\venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel --quiet

# Install dependencies
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
.\venv\Scripts\python.exe -m pip install -r requirements.txt --quiet

# Verify installation
Write-Host "[5/5] Verifying installation..." -ForegroundColor Yellow
$version = .\venv\Scripts\python.exe -c "import PySide6.QtCore as QtCore; print(f'PySide6 {QtCore.__version__} (Qt {QtCore.qVersion()})')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: $version" -ForegroundColor Green
} else {
    Write-Host "WARNING: PySide6 verification failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Press F5 in VS Code to run with debugger" -ForegroundColor White
Write-Host "  2. Or run: .\venv\Scripts\python.exe app.py" -ForegroundColor White
Write-Host ""
