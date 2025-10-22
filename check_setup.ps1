# Проверка настроек проекта PneumoStabSim Professional
# Запуск: .\check_setup.ps1

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host " ПРОВЕРКА НАСТРОЕК ПРОЕКТА" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# 1. Python version
Write-Host "`n1️⃣  Python Environment:" -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "   Version: $pythonVersion"

if (Test-Path ".venv/Scripts/python.exe") {
    Write-Host "   ✅ Virtual environment exists" -ForegroundColor Green
 $venvPython = .\.venv\Scripts\python.exe --version 2>&1
    Write-Host " venv Python: $venvPython"
} else {
    Write-Host "   ⚠️  Virtual environment not found" -ForegroundColor Yellow
}

# 2. Dependencies
Write-Host "`n2️⃣  Dependencies:" -ForegroundColor Yellow
$reqFiles = @("requirements.txt", "requirements-dev.txt")
foreach ($file in $reqFiles) {
 if (Test-Path $file) {
     Write-Host "   ✅ $file exists" -ForegroundColor Green
    } else {
   Write-Host "   ❌ $file missing" -ForegroundColor Red
    }
}

# 3. VS Code settings
Write-Host "`n3️⃣  VS Code Configuration:" -ForegroundColor Yellow
$vscodeFiles = @(".vscode/settings.json", ".vscode/launch.json")
foreach ($file in $vscodeFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file missing" -ForegroundColor Red
    }
}

# 4. EditorConfig
Write-Host "`n4️⃣  EditorConfig:" -ForegroundColor Yellow
if (Test-Path ".editorconfig") {
    Write-Host "   ✅ .editorconfig exists" -ForegroundColor Green
} else {
    Write-Host "   ❌ .editorconfig missing" -ForegroundColor Red
}

# 5. Pre-commit hooks
Write-Host "`n5️⃣  Pre-commit Hooks:" -ForegroundColor Yellow
if (Test-Path ".pre-commit-config.yaml") {
    Write-Host "   ✅ .pre-commit-config.yaml exists" -ForegroundColor Green

    $precommitInstalled = pre-commit --version 2>$null
    if ($precommitInstalled) {
  Write-Host "   ✅ pre-commit installed" -ForegroundColor Green
    } else {
    Write-Host "   ⚠️  pre-commit not installed (pip install pre-commit)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ .pre-commit-config.yaml missing" -ForegroundColor Red
}

# 6. Git configuration
Write-Host "`n6️⃣  Git Configuration:" -ForegroundColor Yellow
$gitConfigured = $false
try {
    $userName = git config --local user.name 2>$null
$userEmail = git config --local user.email 2>$null

    if ($userName -and $userEmail) {
        Write-Host "   ✅ Git user configured" -ForegroundColor Green
        Write-Host "      Name: $userName"
     Write-Host "   Email: $userEmail"
      $gitConfigured = $true
    } else {
     Write-Host "   ⚠️  Git user not configured locally" -ForegroundColor Yellow
        Write-Host "      Run: git config --local user.name 'Your Name'" -ForegroundColor Gray
        Write-Host "      Run: git config --local user.email 'your@email.com'" -ForegroundColor Gray
    }

    $autocrlf = git config --local core.autocrlf 2>$null
    if ($autocrlf -eq "true") {
        Write-Host " ✅ CRLF handling configured" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  CRLF not configured (run .\setup_git_config.ps1)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Not a git repository" -ForegroundColor Red
}

# 7. Copilot instructions
Write-Host "`n7️⃣  GitHub Copilot:" -ForegroundColor Yellow
if (Test-Path ".github/copilot-instructions.md") {
    Write-Host "   ✅ Copilot instructions exist" -ForegroundColor Green
    $lines = (Get-Content ".github/copilot-instructions.md" | Measure-Object -Line).Lines
    Write-Host "  Lines: $lines"
} else {
    Write-Host "   ❌ Copilot instructions missing" -ForegroundColor Red
}

# 8. Project structure
Write-Host "`n8️⃣  Project Structure:" -ForegroundColor Yellow
$keyDirs = @("src", "assets", "tests", "config")
foreach ($dir in $keyDirs) {
    if (Test-Path $dir) {
        Write-Host "   ✅ $dir/ exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $dir/ missing" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host " SUMMARY" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$checks = @(
@{Name="Python"; Status=(Test-Path ".venv/Scripts/python.exe")},
    @{Name="Dependencies"; Status=(Test-Path "requirements.txt")},
    @{Name="VS Code"; Status=(Test-Path ".vscode/settings.json")},
    @{Name="EditorConfig"; Status=(Test-Path ".editorconfig")},
    @{Name="Pre-commit"; Status=(Test-Path ".pre-commit-config.yaml")},
    @{Name="Git Config"; Status=$gitConfigured},
    @{Name="Copilot"; Status=(Test-Path ".github/copilot-instructions.md")},
    @{Name="Project Structure"; Status=(Test-Path "src")}
)

$passed = ($checks | Where-Object {$_.Status}).Count
$total = $checks.Count

Write-Host "`n📊 Score: $passed/$total checks passed" -ForegroundColor $(if ($passed -eq $total) {"Green"} elseif ($passed -ge $total * 0.75) {"Yellow"} else {"Red"})

if ($passed -eq $total) {
    Write-Host "✅ All checks passed! You're ready to go! " -ForegroundColor Green
} else {
    Write-Host "⚠️  Some checks failed. Review the output above." -ForegroundColor Yellow
}

Write-Host "`n💡 Quick fixes:" -ForegroundColor Cyan
if (-not $gitConfigured) {
    Write-Host "   • Git config: .\setup_git_config.ps1" -ForegroundColor Gray
}
if (-not (Test-Path ".venv")) {
    Write-Host "   • Create venv: python -m venv .venv" -ForegroundColor Gray
    Write-Host "   • Activate: .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "   • Install deps: pip install -r requirements-dev.txt" -ForegroundColor Gray
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
