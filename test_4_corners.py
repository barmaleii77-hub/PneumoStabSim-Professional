#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test 4-corner suspension system with all components
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl
from pathlib import Path

# Создаём QML для 4 углов напрямую в коде
qml_content = """
import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    property real animationTime: 0.0
    property real animationSpeed: 0.8

    // Углы для каждого угла (разные фазы)
    property real fl_angle: 8 * Math.sin(animationTime)
    property real fr_angle: 8 * Math.sin(animationTime + Math.PI/4)
    property real rl_angle: 8 * Math.sin(animationTime + Math.PI/2)
    property real rr_angle: 8 * Math.sin(animationTime + 3*Math.PI/4)

    Timer {
        running: true
        interval: 33  // 30 FPS
        repeat: true
        onTriggered: {
            animationTime += animationSpeed * 0.033
        }
    }

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#f0f0f0"
        antialiasingMode: SceneEnvironment.MSAA
    }

    Node {
        id: rig
        position: Qt.vector3d(0, 325, 0)
        eulerRotation: Qt.vector3d(-25, 35, 0)

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 4000)
            fieldOfView: 45
        }
    }

    DirectionalLight {
        eulerRotation.x: -30
        eulerRotation.y: -45
        brightness: 2.5
    }

    // Маркер центра
    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        scale: Qt.vector3d(3.0, 3.0, 3.0)
        materials: PrincipledMaterial { baseColor: "#ffff00"; lighting: PrincipledMaterial.NoLighting }
    }

    // U-РАМА
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, 60, 0)
        scale: Qt.vector3d(1.2, 1.2, 20)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, 385, -1000)
        scale: Qt.vector3d(1.2, 6.5, 1.2)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, 385, 1000)
        scale: Qt.vector3d(1.2, 6.5, 1.2)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // КОМПОНЕНТ ПОДВЕСКИ
    component SuspensionCorner: Node {
        property vector3d j_arm
        property vector3d j_tail  
        property vector3d j_rod
        property real leverAngle
        
        // РЫЧАГ (анимированный)
        Model {
            source: "#Cube"
            property real baseAngle: (j_arm.x < 0) ? 180 : 0
            property real totalAngle: baseAngle + leverAngle
            
            position: Qt.vector3d(j_arm.x + (315/2) * Math.cos(totalAngle * Math.PI / 180), 
                                 j_arm.y + (315/2) * Math.sin(totalAngle * Math.PI / 180), 
                                 j_arm.z)
            scale: Qt.vector3d(3.15, 0.8, 0.8)
            eulerRotation: Qt.vector3d(0, 0, totalAngle)
            materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
        }
        
        // ЦИЛИНДР (прозрачный корпус)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: 250
            property real lTailRod: 100
            
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            property vector3d cylStart: tailRodEnd
            property vector3d cylEnd: Qt.vector3d(
                cylStart.x + cylDirection.x * (lBody / cylDirectionLength),
                cylStart.y + cylDirection.y * (lBody / cylDirectionLength),
                cylStart.z
            )
            
            position: Qt.vector3d((cylStart.x + cylEnd.x)/2, (cylStart.y + cylEnd.y)/2, cylStart.z)
            scale: Qt.vector3d(1.2, lBody/100, 1.2)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylEnd.y - cylStart.y, cylEnd.x - cylStart.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.15; alphaMode: PrincipledMaterial.Blend }
        }
        
        // ПОРШЕНЬ (движущийся внутри цилиндра)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: 250
            property real lTailRod: 100
            property real pistonRatio: Math.max(0.0, Math.min(1.0, (leverAngle + 8) / 16))
            
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            property vector3d cylStart: tailRodEnd
            
            property vector3d pistonPos: Qt.vector3d(
                cylStart.x + cylDirection.x * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.y + cylDirection.y * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.z
            )
            
            position: pistonPos
            scale: Qt.vector3d(1.08, 0.2, 1.08)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ff0066"; metalness: 0.9; roughness: 0.1 }
        }
        
        // ШТОК (от поршня к рычагу)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: 250
            property real lTailRod: 100
            property real pistonRatio: Math.max(0.0, Math.min(1.0, (leverAngle + 8) / 16))
            
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            property vector3d cylStart: tailRodEnd
            
            property vector3d rodStart: Qt.vector3d(
                cylStart.x + cylDirection.x * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.y + cylDirection.y * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.z
            )
            
            position: Qt.vector3d((rodStart.x + j_rod.x)/2, (rodStart.y + j_rod.y)/2, j_rod.z)
            scale: Qt.vector3d(0.5, Math.hypot(j_rod.x - rodStart.x, j_rod.y - rodStart.y, 0)/100, 0.5)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - rodStart.y, j_rod.x - rodStart.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }
        }
        
        // ХВОСТОВИК (от цилиндра к раме)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lTailRod: 100
            
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            
            position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
            scale: Qt.vector3d(0.5, lTailRod/100, 0.5)
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(tailRodEnd.y - j_tail.y, tailRodEnd.x - j_tail.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }
        }
        
        // ШАРНИРЫ (круглые цилиндры по оси Z)
        
        // Шарнир цилиндра (синий)
        Model {
            source: "#Cylinder"
            position: j_tail
            scale: Qt.vector3d(1.2, 2.4, 1.2)
            eulerRotation: Qt.vector3d(90, 0, 0)
            materials: PrincipledMaterial { baseColor: "#0088ff"; metalness: 0.8; roughness: 0.2 }
        }
        
        // Шарнир рычага (оранжевый)
        Model {
            source: "#Cylinder"
            position: j_arm
            scale: Qt.vector3d(1.0, 2.0, 1.0)
            eulerRotation: Qt.vector3d(90, 0, 0)
            materials: PrincipledMaterial { baseColor: "#ff8800"; metalness: 0.8; roughness: 0.2 }
        }
        
        // Шарнир штока (зелёный)
        Model {
            source: "#Cylinder" 
            position: j_rod
            scale: Qt.vector3d(0.8, 1.6, 0.8)
            eulerRotation: Qt.vector3d(90, 0, 0)
            materials: PrincipledMaterial { baseColor: "#00ff44"; metalness: 0.7; roughness: 0.3 }
        }
    }

    // ЧЕТЫРЕ УГЛА ПОДВЕСКИ
    SuspensionCorner { 
        j_arm: Qt.vector3d(-150, 60, -1000)
        j_tail: Qt.vector3d(-100, 710, -1000)
        j_rod: Qt.vector3d(-150 + 315 * Math.cos((180 + fl_angle) * Math.PI / 180),
                           60 + 315 * Math.sin((180 + fl_angle) * Math.PI / 180), -1000)
        leverAngle: fl_angle
    }
    
    SuspensionCorner { 
        j_arm: Qt.vector3d(150, 60, -1000)
        j_tail: Qt.vector3d(100, 710, -1000)
        j_rod: Qt.vector3d(150 + 315 * Math.cos((0 + fr_angle) * Math.PI / 180),
                           60 + 315 * Math.sin((0 + fr_angle) * Math.PI / 180), -1000)
        leverAngle: fr_angle
    }
    
    SuspensionCorner { 
        j_arm: Qt.vector3d(-150, 60, 1000)
        j_tail: Qt.vector3d(-100, 710, 1000)
        j_rod: Qt.vector3d(-150 + 315 * Math.cos((180 + rl_angle) * Math.PI / 180),
                           60 + 315 * Math.sin((180 + rl_angle) * Math.PI / 180), 1000)
        leverAngle: rl_angle
    }
    
    SuspensionCorner { 
        j_arm: Qt.vector3d(150, 60, 1000)
        j_tail: Qt.vector3d(100, 710, 1000)
        j_rod: Qt.vector3d(150 + 315 * Math.cos((0 + rr_angle) * Math.PI / 180),
                           60 + 315 * Math.sin((0 + rr_angle) * Math.PI / 180), 1000)
        leverAngle: rr_angle
    }

    // Маркеры шарниров рычагов
    Model { source: "#Sphere"; position: Qt.vector3d(-150, 60, -1000); scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: Qt.vector3d(150, 60, -1000); scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: Qt.vector3d(-150, 60, 1000); scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: Qt.vector3d(150, 60, 1000); scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }

    Component.onCompleted: {
        console.log("=== ?? ТЕСТ 4 УГЛОВ ПОДВЕСКИ ===")
        console.log("? FL, FR, RL, RR")
        console.log("? Все компоненты:")
        console.log("   - Рычаг (серый)")
        console.log("   - Цилиндр (прозрачный)")
        console.log("   - Поршень (розовый, анимированный)")
        console.log("   - Шток (серый, меняет длину)")
        console.log("   - Хвостовик (серый)")
        console.log("   - Шарниры: рычаг (оранжевый), шток (зелёный), цилиндр (синий)")
        console.log("? Готов!")
        view3d.forceActiveFocus()
    }
}
"""

