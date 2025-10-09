#!/usr/bin/env python3
"""
Поиск строк с emissiveColor в QML файле
"""

import sys
from pathlib import Path

def find_emissive_color():
    qml_file = Path("assets/qml/main_v2_realism.qml")
    if not qml_file.exists():
        print(f"Файл не найден: {qml_file}")
        return
    
    content = qml_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    print("Поиск 'emissiveColor' в main_v2_realism.qml:")
    print("=" * 50)
    
    found = False
    for i, line in enumerate(lines, 1):
        if 'emissiveColor' in line:
            print(f"Строка {i}: {line}")
            found = True
    
    if not found:
        print("❌ emissiveColor не найден в файле")
    else:
        print(f"\n✅ Найдено {sum(1 for line in lines if 'emissiveColor' in line)} вхождений")

if __name__ == "__main__":
    find_emissive_color()
