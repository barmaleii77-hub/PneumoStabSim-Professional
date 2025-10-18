#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_camera_overlay.py
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Перемещает CameraController из View3D наружу как overlay
"""
import re
from pathlib import Path

def fix_camera_controller_placement():
    """Исправляет размещение CameraController в main.qml"""
    main_qml = Path("assets/qml/main.qml")
    
    if not main_qml.exists():
        print("❌ Файл main.qml не найден!")
        return False
    
    print("📖 Читаем main.qml...")
    content = main_qml.read_text(encoding='utf-8')
    
    # Паттерн для поиска CameraController внутри View3D
    # Ищем блок от "CameraController {" до закрывающей "}"
    camera_pattern = re.compile(
        r'(\s+)(CameraController\s*\{.*?'  # Начало CameraController
        r'Component\.onCompleted:\s*\{.*?'  # Component.onCompleted блок
        r'console\.log\("📷 Camera initialized.*?\)\s*'  # console.log
        r'\}\s*'  # закрытие onCompleted
        r'\})',  # закрытие CameraController
        re.DOTALL | re.MULTILINE
    )
    
    match = camera_pattern.search(content)
    
    if not match:
        print("❌ Не найден CameraController блок!")
        return False
    
    indent = match.group(1)
    camera_block = match.group(2)
    
    print(f"✅ Найден CameraController на позиции {match.start()}")
    print(f"   Отступ: {len(indent)} пробелов")
    
    # Удаляем CameraController из View3D
    content_without_camera = content[:match.start()] + content[match.end():]
    
    # Находим конец View3D
    view3d_end_pattern = re.compile(
        r'(    \}  // конец View3D\n'  # комментарий после закрытия View3D
        r'|'
        r'    \}\s*//\s*View3D\n'  # альтернативный формат
        r'|'
        r'(\s{4}\})\n\s*\n\s*//\s*===.*MOUSE CONTROLS)',  # или секция после View3D
        re.MULTILINE
    )
    
    view3d_end = view3d_end_pattern.search(content_without_camera)
    
    if not view3d_end:
        print("⚠️ Не найден конец View3D, используем альтернативный поиск...")
        # Ищем закрытие View3D по количеству открывающих/закрывающих скобок
        view3d_start = content_without_camera.find("View3D {")
        if view3d_start == -1:
            print("❌ View3D не найден!")
            return False
        
        # Подсчитываем скобки для определения конца View3D
        depth = 0
        pos = view3d_start
        while pos < len(content_without_camera):
            if content_without_camera[pos] == '{':
                depth += 1
            elif content_without_camera[pos] == '}':
                depth -= 1
                if depth == 0:
                    view3d_end_pos = pos + 1
                    break
            pos += 1
        else:
            print("❌ Не найдена закрывающая скобка View3D!")
            return False
    else:
        view3d_end_pos = view3d_end.end()
    
    print(f"✅ Найден конец View3D на позиции {view3d_end_pos}")
    
    # Формируем новый CameraController блок с правильным размещением
    new_camera_block = f"""
    // ===============================================================
    // ✅ CRITICAL FIX: CAMERA CONTROLLER AS OVERLAY
    // ===============================================================
    
    // ✅ CameraController ПОВЕРХ View3D для перехвата событий мыши!
    CameraController {{
        id: cameraController
        
        // ✅ КРИТИЧНО: Заполняет весь экран поверх View3D!
        anchors.fill: parent
        z: 1000  // поверх всего для обработки мыши
        
        worldRoot: worldRoot
        view3d: view3d
        
        // ✅ Bind to geometry for pivot/fit calculations
        frameLength: root.userFrameLength
        frameHeight: root.userFrameHeight
        beamSize: root.userBeamSize
        trackWidth: root.userTrackWidth
        
        // ✅ Bind to TAA for motion detection
        taaMotionAdaptive: root.taaMotionAdaptive
        
        // ✅ Callback for animation toggle
        onToggleAnimation: {{
            root.isRunning = !root.isRunning
        }}
        
        // ✅ Initial camera state
        Component.onCompleted: {{
            // Sync camera settings from root to CameraState
            state.fov = root.cameraFov
            state.nearPlane = root.cameraNear
            state.farPlane = root.cameraFar
            state.speed = root.cameraSpeed
            state.autoRotate = root.autoRotate
            state.autoRotateSpeed = root.autoRotateSpeed
            
            console.log("📷 Camera initialized: distance =", state.distance, "yaw =", state.yawDeg, "pitch =", state.pitchDeg)
            console.log("🖱️ Mouse controls: OVERLAY MODE ACTIVE (z=1000)")
        }}
    }}
"""
    
    # Вставляем CameraController после View3D
    fixed_content = (
        content_without_camera[:view3d_end_pos] +
        new_camera_block +
        content_without_camera[view3d_end_pos:]
    )
    
    # Сохраняем изменения
    print("\n💾 Сохраняем изменения...")
    main_qml.write_text(fixed_content, encoding='utf-8')
    
    print("\n✅ ИСПРАВЛЕНИЕ ПРИМЕНЕНО!")
    print("\n📊 РЕЗУЛЬТАТ:")
    print("   ✅ CameraController перемещён ИЗ View3D")
    print("   ✅ CameraController теперь OVERLAY (z=1000)")
    print("   ✅ anchors.fill: parent для полного охвата экрана")
    print("   ✅ MouseArea внутри CameraController теперь работает!")
    
    print("\n🎯 ОЖИДАЕМОЕ ПОВЕДЕНИЕ:")
    print("   🖱️ ЛКМ + drag → орбитальное вращение")
    print("   🖱️ ПКМ + drag → панорамирование")
    print("   🖱️ Колесо → зум")
    print("   ⌨️  R → сброс камеры")
    print("   ⌨️  F → автофит")
    
    return True

if __name__ == "__main__":
    print("═" * 60)
    print("🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: CameraController Overlay")
    print("═" * 60)
    
    success = fix_camera_controller_placement()
    
    if success:
        print("\n" + "═" * 60)
        print("✅ ГОТОВО! Запустите приложение для проверки.")
        print("═" * 60)
    else:
        print("\n" + "═" * 60)
        print("❌ ОШИБКА! Проверьте структуру main.qml вручную.")
        print("═" * 60)
