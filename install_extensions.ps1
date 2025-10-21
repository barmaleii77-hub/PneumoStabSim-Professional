# =============================================================================
# VS Code Extensions - Quick Check & Install
# Quick check and installation of VS Code extensions
# =============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " VS Code Extensions Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Find VS Code
$codeCmd = "code"
try {
    $version = & $codeCmd --version 2>&1
    if ($LASTEXITCODE -eq 0) {
    Write-Host "Found VS Code" -ForegroundColor Green
        Write-Host "   Version: $($version[0])`n" -ForegroundColor Gray
    } else {
        Write-Host "ERROR: VS Code not found!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: VS Code not found in PATH!" -ForegroundColor Red
    exit 1
}

# Critical extensions list
$criticalExtensions = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "github.copilot",
    "github.copilot-chat"
)

# Recommended extensions list
$recommendedExtensions = @(
    "ms-python.black-formatter",
    "bbenoist.qml",
    "seanwu.vscode-qt-for-python",
    "eamodio.gitlens",
    "ms-vscode.powershell"
)

# Get installed extensions
Write-Host "Getting list of installed extensions..." -ForegroundColor Yellow
$installed = & $codeCmd --list-extensions 2>&1

Write-Host "`nCritical Extensions:" -ForegroundColor Cyan
Write-Host ("-" * 60) -ForegroundColor Gray

$criticalMissing = @()
foreach ($ext in $criticalExtensions) {
    if ($installed -contains $ext) {
     Write-Host "  OK: $ext" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $ext" -ForegroundColor Red
  $criticalMissing += $ext
    }
}

Write-Host "`nRecommended Extensions:" -ForegroundColor Cyan
Write-Host ("-" * 60) -ForegroundColor Gray

$recommendedMissing = @()
foreach ($ext in $recommendedExtensions) {
    if ($installed -contains $ext) {
        Write-Host "  OK: $ext" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $ext" -ForegroundColor Yellow
        $recommendedMissing += $ext
    }
}

# Install missing extensions
$allMissing = $criticalMissing + $recommendedMissing

if ($allMissing.Count -gt 0) {
 Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " Installing Missing Extensions" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Write-Host "Found $($allMissing.Count) missing extensions" -ForegroundColor Yellow
    Write-Host "Press Enter to install or Ctrl+C to cancel..."
    Read-Host
    
    $success = 0
    $failed = 0
    
    foreach ($ext in $allMissing) {
        Write-Host "`nInstalling: $ext..." -ForegroundColor Yellow
  
        try {
            & $codeCmd --install-extension $ext --force 2>&1 | Out-Null
            
    if ($LASTEXITCODE -eq 0) {
                Write-Host "  SUCCESS: Installed" -ForegroundColor Green
       $success++
        } else {
         Write-Host "  ERROR: Failed" -ForegroundColor Red
 $failed++
 }
        } catch {
          Write-Host "  ERROR: $_" -ForegroundColor Red
 $failed++
        }
    }
  
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " Summary" -ForegroundColor Cyan
 Write-Host "========================================`n" -ForegroundColor Cyan
    
  Write-Host "  Installed: $success" -ForegroundColor Green
    Write-Host "  Failed: $failed" -ForegroundColor Red
    
} else {
    Write-Host "`nAll extensions are already installed!" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Next Steps" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "1. Restart VS Code" -ForegroundColor White
Write-Host "2. Configure GitHub Copilot (sign in to GitHub)" -ForegroundColor White
Write-Host "3. Select Python interpreter: Ctrl+Shift+P -> Python: Select Interpreter" -ForegroundColor White

Write-Host "`nCheck complete!`n" -ForegroundColor Green
