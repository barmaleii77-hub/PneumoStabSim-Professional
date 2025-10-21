# ============================================================================
# CHECK VS CODE EXTENSIONS (Alternative Method - File System)
# Checks extensions by scanning VS Code extensions directory
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " VS CODE EXTENSIONS CHECKER" -ForegroundColor Cyan
Write-Host " (File System Method)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Find VS Code extensions directory
$possiblePaths = @(
 "$env:USERPROFILE\.vscode\extensions",
    "$env:USERPROFILE\.vscode-insiders\extensions",
    "$env:APPDATA\Code\User\extensions"
)

$extensionsDir = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
  $extensionsDir = $path
        Write-Host "`n✅ Found extensions directory: $path" -ForegroundColor Green
        break
    }
}

if (-not $extensionsDir) {
    Write-Host "`n❌ ERROR: VS Code extensions directory not found!" -ForegroundColor Red
    Write-Host "`nTried:" -ForegroundColor Yellow
    foreach ($path in $possiblePaths) {
        Write-Host "  - $path" -ForegroundColor Gray
    }
    Write-Host "`nPlease ensure VS Code is installed." -ForegroundColor Yellow
  exit 1
}

# Scan installed extensions
Write-Host "`nScanning installed extensions..." -ForegroundColor Yellow
$installedFolders = Get-ChildItem -Path $extensionsDir -Directory | Select-Object -ExpandProperty Name
$installed = @()

foreach ($folder in $installedFolders) {
  # Extract extension ID (format: publisher.name-version)
    if ($folder -match '^([^-]+\.[^-]+)-(.+)$') {
        $extId = $matches[1]
        if ($extId -notin $installed) {
   $installed += $extId
    }
    }
}

Write-Host "OK: Found $($installed.Count) unique extensions" -ForegroundColor Green

