# -*- coding: utf-8 -*-
"""Simple validation check for PROMPT #1"""
from pathlib import Path

print("=" * 60)
print("?? PROMPT #1 VALIDATION")
print("=" * 60)

# Check modified files
files = {
    "Main Window": "src/ui/main_window.py",
    "GeometryPanel": "src/ui/panels/panel_geometry.py",
    "PneumoPanel": "src/ui/panels/panel_pneumo.py",
    "Test Layout": "tests/ui/test_ui_layout.py",
    "Test Functionality": "tests/ui/test_panel_functionality.py",
    "Test Runner": "run_ui_tests.py",
}

missing = []
for name, path in files.items():
    if Path(path).exists():
        size = Path(path).stat().st_size
        print(f"? {name:20s} {size:8d} bytes")
    else:
        print(f"? {name:20s} MISSING")
        missing.append(path)

print()
if missing:
    print(f"? {len(missing)} files missing!")
    for f in missing:
        print(f"  - {f}")
else:
    print("? All files present!")
    print()
    print("Ready for:")
    print("  1. Run tests: python run_ui_tests.py")
    print("  2. Git commit")

print("=" * 60)
