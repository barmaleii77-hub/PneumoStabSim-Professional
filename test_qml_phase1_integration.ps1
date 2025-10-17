# ═══════════════════════════════════════════════════════════════════════
# QML PHASE 1 - Integration Test Script
# ═══════════════════════════════════════════════════════════════════════

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🧪 QML PHASE 1 INTEGRATION TEST" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check if core modules exist
Write-Host "📁 Checking Core Modules..." -ForegroundColor Yellow
$coreFiles = @(
    "assets\qml\core\qmldir",
    "assets\qml\core\MathUtils.qml",
    "assets\qml\core\GeometryCalculations.qml",
    "assets\qml\core\StateCache.qml"
)

$allExist = $true
foreach ($file in $coreFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file NOT FOUND" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host ""
    Write-Host "❌ MISSING FILES! Cannot proceed with integration test." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All core modules present" -ForegroundColor Green
Write-Host ""

# Check main.qml import
Write-Host "🔍 Checking main.qml import..." -ForegroundColor Yellow
$mainQml = Get-Content "assets\qml\main.qml" -Raw
if ($mainQml -match 'import "core"') {
    Write-Host "   ✅ Core import found in main.qml" -ForegroundColor Green
} else {
    Write-Host "   ❌ Core import NOT found in main.qml" -ForegroundColor Red
    Write-Host "   Please add: import `"core`"" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🚀 LAUNCHING APPLICATION" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Expected QML console output:" -ForegroundColor Yellow
Write-Host "   ✅ MathUtils Singleton initialized (v1.0.0)" -ForegroundColor Gray
Write-Host "   ✅ GeometryCalculations Singleton initialized (v1.0.0)" -ForegroundColor Gray
Write-Host "   ✅ StateCache Singleton initialized (v1.0.0)" -ForegroundColor Gray
Write-Host ""
Write-Host "If you see these messages, INTEGRATION IS SUCCESSFUL!" -ForegroundColor Green
Write-Host ""
Write-Host "Testing checklist:" -ForegroundColor Yellow
Write-Host "   [ ] Application starts without QML errors" -ForegroundColor White
Write-Host "   [ ] 3D scene renders correctly" -ForegroundColor White
Write-Host "   [ ] Animation runs smoothly (if enabled)" -ForegroundColor White
Write-Host "   [ ] Camera controls work (mouse rotation/zoom)" -ForegroundColor White
Write-Host "   [ ] GraphicsPanel updates apply correctly" -ForegroundColor White
Write-Host ""
Write-Host "Press ENTER to launch application..." -ForegroundColor Cyan
Read-Host

# Launch application
Write-Host ""
Write-Host "🚀 Starting PneumoStabSim Professional..." -ForegroundColor Green
Write-Host ""

python app.py

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  📊 INTEGRATION TEST REPORT" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Did the application start successfully? (Y/N)" -ForegroundColor Yellow
$startOk = Read-Host

if ($startOk -eq "Y" -or $startOk -eq "y") {
    Write-Host ""
    Write-Host "✅ Application started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Did you see Core Utilities initialization messages? (Y/N)" -ForegroundColor Yellow
    $initOk = Read-Host
    
    if ($initOk -eq "Y" -or $initOk -eq "y") {
        Write-Host ""
        Write-Host "✅ Core Utilities initialized successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Was the 3D rendering correct? (Y/N)" -ForegroundColor Yellow
        $renderOk = Read-Host
        
        if ($renderOk -eq "Y" -or $renderOk -eq "y") {
            Write-Host ""
            Write-Host "✅ 3D rendering working correctly!" -ForegroundColor Green
            Write-Host ""
            Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
            Write-Host "  🎉 QML PHASE 1 INTEGRATION TEST: PASSED!" -ForegroundColor Green
            Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
            Write-Host ""
            Write-Host "Integration Status:" -ForegroundColor Yellow
            Write-Host "   ✅ Core modules loading correctly" -ForegroundColor Green
            Write-Host "   ✅ Singletons initialized successfully" -ForegroundColor Green
            Write-Host "   ✅ main.qml integration working" -ForegroundColor Green
            Write-Host "   ✅ 3D rendering functional" -ForegroundColor Green
            Write-Host ""
            Write-Host "Next Steps:" -ForegroundColor Yellow
            Write-Host "   1. 📊 Measure performance improvements (FPS)" -ForegroundColor White
            Write-Host "   2. 🧪 Test GraphicsPanel batch updates" -ForegroundColor White
            Write-Host "   3. 🚀 Begin Phase 2: Camera System refactoring" -ForegroundColor White
            Write-Host ""
            Write-Host "PHASE 1 INTEGRATION: ✅ COMPLETE" -ForegroundColor Green
            Write-Host ""
        } else {
            Write-Host ""
            Write-Host "⚠️ 3D rendering issue detected!" -ForegroundColor Red
            Write-Host ""
            Write-Host "Troubleshooting:" -ForegroundColor Yellow
            Write-Host "   1. Check QML console for errors" -ForegroundColor White
            Write-Host "   2. Verify GeometryCalculations functions" -ForegroundColor White
            Write-Host "   3. Check StateCache property bindings" -ForegroundColor White
        }
    } else {
        Write-Host ""
        Write-Host "⚠️ Core Utilities initialization issue!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "   1. Check qmldir registration" -ForegroundColor White
        Write-Host "   2. Verify singleton pragma in QML files" -ForegroundColor White
        Write-Host "   3. Check import 'core' in main.qml" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "❌ Application failed to start!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check for errors in the console output above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "   - QML syntax errors" -ForegroundColor White
    Write-Host "   - Missing core modules" -ForegroundColor White
    Write-Host "   - Invalid singleton registration" -ForegroundColor White
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Test completed. Press ENTER to exit." -ForegroundColor White
Read-Host
