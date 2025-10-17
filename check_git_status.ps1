# ============================================================================
# Скрипт проверки актуальности Git репозитория
# Версия: 1.0.0
# ============================================================================

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🔍 Проверка актуальности Git репозитория" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Функция для безопасного выполнения git команд
function Invoke-GitCommand {
    param([string]$Command)
    try {
        $result = Invoke-Expression "git $Command 2>&1" -ErrorAction Stop
        return $result
    } catch {
        Write-Host "⚠️  Ошибка выполнения: git $Command" -ForegroundColor Yellow
        return $null
    }
}

# 1. Текущая ветка
Write-Host "📌 Текущая ветка:" -ForegroundColor Green
$currentBranch = Invoke-GitCommand "branch --show-current"
Write-Host "   $currentBranch" -ForegroundColor White
Write-Host ""

# 2. Последний локальный коммит
Write-Host "📝 Последний локальный коммит:" -ForegroundColor Green
$lastCommit = Invoke-GitCommand "log -1 --oneline"
Write-Host "   $lastCommit" -ForegroundColor White
Write-Host ""

# 3. Статус репозитория
Write-Host "📊 Статус репозитория:" -ForegroundColor Green
$status = Invoke-GitCommand "status --short"
if ($status) {
    Write-Host $status -ForegroundColor Yellow
} else {
    Write-Host "   ✅ Рабочая директория чистая" -ForegroundColor Green
}
Write-Host ""

# 4. Обновление информации о удаленном репозитории
Write-Host "🔄 Обновление информации о remote..." -ForegroundColor Green
$fetchResult = Invoke-GitCommand "fetch origin --dry-run"
if ($fetchResult) {
    Write-Host "   Доступны обновления:" -ForegroundColor Yellow
    Write-Host $fetchResult -ForegroundColor White
} else {
    Write-Host "   ✅ Локальная ветка синхронизирована" -ForegroundColor Green
}
Write-Host ""

# 5. Сравнение с удаленной веткой
Write-Host "Сравнение с origin/${currentBranch}:" -ForegroundColor Green
$ahead = Invoke-GitCommand "rev-list --count origin/${currentBranch}..HEAD"
$behind = Invoke-GitCommand "rev-list --count HEAD..origin/${currentBranch}"

if ($ahead -and $behind) {
    if ($ahead -eq "0" -and $behind -eq "0") {
        Write-Host "   Ветка полностью синхронизирована" -ForegroundColor Green
    } elseif ($ahead -gt 0 -and $behind -eq "0") {
        Write-Host "   На $ahead коммит(ов) впереди remote" -ForegroundColor Cyan
    } elseif ($ahead -eq 0 -and $behind -gt 0) {
        Write-Host "   На $behind коммит(ов) отстаёт от remote" -ForegroundColor Yellow
    } else {
        Write-Host "   Ветки разошлись: +$ahead / -$behind" -ForegroundColor Red
    }
}
Write-Host ""

# 6. Список всех веток в remote
Write-Host "🌿 Ветки в удаленном репозитории:" -ForegroundColor Green
$remoteBranches = Invoke-GitCommand "branch -r"
if ($remoteBranches) {
    $remoteBranches | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
}
Write-Host ""

# 7. Последние 5 коммитов текущей ветки
Write-Host "📜 Последние 5 коммитов:" -ForegroundColor Green
$recentCommits = Invoke-GitCommand "log --oneline -5"
if ($recentCommits) {
    $recentCommits | ForEach-Object { Write-Host "   $_" -ForegroundColor White }
}
Write-Host ""

# 8. Изменённые файлы
Write-Host "📁 Изменённые файлы:" -ForegroundColor Green
$modifiedFiles = Invoke-GitCommand "diff --name-only"
if ($modifiedFiles) {
    $modifiedFiles | ForEach-Object { Write-Host "   Modified: $_" -ForegroundColor Yellow }
} else {
    Write-Host "   ✅ Нет изменённых файлов" -ForegroundColor Green
}
Write-Host ""

# 9. Неотслеживаемые файлы
Write-Host "➕ Неотслеживаемые файлы:" -ForegroundColor Green
$untrackedFiles = Invoke-GitCommand "ls-files --others --exclude-standard"
if ($untrackedFiles) {
    $untrackedFiles | ForEach-Object { Write-Host "   Untracked: $_" -ForegroundColor Cyan }
} else {
    Write-Host "   ✅ Нет неотслеживаемых файлов" -ForegroundColor Green
}
Write-Host ""

# 10. Рекомендации
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  Рекомендации:" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan

if ($behind -gt 0) {
    Write-Host "   Выполните: git pull origin ${currentBranch}" -ForegroundColor Yellow
}

if ($ahead -gt 0) {
    Write-Host "   Выполните: git push origin ${currentBranch}" -ForegroundColor Cyan
}

if ($modifiedFiles -or $untrackedFiles) {
    Write-Host "   Сохраните изменения: git add . && git commit -m 'message'" -ForegroundColor Magenta
}

if (-not $behind -and -not $ahead -and -not $modifiedFiles -and -not $untrackedFiles) {
    Write-Host "   Репозиторий в идеальном состоянии!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Проверка завершена!" -ForegroundColor Green
Write-Host ""
