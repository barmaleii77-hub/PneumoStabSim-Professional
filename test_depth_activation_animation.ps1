# Скрипт для тестирования depth texture activation и анимации
# PneumoStabSim Professional - Animation Test with Full QML Logging

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
}

Write-Host "🎬 Starting PneumoStabSim with full QML logging..." -ForegroundColor Cyan

# Включить все QML/JS логи
$env:QT_LOGGING_RULES = "js.debug=true;qt.qml.*=true;qt.quick.*=true"
if ($headlessRequested -or -not $env:QSG_INFO) {
    $env:QSG_INFO = if ($headlessRequested) { '1' } else { '0' }
}
$env:QT_DEBUG_PLUGINS = "0"

# Настройки для animation
$env:PSS_ENABLE_ANIMATION = "true"
$env:PSS_ANIMATION_FREQUENCY = "0.5"  # 0.5 Hz для медленной анимации

Write-Host "📋 Environment variables set:" -ForegroundColor Yellow
Write-Host "  QT_LOGGING_RULES: $env:QT_LOGGING_RULES"
Write-Host "  QSG_INFO: $env:QSG_INFO"
Write-Host "  PSS_ENABLE_ANIMATION: $env:PSS_ENABLE_ANIMATION"
Write-Host ""

# Запуск приложения с логированием в файл
$logFile = "reports/animation_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

Write-Host "🚀 Launching application (will run for 15 seconds)..." -ForegroundColor Green
Write-Host "📝 Log file: $logFile" -ForegroundColor Gray
Write-Host ""

# Запуск с перенаправлением в файл И на экран
python app.py 2>&1 | Tee-Object -FilePath $logFile

Write-Host ""
Write-Host "✅ Application closed" -ForegroundColor Green
Write-Host ""

# Анализ логов
Write-Host "📊 Analyzing logs..." -ForegroundColor Cyan
Write-Host ""

Write-Host "=== DEPTH TEXTURE ACTIVATION ===" -ForegroundColor Yellow
Select-String -Path $logFile -Pattern "DepthTextureActivator" -Context 0,2 | Select-Object -First 10
Write-Host ""

Write-Host "=== SCENE ENVIRONMENT CONTROLLER ===" -ForegroundColor Yellow
Select-String -Path $logFile -Pattern "SceneEnvironmentController" -Context 0,1 | Select-Object -First 5
Write-Host ""

Write-Host "=== SHADER COMPILATION ===" -ForegroundColor Yellow
Select-String -Path $logFile -Pattern "shader|GLSL|fog.*effect" -CaseSensitive:$false | Select-Object -First 10
Write-Host ""

Write-Host "=== ANIMATION EVENTS ===" -ForegroundColor Yellow
Select-String -Path $logFile -Pattern "animation|frequency|amplitude" -CaseSensitive:$false | Select-Object -First 15
Write-Host ""

Write-Host "=== QML BATCH UPDATES ===" -ForegroundColor Yellow
Select-String -Path $logFile -Pattern "QML updated" | Select-Object -First 10
Write-Host ""

Write-Host "📈 Statistics:" -ForegroundColor Cyan
$totalLines = (Get-Content $logFile).Count
$depthActivations = (Select-String -Path $logFile -Pattern "DepthTextureActivator").Count
$qmlUpdates = (Select-String -Path $logFile -Pattern "QML updated").Count
$shaderLogs = (Select-String -Path $logFile -Pattern "shader|GLSL").Count

Write-Host "  Total log lines: $totalLines"
Write-Host "  DepthTextureActivator mentions: $depthActivations"
Write-Host "  QML updates: $qmlUpdates"
Write-Host "  Shader-related logs: $shaderLogs"
Write-Host ""

if ($depthActivations -gt 0) {
    Write-Host "✅ Depth Texture Activation: WORKING" -ForegroundColor Green
} else {
    Write-Host "❌ Depth Texture Activation: NOT DETECTED" -ForegroundColor Red
}

if ($qmlUpdates -gt 5) {
    Write-Host "✅ QML Batch Updates: WORKING ($qmlUpdates updates)" -ForegroundColor Green
} else {
    Write-Host "⚠️  QML Batch Updates: LOW ACTIVITY ($qmlUpdates updates)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📄 Full log saved to: $logFile" -ForegroundColor Gray
Write-Host "🎬 Test complete!" -ForegroundColor Cyan
