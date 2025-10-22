# ============================================================================
# CHECK INSTALLED VS CODE EXTENSIONS
# Compares installed extensions with recommended ones
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " VS CODE EXTENSIONS CHECKER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if code command is available
$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if (-not $codeCmd) {
    Write-Host "`nERROR: 'code' command not found in PATH!" -ForegroundColor Red
    Write-Host "Please ensure VS Code is installed and added to PATH." -ForegroundColor Yellow
    Write-Host "`nYou can add it manually:" -ForegroundColor Yellow
    Write-Host "1. Open VS Code" -ForegroundColor White
    Write-Host "2. Press Ctrl+Shift+P" -ForegroundColor White
    Write-Host "3. Type 'Shell Command: Install code command in PATH'" -ForegroundColor White
    Write-Host "4. Run this script again" -ForegroundColor White
    exit 1
}

Write-Host "`nFetching installed extensions..." -ForegroundColor Yellow

try {
    $installed = & code --list-extensions 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to list extensions"
    }
    Write-Host "OK: Found $($installed.Count) installed extensions" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to fetch extensions: $_" -ForegroundColor Red
    exit 1
}

# Read recommended extensions from .vscode/extensions.json
$extensionsFile = ".vscode\extensions.json"
if (-not (Test-Path $extensionsFile)) {
    Write-Host "`nWARNING: $extensionsFile not found!" -ForegroundColor Yellow
    Write-Host "Creating recommended extensions list..." -ForegroundColor Yellow

    # Create recommended list
    $recommended = @{
  recommendations = @(
       # Core Python
            "ms-python.python",
            "ms-python.vscode-pylance",
   "ms-python.black-formatter",
    "ms-python.flake8",
     "ms-python.mypy-type-checker",

          # AI & Copilot
            "github.copilot",
      "github.copilot-chat",

            # Git
            "eamodio.gitlens",
            "donjayamanne.githistory",
    "mhutchie.git-graph",

      # QML
            "bbenoist.QML",

            # Productivity
        "streetsidesoftware.code-spell-checker",
            "streetsidesoftware.code-spell-checker-russian",
            "aaron-bond.better-comments",
  "wayou.vscode-todo-highlight",
            "usernamehw.errorlens",

          # Markdown
            "yzhang.markdown-all-in-one",
         "davidanson.vscode-markdownlint"
    )
    }

    New-Item -ItemType Directory -Path ".vscode" -Force | Out-Null
    $recommended | ConvertTo-Json -Depth 10 | Set-Content $extensionsFile -Encoding UTF8
    Write-Host "OK: Created $extensionsFile" -ForegroundColor Green
}

