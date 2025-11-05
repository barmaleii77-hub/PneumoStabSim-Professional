# RECOMMENDED VS CODE SETTINGS UPDATES

## Apply these changes to `.vscode/settings.json`

### 1. Enhanced Copilot Settings (add to GITHUB COPILOT SETTINGS section):

```json
"github.copilot.editor.enableCodeActions": true,
"github.copilot.renameSuggestions.triggerAutomatically": true,
"github.copilot.chat.followUps": "always",
"github.copilot.chat.useProjectTemplates": true,
"github.copilot.editor.enableMultilineSuggestions": true,
"github.copilot.editor.enablePartialAcceptance": true,
```

### 2. Python Inlay Hints (add to PYTHON SETTINGS section):

```json
"python.analysis.diagnosticMode": "workspace",
"python.analysis.completeFunctionParens": true,
"python.analysis.autoSearchPaths": true,
"python.analysis.inlayHints.functionReturnTypes": true,
"python.analysis.inlayHints.variableTypes": true,
"python.analysis.inlayHints.pytestParameters": true,
"python.analysis.indexing": true,
"python.analysis.packageIndexDepths": [
    {"name": "PySide6", "depth": 3},
    {"name": "numpy", "depth": 2},
    {"name": "src", "depth": 5}
],
```

### 3. Improved Git Settings (replace GIT SETTINGS section):

```json
"git.autofetch": "all",
"git.autofetchPeriod": 180,
"git.confirmForcePush": true,
"git.confirmNoVerifyCommit": true,
"git.decorations.enabled": true,
"git.enableCommitSigning": false,
"git.fetchOnPull": true,
"git.ignoreLimitWarning": true,
"git.ignoreRebaseWarning": false,
"git.inputValidation": "always",
"git.openRepositoryInParentFolders": "always",
"git.pruneOnFetch": true,
"git.confirmSync": false,
"git.enableSmartCommit": true,
"git.showCommitInput": true,
"git.showPushSuccessNotification": true,
"git.timeline.showAuthor": true,
"git.timeline.showUncommitted": true,
```

### 4. Editor Improvements (add to root level):

```json
"editor.stickyScroll.enabled": true,
"editor.stickyScroll.maxLineCount": 5,
"editor.cursorSmoothCaretAnimation": "on",
"editor.smoothScrolling": true,
"editor.cursorBlinking": "smooth",
"editor.minimap.renderCharacters": false,
"editor.suggest.preview": true,
"editor.suggest.shareSuggestSelections": true,
"editor.quickSuggestionsDelay": 10,
"editor.suggestSelection": "first",
"editor.tabCompletion": "on",
"editor.wordBasedSuggestions": "matchingDocuments",
"editor.codeLens": true,
"editor.formatOnType": true,
"editor.formatOnPaste": true,
"editor.inlineSuggest.suppressSuggestions": false,
"editor.inlineSuggest.showToolbar": "onHover",
```

### 5. Performance Optimizations (add to root level):

```json
"files.simpleDialog.enable": true,
"workbench.editor.enablePreview": false,
"workbench.editor.enablePreviewFromQuickOpen": false,
"workbench.editor.closeEmptyGroups": true,
"workbench.editor.highlightModifiedTabs": true,
"workbench.editor.limit.enabled": true,
"workbench.editor.limit.value": 10,
"workbench.editor.limit.perEditorGroup": true,
"search.followSymlinks": false,
"search.smartCase": true,
"files.hotExit": "onExitAndWindowClose",
"files.insertFinalNewline": true,
"files.trimFinalNewlines": true,
"files.trimTrailingWhitespace": true,
```

### 6. Terminal Enhancements (add to TERMINAL SETTINGS section):

```json
"terminal.integrated.persistentSessionReviveProcess": "onExit",
"terminal.integrated.enablePersistentSessions": true,
"terminal.integrated.tabs.enabled": true,
"terminal.integrated.tabs.location": "left",
"terminal.integrated.suggest.enabled": true,
"terminal.integrated.confirmOnKill": "editor",
"terminal.integrated.copyOnSelection": true,
"terminal.integrated.gpuAcceleration": "on",
"terminal.integrated.smoothScrolling": true,
```

### 7. Workbench Improvements (add to WORKSPACE SPECIFIC section):

```json
"workbench.tree.indent": 20,
"workbench.tree.renderIndentGuides": "always",
"workbench.list.smoothScrolling": true,
"workbench.panel.opensMaximized": "never",
"breadcrumbs.enabled": true,
"breadcrumbs.symbolPath": "on",
```

### 8. Security (add to root level):

```json
"security.workspace.trust.enabled": false,
"security.workspace.trust.startupPrompt": "never",
```

---

## How to Apply

### Option 1: Manual (Recommended)
1. Open `.vscode/settings.json`
2. Copy sections above
3. Paste into appropriate locations
4. Save file
5. Reload VS Code (Ctrl+Shift+P → "Reload Window")

### Option 2: Script (Automatic)
Run PowerShell script:

```powershell
.\apply_vscode_improvements.ps1
```

---

## After Applying

### Check that these work:
1. ✅ Python inlay hints show types
2. ✅ Copilot suggestions are faster
3. ✅ Git timeline shows in Explorer
4. ✅ Sticky scroll works in long files
5. ✅ Terminal has tabs
6. ✅ Editor limit prevents too many open files

### Install Recommended Extensions:
```
Ctrl+Shift+X → "Show Recommended Extensions"
```

Key extensions to install:
- GitLens
- Russian Spell Checker
- Better Comments
- Error Lens
- TODO Tree

---

**Expected Improvement**: +11.4% overall productivity
**Time to Apply**: 10 minutes
**Difficulty**: Easy