def main():
    app = QApplication([])
    
    # Создаём временный QML файл
    temp_qml = Path("temp_4_corners.qml")
    with open(temp_qml, 'w', encoding='utf-8') as f:
        f.write(qml_content)
    
    # Создаём виджет
    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
    widget.setSource(QUrl.fromLocalFile(str(temp_qml.absolute())))
    
    if widget.status() == QQuickWidget.Status.Error:
        errors = widget.errors()
        error_msg = "\n".join(str(e) for e in errors)
        print(f"? QML ERRORS:\n{error_msg}")
        return 1
    
    widget.setWindowTitle("Тест 4 углов подвески - Все компоненты")
    widget.resize(1200, 800)
    widget.show()
    
    print("? 4-угловая схема загружена!")
    print("?? Видишь:")
    print("   - 4 рычага (серые, анимированные)")
    print("   - 4 цилиндра (прозрачные)")
    print("   - 4 поршня (розовые, движутся)")
    print("   - 4 штока (серые, меняют длину)")
    print("   - 4 хвостовика (серые)")
    print("   - 12 шарниров (оранжевые, зелёные, синие)")
    
    result = app.exec()
    
    # Удаляем временный файл
    temp_qml.unlink(missing_ok=True)
    
    return result

if __name__ == "__main__":
    sys.exit(main())