# Load recommended extensions
try {
    $recommendedData = Get-Content $extensionsFile -Raw | ConvertFrom-Json
    $recommended = $recommendedData.recommendations
    Write-Host "OK: Loaded $($recommended.Count) recommended extensions" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to parse $extensionsFile : $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " ANALYSIS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Categorize extensions
$categories = @{
    "Python Development" = @(
     "ms-python.python",
 "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "ms-python.mypy-type-checker"
    )
    "AI & Copilot" = @(
        "github.copilot",
      "github.copilot-chat",
     "visualstudioexptteam.vscodeintellicode"
 )
    "Git Integration" = @(
        "eamodio.gitlens",
        "donjayamanne.githistory",
  "mhutchie.git-graph"
    )
    "QML/Qt" = @(
   "bbenoist.QML",
   "seanwu.vscode-qt-for-python"
    )
    "Code Quality" = @(
  "streetsidesoftware.code-spell-checker",
   "streetsidesoftware.code-spell-checker-russian",
        "editorconfig.editorconfig",
        "usernamehw.errorlens"
    )
    "Productivity" = @(
        "aaron-bond.better-comments",
        "wayou.vscode-todo-highlight",
        "gruntfuggly.todo-tree"
    )
    "Markdown" = @(
        "yzhang.markdown-all-in-one",
        "davidanson.vscode-markdownlint"
    )
}

$missingCritical = @()
$missingOptional = @()
$installedCount = 0

foreach ($category in $categories.Keys) {
    Write-Host "`n$category :" -ForegroundColor Yellow

    foreach ($ext in $categories[$category]) {
        $isInstalled = $installed -contains $ext
     $isCritical = $ext -in @(
            "ms-python.python",
            "ms-python.vscode-pylance",
       "github.copilot",
            "github.copilot-chat",
      "eamodio.gitlens",
  "streetsidesoftware.code-spell-checker-russian"
        )

   if ($isInstalled) {
       Write-Host "  ✅ $ext" -ForegroundColor Green
          $installedCount++
        } else {
   $marker = if ($isCritical) { "🔴" } else { "⚠️" }
            Write-Host "  $marker $ext" -ForegroundColor $(if ($isCritical) { "Red" } else { "Yellow" })

            if ($isCritical) {
    $missingCritical += $ext
    } else {
     $missingOptional += $ext
     }
    }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$totalRecommended = $recommended.Count
$installedPercent = [math]::Round(($installedCount / $totalRecommended) * 100, 1)

Write-Host "`nInstalled: $installedCount / $totalRecommended ($installedPercent%)" -ForegroundColor $(if ($installedPercent -ge 80) { "Green" } elseif ($installedPercent -ge 50) { "Yellow" } else { "Red" })

if ($missingCritical.Count -gt 0) {
    Write-Host "`n🔴 CRITICAL MISSING ($($missingCritical.Count)):" -ForegroundColor Red
    foreach ($ext in $missingCritical) {
        Write-Host "  - $ext" -ForegroundColor Red
    }
}

if ($missingOptional.Count -gt 0) {
    Write-Host "`n⚠️  OPTIONAL MISSING ($($missingOptional.Count)):" -ForegroundColor Yellow
    foreach ($ext in $missingOptional) {
        Write-Host "  - $ext" -ForegroundColor Gray
    }
}

# Recommendations
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($missingCritical.Count -gt 0) {
    Write-Host "`n🔴 INSTALL CRITICAL EXTENSIONS (REQUIRED):" -ForegroundColor Red
    Write-Host "`nOption 1 - Install all critical at once:" -ForegroundColor White
    Write-Host "code --install-extension $($missingCritical -join ' --install-extension ')" -ForegroundColor Gray

    Write-Host "`nOption 2 - Use VS Code UI:" -ForegroundColor White
    Write-Host "1. Press Ctrl+Shift+X" -ForegroundColor Gray
    Write-Host "2. Type '@recommended'" -ForegroundColor Gray
    Write-Host "3. Click 'Install' on critical extensions" -ForegroundColor Gray
}

if ($missingOptional.Count -gt 0) {
    Write-Host "`n⚠️  INSTALL OPTIONAL EXTENSIONS (RECOMMENDED):" -ForegroundColor Yellow
    Write-Host "code --install-extension $($missingOptional -join ' --install-extension ')" -ForegroundColor Gray
}

if ($missingCritical.Count -eq 0 -and $missingOptional.Count -eq 0) {
    Write-Host "`n✅ ALL RECOMMENDED EXTENSIONS INSTALLED!" -ForegroundColor Green
    Write-Host "Your VS Code setup is complete." -ForegroundColor Green
} else {
    Write-Host "`n📝 After installing extensions:" -ForegroundColor Cyan
    Write-Host "1. Restart VS Code (Ctrl+Shift+P -> 'Reload Window')" -ForegroundColor White
    Write-Host "2. Run this script again to verify" -ForegroundColor White
}

# Quick install command
if ($missingCritical.Count -gt 0 -or $missingOptional.Count -gt 0) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " QUICK INSTALL COMMAND" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    $allMissing = $missingCritical + $missingOptional
    $installCmd = "code " + ($allMissing | ForEach-Object { "--install-extension $_" }) -join " "

    Write-Host "`nCopy and run this command to install ALL missing extensions:" -ForegroundColor Yellow
    Write-Host $installCmd -ForegroundColor Gray

    Write-Host "`nOr save to file:" -ForegroundColor Yellow
    $installScript = "install_missing_extensions.ps1"
    $installCmd | Set-Content $installScript -Encoding UTF8
    Write-Host "Created: $installScript" -ForegroundColor Green
    Write-Host "Run: .\$installScript" -ForegroundColor Gray
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Check complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
