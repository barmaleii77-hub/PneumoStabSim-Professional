# -*- coding: utf-8 -*-
"""
Автоматическое применение рекомендаций по синхронизации QML и Python
Добавляет недостающие свойства и обработчики
"""

import re
from pathlib import Path
from datetime import datetime

def backup_file(file_path):
    """Создать резервную копию файла"""
    backup_path = file_path.with_suffix(file_path.suffix + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    with open(file_path, 'r', encoding='utf-8') as src:
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    print(f"✅ Создана резервная копия: {backup_path}")
    return backup_path

def add_qml_properties(qml_file):
    """Добавить недостающие свойства в QML файл"""
    print(f"\n📝 Обновление {qml_file}...")
    
    with open(qml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Найти раздел COMPLETE GRAPHICS PROPERTIES
    pattern = r'(// ={60,}\s+// ✅ COMPLETE GRAPHICS PROPERTIES.*?\s+// ={60,})'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ Не найден раздел COMPLETE GRAPHICS PROPERTIES")
        return False
    
    # Свойства для добавления
    new_properties = """
    // ===== РАСШИРЕННЫЕ МАТЕРИАЛЫ =====
    
    // Cylinder (корпус цилиндра)
    property string cylinderColor: "#ffffff"
    property real cylinderMetalness: 0.0
    property real cylinderRoughness: 0.05
    
    // Piston body (корпус поршня)
    property string pistonBodyColor: "#ff0066"
    property string pistonBodyWarningColor: "#ff4444"
    property real pistonBodyMetalness: 1.0
    property real pistonBodyRoughness: 0.28
    
    // Piston rod (шток поршня)
    property string pistonRodColor: "#cccccc"
    property string pistonRodWarningColor: "#ff0000"
    property real pistonRodMetalness: 1.0
    property real pistonRodRoughness: 0.28
    
    // Joints (шарниры)
    property string jointTailColor: "#0088ff"
    property string jointArmColor: "#ff8800"
    property string jointRodOkColor: "#00ff44"
    property string jointRodErrorColor: "#ff0000"
    property real jointMetalness: 0.9
    property real jointRoughness: 0.35
    
    // Frame advanced (расширенные параметры рамы)
    property string frameColor: "#cc0000"
    property real frameClearcoat: 0.1
    property real frameClearcoatRoughness: 0.2
    
    // Lever advanced (расширенные параметры рычагов)
    property string leverColor: "#888888"
    property real leverClearcoat: 0.25
    property real leverClearcoatRoughness: 0.1
    
    // Tail rod (хвостовой шток)
    property string tailColor: "#cccccc"
    property real tailMetalness: 1.0
    property real tailRoughness: 0.3
    
    // ===== РАСШИРЕННОЕ ОСВЕЩЕНИЕ =====
    property real rimBrightness: 1.5
    property string rimColor: "#ffffcc"
    property string pointColor: "#ffffff"
    property real pointFade: 0.00008
    
    // ===== IBL РАСШИРЕННЫЕ =====
    property string iblSource: "../hdr/studio.hdr"
    property string iblFallback: "assets/studio_small_09_2k.hdr"
"""
    
    # Проверяем, не добавлены ли уже эти свойства
    if 'property string cylinderColor' in content:
        print("⚠️ Свойства уже добавлены, пропускаем")
        return True
    
    # Найти конец раздела свойств (перед следующим комментарием или функцией)
    # Ищем строку после последнего property в разделе
    insert_position = content.find('// ===============================================================', match.end())
    
    if insert_position == -1:
        print("❌ Не найдена позиция для вставки")
        return False
    
    # Вставляем новые свойства
    updated_content = content[:insert_position] + new_properties + "\n    " + content[insert_position:]
    
    # Сохраняем файл
    with open(qml_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✅ Добавлено {new_properties.count('property')} новых свойств")
    return True

def update_qml_material_function(qml_file):
    """Обновить функцию applyMaterialUpdates в QML"""
    print(f"\n🔧 Обновление applyMaterialUpdates()...")
    
    with open(qml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Найти функцию applyMaterialUpdates
    pattern = r'(function applyMaterialUpdates\(params\) \{.*?)(console\.log\("  ✅ Materials updated.*?\"\))'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ Не найдена функция applyMaterialUpdates")
        return False
    
    # Новый код для добавления
    new_code = """
        
        // ✅ НОВОЕ: Frame advanced
        if (params.frame !== undefined) {
            if (params.frame.color !== undefined) frameColor = params.frame.color
            if (params.frame.metalness !== undefined) frameMetalness = params.frame.metalness
            if (params.frame.roughness !== undefined) frameRoughness = params.frame.roughness
            if (params.frame.clearcoat !== undefined) frameClearcoat = params.frame.clearcoat
            if (params.frame.clearcoat_roughness !== undefined) frameClearcoatRoughness = params.frame.clearcoat_roughness
        }
        
        // ✅ НОВОЕ: Lever advanced
        if (params.lever !== undefined) {
            if (params.lever.color !== undefined) leverColor = params.lever.color
            if (params.lever.metalness !== undefined) leverMetalness = params.lever.metalness
            if (params.lever.roughness !== undefined) leverRoughness = params.lever.roughness
            if (params.lever.clearcoat !== undefined) leverClearcoat = params.lever.clearcoat
            if (params.lever.clearcoat_roughness !== undefined) leverClearcoatRoughness = params.lever.clearcoat_roughness
        }
        
        // ✅ НОВОЕ: Tail rod
        if (params.tail !== undefined) {
            if (params.tail.color !== undefined) tailColor = params.tail.color
            if (params.tail.metalness !== undefined) tailMetalness = params.tail.metalness
            if (params.tail.roughness !== undefined) tailRoughness = params.tail.roughness
        }
        
        // ✅ НОВОЕ: Cylinder
        if (params.cylinder !== undefined) {
            if (params.cylinder.color !== undefined) cylinderColor = params.cylinder.color
            if (params.cylinder.metalness !== undefined) cylinderMetalness = params.cylinder.metalness
            if (params.cylinder.roughness !== undefined) cylinderRoughness = params.cylinder.roughness
        }
        
        // ✅ НОВОЕ: Piston body
        if (params.piston_body !== undefined) {
            if (params.piston_body.color !== undefined) pistonBodyColor = params.piston_body.color
            if (params.piston_body.warning_color !== undefined) pistonBodyWarningColor = params.piston_body.warning_color
            if (params.piston_body.metalness !== undefined) pistonBodyMetalness = params.piston_body.metalness
            if (params.piston_body.roughness !== undefined) pistonBodyRoughness = params.piston_body.roughness
        }
        
        // ✅ НОВОЕ: Piston rod
        if (params.piston_rod !== undefined) {
            if (params.piston_rod.color !== undefined) pistonRodColor = params.piston_rod.color
            if (params.piston_rod.warning_color !== undefined) pistonRodWarningColor = params.piston_rod.warning_color
            if (params.piston_rod.metalness !== undefined) pistonRodMetalness = params.piston_rod.metalness
            if (params.piston_rod.roughness !== undefined) pistonRodRoughness = params.piston_rod.roughness
        }
        
        // ✅ НОВОЕ: Joints
        if (params.joint !== undefined) {
            if (params.joint.tail_color !== undefined) jointTailColor = params.joint.tail_color
            if (params.joint.arm_color !== undefined) jointArmColor = params.joint.arm_color
            if (params.joint.rod_ok_color !== undefined) jointRodOkColor = params.joint.rod_ok_color
            if (params.joint.rod_error_color !== undefined) jointRodErrorColor = params.joint.rod_error_color
            if (params.joint.metalness !== undefined) jointMetalness = params.joint.metalness
            if (params.joint.roughness !== undefined) jointRoughness = params.joint.roughness
        }
        
        """
    
    # Проверяем, не добавлен ли уже этот код
    if 'params.cylinder' in content:
        print("⚠️ Код уже добавлен, пропускаем")
        return True
    
    # Заменяем функцию
    updated_content = content[:match.start(2)] + new_code + "\n        " + content[match.start(2):]
    
    # Обновляем сообщение о завершении
    updated_content = updated_content.replace(
        'console.log("  ✅ Materials updated successfully (including IOR)")',
        'console.log("  ✅ Materials updated successfully (COMPLETE with all colors)")'
    )
    
    # Сохраняем файл
    with open(qml_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Функция applyMaterialUpdates() обновлена")
    return True

def update_qml_lighting_function(qml_file):
    """Обновить функцию applyLightingUpdates в QML"""
    print(f"\n💡 Обновление applyLightingUpdates()...")
    
    with open(qml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Найти функцию applyLightingUpdates
    pattern = r'(function applyLightingUpdates\(params\) \{.*?)(console\.log\("  ✅ Lighting updated.*?\"\))'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ Не найдена функция applyLightingUpdates")
        return False
    
    # Новый код для добавления
    new_code = """
        
        // ✅ НОВОЕ: Rim light
        if (params.rim_light) {
            if (params.rim_light.brightness !== undefined) rimBrightness = params.rim_light.brightness
            if (params.rim_light.color !== undefined) rimColor = params.rim_light.color
        }
        
        // ✅ РАСШИРЕННОЕ: Point light
        if (params.point_light) {
            if (params.point_light.brightness !== undefined) pointLightBrightness = params.point_light.brightness
            if (params.point_light.color !== undefined) pointColor = params.point_light.color
            if (params.point_light.position_y !== undefined) pointLightY = params.point_light.position_y
            if (params.point_light.fade !== undefined) pointFade = params.point_light.fade
        }
        """
    
    # Проверяем, не добавлен ли уже этот код
    if 'params.rim_light' in content:
        print("⚠️ Код уже добавлен, пропускаем")
        return True
    
    # Заменяем функцию
    updated_content = content[:match.start(2)] + new_code + "\n        " + content[match.start(2):]
    
    # Обновляем сообщение о завершении
    updated_content = updated_content.replace(
        'console.log("  ✅ Lighting updated successfully")',
        'console.log("  ✅ Lighting updated successfully (COMPLETE)")'
    )
    
    # Сохраняем файл
    with open(qml_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Функция applyLightingUpdates() обновлена")
    return True

def update_python_material_emit(py_file):
    """Обновить emit_material_update в Python"""
    print(f"\n🐍 Обновление emit_material_update()...")
    
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Найти функцию emit_material_update
    pattern = r'(def emit_material_update\(self\):.*?)(self\.logger\.info.*?self\.material_changed\.emit\(material_params\))'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ Не найдена функция emit_material_update")
        return False
    
    # Новый код функции
    new_function_body = '''"""Отправить сигнал об изменении материалов (ПОЛНЫЙ НАБОР)"""
        material_params = {
            # Metal (общие металлические части)
            'metal': {
                'roughness': self.current_graphics['metal_roughness'],
                'metalness': self.current_graphics['metal_metalness'],
                'clearcoat': self.current_graphics['metal_clearcoat'],
            },
            
            # Glass (стеклянные части)
            'glass': {
                'opacity': self.current_graphics['glass_opacity'],
                'roughness': self.current_graphics['glass_roughness'],
                'ior': self.current_graphics['glass_ior'],
            },
            
            # Frame (рама)
            'frame': {
                'color': self.current_graphics['frame_color'],
                'metalness': self.current_graphics['frame_metalness'],
                'roughness': self.current_graphics['frame_roughness'],
                'clearcoat': self.current_graphics['frame_clearcoat'],
                'clearcoat_roughness': self.current_graphics['frame_clearcoat_roughness'],
            },
            
            # Lever (рычаги)
            'lever': {
                'color': self.current_graphics['lever_color'],
                'metalness': self.current_graphics['lever_metalness'],
                'roughness': self.current_graphics['lever_roughness'],
                'clearcoat': self.current_graphics['lever_clearcoat'],
                'clearcoat_roughness': self.current_graphics['lever_clearcoat_roughness'],
            },
            
            # Tail (хвостовой шток)
            'tail': {
                'color': self.current_graphics['tail_color'],
                'metalness': self.current_graphics['tail_metalness'],
                'roughness': self.current_graphics['tail_roughness'],
            },
            
            # Cylinder (корпус цилиндра)
            'cylinder': {
                'color': self.current_graphics['cylinder_color'],
                'metalness': self.current_graphics['cylinder_metalness'],
                'roughness': self.current_graphics['cylinder_roughness'],
            },
            
            # Piston body (корпус поршня)
            'piston_body': {
                'color': self.current_graphics['piston_body_color'],
                'warning_color': self.current_graphics['piston_body_warning_color'],
                'metalness': self.current_graphics['piston_body_metalness'],
                'roughness': self.current_graphics['piston_body_roughness'],
            },
            
            # Piston rod (шток поршня)
            'piston_rod': {
                'color': self.current_graphics['piston_rod_color'],
                'warning_color': self.current_graphics['piston_rod_warning_color'],
                'metalness': self.current_graphics['piston_rod_metalness'],
                'roughness': self.current_graphics['piston_rod_roughness'],
            },
            
            # Joints (шарниры)
            'joint': {
                'tail_color': self.current_graphics['joint_tail_color'],
                'arm_color': self.current_graphics['joint_arm_color'],
                'rod_ok_color': self.current_graphics['joint_rod_ok_color'],
                'rod_error_color': self.current_graphics['joint_rod_error_color'],
                'metalness': self.current_graphics['joint_metalness'],
                'roughness': self.current_graphics['joint_roughness'],
            },
        }
        
        '''
    
    # Проверяем, не обновлена ли уже функция
    if "'cylinder':" in content and 'emit_material_update' in content:
        print("⚠️ Функция уже обновлена, пропускаем")
        return True
    
    # Заменяем тело функции
    updated_content = content.replace(match.group(0), 
        f"def emit_material_update(self):\n        {new_function_body}" +
        f"self.logger.info(f\"Materials updated (COMPLETE): {{len(material_params)}} groups\")\n        " +
        "self.material_changed.emit(material_params)")
    
    # Сохраняем файл
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Функция emit_material_update() обновлена")
    return True

def main():
    """Основная функция"""
    print("=" * 80)
    print("🚀 АВТОМАТИЧЕСКОЕ ПРИМЕНЕНИЕ РЕКОМЕНДАЦИЙ ПО СИНХРОНИЗАЦИИ QML И PYTHON")
    print("=" * 80)
    
    qml_file = Path('assets/qml/main_optimized.qml')
    py_file = Path('src/ui/panels/panel_graphics.py')
    
    if not qml_file.exists():
        print(f"❌ QML файл не найден: {qml_file}")
        return
    
    if not py_file.exists():
        print(f"❌ Python файл не найден: {py_file}")
        return
    
    # Создаем резервные копии
    print("\n📦 Создание резервных копий...")
    qml_backup = backup_file(qml_file)
    py_backup = backup_file(py_file)
    
    try:
        # Обновляем QML
        success_qml_props = add_qml_properties(qml_file)
        success_qml_materials = update_qml_material_function(qml_file)
        success_qml_lighting = update_qml_lighting_function(qml_file)
        
        # Обновляем Python
        success_py_materials = update_python_material_emit(py_file)
        
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ:")
        print("=" * 80)
        print(f"{'✅' if success_qml_props else '❌'} Добавление свойств в QML")
        print(f"{'✅' if success_qml_materials else '❌'} Обновление applyMaterialUpdates() в QML")
        print(f"{'✅' if success_qml_lighting else '❌'} Обновление applyLightingUpdates() в QML")
        print(f"{'✅' if success_py_materials else '❌'} Обновление emit_material_update() в Python")
        
        all_success = all([success_qml_props, success_qml_materials, success_qml_lighting, success_py_materials])
        
        if all_success:
            print("\n✅ ВСЕ ОБНОВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!")
            print(f"\n💡 Резервные копии сохранены:")
            print(f"   - {qml_backup}")
            print(f"   - {py_backup}")
            print(f"\n🚀 Теперь можно запустить приложение:")
            print(f"   py app.py --force-optimized")
        else:
            print("\n⚠️ НЕКОТОРЫЕ ОБНОВЛЕНИЯ НЕ ПРИМЕНЕНЫ")
            print("   Проверьте файлы вручную")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        print(f"\n↩️ Восстановление из резервных копий...")
        
        # Восстанавливаем из бэкапов
        import shutil
        shutil.copy(qml_backup, qml_file)
        shutil.copy(py_backup, py_file)
        
        print("✅ Файлы восстановлены из резервных копий")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
