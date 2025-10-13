#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ СИНХРОНИЗАЦИИ GRAPHICS PANEL ↔ QML

Исправляет критические проблемы:
1. Параметры освещения (position_y → height)
2. Автовращение камеры (добавление обработки в QML)
3. Параметры эффектов (vignette, motion blur, dof)
"""

import sys
from pathlib import Path
import re

def fix_lighting_payload():
    """Исправить payload освещения в panel_graphics.py"""
    file_path = Path("src/ui/panels/panel_graphics.py")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    print("🔧 Fixing lighting payload in panel_graphics.py...")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Исправить position_y → height
    old_code = '''if "height" in point:
                pl["position_y"] = point.get("height")'''
    
    new_code = '''if "height" in point:
                pl["height"] = point.get("height")  # ✅ FIXED: use "height" instead of "position_y"'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        file_path.write_text(content, encoding='utf-8')
        print("  ✅ Fixed: position_y → height")
        return True
    else:
        print("  ⚠️ Pattern not found or already fixed")
        return False

def check_qml_camera_updates():
    """Проверить и исправить applyCameraUpdates в QML"""
    file_path = Path("assets/qml/main.qml")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    print("\n🔧 Checking applyCameraUpdates in main.qml...")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Проверяем наличие обработки auto_rotate
    if "params.auto_rotate !== undefined" in content:
        print("  ✅ auto_rotate handling already present")
        return True
    
    # Ищем функцию applyCameraUpdates
    pattern = r'(function applyCameraUpdates\(params\) \{.*?if \(params\.speed !== undefined\) cameraSpeed = params\.speed)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("  ❌ applyCameraUpdates function not found")
        return False
    
    # Добавляем обработку auto_rotate
    new_code = match.group(1) + '''
    
    // ✅ FIXED: Handle auto_rotate from panel_graphics
    if (params.auto_rotate !== undefined) autoRotate = params.auto_rotate
    if (params.auto_rotate_speed !== undefined) autoRotateSpeed = params.auto_rotate_speed'''
    
    content = content.replace(match.group(0), new_code)
    file_path.write_text(content, encoding='utf-8')
    print("  ✅ Added auto_rotate handling")
    return True

def check_qml_effects_updates():
    """Проверить и дополнить applyEffectsUpdates в QML"""
    file_path = Path("assets/qml/main.qml")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    print("\n🔧 Checking applyEffectsUpdates in main.qml...")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Проверяем наличие vignette_strength
    if "params.vignette_strength !== undefined" in content:
        print("  ✅ vignette_strength handling already present")
        return True
    
    # Ищем функцию applyEffectsUpdates
    pattern = r'(function applyEffectsUpdates\(params\) \{.*?)(console\.log\("  ✅.*?"\))'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("  ❌ applyEffectsUpdates function not found")
        return False
    
    # Проверяем, есть ли уже все параметры
    existing_code = match.group(1)
    
    needs_update = False
    missing_params = []
    
    if "params.vignette_strength" not in existing_code:
        missing_params.append("vignette_strength")
        needs_update = True
    
    if "params.motion_blur_amount" not in existing_code:
        missing_params.append("motion_blur_amount")
        needs_update = True
    
    if "params.dof_blur" not in existing_code:
        missing_params.append("dof_blur")
        needs_update = True
    
    if not needs_update:
        print("  ✅ All effects parameters already handled")
        return True
    
    # Добавляем недостающие параметры
    additional_code = "\n    // ✅ FIXED: Added missing effects parameters\n"
    
    if "vignette_strength" in missing_params:
        additional_code += '''    if (params.vignette !== undefined) vignetteEnabled = params.vignette
    if (params.vignette_strength !== undefined) vignetteStrength = params.vignette_strength
    '''
    
    if "motion_blur_amount" in missing_params:
        additional_code += '''    if (params.motion_blur !== undefined) motionBlurEnabled = params.motion_blur
    if (params.motion_blur_amount !== undefined) motionBlurAmount = params.motion_blur_amount
    '''
    
    if "dof_blur" in missing_params:
        additional_code += '''    if (params.depth_of_field !== undefined) depthOfFieldEnabled = params.depth_of_field
    if (params.dof_focus_distance !== undefined) dofFocusDistance = params.dof_focus_distance
    if (params.dof_blur !== undefined) dofBlurAmount = params.dof_blur
    '''
    
    new_code = match.group(1) + additional_code + "\n    " + match.group(2)
    
    content = content.replace(match.group(0), new_code)
    file_path.write_text(content, encoding='utf-8')
    print(f"  ✅ Added {len(missing_params)} missing parameter(s): {', '.join(missing_params)}")
    return True

def verify_fixes():
    """Проверить примененные исправления"""
    print("\n" + "="*60)
    print("🔍 VERIFYING FIXES")
    print("="*60)
    
    # Проверка 1: Lighting payload
    py_file = Path("src/ui/panels/panel_graphics.py")
    if py_file.exists():
        content = py_file.read_text(encoding='utf-8')
        if 'pl["height"] = point.get("height")' in content:
            print("✅ Lighting payload fixed (position_y → height)")
        else:
            print("❌ Lighting payload NOT fixed")
    
    # Проверка 2: Camera auto_rotate
    qml_file = Path("assets/qml/main.qml")
    if qml_file.exists():
        content = qml_file.read_text(encoding='utf-8')
        if "params.auto_rotate !== undefined" in content:
            print("✅ Camera auto_rotate handling present")
        else:
            print("❌ Camera auto_rotate handling MISSING")
    
    # Проверка 3: Effects parameters
    if qml_file.exists():
        content = qml_file.read_text(encoding='utf-8')
        vignette_ok = "params.vignette_strength !== undefined" in content
        motion_ok = "params.motion_blur_amount !== undefined" in content
        dof_ok = "params.dof_blur !== undefined" in content
        
        if vignette_ok and motion_ok and dof_ok:
            print("✅ All effects parameters handled")
        else:
            missing = []
            if not vignette_ok:
                missing.append("vignette_strength")
            if not motion_ok:
                missing.append("motion_blur_amount")
            if not dof_ok:
                missing.append("dof_blur")
            print(f"❌ Missing effects: {', '.join(missing)}")

def main():
    print("="*60)
    print("🔧 GRAPHICS PANEL ↔ QML SYNC AUTO-FIX")
    print("="*60)
    
    # Применяем исправления
    success_count = 0
    
    if fix_lighting_payload():
        success_count += 1
    
    if check_qml_camera_updates():
        success_count += 1
    
    if check_qml_effects_updates():
        success_count += 1
    
    # Проверяем результаты
    verify_fixes()
    
    print("\n" + "="*60)
    if success_count == 3:
        print("✅ ALL FIXES APPLIED SUCCESSFULLY")
        print("\n🚀 Next steps:")
        print("   1. Run: python app.py")
        print("   2. Test lighting changes")
        print("   3. Test camera auto-rotate")
        print("   4. Test effects (vignette, motion blur, dof)")
        print("="*60)
        return 0
    else:
        print(f"⚠️ PARTIAL SUCCESS: {success_count}/3 fixes applied")
        print("\n🔧 Manual review required for failed fixes")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