# Recommended extensions
$recommended = @{
    "Python Development" = @(
 @{ id = "ms-python.python"; name = "Python"; critical = $true },
        @{ id = "ms-python.vscode-pylance"; name = "Pylance"; critical = $true },
        @{ id = "ms-python.black-formatter"; name = "Black Formatter"; critical = $false },
        @{ id = "ms-python.flake8"; name = "Flake8"; critical = $false },
        @{ id = "ms-python.mypy-type-checker"; name = "Mypy"; critical = $false }
    )
    "AI & Copilot" = @(
        @{ id = "github.copilot"; name = "GitHub Copilot"; critical = $true },
  @{ id = "github.copilot-chat"; name = "GitHub Copilot Chat"; critical = $true },
    @{ id = "visualstudioexptteam.vscodeintellicode"; name = "IntelliCode"; critical = $false }
    )
    "Git Integration" = @(
        @{ id = "eamodio.gitlens"; name = "GitLens"; critical = $true },
  @{ id = "donjayamanne.githistory"; name = "Git History"; critical = $false },
        @{ id = "mhutchie.git-graph"; name = "Git Graph"; critical = $false }
    )
    "QML/Qt" = @(
        @{ id = "bbenoist.QML"; name = "QML"; critical = $false },
        @{ id = "seanwu.vscode-qt-for-python"; name = "Qt for Python"; critical = $false }
    )
 "Code Quality" = @(
        @{ id = "streetsidesoftware.code-spell-checker"; name = "Code Spell Checker"; critical = $false },
        @{ id = "streetsidesoftware.code-spell-checker-russian"; name = "Russian Spell Checker"; critical = $true },
        @{ id = "editorconfig.editorconfig"; name = "EditorConfig"; critical = $false },
        @{ id = "usernamehw.errorlens"; name = "Error Lens"; critical = $true }
    )
    "Productivity" = @(
        @{ id = "aaron-bond.better-comments"; name = "Better Comments"; critical = $true },
        @{ id = "wayou.vscode-todo-highlight"; name = "TODO Highlight"; critical = $false },
        @{ id = "gruntfuggly.todo-tree"; name = "Todo Tree"; critical = $false }
    )
    "Markdown" = @(
  @{ id = "yzhang.markdown-all-in-one"; name = "Markdown All in One"; critical = $false },
     @{ id = "davidanson.vscode-markdownlint"; name = "markdownlint"; critical = $false }
    )
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " ANALYSIS BY CATEGORY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$missingCritical = @()
$missingOptional = @()
$installedCount = 0
$totalCount = 0

foreach ($category in $recommended.Keys) {
    Write-Host "`n📦 $category :" -ForegroundColor Yellow

    foreach ($ext in $recommended[$category]) {
        $totalCount++
        $isInstalled = $installed -contains $ext.id

        if ($isInstalled) {
        Write-Host "  ✅ $($ext.name) ($($ext.id))" -ForegroundColor Green
            $installedCount++
  } else {
 $marker = if ($ext.critical) { "🔴" } else { "⚠️" }
            $color = if ($ext.critical) { "Red" } else { "Yellow" }
            Write-Host "  $marker $($ext.name) ($($ext.id))" -ForegroundColor $color

         if ($ext.critical) {
    $missingCritical += @{ id = $ext.id; name = $ext.name }
     } else {
      $missingOptional += @{ id = $ext.id; name = $ext.name }
      }
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$installedPercent = [math]::Round(($installedCount / $totalCount) * 100, 1)
$color = if ($installedPercent -ge 80) { "Green" } elseif ($installedPercent -ge 50) { "Yellow" } else { "Red" }

Write-Host "`n📊 Installed: $installedCount / $totalCount ($installedPercent%)" -ForegroundColor $color

if ($missingCritical.Count -gt 0) {
    Write-Host "`n🔴 CRITICAL MISSING ($($missingCritical.Count)):" -ForegroundColor Red
    foreach ($ext in $missingCritical) {
        Write-Host "  - $($ext.name) ($($ext.id))" -ForegroundColor Red
    }
}

if ($missingOptional.Count -gt 0) {
    Write-Host "`n⚠️  OPTIONAL MISSING ($($missingOptional.Count)):" -ForegroundColor Yellow
    foreach ($ext in $missingOptional) {
        Write-Host "  - $($ext.name) ($($ext.id))" -ForegroundColor Gray
}
}

# Installation instructions
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " HOW TO INSTALL MISSING EXTENSIONS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($missingCritical.Count -gt 0 -or $missingOptional.Count -gt 0) {
    Write-Host "`n📝 METHOD 1: VS Code UI (EASIEST)" -ForegroundColor Yellow
Write-Host "1. Open VS Code" -ForegroundColor White
    Write-Host "2. Press Ctrl+Shift+X (Extensions)" -ForegroundColor White
    Write-Host "3. Type: @recommended" -ForegroundColor White
    Write-Host "4. Click 'Install Workspace Extension Recommendations'" -ForegroundColor White

    Write-Host "`n📝 METHOD 2: Search Manually" -ForegroundColor Yellow
    Write-Host "In VS Code Extensions (Ctrl+Shift+X), search for:" -ForegroundColor White

    if ($missingCritical.Count -gt 0) {
      Write-Host "`nCRITICAL:" -ForegroundColor Red
     foreach ($ext in $missingCritical) {
       Write-Host "  - $($ext.name)" -ForegroundColor White
        }
    }

    if ($missingOptional.Count -gt 0) {
  Write-Host "`nOPTIONAL:" -ForegroundColor Yellow
        foreach ($ext in $missingOptional) {
            Write-Host "  - $($ext.name)" -ForegroundColor Gray
        }
 }

    Write-Host "`n📝 METHOD 3: Command Line (if 'code' in PATH)" -ForegroundColor Yellow
 $allMissing = ($missingCritical + $missingOptional) | ForEach-Object { $_.id }
    foreach ($extId in $allMissing) {
        Write-Host "code --install-extension $extId" -ForegroundColor Gray
    }
} else {
    Write-Host "`n✅ ALL RECOMMENDED EXTENSIONS INSTALLED!" -ForegroundColor Green
    Write-Host "Your VS Code setup is perfect! 🎉" -ForegroundColor Green
}

# Priority list
if ($missingCritical.Count -gt 0) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " ⭐ TOP PRIORITY (Install First)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    $priority = $missingCritical | Sort-Object {
      switch ($_.id) {
        "github.copilot" { 1 }
  "github.copilot-chat" { 2 }
            "ms-python.python" { 3 }
     "ms-python.vscode-pylance" { 4 }
            "eamodio.gitlens" { 5 }
            "streetsidesoftware.code-spell-checker-russian" { 6 }
            "usernamehw.errorlens" { 7 }
        "aaron-bond.better-comments" { 8 }
            default { 99 }
 }
    }

  $num = 1
    foreach ($ext in $priority) {
        Write-Host "$num. $($ext.name)" -ForegroundColor White
        Write-Host "   Extension ID: $($ext.id)" -ForegroundColor Gray
        $num++
  }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Check complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# Create extensions.json if missing
$extensionsJsonPath = ".vscode\extensions.json"
if (-not (Test-Path $extensionsJsonPath)) {
    Write-Host "`nCreating .vscode\extensions.json..." -ForegroundColor Yellow

    $allExtIds = @()
    foreach ($category in $recommended.Keys) {
     foreach ($ext in $recommended[$category]) {
            $allExtIds += $ext.id
        }
    }

    $extensionsJson = @{
      recommendations = $allExtIds
    } | ConvertTo-Json -Depth 10

    New-Item -ItemType Directory -Path ".vscode" -Force -ErrorAction SilentlyContinue | Out-Null
    $extensionsJson | Set-Content $extensionsJsonPath -Encoding UTF8
    Write-Host "✅ Created: $extensionsJsonPath" -ForegroundColor Green
}

Write-Host "`n💡 TIP: After installing, reload VS Code (Ctrl+Shift+P -> 'Reload Window')" -ForegroundColor Cyan
