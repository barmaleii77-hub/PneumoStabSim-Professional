# Git Repository Status Checker
# Version: 1.0.0

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  Git Repository Status Check" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Current branch
Write-Host "[1] Current branch:" -ForegroundColor Green
$currentBranch = git branch --show-current
Write-Host "    $currentBranch" -ForegroundColor White
Write-Host ""

# 2. Last local commit
Write-Host "[2] Last local commit:" -ForegroundColor Green
$lastCommit = git log -1 --oneline
Write-Host "    $lastCommit" -ForegroundColor White
Write-Host ""

# 3. Repository status
Write-Host "[3] Repository status:" -ForegroundColor Green
$status = git status --short
if ($status) {
    Write-Host $status -ForegroundColor Yellow
} else {
    Write-Host "    Working directory clean" -ForegroundColor Green
}
Write-Host ""

# 4. Fetch updates
Write-Host "[4] Fetching remote updates..." -ForegroundColor Green
git fetch origin | Out-Null
Write-Host "    Done" -ForegroundColor Green
Write-Host ""

# 5. Compare with remote
Write-Host "[5] Compare with origin/${currentBranch}:" -ForegroundColor Green
$ahead = git rev-list --count "origin/${currentBranch}..HEAD" 2>$null
$behind = git rev-list --count "HEAD..origin/${currentBranch}" 2>$null

if ($ahead -eq 0 -and $behind -eq 0) {
    Write-Host "    Branch is fully synchronized" -ForegroundColor Green
} elseif ($ahead -gt 0 -and $behind -eq 0) {
    Write-Host "    Ahead by $ahead commit(s)" -ForegroundColor Cyan
} elseif ($ahead -eq 0 -and $behind -gt 0) {
    Write-Host "    Behind by $behind commit(s)" -ForegroundColor Yellow
} else {
    Write-Host "    Diverged: +$ahead / -$behind" -ForegroundColor Red
}
Write-Host ""

# 6. Remote branches
Write-Host "[6] Remote branches:" -ForegroundColor Green
$remoteBranches = git branch -r
$remoteBranches | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
Write-Host ""

# 7. Recent commits
Write-Host "[7] Recent 5 commits:" -ForegroundColor Green
$recentCommits = git log --oneline -5
$recentCommits | ForEach-Object { Write-Host "    $_" -ForegroundColor White }
Write-Host ""

# 8. Modified files
Write-Host "[8] Modified files:" -ForegroundColor Green
$modifiedFiles = git diff --name-only
if ($modifiedFiles) {
    $modifiedFiles | ForEach-Object { Write-Host "    Modified: $_" -ForegroundColor Yellow }
} else {
    Write-Host "    No modified files" -ForegroundColor Green
}
Write-Host ""

# 9. Untracked files
Write-Host "[9] Untracked files:" -ForegroundColor Green
$untrackedFiles = git ls-files --others --exclude-standard
if ($untrackedFiles) {
    $untrackedFiles | ForEach-Object { Write-Host "    Untracked: $_" -ForegroundColor Cyan }
} else {
    Write-Host "    No untracked files" -ForegroundColor Green
}
Write-Host ""

# 10. Recommendations
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  Recommendations:" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan

if ($behind -gt 0) {
    Write-Host "    [ACTION] Pull updates: git pull origin $currentBranch" -ForegroundColor Yellow
}

if ($ahead -gt 0) {
    Write-Host "    [ACTION] Push commits: git push origin $currentBranch" -ForegroundColor Cyan
}

if ($modifiedFiles -or $untrackedFiles) {
    Write-Host "    [ACTION] Commit changes: git add . && git commit -m 'message'" -ForegroundColor Magenta
}

if ($behind -eq 0 -and $ahead -eq 0 -and -not $modifiedFiles -and -not $untrackedFiles) {
    Write-Host "    [OK] Repository is in perfect state!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Check completed!" -ForegroundColor Green
Write-Host ""
