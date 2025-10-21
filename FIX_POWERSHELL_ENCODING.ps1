# ============================================================================
# FIX POWERSHELL ENCODING ISSUES
# Исправление проблем с кодировкой PowerShell в VS Code
# ============================================================================

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " ДИАГНОСТИКА И ИСПРАВЛЕНИЕ POWERSHELL" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

# 1. Текущая версия PowerShell
Write-Host "`n[1/6] Проверка версии PowerShell..." -ForegroundColor Yellow
Write-Host "Текущая версия: $($PSVersionTable.PSVersion)" -ForegroundColor White

if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Host "⚠️  PowerShell 5.x обнаружен - рекомендуется обновление до PowerShell 7+" -ForegroundColor Red
    Write-Host "   Скачать: https://github.com/PowerShell/PowerShell/releases" -ForegroundColor Gray
} else {
    Write-Host "✅ PowerShell 7+ установлен" -ForegroundColor Green
}

# 2. Текущая кодировка
Write-Host "`n[2/6] Проверка кодировки..." -ForegroundColor Yellow
Write-Host "Console Output Encoding: $([Console]::OutputEncoding.EncodingName)" -ForegroundColor White
Write-Host "Console Input Encoding:  $([Console]::InputEncoding.EncodingName)" -ForegroundColor White
Write-Host "Default Encoding: $([System.Text.Encoding]::Default.EncodingName)" -ForegroundColor White

# 3. Исправление кодировки на UTF-8
Write-Host "`n[3/6] Установка UTF-8 кодировки..." -ForegroundColor Yellow
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 | Out-Null
    Write-Host "✅ UTF-8 установлен для текущей сессии" -ForegroundColor Green
} catch {
    Write-Host "❌ Ошибка установки UTF-8: $_" -ForegroundColor Red
}

# 4. Проверка профиля PowerShell
Write-Host "`n[4/6] Проверка профиля PowerShell..." -ForegroundColor Yellow
Write-Host "Путь к профилю: $PROFILE" -ForegroundColor White

if (Test-Path $PROFILE) {
    Write-Host "✅ Профиль существует" -ForegroundColor Green
 
  # Проверяем, есть ли уже настройки кодировки
  $profileContent = Get-Content $PROFILE -Raw
    if ($profileContent -match "Console.*OutputEncoding.*UTF8") {
        Write-Host "✅ UTF-8 настройки уже есть в профиле" -ForegroundColor Green
    } else {
        Write-Host "⚠️  UTF-8 настройки отсутствуют в профиле" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Профиль не существует" -ForegroundColor Yellow
}

# 5. Создание/обновление профиля PowerShell
Write-Host "`n[5/6] Настройка профиля PowerShell..." -ForegroundColor Yellow

$profileDir = Split-Path $PROFILE -Parent
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
 Write-Host "✅ Создана директория профиля: $profileDir" -ForegroundColor Green
}

$utfSettings = @'

# ═══════════════════════════════════════════════════════════════════
# UTF-8 ENCODING FIX for PneumoStabSim Professional
# Добавлено автоматически скриптом FIX_POWERSHELL_ENCODING.ps1
# ═══════════════════════════════════════════════════════════════════

# Установка UTF-8 кодировки для PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Установка кодовой страницы 65001 (UTF-8)
if ($Host.Name -eq 'ConsoleHost') {
    chcp 65001 | Out-Null
}

# Отключение предупреждений о прогрессе (ускорение)
$ProgressPreference = 'SilentlyContinue'

# Улучшенное отображение ошибок
$ErrorView = 'NormalView'

# PSReadLine настройки (если установлен)
if (Get-Module -ListAvailable -Name PSReadLine) {
  Import-Module PSReadLine
    Set-PSReadLineOption -EditMode Windows
    Set-PSReadLineOption -PredictionSource History
}

# ═══════════════════════════════════════════════════════════════════

'@

if (Test-Path $PROFILE) {
    $currentProfile = Get-Content $PROFILE -Raw
    if ($currentProfile -notmatch "UTF-8 ENCODING FIX for PneumoStabSim") {
 Add-Content -Path $PROFILE -Value $utfSettings
 Write-Host "✅ UTF-8 настройки добавлены в профиль" -ForegroundColor Green
    } else {
Write-Host "✅ UTF-8 настройки уже присутствуют" -ForegroundColor Green
  }
} else {
    Set-Content -Path $PROFILE -Value $utfSettings -Encoding UTF8
    Write-Host "✅ Профиль создан с UTF-8 настройками" -ForegroundColor Green
}

# 6. Тестирование команд
Write-Host "`n[6/6] Тестирование команд..." -ForegroundColor Yellow

$testCommands = @(
    @{Name = "Test-Path"; Command = { Test-Path . }},
    @{Name = "Get-Content"; Command = { Get-Content README.md -TotalCount 1 -ErrorAction SilentlyContinue }},
    @{Name = "Get-ChildItem"; Command = { Get-ChildItem -Path . -ErrorAction SilentlyContinue | Select-Object -First 1 }}
)

$testsPassed = 0
foreach ($test in $testCommands) {
    try {
        $result = & $test.Command
        Write-Host "✅ $($test.Name) работает" -ForegroundColor Green
  $testsPassed++
    } catch {
 Write-Host "❌ $($test.Name) не работает: $_" -ForegroundColor Red
}
}

# Итоговый отчёт
Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " ИТОГОВЫЙ ОТЧЁТ" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host "`n✅ Тестов пройдено: $testsPassed/$($testCommands.Count)" -ForegroundColor $(if ($testsPassed -eq $testCommands.Count) {"Green"} else {"Yellow"})

Write-Host "`n📋 СЛЕДУЮЩИЕ ШАГИ:" -ForegroundColor Cyan
Write-Host "1. Перезапустите VS Code для применения изменений профиля" -ForegroundColor White
Write-Host "2. Или перезапустите терминал (Ctrl+Shift+``)" -ForegroundColor White
Write-Host "3. Запустите: .\check_setup.ps1 для проверки" -ForegroundColor White

if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Host "`n⚠️  РЕКОМЕНДАЦИЯ: Установите PowerShell 7+" -ForegroundColor Yellow
    Write-Host "   URL: https://aka.ms/powershell-release?tag=stable" -ForegroundColor Gray
    Write-Host "   После установки настройте VS Code на использование pwsh.exe" -ForegroundColor Gray
}

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
