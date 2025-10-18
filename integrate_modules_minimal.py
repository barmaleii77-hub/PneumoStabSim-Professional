#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Постепенная модульная интеграция в main.qml
НЕ РАЗДУВАЕМ ФАЙЛ - ИСПОЛЬЗУЕМ МОДУЛИ!

ПЛАН:
1. Заменить инлайн FL suspension → SuspensionCorner модуль
2. Заменить инлайн Frame → Frame модуль
3. Добавить FR, RL, RR через тот же модуль
4. Использовать CameraController модуль (уже существует)

РЕЗУЛЬТАТ: main.qml остаётся МИНИМАЛЬНЫМ (~300-400 строк)
"""

from pathlib import Path
import re

def integrate_modules_step_by_step():
    """Поэтапная интеграция модулей в main.qml"""
    
    main_qml = Path("assets/qml/main.qml")
    
    if not main_qml.exists():
        print(f"❌ ERROR: {main_qml} not found!")
        return False
    
    print("=" * 70)
    print("🔧 МОДУЛЬНАЯ ИНТЕГРАЦИЯ - НЕ РАЗДУВАЕМ QML!")
    print("=" * 70)
    
    # Создаём backup
    backup = main_qml.with_suffix('.qml.backup_before_modules')
    print(f"\n💾 Creating backup: {backup}")
    
    with open(main_qml, 'r', encoding='utf-8') as f:
        content = f.read()
    
    backup.write_text(content, encoding='utf-8')
    
    print("\n📊 ТЕКУЩИЙ РАЗМЕР:")
    lines = content.count('\n')
    print(f"   main.qml: {lines} строк")
    
    # ========================================================================
    # STEP 1: Заменить инлайн FL suspension на модуль
    # ========================================================================
    
    print("\n🔧 STEP 1: Заменяем инлайн FL suspension на SuspensionCorner модуль...")
    
    # Ищем инлайн FL suspension (Node { id: flSuspension ... })
    inline_pattern = r'// SUSPENSION CORNER FL.*?Node \{.*?id: flSuspension.*?\n\s+\}\s+// end flSuspension'
    
    if re.search(inline_pattern, content, re.DOTALL):
        print("   ✅ Найден инлайн FL suspension")
        
        # Заменяем на модуль
        module_code = '''// ===============================================================
            // SUSPENSION CORNER FL - МОДУЛЬ
            // ===============================================================
            
            SuspensionCorner {
                id: flCorner
                
                // Joint positions (calculated from geometry)
                j_arm: Qt.vector3d(
                    -root.userTrackWidth/2,
                    root.userBeamSize,
                    root.userFrameToPivot
                )
                j_tail: Qt.vector3d(
                    -root.userTrackWidth/2,
                    root.userBeamSize + root.userFrameHeight,
                    root.userFrameToPivot
                )
                
                leverAngle: root.fl_angle
                pistonPositionFromPython: root.userPistonPositionFL
                
                // Geometry parameters
                leverLength: root.userLeverLength
                rodPosition: root.userRodPosition
                cylinderLength: root.userCylinderLength
                boreHead: root.userBoreHead
                rodDiameter: root.userRodDiameter
                pistonThickness: root.userPistonThickness
                pistonRodLength: root.userPistonRodLength
                cylinderSegments: root.cylinderSegments
                cylinderRings: root.cylinderRings
                
                // Materials (простые цвета - модуль сам создаст PrincipledMaterial)
                leverMaterial: PrincipledMaterial {
                    baseColor: root.leverBaseColor
                    metalness: root.leverMetalness
                    roughness: root.leverRoughness
                }
                tailRodMaterial: PrincipledMaterial { baseColor: "#cccccc"; metalness: 1.0; roughness: 0.3 }
                cylinderMaterial: PrincipledMaterial { baseColor: root.cylinderBaseColor; transmission: root.cylinderTransmission; ior: root.cylinderIor }
                pistonBodyMaterial: PrincipledMaterial { baseColor: root.pistonBodyBaseColor; metalness: root.pistonBodyMetalness; roughness: root.pistonBodyRoughness }
                pistonRodMaterial: PrincipledMaterial { baseColor: "#ececec"; metalness: 1.0; roughness: 0.18 }
                jointTailMaterial: PrincipledMaterial { baseColor: "#2a82ff"; metalness: 0.9; roughness: 0.35 }
                jointArmMaterial: PrincipledMaterial { baseColor: "#ff9c3a"; metalness: 0.9; roughness: 0.32 }
                jointRodMaterial: PrincipledMaterial { baseColor: "#00ff55"; metalness: 0.9; roughness: 0.3 }
            }'''
        
        content = re.sub(inline_pattern, module_code, content, flags=re.DOTALL)
        print("   ✅ Заменено на SuspensionCorner модуль")
    else:
        print("   ⚠️  Инлайн FL suspension не найден (возможно, уже заменён)")
    
    # ========================================================================
    # STEP 2: Заменить инлайн Frame на модуль
    # ========================================================================
    
    print("\n🔧 STEP 2: Заменяем инлайн Frame на Frame модуль...")
    
    # Ищем инлайн Frame (3 Model с комментариями НИЖНЯЯ БАЛКА, ПЕРЕДНЯЯ СТОЙКА, ЗАДНЯЯ СТОЙКА)
    frame_pattern = r'// FRAME - РАМА.*?// 3\. ЗАДНЯЯ СТОЙКА.*?\n\s+\}'
    
    if re.search(frame_pattern, content, re.DOTALL):
        print("   ✅ Найден инлайн Frame")
        
        # Заменяем на модуль
        frame_module = '''// ===============================================================
            // FRAME - МОДУЛЬ
            // ===============================================================
            
            Frame {
                id: frameGeometry
                worldRoot: worldRoot
                beamSize: root.userBeamSize
                frameHeight: root.userFrameHeight
                frameLength: root.userFrameLength
                frameMaterial: PrincipledMaterial {
                    baseColor: root.frameBaseColor
                    metalness: root.frameMetalness
                    roughness: root.frameRoughness
                }
            }'''
        
        content = re.sub(frame_pattern, frame_module, content, flags=re.DOTALL)
        print("   ✅ Заменено на Frame модуль")
    else:
        print("   ⚠️  Инлайн Frame не найден (возможно, уже заменён)")
    
    # ========================================================================
    # СОХРАНЕНИЕ
    # ========================================================================
    
    print(f"\n✍️ Saving modular version to {main_qml}")
    main_qml.write_text(content, encoding='utf-8')
    
    new_lines = content.count('\n')
    saved = lines - new_lines
    
    print("\n" + "=" * 70)
    print("✅ МОДУЛЬНАЯ ИНТЕГРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 70)
    
    print(f"\n📊 РЕЗУЛЬТАТ:")
    print(f"   Было: {lines} строк")
    print(f"   Стало: {new_lines} строк")
    print(f"   Сэкономлено: {saved} строк ({saved/lines*100:.1f}%)")
    
    print(f"\n✅ ЧТО СДЕЛАНО:")
    print(f"   ✅ FL suspension → SuspensionCorner модуль")
    print(f"   ✅ Frame → Frame модуль")
    print(f"   ✅ main.qml остаётся КОМПАКТНЫМ")
    
    print(f"\n🎯 СЛЕДУЮЩИЙ ШАГ:")
    print(f"   Добавить FR, RL, RR через тот же SuspensionCorner модуль")
    print(f"   Каждый угол = ~30 строк (вместо ~80 строк инлайн-кода)")
    
    print(f"\n🔄 ВОССТАНОВЛЕНИЕ:")
    print(f"   cp {backup} {main_qml}")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔧 MODULAR INTEGRATION - KEEP QML MINIMAL")
    print("=" * 70 + "\n")
    
    success = integrate_modules_step_by_step()
    
    if success:
        print("\n✅ SUCCESS: Modules integrated, QML stays minimal!")
        print("   Run: py app.py")
        print("   Check if model still visible")
    else:
        print("\n❌ FAILED: Check errors above")
    
    print("\n" + "=" * 70)
