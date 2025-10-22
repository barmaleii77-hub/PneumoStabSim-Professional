#!/usr/bin/env python3
"""
Быстрое исправление импортов PneumoStabSim
Quick fix for PneumoStabSim imports
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fix_critical_imports import main

    main()
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Убедитесь, что файл fix_critical_imports.py находится в той же директории")
