# ============================================================================
# APPLY VS CODE IMPROVEMENTS - Automatic settings updater
# Applies recommended settings from COPILOT_VSCODE_AUDIT_FULL.md
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " VS CODE SETTINGS IMPROVEMENTS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$settingsPath = ".vscode\settings.json"

# Check if settings.json exists
if (-not (Test-Path $settingsPath)) {
    Write-Host "ERROR: $settingsPath not found!" -ForegroundColor Red
    exit 1
}

Write-Host "`nBacking up current settings..." -ForegroundColor Yellow
$backupPath = ".vscode\settings.json.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $settingsPath $backupPath
Write-Host "OK: Backup created: $backupPath" -ForegroundColor Green

Write-Host "`nReading current settings..." -ForegroundColor Yellow
try {
    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
Write-Host "OK: Settings loaded" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to parse settings.json: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nApplying improvements..." -ForegroundColor Yellow

# 1. Enhanced Copilot Settings
Write-Host "[1/7] Copilot enhancements..." -ForegroundColor White
$settings | Add-Member -Force -MemberType NoteProperty -Name "github.copilot.editor.enableCodeActions" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "github.copilot.renameSuggestions.triggerAutomatically" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "github.copilot.chat.followUps" -Value "always"
$settings | Add-Member -Force -MemberType NoteProperty -Name "github.copilot.chat.useProjectTemplates" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "github.copilot.editor.enableMultilineSuggestions" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "github.copilot.editor.enablePartialAcceptance" -Value $true

# 2. Python Inlay Hints
Write-Host "  [2/7] Python inlay hints..." -ForegroundColor White
$settings | Add-Member -Force -MemberType NoteProperty -Name "python.analysis.diagnosticMode" -Value "workspace"
$settings | Add-Member -Force -MemberType NoteProperty -Name "python.analysis.completeFunctionParens" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "python.analysis.autoSearchPaths" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "python.analysis.indexing" -Value $true

$inlayHints = @{
    functionReturnTypes = $true
    variableTypes = $true
    pytestParameters = $true
}
$settings | Add-Member -Force -MemberType NoteProperty -Name "python.analysis.inlayHints.functionReturnTypes" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "python.analysis.inlayHints.variableTypes" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "python.analysis.inlayHints.pytestParameters" -Value $true

# 3. Git Improvements
Write-Host "  [3/7] Git settings..." -ForegroundColor White
$settings | Add-Member -Force -MemberType NoteProperty -Name "git.autofetch" -Value "all"
$settings | Add-Member -Force -MemberType NoteProperty -Name "git.autofetchPeriod" -Value 180
$settings | Add-Member -Force -MemberType NoteProperty -Name "git.decorations.enabled" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "git.showPushSuccessNotification" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "git.timeline.showAuthor" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "git.timeline.showUncommitted" -Value $true

# 4. Editor Improvements
Write-Host "  [4/7] Editor enhancements..." -ForegroundColor White
$settings | Add-Member -Force -MemberType NoteProperty -Name "editor.stickyScroll.enabled" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "editor.stickyScroll.maxLineCount" -Value 5
$settings | Add-Member -Force -MemberType NoteProperty -Name "editor.cursorSmoothCaretAnimation" -Value "on"
$settings | Add-Member -Force -MemberType NoteProperty -Name "editor.smoothScrolling" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "editor.formatOnType" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "editor.formatOnPaste" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "editor.codeLens" -Value $true

# 5. Performance
Write-Host "  [5/7] Performance optimizations..." -ForegroundColor White
$settings | Add-Member -Force -MemberType NoteProperty -Name "workbench.editor.limit.enabled" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "workbench.editor.limit.value" -Value 10
$settings | Add-Member -Force -MemberType NoteProperty -Name "search.smartCase" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "files.trimTrailingWhitespace" -Value $true

# 6. Terminal
Write-Host "  [6/7] Terminal improvements..." -ForegroundColor White
$settings | Add-Member -Force -MemberType NoteProperty -Name "terminal.integrated.enablePersistentSessions" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "terminal.integrated.tabs.enabled" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "terminal.integrated.gpuAcceleration" -Value "on"
$settings | Add-Member -Force -MemberType NoteProperty -Name "terminal.integrated.copyOnSelection" -Value $true

# 7. Workspace
Write-Host "  [7/7] Workspace settings..." -ForegroundColor White
$settings | Add-Member -Force -MemberType NoteProperty -Name "workbench.tree.indent" -Value 20
$settings | Add-Member -Force -MemberType NoteProperty -Name "workbench.list.smoothScrolling" -Value $true
$settings | Add-Member -Force -MemberType NoteProperty -Name "breadcrumbs.enabled" -Value $true

Write-Host "`nSaving updated settings..." -ForegroundColor Yellow
try {
    $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
    Write-Host "OK: Settings updated successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to save settings: $_" -ForegroundColor Red
    Write-Host "Restoring backup..." -ForegroundColor Yellow
    Copy-Item $backupPath $settingsPath -Force
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nApplied improvements:" -ForegroundColor Green
Write-Host "  + Enhanced Copilot settings (6 options)" -ForegroundColor White
Write-Host "  + Python inlay hints (4 options)" -ForegroundColor White
Write-Host "+ Git timeline & decorations (6 options)" -ForegroundColor White
Write-Host "  + Editor smooth scrolling & sticky scroll (7 options)" -ForegroundColor White
Write-Host "  + Performance optimizations (4 options)" -ForegroundColor White
Write-Host "  + Terminal enhancements (4 options)" -ForegroundColor White
Write-Host "  + Workspace improvements (3 options)" -ForegroundColor White

Write-Host "`nBackup location:" -ForegroundColor Yellow
Write-Host "  $backupPath" -ForegroundColor Gray

Write-Host "`nNEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Restart VS Code (Ctrl+Shift+P -> 'Reload Window')" -ForegroundColor White
Write-Host "2. Install recommended extensions:" -ForegroundColor White
Write-Host "   - GitLens" -ForegroundColor Gray
Write-Host "   - Russian Spell Checker" -ForegroundColor Gray
Write-Host "   - Better Comments" -ForegroundColor Gray
Write-Host "   - Error Lens" -ForegroundColor Gray
Write-Host "3. Verify Python inlay hints are visible" -ForegroundColor White
Write-Host "4. Check Git timeline in Explorer" -ForegroundColor White

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "OK: Improvements applied successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
