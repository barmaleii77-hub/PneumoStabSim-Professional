# =============================================================================
# VS Code Extensions - Quick Check & Install
# Быстрая проверка и установка расширений
# =============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " VS Code Extensions Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Поиск VS Code
$codeCmd = "code"
try {
  $version = & $codeCmd --version 2>&1
    if ($LASTEXITCODE -eq 0) {
     Write-Host "✅ VS Code найден" -ForegroundColor Green
 Write-Host "   Версия: $($version[0])`n" -ForegroundColor Gray
  } else {
        Write-Host "❌ VS Code не найден!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ VS Code не найден в PATH!" -ForegroundColor Red
    exit 1
}

# Список критических расширений
$criticalExtensions = @(
 "ms-python.python",
    "ms-python.vscode-pylance",
    "github.copilot",
    "github.copilot-chat"
)

# Список рекомендуемых расширений
$recommendedExtensions = @(
    "ms-python.black-formatter",
    "bbenoist.qml",
    "seanwu.vscode-qt-for-python",
    "eamodio.gitlens",
    "ms-vscode.powershell"
)

# Получение установленных расширений
Write-Host "Получение списка установленных расширений..." -ForegroundColor Yellow
$installed = & $codeCmd --list-extensions 2>&1

Write-Host "`n📦 Критические расширения:" -ForegroundColor Cyan
Write-Host ("-" * 60) -ForegroundColor Gray

$criticalMissing = @()
foreach ($ext in $criticalExtensions) {
  if ($installed -contains $ext) {
        Write-Host "  ✅ $ext" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $ext" -ForegroundColor Red
   $criticalMissing += $ext
    }
}

Write-Host "`n📦 Рекомендуемые расширения:" -ForegroundColor Cyan
Write-Host ("-" * 60) -ForegroundColor Gray

$recommendedMissing = @()
foreach ($ext in $recommendedExtensions) {
    if ($installed -contains $ext) {
        Write-Host "  ✅ $ext" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $ext" -ForegroundColor Yellow
        $recommendedMissing += $ext
    }
}

# Установка недостающих
$allMissing = $criticalMissing + $recommendedMissing

if ($allMissing.Count -gt 0) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " Установка недостающих расширений" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Write-Host "Найдено недостающих: $($allMissing.Count)" -ForegroundColor Yellow
    Write-Host "Нажмите Enter для установки или Ctrl+C для отмены..."
    Read-Host
    
    $success = 0
    $failed = 0
    
    foreach ($ext in $allMissing) {
   Write-Host "`nУстановка: $ext..." -ForegroundColor Yellow
        
     try {
  & $codeCmd --install-extension $ext --force 2>&1 | Out-Null
        
 if ($LASTEXITCODE -eq 0) {
           Write-Host "  ✅ Установлено" -ForegroundColor Green
    $success++
            } else {
     Write-Host "  ❌ Ошибка" -ForegroundColor Red
     $failed++
   }
        } catch {
         Write-Host "  ❌ Ошибка: $_" -ForegroundColor Red
   $failed++
}
    }
    
  Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " Итого" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
  
    Write-Host "  ✅ Установлено: $success" -ForegroundColor Green
    Write-Host "  ❌ Ошибок: $failed" -ForegroundColor Red
    
} else {
    Write-Host "`n✅ Все расширения уже установлены!" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Рекомендации" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "1. Перезапустите VS Code" -ForegroundColor White
Write-Host "2. Настройте GitHub Copilot (войдите в GitHub)" -ForegroundColor White
Write-Host "3. Выберите Python interpreter: Ctrl+Shift+P -> Python: Select Interpreter" -ForegroundColor White

Write-Host "`n✅ Проверка завершена!`n" -ForegroundColor Green
