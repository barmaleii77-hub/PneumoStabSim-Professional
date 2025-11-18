# Git Repository Status Checker
# Version: 1.1.0

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  Git Repository Status Check" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""

function Invoke-GitSafe {
    param(
        [string[]]$Arguments
    )

    $output = & git @Arguments 2>&1
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output   = $output
    }
}

# 0. Platform detection for cross-platform logging
$osDescription = [System.Runtime.InteropServices.RuntimeInformation]::OSDescription
Write-Host "[0] Platform: $osDescription" -ForegroundColor Green
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

# 4. Remote detection and fetch
$remotes = git remote
$hasOrigin = $remotes -contains "origin"

if (-not $hasOrigin) {
    Write-Host "[4] Remote: origin not configured — skipping fetch" -ForegroundColor Yellow
    Write-Host "    Hint: git remote add origin <url>" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "[4] Fetching remote updates..." -ForegroundColor Green
    $fetchResult = Invoke-GitSafe @('fetch','origin')
    if ($fetchResult.ExitCode -eq 0) {
        Write-Host "    Done" -ForegroundColor Green
    } else {
        Write-Host "    Fetch failed: $($fetchResult.Output -join ' ')" -ForegroundColor Red
    }
    Write-Host ""
}

# 5. Compare with remote
if (-not $hasOrigin) {
    Write-Host "[5] Compare with remote: skipped (no origin remote)" -ForegroundColor Yellow
} else {
    Write-Host "[5] Compare with origin/${currentBranch}:" -ForegroundColor Green
    $ahead = git rev-list --count "origin/${currentBranch}..HEAD" 2>$null
    $behind = git rev-list --count "HEAD..origin/${currentBranch}" 2>$null

    if ($ahead -eq $null -or $behind -eq $null) {
        Write-Host "    Remote branch not found. Push to create origin/${currentBranch}." -ForegroundColor Yellow
    } elseif ($ahead -eq 0 -and $behind -eq 0) {
        Write-Host "    Branch is fully synchronized" -ForegroundColor Green
    } elseif ($ahead -gt 0 -and $behind -eq 0) {
        Write-Host "    Ahead by $ahead commit(s)" -ForegroundColor Cyan
    } elseif ($ahead -eq 0 -and $behind -gt 0) {
        Write-Host "    Behind by $behind commit(s)" -ForegroundColor Yellow
    } else {
        Write-Host "    Diverged: +$ahead / -$behind" -ForegroundColor Red
    }
}
Write-Host ""

# 6. Remote branches
Write-Host "[6] Remote branches:" -ForegroundColor Green
if ($remotes) {
    $remoteBranches = git branch -r
    if ($remoteBranches) {
        $remoteBranches | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    } else {
        Write-Host "    No remote branches found" -ForegroundColor Yellow
    }
} else {
    Write-Host "    No remotes configured" -ForegroundColor Yellow
}
Write-Host ""

# 7. Recent commits
Write-Host "[7] Recent 5 commits:" -ForegroundColor Green
$recentCommits = git log -5 --oneline
$recentCommits | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
Write-Host ""

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  Git Repository Status Check Complete" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""
