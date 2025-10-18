# -*- coding: utf-8 -*-
"""
Cleanup Old QML Blocks
Удаляет старые inline материалы и источники света после успешной интеграции модулей
"""

import re
import shutil
from pathlib import Path
from datetime import datetime


def create_backup(main_qml_path: Path) -> Path:
    """Создать резервную копию"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = main_qml_path.with_suffix(f'.qml.backup_cleanup_{timestamp}')
    shutil.copy2(main_qml_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def remove_old_materials(content: str) -> str:
    """Удалить старые inline материалы"""
    print("\n🗑️ Removing old inline materials...")
    
    # Паттерн для поиска старых PrincipledMaterial блоков
    # (только те, что НЕ внутри SharedMaterials)
    material_pattern = r'\n\s*PrincipledMaterial\s*\{\s*id:\s*(\w+Material)[^}]*?baseColor:[^}]*?\}[^\n]*\n'
    
    matches = list(re.finditer(material_pattern, content, flags=re.MULTILINE | re.DOTALL))
    
    if not matches:
        print("  ⏭️ No old materials found")
        return content
    
    # Удаляем только если они НЕ внутри SharedMaterials
    lines_removed = 0
    for match in matches:
        # Проверяем, что это не внутри SharedMaterials
        before_match = content[:match.start()]
        if 'SharedMaterials {' in before_match and '}' not in before_match[before_match.rfind('SharedMaterials {'):]:
            # Это внутри SharedMaterials, пропускаем
            continue
        
        material_name = match.group(1)
        content = content.replace(match.group(0), f'\n    // REMOVED: old {material_name} (now in SharedMaterials)\n')
        lines_removed += 1
    
    print(f"  ✅ Removed {lines_removed} old material blocks")
    return content


def remove_old_lights(content: str) -> str:
    """Удалить старые inline источники света"""
    print("\n🗑️ Removing old inline lights...")
    
    # Паттерн для поиска старых DirectionalLight
    dir_light_pattern = r'\n\s*DirectionalLight\s*\{\s*id:\s*(keyLight|fillLight|rimLight)[^}]*?\}[^\n]*\n'
    
    matches = list(re.finditer(dir_light_pattern, content, flags=re.MULTILINE | re.DOTALL))
    
    lines_removed = 0
    for match in matches:
        # Проверяем, что это не внутри DirectionalLights
        before_match = content[:match.start()]
        if 'DirectionalLights {' in before_match and '}' not in before_match[before_match.rfind('DirectionalLights {'):]:
            # Это внутри DirectionalLights, пропускаем
            continue
        
        light_name = match.group(1)
        content = content.replace(match.group(0), f'\n    // REMOVED: old {light_name} (now in DirectionalLights)\n')
        lines_removed += 1
    
    # Паттерн для поиска старого PointLight
    point_light_pattern = r'\n\s*PointLight\s*\{\s*id:\s*pointLight[^}]*?\}[^\n]*\n'
    
    matches = list(re.finditer(point_light_pattern, content, flags=re.MULTILINE | re.DOTALL))
    
    for match in matches:
        # Проверяем, что это не внутри PointLights
        before_match = content[:match.start()]
        if 'PointLights {' in before_match and '}' not in before_match[before_match.rfind('PointLights {'):]:
            continue
        
        content = content.replace(match.group(0), '\n    // REMOVED: old pointLight (now in PointLights)\n')
        lines_removed += 1
    
    print(f"  ✅ Removed {lines_removed} old light blocks")
    return content


def validate_syntax(content: str) -> bool:
    """Проверка синтаксиса"""
    open_braces = content.count('{')
    close_braces = content.count('}')
    
    if open_braces != close_braces:
        print(f"  ❌ Brace mismatch: {open_braces} {{ vs {close_braces} }}")
        return False
    
    required_blocks = ['SharedMaterials {', 'DirectionalLights {', 'PointLights {']
    for block in required_blocks:
        if block not in content:
            print(f"  ❌ Missing required block: {block}")
            return False
    
    print("  ✅ Syntax validation passed")
    return True


def main():
    main_qml = Path("assets/qml/main.qml")
    
    if not main_qml.exists():
        print(f"❌ File not found: {main_qml}")
        return 1
    
    print("=" * 70)
    print("🧹 QML CLEANUP SCRIPT")
    print("=" * 70)
    
    # Создать бэкап
    backup_path = create_backup(main_qml)
    
    # Прочитать файл
    with open(main_qml, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_lines = len(content.split('\n'))
    print(f"\n📖 Original: {original_lines} lines")
    
    # Удалить старые блоки
    content = remove_old_materials(content)
    content = remove_old_lights(content)
    
    # Валидация
    print("\n🔍 Validating QML syntax...")
    if not validate_syntax(content):
        print("\n❌ Validation failed! Restoring backup...")
        shutil.copy2(backup_path, main_qml)
        return 1
    
    # Записать изменения
    with open(main_qml, 'w', encoding='utf-8') as f:
        f.write(content)
    
    new_lines = len(content.split('\n'))
    reduction = original_lines - new_lines
    
    print("\n" + "=" * 70)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Statistics:")
    print(f"  Original lines:    {original_lines}")
    print(f"  New lines:         {new_lines}")
    print(f"  Lines reduced:     {reduction} ({reduction/original_lines*100:.1f}%)")
    
    print(f"\n💾 Backup saved at: {backup_path}")
    print(f"✅ {main_qml} successfully cleaned!")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
