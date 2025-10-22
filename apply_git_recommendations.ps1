# ============================================================================
# Применение рекомендаций после проверки Git
# ============================================================================

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  Применение рекомендаций Git Check" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Удалить нерабочий скрипт
Write-Host "[1] Удаление нерабочего скрипта..." -ForegroundColor Yellow
if (Test-Path "check_git_status.ps1") {
    Remove-Item "check_git_status.ps1" -Force
    Write-Host "    OK: check_git_status.ps1 удален" -ForegroundColor Green
} else {
    Write-Host "    SKIP: файл уже удален" -ForegroundColor Gray
}
Write-Host ""

# 2. Показать изменения
Write-Host "[2] Изменённые файлы:" -ForegroundColor Yellow
git status --short
Write-Host ""

# 3. Спросить пользователя
Write-Host "[3] Выберите действие:" -ForegroundColor Yellow
Write-Host "    [1] Сохранить ТОЛЬКО .vscode исправления" -ForegroundColor Cyan
Write-Host "    [2] Сохранить ВСЁ (включая скрипты и документацию)" -ForegroundColor Cyan
Write-Host "    [3] Ничего не делать (выход)" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Ваш выбор (1/2/3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Сохранение только .vscode изменений..." -ForegroundColor Green

        # Добавить только .vscode
        git add .vscode/tasks.json .vscode/launch.json

        # Показать что будет закоммичено
        Write-Host ""
        Write-Host "Будет закоммичено:" -ForegroundColor Yellow
        git status --short
        Write-Host ""

        # Коммит
        $commitMsg = @"
FIX: .vscode tasks - use venv Python 3.13 for all commands

CHANGES:
- Replaced 'py' with venv Python path in all 23 tasks
- Fixed PYTHONPATH: added workspace root folder
- Updated git check task to use check_git_sync.ps1

RESULT:
- All tasks now use correct venv Python 3.13
- No conflicts with global Python installations
- Consistent environment across all tasks
"@

        git commit -m $commitMsg

        Write-Host ""
        Write-Host "OK: Изменения закоммичены!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Отправить в remote? (Y/N)" -ForegroundColor Yellow
        $push = Read-Host

        if ($push -eq "Y" -or $push -eq "y") {
            git push origin feature/hdr-assets-migration
            Write-Host ""
            Write-Host "OK: Изменения отправлены в remote!" -ForegroundColor Green
        }
    }

    "2" {
        Write-Host ""
        Write-Host "Сохранение всех изменений..." -ForegroundColor Green

        # Добавить .vscode
        git add .vscode/

        # Добавить полезные скрипты
        git add check_git_sync.ps1 quick_setup.ps1 run.ps1 setup_environment.ps1

        # Добавить документацию
        git add FINAL_GIT_REPORT.md README_GIT_CHECK.md QUICKSTART.md SETUP_GUIDE.md

        # Показать что будет закоммичено
        Write-Host ""
        Write-Host "Будет закоммичено:" -ForegroundColor Yellow
        git status --short
        Write-Host ""

        # Два коммита: сначала .vscode, потом скрипты
        $commitMsg1 = @"
FIX: .vscode tasks - use venv Python 3.13 for all commands

CHANGES:
- Replaced 'py' with venv Python path in all 23 tasks
- Fixed PYTHONPATH: added workspace root folder
- Updated git check task to use check_git_sync.ps1

RESULT:
- All tasks now use correct venv Python 3.13
- No conflicts with global Python installations
"@

        git commit .vscode/ -m $commitMsg1

        $commitMsg2 = @"
ADD: Git sync checker and automation scripts

ADDED:
- check_git_sync.ps1: comprehensive Git status checker
- FINAL_GIT_REPORT.md: detailed repository analysis
- README_GIT_CHECK.md: quick summary
- quick_setup.ps1: automated environment setup
- run.ps1: quick app launcher
- setup_environment.ps1: venv configuration
- QUICKSTART.md, SETUP_GUIDE.md: documentation

RESULT:
- Easier repository management
- Automated setup process
- Better documentation
"@

        git add check_git_sync.ps1 *.ps1 *.md
        git commit -m $commitMsg2

        Write-Host ""
        Write-Host "OK: Все изменения закоммичены!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Отправить в remote? (Y/N)" -ForegroundColor Yellow
        $push = Read-Host

        if ($push -eq "Y" -or $push -eq "y") {
            git push origin feature/hdr-assets-migration
            Write-Host ""
            Write-Host "OK: Изменения отправлены в remote!" -ForegroundColor Green
        }
    }

    "3" {
        Write-Host ""
        Write-Host "Выход без изменений." -ForegroundColor Gray
        Write-Host ""
        exit
    }

    default {
        Write-Host ""
        Write-Host "ОШИБКА: Неверный выбор!" -ForegroundColor Red
        Write-Host ""
        exit 1
    }
}

Write-Host ""
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  Готово!" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Проверить результат:" -ForegroundColor Yellow
Write-Host "    git log -3 --oneline" -ForegroundColor Gray
Write-Host ""
