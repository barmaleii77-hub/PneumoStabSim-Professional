# PneumoStabSim Professional - Enhanced Virtual Environment Setup (PowerShell)
# Enhanced encoding, terminal support, and Python compatibility

# Set console encoding to UTF-8
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " PneumoStabSim Professional - Enhanced Environment Setup" -ForegroundColor Cyan  
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Configure terminal encoding and display
try {
    # Set UTF-8 for current session
    chcp 65001 | Out-Null
    Write-Host "✓ Terminal encoding set to UTF-8" -ForegroundColor Green
} catch {
    Write-Host "⚠ Warning: Could not set UTF-8 encoding" -ForegroundColor Yellow
}

# Enhanced environment variable configuration
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PYTHONLEGACYWINDOWSFSENCODING = "utf-8"
Write-Host "✓ Python encoding variables configured" -ForegroundColor Green

# Check Python availability and version
Write-Host ""
Write-Host "🐍 Checking Python installation..." -ForegroundColor Yellow

$pythonCmd = $null
$pythonCommands = @("python", "python3", "py")

foreach ($cmd in $pythonCommands) {
    try {
        $version = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Host "✓ Found Python: $version using '$cmd'" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ ERROR: Python not found" -ForegroundColor Red
    Write-Host "Please install Python 3.8-3.11 from python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Python version compatibility
try {
    $versionCheck = & $pythonCmd -c "import sys; major, minor = sys.version_info[:2]; print(f'{major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠ WARNING: Python version may have compatibility issues" -ForegroundColor Yellow
        Write-Host "Recommended: Python 3.8 - 3.11 for optimal stability" -ForegroundColor Yellow
        
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -notmatch '^[Yy]') {
            Write-Host "Setup cancelled by user" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "✓ Python version $versionCheck is compatible" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Could not verify Python version, continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Setting up virtual environment..." -ForegroundColor Yellow

# Check if virtual environment exists
if (-Not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Creating new virtual environment..." -ForegroundColor Yellow
    
    try {
        & $pythonCmd -m venv venv --clear
        if ($LASTEXITCODE -ne 0) {
            throw "Virtual environment creation failed"
        }
        Write-Host "✓ Virtual environment created successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ ERROR: Failed to create virtual environment" -ForegroundColor Red
        Write-Host "This might be due to permissions or Python installation issues" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
try {
    & "venv\Scripts\Activate.ps1"
    if (-not $env:VIRTUAL_ENV) {
        throw "Virtual environment activation failed"
    }
    Write-Host "✓ Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Virtual environment activation failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "⬆️ Upgrading pip..." -ForegroundColor Yellow

# Upgrade pip with error handling
try {
    python -m pip install --upgrade pip --disable-pip-version-check --quiet
    Write-Host "✓ Pip upgraded successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠ Warning: Pip upgrade failed, continuing with existing version" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow

# Install requirements with fallback strategy
$requirementsFiles = @("requirements-compatible.txt", "requirements.txt")
$installed = $false

foreach ($reqFile in $requirementsFiles) {
    if (Test-Path $reqFile) {
        Write-Host "Installing from $reqFile..." -ForegroundColor Cyan
        try {
            pip install -r $reqFile --disable-pip-version-check --quiet
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Dependencies installed successfully from $reqFile" -ForegroundColor Green
                $installed = $true
                break
            } else {
                throw "Installation failed"
            }
        } catch {
            Write-Host "⚠ Installation from $reqFile failed, trying next method..." -ForegroundColor Yellow
        }
    }
}

if (-not $installed) {
    Write-Host "Installing essential packages manually..." -ForegroundColor Yellow
    
    $essentialPackages = @(
        "numpy>=1.21.0,<2.0.0",
        "scipy>=1.7.0,<2.0.0", 
        "PySide6>=6.4.0,<7.0.0",
        "matplotlib>=3.5.0",
        "PyOpenGL>=3.1.0",
        "PyOpenGL-accelerate>=3.1.0"
    )
    
    foreach ($package in $essentialPackages) {
        try {
            Write-Host "  Installing $($package.Split('>=')[0])..." -ForegroundColor Cyan
            pip install $package --disable-pip-version-check --quiet
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ $($package.Split('>=')[0]) installed" -ForegroundColor Green
            }
        } catch {
            Write-Host "  ⚠ Failed to install $($package.Split('>=')[0])" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "🌍 Configuring environment variables..." -ForegroundColor Yellow

# Set comprehensive environment variables
$env:PYTHONPATH = "$PWD;$PWD\src"
$env:QSG_RHI_BACKEND = "d3d11"
$env:QT_LOGGING_RULES = "js.debug=true;qt.qml.debug=true"
$env:PYTHONOPTIMIZE = "0"  # Keep debug info for development
$env:PYTHONUNBUFFERED = "1"

# Qt-specific optimizations
$env:QT_AUTO_SCREEN_SCALE_FACTOR = "1"
$env:QT_SCALE_FACTOR_ROUNDING_POLICY = "PassThrough"
$env:QT_ENABLE_HIGHDPI_SCALING = "1"

Write-Host "✓ Environment variables configured" -ForegroundColor Green

Write-Host ""
Write-Host "🧪 Testing installation..." -ForegroundColor Yellow

# Test critical imports
$testScript = @"
import sys
try:
    import numpy as np
    import scipy
    import PySide6
    print('✓ Critical packages: numpy, scipy, PySide6')
except ImportError as e:
    print(f'⚠ Import warning: {e}')
    sys.exit(1)

# Test Unicode support
try:
    test_str = '🔧 Unicode test: ✅ ❌ ⚠️ 🎯 📊'
    print(test_str)
    print('✓ Unicode support: working')
except UnicodeEncodeError:
    print('⚠ Unicode support: limited')
"@

try {
    $testResult = python -c $testScript
    Write-Host $testResult -ForegroundColor Green
} catch {
    Write-Host "⚠ Some packages may have issues, but basic functionality should work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host " Virtual Environment Ready!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

# Display environment info
Write-Host "Environment Information:" -ForegroundColor Cyan
Write-Host "  Virtual Environment: $env:VIRTUAL_ENV" -ForegroundColor White
Write-Host "  Python Version: $(python --version)" -ForegroundColor White
Write-Host "  Pip Version: $(pip --version)" -ForegroundColor White
Write-Host ""

Write-Host "Available commands:" -ForegroundColor Yellow
Write-Host "  python app.py                    # Run main application"
Write-Host "  python app.py --test-mode        # Test mode (auto-close 5s)"  
Write-Host "  python app.py --debug            # Debug mode"
Write-Host "  python app.py --safe-mode        # Safe mode (basic features)"
Write-Host "  python scripts\terminal_diagnostic.py  # Terminal diagnostic"
Write-Host "  python scripts\check_environment.py     # Environment check"
Write-Host "  deactivate                       # Exit virtual environment"
Write-Host ""

Write-Host "🔧 Troubleshooting:" -ForegroundColor Cyan
Write-Host "  If you see encoding issues: .\fix_terminal.bat"
Write-Host "  If app won't start: python scripts\terminal_diagnostic.py"
Write-Host "  For full diagnostics: python scripts\comprehensive_test.py"
Write-Host ""

Write-Host "================================================================" -ForegroundColor Green
