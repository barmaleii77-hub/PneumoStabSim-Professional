# PneumoStabSim Professional Environment Setup
Write-Host "Setting up PneumoStabSim Professional environment..." -ForegroundColor Green

# Set Python path
$env:PYTHONPATH = "$PWD;$PWD\src"

# Set Qt environment
$env:QSG_RHI_BACKEND = "d3d11"
$env:QT_LOGGING_RULES = "js.debug=true;qt.qml.debug=true"

# Performance settings
$env:PYTHONOPTIMIZE = "1"
$env:PYTHONUNBUFFERED = "1"

Write-Host "Environment configured. You can now run:" -ForegroundColor Yellow
Write-Host "  python app.py                    # Standard mode"
Write-Host "  python app.py --no-block         # Non-blocking mode"
Write-Host "  python app.py --test-mode        # Test mode (5 sec auto-close)"
Write-Host "  dotnet run                       # C# .NET version"
