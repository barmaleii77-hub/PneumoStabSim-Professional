# PowerShell Profile для PneumoStabSim
# Расположите этот файл в: $PROFILE или создайте псевдонимы

# Настройка для запуска PneumoStabSim
$PneumoPath = "C:\Users\Алексей\source\repos\barmaleii77-hub\PneumoStabSim-Professional"

# Псевдонимы для быстрого запуска
function Start-PneumoStabSim {
    [CmdletBinding()]
    param(
        [switch]$TestMode,
        [switch]$Monitor,
        [switch]$Safe,
        [switch]$Legacy,
        [switch]$Debug,
        [switch]$NoBlock
    )
    
    Set-Location $PneumoPath
    
    $arguments = @()
    if ($TestMode) { $arguments += "--test-mode" }
    if ($Monitor) { $arguments += "--monitor-perf" }
    if ($Safe) { $arguments += "--safe-mode" }
    if ($Legacy) { $arguments += "--legacy" }
    if ($Debug) { $arguments += "--debug" }
    if ($NoBlock) { $arguments += "--no-block" }
    
    Write-Host "🚀 Запуск PneumoStabSim..." -ForegroundColor Green
    py app.py @arguments
}

function Start-PneumoDiag {
    Set-Location $PneumoPath
    Write-Host "🔍 Запуск диагностики..." -ForegroundColor Yellow
    py diag.py
}

function Start-PneumoTest {
    Set-Location $PneumoPath
    Write-Host "🧪 Запуск тестов оптимизации..." -ForegroundColor Cyan
    py test_optimizations.py
}

function Start-PneumoQuickTest {
    Set-Location $PneumoPath
    Write-Host "⚡ Быстрый тест производительности..." -ForegroundColor Magenta
    py quick_performance_test.py
}

# Псевдонимы для краткости
Set-Alias pneumo Start-PneumoStabSim
Set-Alias pneumo-diag Start-PneumoDiag
Set-Alias pneumo-test Start-PneumoTest
Set-Alias pneumo-quick Start-PneumoQuickTest

# Информация о доступных командах
function Show-PneumoHelp {
    Write-Host "🎯 PNEUMOSTABSIM БЫСТРЫЕ КОМАНДЫ" -ForegroundColor Green
    Write-Host "=================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Основные команды:" -ForegroundColor Yellow
    Write-Host "  pneumo                    # Обычный запуск" -ForegroundColor White
    Write-Host "  pneumo -TestMode          # Тестовый режим (5 сек)" -ForegroundColor White
    Write-Host "  pneumo -Monitor           # С мониторингом производительности" -ForegroundColor White
    Write-Host "  pneumo -Safe              # Безопасный режим" -ForegroundColor White
    Write-Host "  pneumo -Legacy            # Legacy OpenGL" -ForegroundColor White
    Write-Host "  pneumo -NoBlock           # Неблокирующий режим" -ForegroundColor White
    Write-Host ""
    Write-Host "Диагностика и тесты:" -ForegroundColor Yellow
    Write-Host "  pneumo-diag               # Быстрая диагностика" -ForegroundColor White
    Write-Host "  pneumo-test               # Полные тесты оптимизации" -ForegroundColor White
    Write-Host "  pneumo-quick              # Быстрый тест производительности" -ForegroundColor White
    Write-Host ""
    Write-Host "Комбинированные команды:" -ForegroundColor Yellow
    Write-Host "  pneumo -TestMode -Monitor # Тест с мониторингом" -ForegroundColor White
    Write-Host "  pneumo -Debug -Safe       # Отладка в безопасном режиме" -ForegroundColor White
    Write-Host ""
}

# Показать справку при загрузке профиля
Show-PneumoHelp

Write-Host "✅ PneumoStabSim PowerShell Profile загружен!" -ForegroundColor Green
Write-Host "   Используйте команду 'Show-PneumoHelp' для справки" -ForegroundColor Gray
