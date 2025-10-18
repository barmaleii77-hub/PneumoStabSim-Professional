#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Удаление дублирующихся 3 Model для U-рамы из main.qml
"""

import re
from pathlib import Path
from datetime import datetime

def remove_duplicate_uframe():
    """Удалить дублирующиеся 3 Model для U-рамы"""
    
    main_qml = Path("assets/qml/main.qml")
    
    if not main_qml.exists():
        print(f"❌ {main_qml} не найден!")
        return False
    
    print(f"📖 Читаем {main_qml}...")
    with open(main_qml, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📏 Исходно: {len(lines)} строк")
    
    # Ищем блок с дублирующимися Model между комментарием "// U-FRAME" и "// Frame component"
    # Паттерн: ищем строку с "// U-FRAME" и следующие 3 Model блока до "// Frame component"
    
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if '// U-FRAME (3 beams)' in line and 'controlled materials' in line:
            start_idx = i
            print(f"✅ Найден старый блок U-FRAME на строке {i+1}")
        
        if start_idx is not None and '// ✅ Frame component' in line:
            end_idx = i
            print(f"✅ Найдена граница на строке {i+1}")
            break
    
    if start_idx is None:
        print("⚠️ Старый блок U-FRAME не найден")
        return False
    
    if end_idx is None:
        print("⚠️ Граница Frame component не найдена")
        return False
    
    # Подсчитываем количество Model между start и end
    models_count = 0
    for i in range(start_idx, end_idx):
        if 'Model {' in lines[i]:
            models_count += 1
    
    print(f"📊 Найдено {models_count} Model блоков для удаления")
    print(f"   Строки {start_idx+1} - {end_idx}")
    
    if models_count != 3:
        print(f"⚠️ Ожидалось 3 Model, найдено {models_count}")
        print("   Возможно, структура файла изменилась")
    
    # Создаём backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = main_qml.with_suffix(f'.qml.backup_uframe_{timestamp}')
    print(f"💾 Создаём backup: {backup_path}")
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # Удаляем строки от start до end (не включая end)
    new_lines = lines[:start_idx] + lines[end_idx:]
    
    print(f"📏 Новый размер: {len(new_lines)} строк")
    print(f"   Удалено: {len(lines) - len(new_lines)} строк")
    
    # Сохраняем
    with open(main_qml, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Дублирующийся блок успешно удалён!")
    
    return True

def main():
    """Главная функция"""
    print("=" * 70)
    print("🧹 УДАЛЕНИЕ ДУБЛИРУЮЩИХСЯ U-FRAME MODEL")
    print("=" * 70)
    print()
    
    success = remove_duplicate_uframe()
    
    print()
    print("=" * 70)
    if success:
        print("✅ ОЧИСТКА ЗАВЕРШЕНА!")
        print("   Старые 3 Model для U-рамы удалены")
        print("   Остался только Frame компонент")
    else:
        print("⚠️ НИЧЕГО НЕ ИЗМЕНЕНО")
        print("   Дублирующийся блок не найден")
    print("=" * 70)

if __name__ == "__main__":
    main()
