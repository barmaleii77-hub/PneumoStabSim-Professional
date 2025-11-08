# ============================================================================
# Скрипт проверки актуальности Git репозитория
# Версия: 2.0.0 (адаптирована для локальных и удалённых сценариев)
# ============================================================================

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🔍 Проверка актуальности Git репозитория" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

function Invoke-GitCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    try {
        $output = & git @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        return [pscustomobject]@{
            Success = ($exitCode -eq 0)
            Output  = $output
        }
    } catch {
        return [pscustomobject]@{
            Success = $false
            Output  = @($_.Exception.Message)
        }
    }
}

function Get-TrimmedText {
    param([object]$Value)

    if (-not $Value) {
        return ""
    }

    return ($Value | Out-String).Trim()
}

function Write-Lines {
    param(
        [object]$Lines,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )

    if (-not $Lines) {
        return
    }

    foreach ($line in $Lines) {
        if ($null -ne $line -and $line.ToString().Trim().Length -gt 0) {
            Write-Host "   $line" -ForegroundColor $Color
        }
    }
}

$currentBranch = ""
$hasWorkingChanges = $false
$aheadCount = $null
$behindCount = $null
$upstreamName = $null

# 1. Текущая ветка
Write-Host "📌 Текущая ветка:" -ForegroundColor Green
$branchResult = Invoke-GitCommand -Arguments @("branch", "--show-current")
if ($branchResult.Success) {
    $currentBranch = Get-TrimmedText $branchResult.Output
    if (-not $currentBranch) {
        $currentBranch = "(detached HEAD)"
    }
    Write-Host "   $currentBranch" -ForegroundColor White
} else {
    Write-Host "   ⚠️  Не удалось определить текущую ветку" -ForegroundColor Yellow
}
Write-Host ""

# 2. Последний локальный коммит
Write-Host "📝 Последний локальный коммит:" -ForegroundColor Green
$lastCommitResult = Invoke-GitCommand -Arguments @("log", "-1", "--oneline")
if ($lastCommitResult.Success -and $lastCommitResult.Output) {
    Write-Lines -Lines $lastCommitResult.Output -Color ([ConsoleColor]::White)
} else {
    Write-Host "   ⚠️  Коммиты отсутствуют" -ForegroundColor Yellow
}
Write-Host ""

# 3. Статус репозитория
Write-Host "📊 Статус репозитория:" -ForegroundColor Green
$statusResult = Invoke-GitCommand -Arguments @("status", "--short")
if ($statusResult.Success -and $statusResult.Output) {
    $hasWorkingChanges = $true
    Write-Lines -Lines $statusResult.Output -Color ([ConsoleColor]::Yellow)
} elseif ($statusResult.Success) {
    Write-Host "   ✅ Рабочая директория чистая" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Не удалось получить статус" -ForegroundColor Yellow
}
Write-Host ""

# 4. Информация о доступных remotes
Write-Host "🌐 Доступные remotes:" -ForegroundColor Green
$remoteResult = Invoke-GitCommand -Arguments @("remote")
$remotes = @()
if ($remoteResult.Success -and $remoteResult.Output) {
    $remotes = $remoteResult.Output | Where-Object { $_.Trim().Length -gt 0 }
    Write-Lines -Lines $remotes -Color ([ConsoleColor]::Gray)
} else {
    Write-Host "   ⚠️  Remotes не настроены" -ForegroundColor Yellow
}
Write-Host ""

$originConfigured = $remotes | Where-Object { $_.Trim() -eq "origin" }

# 5. Обновление информации о удаленном репозитории
Write-Host "🔄 Проверка удалённых обновлений..." -ForegroundColor Green
if ($originConfigured) {
    $fetchResult = Invoke-GitCommand -Arguments @("fetch", "origin", "--dry-run")
    if ($fetchResult.Success -and $fetchResult.Output) {
        Write-Host "   Доступны новые данные:" -ForegroundColor Yellow
        Write-Lines -Lines $fetchResult.Output
    } elseif ($fetchResult.Success) {
        Write-Host "   ✅ Локальная информация синхронизирована" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Не удалось обновить информацию о remote" -ForegroundColor Yellow
        Write-Lines -Lines $fetchResult.Output -Color ([ConsoleColor]::Yellow)
    }
} else {
    Write-Host "   ⚠️  Remote 'origin' не настроен, пропускаем обновление" -ForegroundColor Yellow
}
Write-Host ""

