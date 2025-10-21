# 🎯 PATH Setup - Quick Reference

## TL;DR (Too Long; Didn't Read)

```powershell
# Windows - ONE COMMAND
.\setup_all_paths.ps1

# Then for each new terminal session
. .\activate_environment.ps1
```

```bash
# Linux/macOS - ONE COMMAND
chmod +x setup_all_paths.sh && ./setup_all_paths.sh

# Then for each new terminal session
source ./activate_environment.sh
```

## What This Does

✅ Configures `PYTHONPATH` (adds `src/`, `tests/`, `scripts/`)
✅ Sets up Qt environment (QML paths, graphics backend, High DPI)
✅ Creates `.env` file with all settings
✅ Verifies Python, PySide6, QtQuick3D installation
✅ Checks project structure integrity

## Files Created

- `setup_all_paths.ps1` - Windows PowerShell setup
- `setup_all_paths.sh` - Linux/macOS Bash setup
- `activate_environment.ps1` - Quick activate (Windows)
- `activate_environment.sh` - Quick activate (Linux/macOS)
- `.env` - Environment variables (auto-generated)

## Usage Patterns

### Daily Development
```bash
# Activate environment once per session
. .\activate_environment.ps1  # Windows
source ./activate_environment.sh  # Linux

# Run app
py app.py
```

### First Time Setup
```bash
# Run full setup
.\setup_all_paths.ps1  # Windows
./setup_all_paths.sh    # Linux
```

### Verify Only (No Changes)
```powershell
.\setup_all_paths.ps1 -VerifyOnly
```

## Troubleshooting One-Liners

```powershell
# Execution Policy (Windows)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Reinstall PySide6
pip install PySide6 --force-reinstall

# Check PYTHONPATH
$env:PYTHONPATH  # Windows
echo $PYTHONPATH  # Linux
```

## Links

- 📖 Full Documentation: [PATH_SETUP_GUIDE.md](PATH_SETUP_GUIDE.md)
- ✅ Complete Report: [PATH_SETUP_COMPLETE.md](PATH_SETUP_COMPLETE.md)
- 🐛 Issues: Check script output for detailed error messages

---

**Status**: ✅ Ready to use
**Platforms**: Windows 10+, Linux, macOS
**Last Updated**: 2025-01-24
