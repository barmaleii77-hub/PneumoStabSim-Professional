# QUICK ACTION CHECKLIST - PowerShell Encoding Fix

## IMMEDIATE ACTIONS (Do Now!)

### 1. RESTART VS CODE ⭐ MOST IMPORTANT
```
Ctrl+Shift+P → Type: "Reload Window" → Enter
```
**Why**: PowerShell profile changes apply only in new sessions

---

### 2. VERIFY ENCODING (After Restart)
Open new terminal (Ctrl+Shift+`) and run:
```powershell
[Console]::OutputEncoding  # Should show: UTF-8
Test-Path .         # Should work without corruption
```

**Expected Output**:
```
✅ UTF-8 encoding shown
✅ Test-Path works correctly
```

---

### 3. INSTALL DEPENDENCIES
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pre-commit install
```

---

### 4. CONFIGURE GIT (If not done)
```powershell
git config --local user.name "Your Name"
git config --local user.email "your@email.com"
```

---

## VERIFICATION CHECKLIST

After restart, check these:

- [ ] Terminal opens without errors
- [ ] `[Console]::OutputEncoding` shows UTF-8
- [ ] `Test-Path .` works
- [ ] `Get-Content README.md -TotalCount 1` works
- [ ] `python --version` shows 3.13.8
- [ ] `git config --local user.name` shows your name
- [ ] Virtual environment activates: `.\.venv\Scripts\Activate.ps1`
- [ ] Pre-commit works: `pre-commit --version`

---

## FILES CREATED (For Reference)

### Scripts:
- `FIX_ENCODING.ps1` - ✅ PowerShell encoding fix (WORKING!)
- `setup_git_config.ps1` - Git configuration
- `check_setup.ps1` - Environment validation
- `QUICK_SETUP.ps1` - One-click setup

### Documentation:
- `QUICK_GUIDE_RU.md` - ⭐ Quick guide in Russian
- `SETUP_COMPLETE.md` - Complete guide (English)
- `TERMINAL_AUDIT_REPORT.md` - Full technical audit
- `ENVIRONMENT_SETUP_COMPLETE.md` - Comprehensive setup

### Configuration:
- `.vscode/settings.json` - UPDATED (terminal settings)
- `.pre-commit-config.yaml` - CREATED (hooks)
- `requirements-dev.txt` - ENHANCED (new tools)

---

## TROUBLESHOOTING (Quick Fixes)

### Commands still corrupted?
```powershell
# Check profile exists
Test-Path $PROFILE

# Re-run fix
.\FIX_ENCODING.ps1

# Restart VS Code
```

### Execution Policy error?
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\FIX_ENCODING.ps1
```

### Git not configured?
```powershell
.\setup_git_config.ps1
```

### venv not found?
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

---

## SUCCESS CRITERIA

Environment is ready when:
✅ All checklist items above are checked
✅ Application launches: `python app.py` or F5
✅ No encoding errors in terminal

---

## NEXT STEP

**👉 RESTART VS CODE NOW (Ctrl+Shift+P → Reload Window)**

Then come back and verify the checklist.

---

**Created**: 2024  
**Status**: ✅ READY TO APPLY  
**Time Required**: 5 minutes  
**Priority**: 🔴 CRITICAL
