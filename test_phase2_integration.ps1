# ✅ CAMERA INTEGRATION - QUICK TEST SCRIPT
# Test if application starts with new camera modules

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   QUICK CAMERA INTEGRATION TEST" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "🧪 Testing camera module integration..." -ForegroundColor Yellow
Write-Host "" 

# Headless toggle support mirrors run.ps1 so GPU/D3D11 stays the default.
function Test-PssHeadless {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    $normalised = $Value.Trim().ToLowerInvariant()
    return @('1', 'true', 'yes', 'on') -contains $normalised
}

$headlessRequested = Test-PssHeadless $env:PSS_HEADLESS
if ($headlessRequested) {
    $env:PSS_HEADLESS = '1'
    if (-not $env:QT_QPA_PLATFORM) { $env:QT_QPA_PLATFORM = 'offscreen' }
    if (-not $env:QT_QUICK_BACKEND) { $env:QT_QUICK_BACKEND = 'software' }
    Write-Host "ℹ️ Headless mode active — Qt offscreen/software paths enabled." -ForegroundColor Cyan
} else {
    if ($env:QT_QPA_PLATFORM -eq 'offscreen') {
        Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    }
    if ($env:QT_QUICK_BACKEND -eq 'software') {
        Remove-Item Env:QT_QUICK_BACKEND -ErrorAction SilentlyContinue
    }
    Remove-Item Env:PSS_FORCE_NO_QML_3D -ErrorAction SilentlyContinue
    $env:QSG_RHI_BACKEND = 'd3d11'
    if (-not $env:QT_QUICK_BACKEND) { $env:QT_QUICK_BACKEND = 'rhi' }
    Write-Host "ℹ️ GPU mode active — forcing Direct3D 11 scene graph backend." -ForegroundColor Cyan
}

# Check if Python is available
Write-Host "1. Checking Python..." -ForegroundColor Cyan
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Python OK: $pythonCheck" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python not found!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check if QML files exist
Write-Host "2. Checking QML files..." -ForegroundColor Cyan
$qmlFiles = @(
    "assets\qml\main.qml",
    "assets\qml\camera\qmldir",
    "assets\qml\camera\CameraController.qml",
    "assets\qml\camera\CameraState.qml",
    "assets\qml\camera\CameraRig.qml",
    "assets\qml\camera\MouseControls.qml"
)

$allExist = $true
foreach ($file in $qmlFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file NOT FOUND!" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host ""
    Write-Host "❌ Some QML files are missing!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All camera module files present!" -ForegroundColor Green
Write-Host ""

# Try to start application in test mode
Write-Host "3. Starting application in test mode..." -ForegroundColor Cyan
Write-Host "   (Will auto-close after 5 seconds)" -ForegroundColor Gray
Write-Host ""

$env:PNEUMOSTABSIM_QUICK_TEST = "1"
$process = Start-Process python -ArgumentList "app.py --test-mode" -PassThru -NoNewWindow

# Wait 5 seconds for initialization
Write-Host "   Waiting for initialization..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if process is still running
if ($process.HasExited) {
    if ($process.ExitCode -eq 0) {
        Write-Host "   ✅ Application started and exited cleanly (test mode)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Application crashed! Exit code: $($process.ExitCode)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ Application is running!" -ForegroundColor Green
    Write-Host "   Terminating test process..." -ForegroundColor Yellow
    Stop-Process -Id $process.Id -Force
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ✅ CAMERA INTEGRATION TEST PASSED!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "🚀 Ready for full visual testing!" -ForegroundColor Green
Write-Host ""
Write-Host "Run the application:" -ForegroundColor Yellow
Write-Host "   .\run.ps1" -ForegroundColor White
Write-Host ""
