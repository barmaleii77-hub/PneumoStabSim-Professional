#!/usr/bin/env python3
"""
Скрипт для очистки main.qml от лишнего кода
ПРОБЛЕМА: Фон вращается, модель не видна
РЕШЕНИЕ: Оставить только рабочую геометрию, убрать лишнее
"""

from pathlib import Path


def cleanup_main_qml():
    """Очищает main.qml от избыточного кода"""

    main_qml = Path("assets/qml/main.qml")

    if not main_qml.exists():
        print(f"❌ ERROR: {main_qml} not found!")
        return False

    print("=" * 70)
    print("🧹 ОЧИСТКА main.qml ОТ ЛИШНЕГО КОДА")
    print("=" * 70)

    # Создаём backup
    backup = main_qml.with_suffix(".qml.backup_before_cleanup")
    print(f"\n💾 Creating backup: {backup}")

    with open(main_qml, encoding="utf-8") as f:
        content = f.read()

    backup.write_text(content, encoding="utf-8")

    # ========================================================================
    # КРИТИЧЕСКИЕ ПРОБЛЕМЫ В КОДЕ
    # ========================================================================

    print("\n🔍 АНАЛИЗ ПРОБЛЕМ:")

    # 1. Проверяем наличие worldRoot
    if "id: worldRoot" not in content:
        print("  ❌ worldRoot НЕ НАЙДЕН!")
        return False
    else:
        print("  ✅ worldRoot найден")

    # 2. Проверяем импорты модулей
    required_imports = ['import "geometry"', 'import "lighting"', 'import "scene"']
    for imp in required_imports:
        if imp in content:
            print(f"  ✅ {imp}")
        else:
            print(f"  ❌ ОТСУТСТВУЕТ: {imp}")

    # 3. Проверяем использование компонентов
    components = [
        "Frame {",
        "SuspensionCorner {",
        "DirectionalLights {",
        "PointLights {",
    ]
    for comp in components:
        if comp in content:
            print(f"  ✅ Используется: {comp}")
        else:
            print(f"  ⚠️  НЕ используется: {comp}")

    # ========================================================================
    # СОЗДАЁМ МИНИМАЛЬНУЮ РАБОЧУЮ ВЕРСИЮ
    # ========================================================================

    print("\n🔧 СОЗДАНИЕ МИНИМАЛЬНОЙ ВЕРСИИ...")

    # Читаем шаблон минимального main.qml
    minimal_template = """import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick.Controls
import "components"
import "core"
import "camera"
import "lighting"
import "scene"
import "geometry"

/*
 * PneumoStabSim - MINIMAL WORKING VERSION
 * ✅ ТОЛЬКО РАБОЧАЯ ГЕОМЕТРИЯ
 * ❌ ВЕСЬ ЛИШНИЙ КОД УДАЛЁН
 */
Item {
    id: root
    anchors.fill: parent

    // ===============================================================
    // МИНИМАЛЬНЫЕ СВОЙСТВА
    // ===============================================================

    // Geometry parameters
    property real userBeamSize: 120
    property real userFrameHeight: 650
    property real userFrameLength: 3200
    property real userLeverLength: 800
    property real userCylinderLength: 500
    property real userTrackWidth: 1600
    property real userFrameToPivot: 600
    property real userRodPosition: 0.6
    property real userBoreHead: 80
    property real userRodDiameter: 35
    property real userPistonThickness: 25
    property real userPistonRodLength: 200

    // Animation
    property real animationTime: 0.0
    property bool isRunning: false
    property real userAmplitude: 8.0
    property real userFrequency: 1.0

    property real fl_angle: 0.0
    property real fr_angle: 0.0
    property real rl_angle: 0.0
    property real rr_angle: 0.0

    property real userPistonPositionFL: 250.0
    property real userPistonPositionFR: 250.0
    property real userPistonPositionRL: 250.0
    property real userPistonPositionRR: 250.0

    // Camera
    property real cameraFov: 60.0
    property real cameraNear: 10.0
    property real cameraFar: 50000.0

    // Lighting
    property real keyLightBrightness: 1.2
    property color keyLightColor: "#ffffff"
    property real keyLightAngleX: -35
    property real keyLightAngleY: -40

    // Materials
    property color frameBaseColor: "#c53030"
    property real frameMetalness: 0.85
    property real frameRoughness: 0.35

    property color leverBaseColor: "#9ea4ab"
    property real leverMetalness: 1.0
    property real leverRoughness: 0.28

    property color cylinderBaseColor: "#e1f5ff"
    property real cylinderTransmission: 1.0
    property real cylinderIor: 1.52

    property color pistonBodyBaseColor: "#ff3c6e"
    property real pistonBodyMetalness: 1.0
    property real pistonBodyRoughness: 0.26

    // Environment
    property bool iblEnabled: true
    property bool iblLightingEnabled: true
    property bool iblBackgroundEnabled: true
    property real iblRotationDeg: 0.0
    property real iblIntensity: 1.0
    property color backgroundColor: "#1f242c"

    // Quality
    property bool shadowsEnabled: true
    property string shadowResolution: "2048"
    property int cylinderSegments: 32
    property int cylinderRings: 4

    // ===============================================================
    // VIEW3D - 3D СЦЕНА
    // ===============================================================

    View3D {
        id: view3d
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: root.backgroundColor

            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        // ===============================================================
        // WORLD ROOT - СЦЕНА
        // ===============================================================

        Node {
            id: worldRoot

            // ===============================================================
            // КАМЕРА
            // ===============================================================

            Node {
                id: cameraRig
                position: Qt.vector3d(0, 400, 1600)

                PerspectiveCamera {
                    id: camera
                    position: Qt.vector3d(0, 0, 4000)
                    eulerRotation: Qt.vector3d(-20, 0, 0)
                    fieldOfView: root.cameraFov
                    clipNear: root.cameraNear
                    clipFar: root.cameraFar
                }
            }

            // ===============================================================
            // ОСВЕЩЕНИЕ (ПРОСТОЕ)
            // ===============================================================

            DirectionalLight {
                eulerRotation.x: root.keyLightAngleX
                eulerRotation.y: root.keyLightAngleY
                brightness: root.keyLightBrightness
                color: root.keyLightColor
                castsShadow: root.shadowsEnabled
            }

            DirectionalLight {
                eulerRotation.x: -60
                eulerRotation.y: 135
                brightness: 0.7
                color: "#dfe7ff"
            }

            // ===============================================================
            // FRAME - РАМА (ПРЯМОЕ ОБЪЯВЛЕНИЕ)
            // ===============================================================

            // 1. НИЖНЯЯ БАЛКА
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, root.userBeamSize/2, root.userFrameLength/2)
                scale: Qt.vector3d(root.userBeamSize/100, root.userBeamSize/100, root.userFrameLength/100)

                materials: PrincipledMaterial {
                    baseColor: root.frameBaseColor
                    metalness: root.frameMetalness
                    roughness: root.frameRoughness
                }
            }

            // 2. ПЕРЕДНЯЯ СТОЙКА
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, root.userBeamSize + root.userFrameHeight/2, root.userBeamSize/2)
                scale: Qt.vector3d(root.userBeamSize/100, root.userFrameHeight/100, root.userBeamSize/100)

                materials: PrincipledMaterial {
                    baseColor: root.frameBaseColor
                    metalness: root.frameMetalness
                    roughness: root.frameRoughness
                }
            }

            // 3. ЗАДНЯЯ СТОЙКА
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, root.userBeamSize + root.userFrameHeight/2, root.userFrameLength - root.userBeamSize/2)
                scale: Qt.vector3d(root.userBeamSize/100, root.userFrameHeight/100, root.userBeamSize/100)

                materials: PrincipledMaterial {
                    baseColor: root.frameBaseColor
                    metalness: root.frameMetalness
                    roughness: root.frameRoughness
                }
            }

            // ===============================================================
            // SUSPENSION CORNER FL (ПРЯМОЕ ОБЪЯВЛЕНИЕ)
            // ===============================================================

            Node {
                id: flSuspension

                property vector3d j_arm: Qt.vector3d(
                    -root.userTrackWidth/2,
                    root.userBeamSize,
                    root.userFrameToPivot
                )

                property vector3d j_tail: Qt.vector3d(
                    -root.userTrackWidth/2,
                    root.userBeamSize + root.userFrameHeight,
                    root.userFrameToPivot
                )

                property real baseAngle: 180  // Left side
                property real totalAngle: baseAngle + root.fl_angle

                property vector3d j_rod: Qt.vector3d(
                    j_arm.x + (root.userLeverLength * root.userRodPosition) * Math.cos(totalAngle * Math.PI / 180),
                    j_arm.y + (root.userLeverLength * root.userRodPosition) * Math.sin(totalAngle * Math.PI / 180),
                    j_arm.z
                )

                // LEVER (рычаг)
                Model {
                    source: "#Cube"
                    position: Qt.vector3d(
                        flSuspension.j_arm.x + (root.userLeverLength/2) * Math.cos(flSuspension.totalAngle * Math.PI / 180),
                        flSuspension.j_arm.y + (root.userLeverLength/2) * Math.sin(flSuspension.totalAngle * Math.PI / 180),
                        flSuspension.j_arm.z
                    )
                    scale: Qt.vector3d(root.userLeverLength/100, 0.8, 0.8)
                    eulerRotation: Qt.vector3d(0, 0, flSuspension.totalAngle)

                    materials: PrincipledMaterial {
                        baseColor: root.leverBaseColor
                        metalness: root.leverMetalness
                        roughness: root.leverRoughness
                    }
                }

                // ARM JOINT (оранжевый шарнир)
                Model {
                    source: "#Cylinder"
                    position: flSuspension.j_arm
                    scale: Qt.vector3d(1.0, 2.0, 1.0)
                    eulerRotation: Qt.vector3d(90, 0, 0)

                    materials: PrincipledMaterial {
                        baseColor: "#ff9c3a"
                        metalness: 0.9
                        roughness: 0.32
                    }
                }

                // TAIL JOINT (синий шарнир)
                Model {
                    source: "#Cylinder"
                    position: flSuspension.j_tail
                    scale: Qt.vector3d(1.2, 2.4, 1.2)
                    eulerRotation: Qt.vector3d(90, 0, 0)

                    materials: PrincipledMaterial {
                        baseColor: "#2a82ff"
                        metalness: 0.9
                        roughness: 0.35
                    }
                }

                // ROD JOINT (зелёный шарнир)
                Model {
                    source: "#Cylinder"
                    position: flSuspension.j_rod
                    scale: Qt.vector3d(0.8, 1.6, 0.8)
                    eulerRotation: Qt.vector3d(90, 0, 0)

                    materials: PrincipledMaterial {
                        baseColor: "#00ff55"
                        metalness: 0.9
                        roughness: 0.3
                    }
                }
            }

        }  // end worldRoot
    }  // end View3D

    // ===============================================================
    // INFO PANEL
    // ===============================================================

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 400
        height: 150
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 8

        Column {
            anchors.centerIn: parent
            spacing: 6

            Text {
                text: "PneumoStabSim - MINIMAL VERSION"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true
            }

            Text {
                text: "✅ Frame visible (3 beams)"
                color: "#00ff88"
                font.pixelSize: 11
            }

            Text {
                text: "✅ FL suspension (1 lever + 3 joints)"
                color: "#00ff88"
                font.pixelSize: 11
            }

            Text {
                text: "🎮 Mouse: LMB-rotate | Wheel-zoom"
                color: "#aaddff"
                font.pixelSize: 10
            }
        }
    }

    // ===============================================================
    // MOUSE CONTROLS (ПРОСТЫЕ)
    // ===============================================================

    MouseArea {
        anchors.fill: parent

        property real lastX: 0
        property real lastY: 0

        onWheel: (wheel) => {
            var delta = wheel.angleDelta.y
            var factor = delta > 0 ? 0.9 : 1.1

            if (camera.position.z * factor > 500 && camera.position.z * factor < 20000) {
                camera.position.z *= factor
            }
        }
    }

    Component.onCompleted: {
        console.log("=" * 60)
        console.log("🚀 MINIMAL MAIN.QML LOADED")
        console.log("=" * 60)
        console.log("✅ Frame: 3 beams (U-shape)")
        console.log("✅ FL suspension: 1 lever + 3 joints")
        console.log("✅ Camera: " + camera.position)
        console.log("✅ Lighting: 2 directional lights")
        console.log("=" * 60)
    }
}
"""

    # Сохраняем минимальную версию
    print(f"\n✍️ Writing MINIMAL version to {main_qml}")
    main_qml.write_text(minimal_template, encoding="utf-8")

    print("\n" + "=" * 70)
    print("✅ ОЧИСТКА ЗАВЕРШЕНА!")
    print("=" * 70)

    print("\n📊 ЧТО БЫЛО СДЕЛАНО:")
    print("  ✅ Создан backup: main.qml.backup_before_cleanup")
    print("  ✅ Удалён весь лишний код")
    print("  ✅ Оставлена ТОЛЬКО РАБОЧАЯ геометрия:")
    print("     - 3 балки рамы (U-shape)")
    print("     - 1 рычаг подвески (FL)")
    print("     - 3 шарнира (синий, оранжевый, зелёный)")
    print("     - Простая камера")
    print("     - Простое освещение")

    print("\n🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:")
    print("  1. Запустите: py app.py")
    print("  2. Вы ДОЛЖНЫ УВИДЕТЬ:")
    print("     ✅ U-образную раму (красную)")
    print("     ✅ 1 рычаг слева (серый)")
    print("     ✅ 3 цветных шарнира")
    print("  3. Колесо мыши - зум (должен работать)")

    print("\n💡 ЕСЛИ НЕ ВИДНО:")
    print("  - Проверьте консоль QML на ошибки")
    print("  - Попробуйте zoom out (scroll down)")
    print("  - Сообщите о проблеме")

    print("\n🔄 ВОССТАНОВЛЕНИЕ:")
    print(f"  cp {backup} {main_qml}")
    print("=" * 70)

    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧹 CLEANUP main.qml - REMOVE EXCESS CODE")
    print("=" * 70 + "\n")

    success = cleanup_main_qml()

    if success:
        print("\n✅ SUCCESS: main.qml cleaned up!")
        print("   Run: py app.py")
        print("   You SHOULD see: Frame + 1 lever + 3 joints")
    else:
        print("\n❌ FAILED: Check errors above")

    print("\n" + "=" * 70)
