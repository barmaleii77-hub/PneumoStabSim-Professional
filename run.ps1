# ============================================================================
# PneumoStabSim Professional - Быстрый запуск
# Активация окружения и запуск приложения одной командой
# ============================================================================

param(
    [switch]$Verbose,
    [switch]$Test,
    [switch]$Debug,
    [switch]$SafeMode,
    [switch]$Legacy
)

# Кодировка UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Проверка venv
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "❌ Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "📦 Запустите сначала: .\setup_environment.ps1" -ForegroundColor Yellow
    exit 1
}

# Активация venv
Write-Host "🔧 Активация виртуального окружения..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Настройка переменных окружения
$env:PYTHONPATH = "$PWD;$PWD\src"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"
$env:QT_ASSUME_STDERR_HAS_CONSOLE = "1"
$env:QT_AUTO_SCREEN_SCALE_FACTOR = "1"
$env:QT_SCALE_FACTOR_ROUNDING_POLICY = "PassThrough"
$env:QT_ENABLE_HIGHDPI_SCALING = "1"

$backendLabel = "OpenGL RHI (forced for advanced effects)"

if ($SafeMode) {
    if (Test-Path Env:\QSG_RHI_BACKEND) {
        Remove-Item Env:\QSG_RHI_BACKEND -ErrorAction SilentlyContinue
    }
    if (Test-Path Env:\QSG_OPENGL_VERSION) {
        Remove-Item Env:\QSG_OPENGL_VERSION -ErrorAction SilentlyContinue
    }
    if (Test-Path Env:\QT_OPENGL) {
        Remove-Item Env:\QT_OPENGL -ErrorAction SilentlyContinue
    }
    $backendLabel = "auto (Qt runtime default)"
    Write-Host "ℹ️ Safe mode detected — Qt will auto-select the scene graph backend." -ForegroundColor Yellow
} else {
    $env:QSG_RHI_BACKEND = "opengl"
    Write-Host "ℹ️ Standard mode active — forcing OpenGL scene graph backend for full feature support." -ForegroundColor Cyan
}

Write-Host "ℹ️ Scene graph backend configuration: $backendLabel" -ForegroundColor Cyan

if ($Debug) {
    $env:QSG_INFO = "1"
    $env:QT_LOGGING_RULES = "qt.qml.connections=true;qt.quick.3d=true"
    $env:PSS_DIAG = "1"
} else {
    $env:QSG_INFO = "0"
    $env:QT_LOGGING_RULES = "*.debug=false;*.info=false"
    $env:PSS_DIAG = "1"
}

# Формирование аргументов
$Args = @()
if ($Verbose) { $Args += "--verbose" }
if ($Test) { $Args += "--test-mode" }
if ($SafeMode) { $Args += "--safe-mode" }
if ($Legacy) {
    $Args += "--legacy"
    Write-Host "ℹ️ Legacy UI mode requested — QML loading will be skipped." -ForegroundColor Yellow
}

if (-not $SafeMode -and -not $Legacy) {
    Write-Host "ℹ️ Tips: add --safe-mode to let Qt choose DirectX or --legacy for the classic UI." -ForegroundColor Cyan
}

# Запуск
Write-Host "▶️  Запуск PneumoStabSim Professional..." -ForegroundColor Green
Write-Host ""

& ".\venv\Scripts\python.exe" app.py @Args

# Код выхода
$ExitCode = $LASTEXITCODE
if ($ExitCode -eq 0) {
    Write-Host "`n✅ Приложение завершилось успешно" -ForegroundColor Green
} else {
    Write-Host "`n❌ Приложение завершилось с ошибкой (код: $ExitCode)" -ForegroundColor Red
}

exit $ExitCode