# 6. Сравнение с удалённой веткой
Write-Host "📈 Сравнение с upstream:" -ForegroundColor Green
if ($originConfigured) {
    $upstreamResult = Invoke-GitCommand -Arguments @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if ($upstreamResult.Success -and $upstreamResult.Output) {
        $upstreamName = Get-TrimmedText $upstreamResult.Output
        Write-Host "   Upstream: $upstreamName" -ForegroundColor White

        $aheadResult = Invoke-GitCommand -Arguments @("rev-list", "--count", "${upstreamName}..HEAD")
        if ($aheadResult.Success -and $aheadResult.Output) {
            $aheadCount = [int](Get-TrimmedText $aheadResult.Output)
        }

        $behindResult = Invoke-GitCommand -Arguments @("rev-list", "--count", "HEAD..${upstreamName}")
        if ($behindResult.Success -and $behindResult.Output) {
            $behindCount = [int](Get-TrimmedText $behindResult.Output)
        }

        if ($null -ne $aheadCount -and $null -ne $behindCount) {
            if ($aheadCount -eq 0 -and $behindCount -eq 0) {
                Write-Host "   ✅ Ветка полностью синхронизирована" -ForegroundColor Green
            } elseif ($aheadCount -gt 0 -and $behindCount -eq 0) {
                Write-Host "   🔼 На $aheadCount коммит(ов) впереди upstream" -ForegroundColor Cyan
            } elseif ($aheadCount -eq 0 -and $behindCount -gt 0) {
                Write-Host "   🔽 На $behindCount коммит(ов) отстаёт от upstream" -ForegroundColor Yellow
            } else {
                Write-Host "   ⚠️  Ветки разошлись: +$aheadCount / -$behindCount" -ForegroundColor Red
            }
        } else {
            Write-Host "   ⚠️  Не удалось вычислить разницу коммитов" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠️  Upstream для текущей ветки не настроен" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ℹ️  Сравнение недоступно без настроенного remote" -ForegroundColor Yellow
}
Write-Host ""

# 7. Список всех веток в remote
Write-Host "🌿 Ветки в удаленном репозитории:" -ForegroundColor Green
if ($originConfigured) {
    $remoteBranches = Invoke-GitCommand -Arguments @("branch", "-r")
    if ($remoteBranches.Success -and $remoteBranches.Output) {
        Write-Lines -Lines $remoteBranches.Output -Color ([ConsoleColor]::Gray)
    } else {
        Write-Host "   ⚠️  Удалённых веток не найдено" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  Remote не настроен" -ForegroundColor Yellow
}
Write-Host ""

# 8. Последние 5 коммитов текущей ветки
Write-Host "📜 Последние 5 коммитов:" -ForegroundColor Green
$recentCommits = Invoke-GitCommand -Arguments @("log", "--oneline", "-5")
if ($recentCommits.Success -and $recentCommits.Output) {
    Write-Lines -Lines $recentCommits.Output -Color ([ConsoleColor]::White)
} else {
    Write-Host "   ⚠️  Не удалось получить историю коммитов" -ForegroundColor Yellow
}
Write-Host ""

# 9. Изменённые файлы
Write-Host "📁 Изменённые файлы:" -ForegroundColor Green
$modifiedFiles = Invoke-GitCommand -Arguments @("diff", "--name-only")
if ($modifiedFiles.Success -and $modifiedFiles.Output) {
    $hasWorkingChanges = $true
    Write-Lines -Lines ($modifiedFiles.Output | ForEach-Object { "Modified: $_" }) -Color ([ConsoleColor]::Yellow)
} elseif ($modifiedFiles.Success) {
    Write-Host "   ✅ Нет изменённых файлов" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Не удалось получить список изменённых файлов" -ForegroundColor Yellow
}
Write-Host ""

# 10. Неотслеживаемые файлы
Write-Host "➕ Неотслеживаемые файлы:" -ForegroundColor Green
$untrackedFiles = Invoke-GitCommand -Arguments @("ls-files", "--others", "--exclude-standard")
if ($untrackedFiles.Success -and $untrackedFiles.Output) {
    $hasWorkingChanges = $true
    Write-Lines -Lines ($untrackedFiles.Output | ForEach-Object { "Untracked: $_" }) -Color ([ConsoleColor]::Cyan)
} elseif ($untrackedFiles.Success) {
    Write-Host "   ✅ Нет неотслеживаемых файлов" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Не удалось получить список неотслеживаемых файлов" -ForegroundColor Yellow
}
Write-Host ""

# 11. Рекомендации
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  Рекомендации:" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan

if ($behindCount -gt 0) {
    $target = if ($upstreamName) { $upstreamName } else { "origin/$currentBranch" }
    Write-Host "   Выполните: git pull $target" -ForegroundColor Yellow
}

if ($aheadCount -gt 0) {
    $target = if ($upstreamName) { $upstreamName } else { "origin/$currentBranch" }
    Write-Host "   Выполните: git push $target" -ForegroundColor Cyan
}

if ($hasWorkingChanges) {
    Write-Host "   Сохраните изменения: git add . && git commit -m 'message'" -ForegroundColor Magenta
}

if ($behindCount -eq 0 -and $aheadCount -eq 0 -and -not $hasWorkingChanges -and $originConfigured) {
    Write-Host "   Репозиторий в идеальном состоянии!" -ForegroundColor Green
} elseif (-not $originConfigured -and -not $hasWorkingChanges) {
    Write-Host "   Рабочая директория чистая. Настройте remote для синхронизации." -ForegroundColor Green
}

Write-Host ""
Write-Host "Проверка завершена!" -ForegroundColor Green
Write-Host ""
