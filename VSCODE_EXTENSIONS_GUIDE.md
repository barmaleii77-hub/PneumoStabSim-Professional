# VS Code Extensions - Installation Guide

## ✅ Status: VS Code Not Found

VS Code не обнаружен в системе. Необходимо установить VS Code перед установкой расширений.

## 📥 Install VS Code

**Download:** https://code.visualstudio.com/download

**Windows Installation:**
1. Скачайте User Installer (64-bit)
2. Запустите установщик
3. ✅ Отметьте "Add to PATH"
4. ✅ Отметьте "Register Code as an editor for supported file types"
5. Установите

## 📦 Required Extensions

### Critical (Must Have)

```bash
# Python Development
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance

# GitHub Copilot (REQUIRED for development)
code --install-extension github.copilot
code --install-extension github.copilot-chat
```

### Recommended

```bash
# Python Tools
code --install-extension ms-python.black-formatter
code --install-extension ms-python.mypy-type-checker
code --install-extension ms-python.flake8

# Qt/QML Development
code --install-extension bbenoist.qml
code --install-extension seanwu.vscode-qt-for-python

# Version Control
code --install-extension eamodio.gitlens
code --install-extension github.vscode-pull-request-github

# Utilities
code --install-extension ms-vscode.powershell
code --install-extension visualstudioexptteam.vscodeintellicode
code --install-extension christian-kohler.path-intellisense

# Testing
code --install-extension littlefoxteam.vscode-python-test-adapter

# Documentation
code --install-extension yzhang.markdown-all-in-one
code --install-extension davidanson.vscode-markdownlint
```

## 🚀 Quick Install (After VS Code is installed)

**Option 1: Use our script**
```powershell
.\install_extensions.ps1
```

**Option 2: Manual installation**
1. Open VS Code
2. Press `Ctrl+Shift+X` (Extensions panel)
3. Search and install each extension:
   - `Python` (ms-python.python)
   - `Pylance` (ms-python.vscode-pylance)
   - `GitHub Copilot` (github.copilot)
- `GitHub Copilot Chat` (github.copilot-chat)
   - etc.

**Option 3: Install all at once**
```powershell
# Copy all extension IDs from extensions.json
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension ms-python.mypy-type-checker
code --install-extension ms-python.flake8
code --install-extension github.copilot
code --install-extension github.copilot-chat
code --install-extension bbenoist.qml
code --install-extension seanwu.vscode-qt-for-python
code --install-extension eamodio.gitlens
code --install-extension github.vscode-pull-request-github
code --install-extension littlefoxteam.vscode-python-test-adapter
code --install-extension christian-kohler.path-intellisense
code --install-extension visualstudioexptteam.vscodeintellicode
code --install-extension ms-vscode.powershell
code --install-extension yzhang.markdown-all-in-one
code --install-extension davidanson.vscode-markdownlint
```

## ⚙️ Post-Installation Configuration

### 1. GitHub Copilot Setup
- Sign in to GitHub: `Ctrl+Shift+P` -> `GitHub Copilot: Sign In`
- Verify subscription is active
- Test: Open any Python file and start typing

### 2. Python Interpreter
- `Ctrl+Shift+P` -> `Python: Select Interpreter`
- Choose: `Python 3.14.0` (or your installed version)
- Verify in status bar (bottom right)

### 3. Settings
Check `.vscode/settings.json` is properly configured:
```json
{
    "python.defaultInterpreterPath": "py",
    "python.languageServer": "Pylance",
    "python.analysis.typeCheckingMode": "basic",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "editor.formatOnSave": true,
  "files.encoding": "utf8"
}
```

## 📋 Verification Checklist

After installation, verify:

- [ ] VS Code opens correctly
- [ ] Extensions panel shows all installed (`Ctrl+Shift+X`)
- [ ] Python extension activated (Python icon in left sidebar)
- [ ] GitHub Copilot shows in status bar (bottom right)
- [ ] Can open `.py` files with syntax highlighting
- [ ] Can open `.qml` files with syntax highlighting
- [ ] Copilot suggestions appear when typing

## 🔍 Troubleshooting

### VS Code not in PATH
```powershell
# Add VS Code to PATH manually
$vscodePath = "${env:LOCALAPPDATA}\Programs\Microsoft VS Code\bin"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$vscodePath", "User")

# Restart terminal
```

### Extensions not installing
- Check internet connection
- Try manual installation through Extensions panel
- Check VS Code version (must be recent)
- Clear extension cache: Delete `%USERPROFILE%\.vscode\extensions`

### GitHub Copilot not working
- Verify GitHub account has active Copilot subscription
- Sign out and sign in again
- Check VS Code settings for Copilot configuration

## 📚 Related Files

- `.vscode/extensions.json` - Recommended extensions list
- `.vscode/settings.json` - VS Code settings
- `.vscode/launch.json` - Debug configurations
- `install_extensions.ps1` - Automated installation script

---

**Status**: ⚠️ **VS Code must be installed first**  
**Last Updated**: 2025-01-24  
**Action Required**: Install VS Code from https://code.visualstudio.com/
