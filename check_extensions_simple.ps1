# ============================================================================
# CHECK VS CODE EXTENSIONS - Simple Version (No Emoji)
# ============================================================================

Write-Host "========================================"
Write-Host " VS CODE EXTENSIONS CHECKER"
Write-Host "========================================"

# Check if code command is available
$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if (-not $codeCmd) {
    Write-Host ""
    Write-Host "ERROR: 'code' command not found in PATH!" -ForegroundColor Red
    Write-Host "Add VS Code to PATH:" -ForegroundColor Yellow
    Write-Host "1. Open VS Code"
    Write-Host "2. Press Ctrl+Shift+P"
    Write-Host "3. Type 'Shell Command: Install code command in PATH'"
    Write-Host "4. Run this script again"
    exit 1
}

Write-Host ""
Write-Host "Fetching installed extensions..." -ForegroundColor Yellow

try {
    $installed = & code --list-extensions 2>&1
  if ($LASTEXITCODE -ne 0) {
        throw "Failed to list extensions"
    }
  Write-Host "Found $($installed.Count) installed extensions" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to fetch extensions: $_" -ForegroundColor Red
    exit 1
}

# Recommended extensions
$critical = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "github.copilot",
    "github.copilot-chat",
    "eamodio.gitlens"
)

$recommended = @(
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "bbenoist.qml",
    "seanwu.vscode-qt-for-python",
    "streetsidesoftware.code-spell-checker",
"streetsidesoftware.code-spell-checker-russian",
  "yzhang.markdown-all-in-one",
    "davidanson.vscode-markdownlint",
    "editorconfig.editorconfig"
)

Write-Host ""
Write-Host "========================================"
Write-Host " CRITICAL EXTENSIONS"
Write-Host "========================================"

$missingCritical = @()
foreach ($ext in $critical) {
    if ($installed -contains $ext) {
        Write-Host "[OK] $ext" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $ext" -ForegroundColor Red
        $missingCritical += $ext
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host " RECOMMENDED EXTENSIONS"
Write-Host "========================================"

$missingRecommended = @()
foreach ($ext in $recommended) {
    if ($installed -contains $ext) {
        Write-Host "[OK] $ext" -ForegroundColor Green
    } else {
     Write-Host "[MISSING] $ext" -ForegroundColor Yellow
        $missingRecommended += $ext
    }
}

# Summary
Write-Host ""
Write-Host "========================================"
Write-Host " SUMMARY"
Write-Host "========================================"

$totalInstalled = $critical.Count + $recommended.Count - $missingCritical.Count - $missingRecommended.Count
$totalRequired = $critical.Count + $recommended.Count

Write-Host ""
Write-Host "Installed: $totalInstalled / $totalRequired"

if ($missingCritical.Count -gt 0) {
    Write-Host ""
  Write-Host "CRITICAL MISSING ($($missingCritical.Count)):" -ForegroundColor Red
    foreach ($ext in $missingCritical) {
        Write-Host "  - $ext" -ForegroundColor Red
    }
}

if ($missingRecommended.Count -gt 0) {
    Write-Host ""
    Write-Host "RECOMMENDED MISSING ($($missingRecommended.Count)):" -ForegroundColor Yellow
    foreach ($ext in $missingRecommended) {
        Write-Host "  - $ext"
    }
}

# Install commands
if ($missingCritical.Count -gt 0 -or $missingRecommended.Count -gt 0) {
    Write-Host ""
    Write-Host "========================================"
    Write-Host " INSTALL COMMANDS"
    Write-Host "========================================"
    
    if ($missingCritical.Count -gt 0) {
      Write-Host ""
     Write-Host "Install CRITICAL extensions:" -ForegroundColor Red
        foreach ($ext in $missingCritical) {
Write-Host "code --install-extension $ext"
        }
    }
    
    if ($missingRecommended.Count -gt 0) {
        Write-Host ""
        Write-Host "Install RECOMMENDED extensions:" -ForegroundColor Yellow
        foreach ($ext in $missingRecommended) {
        Write-Host "code --install-extension $ext"
        }
    }
    
    # Create install script
    Write-Host ""
    Write-Host "Creating install_extensions.ps1..." -ForegroundColor Cyan
    $allMissing = $missingCritical + $missingRecommended
    $commands = $allMissing | ForEach-Object { "code --install-extension $_" }
    $commands -join "`n" | Set-Content "install_extensions.ps1" -Encoding UTF8
    Write-Host "Created: install_extensions.ps1" -ForegroundColor Green
    Write-Host "Run: .\install_extensions.ps1" -ForegroundColor Cyan
} else {
    Write-Host ""
Write-Host "ALL EXTENSIONS INSTALLED!" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================"
Write-Host "Check complete!"
Write-Host "========================================"
