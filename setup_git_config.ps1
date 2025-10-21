# Git Configuration Script для PneumoStabSim Professional
# Запуск: .\setup_git_config.ps1

Write-Host "🔧 Настройка Git конфигурации для проекта..." -ForegroundColor Cyan

# Line endings
Write-Host "  ✓ Настройка line endings (CRLF для Windows)..." -ForegroundColor Green
git config --local core.autocrlf true
git config --local core.filemode false

# Pull/Merge strategy
Write-Host "  ✓ Настройка pull/merge стратегии..." -ForegroundColor Green
git config --local pull.rebase false
git config --local merge.conflictstyle diff3

# Diff алгоритм
Write-Host "  ✓ Настройка diff алгоритма (histogram)..." -ForegroundColor Green
git config --local diff.algorithm histogram

# Unicode support
Write-Host "  ✓ Настройка Unicode поддержки..." -ForegroundColor Green
git config --local core.quotepath false
git config --local gui.encoding utf-8

# Performance
Write-Host "  ✓ Оптимизация производительности..." -ForegroundColor Green
git config --local core.preloadindex true
git config --local core.fscache true

# Git LFS для больших файлов (HDR, etc.)
Write-Host "  ✓ Проверка Git LFS..." -ForegroundColor Green
$lfsInstalled = git lfs version 2>$null
if ($lfsInstalled) {
    git lfs install --local
    Write-Host "    Git LFS активирован" -ForegroundColor Green
} else {
    Write-Host "    ⚠ Git LFS не установлен (опционально для HDR файлов)" -ForegroundColor Yellow
}

Write-Host "`n✅ Git конфигурация завершена!" -ForegroundColor Green

# Показать текущую конфигурацию
Write-Host "`n📋 Текущая конфигурация:" -ForegroundColor Cyan
git config --local --list | Select-String "core\.|pull\.|merge\.|diff\."
