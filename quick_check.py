#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Быстрая проверка работоспособности PneumoStabSim
"""
import sys

print("=" * 60)
print("🏥 ЭКСПРЕСС-ПРОВЕРКА PNEUMOSTABSIM")
print("=" * 60)

checks = []

# 1. Python
try:
    assert sys.version_info >= (3, 8), "Python 3.8+ required"
    checks.append(("Python", True, f"{sys.version_info.major}.{sys.version_info.minor}"))
except Exception as e:
    checks.append(("Python", False, str(e)))

# 2. PySide6
try:
    from PySide6.QtWidgets import QApplication
    checks.append(("PySide6", True, "OK"))
except ImportError:
    checks.append(("PySide6", False, "Not installed"))

# 3. Project modules
try:
    from src.common import init_logging
    from src.ui.main_window import MainWindow
    checks.append(("Modules", True, "OK"))
except ImportError as e:
    checks.append(("Modules", False, str(e)))

# 4. QML files
try:
    from pathlib import Path
    qml = Path("assets/qml/main_optimized.qml")
    checks.append(("QML", qml.exists(), "Found" if qml.exists() else "Missing"))
except Exception as e:
    checks.append(("QML", False, str(e)))

# Print results
print("\nРезультаты проверки:\n")
all_ok = True
for name, status, detail in checks:
    icon = "✅" if status else "❌"
    print(f"  {icon} {name:12} : {detail}")
    if not status:
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✅ ВСЁ РАБОТАЕТ - можно запускать приложение!")
    print("\nКоманда запуска:")
    print("  py app.py --test-mode")
else:
    print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ - см. выше")

print("=" * 60)
sys.exit(0 if all_ok else 1)
