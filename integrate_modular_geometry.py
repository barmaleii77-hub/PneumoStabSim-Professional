#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для интеграции модульных компонентов геометрии в main.qml
ЗАВЕРШАЕТ РЕФАКТОРИНГ: добавляет Frame, SuspensionCorner, Lights в worldRoot
"""

import re
from pathlib import Path


def integrate_geometry_modules():
    """Добавляет модульные компоненты в worldRoot в main.qml"""

    main_qml = Path("assets/qml/main.qml")

    if not main_qml.exists():
        print(f"❌ ERROR: {main_qml} not found!")
        return False

    print(f"📄 Reading {main_qml}...")
    content = main_qml.read_text(encoding="utf-8")

    # ✅ STEP 1: Найти worldRoot (пустой Node)
    pattern = r"(Node\s*\{\s*id:\s*worldRoot\s*\})"

    if not re.search(pattern, content):
        print("❌ ERROR: worldRoot not found in main.qml!")
        return False

    print("✅ Found worldRoot")

    # ✅ STEP 2: Создать интеграционный блок
    geometry_integration = """Node {
            id: worldRoot

            // ===============================================================
            // ✅ FRAME GEOMETRY - U-shaped frame
            // ===============================================================

            Frame {
                id: frameGeometry
                worldRoot: worldRoot
                beamSize: root.userBeamSize
                frameHeight: root.userFrameHeight
                frameLength: root.userFrameLength
                frameMaterial: materials.frameMat
            }

            // ===============================================================
            // ✅ LIGHTING SYSTEM - 3-point + accent
            // ===============================================================

            DirectionalLights {
                id: directionalLights
                worldRoot: worldRoot
                cameraRig: cameraController.rig

                shadowsEnabled: root.shadowsEnabled
                shadowResolution: root.shadowResolution
                shadowFilterSamples: root.shadowFilterSamples
                shadowBias: root.shadowBias
                shadowFactor: root.shadowFactor

                keyLightBrightness: root.keyLightBrightness
                keyLightColor: root.keyLightColor
                keyLightAngleX: root.keyLightAngleX
                keyLightAngleY: root.keyLightAngleY
                keyLightCastsShadow: root.keyLightCastsShadow
                keyLightBindToCamera: root.keyLightBindToCamera
                keyLightPosX: root.keyLightPosX
                keyLightPosY: root.keyLightPosY

                fillLightBrightness: root.fillLightBrightness
                fillLightColor: root.fillLightColor
                fillLightCastsShadow: root.fillLightCastsShadow
                fillLightBindToCamera: root.fillLightBindToCamera
                fillLightPosX: root.fillLightPosX
                fillLightPosY: root.fillLightPosY

                rimLightBrightness: root.rimLightBrightness
                rimLightColor: root.rimLightColor
                rimLightCastsShadow: root.rimLightCastsShadow
                rimLightBindToCamera: root.rimLightBindToCamera
                rimLightPosX: root.rimLightPosX
                rimLightPosY: root.rimLightPosY
            }

            PointLights {
                id: pointLights
                worldRoot: worldRoot
                cameraRig: cameraController.rig

                pointLightBrightness: root.pointLightBrightness
                pointLightColor: root.pointLightColor
                pointLightX: root.pointLightX
                pointLightY: root.pointLightY
                pointLightRange: root.pointLightRange
                pointLightCastsShadow: root.pointLightCastsShadow
                pointLightBindToCamera: root.pointLightBindToCamera
            }

            // ===============================================================
            // ✅ SUSPENSION CORNERS - FL, FR, RL, RR
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

                // Materials
                leverMaterial: materials.leverMat
                tailRodMaterial: materials.tailRodMat
                cylinderMaterial: materials.cylinderMat
                pistonBodyMaterial: materials.pistonBodyMat
                pistonRodMaterial: materials.pistonRodMat
                jointTailMaterial: materials.jointTailMat
                jointArmMaterial: materials.jointArmMat
                jointRodMaterial: materials.jointRodMat
            }

            SuspensionCorner {
                id: frCorner

                j_arm: Qt.vector3d(
                    root.userTrackWidth/2,
                    root.userBeamSize,
                    root.userFrameToPivot
                )
                j_tail: Qt.vector3d(
                    root.userTrackWidth/2,
                    root.userBeamSize + root.userFrameHeight,
                    root.userFrameToPivot
                )

                leverAngle: root.fr_angle
                pistonPositionFromPython: root.userPistonPositionFR

                leverLength: root.userLeverLength
                rodPosition: root.userRodPosition
                cylinderLength: root.userCylinderLength
                boreHead: root.userBoreHead
                rodDiameter: root.userRodDiameter
                pistonThickness: root.userPistonThickness
                pistonRodLength: root.userPistonRodLength
                cylinderSegments: root.cylinderSegments
                cylinderRings: root.cylinderRings

                leverMaterial: materials.leverMat
                tailRodMaterial: materials.tailRodMat
                cylinderMaterial: materials.cylinderMat
                pistonBodyMaterial: materials.pistonBodyMat
                pistonRodMaterial: materials.pistonRodMat
                jointTailMaterial: materials.jointTailMat
                jointArmMaterial: materials.jointArmMat
                jointRodMaterial: materials.jointRodMat
            }

            SuspensionCorner {
                id: rlCorner

                j_arm: Qt.vector3d(
                    -root.userTrackWidth/2,
                    root.userBeamSize,
                    root.userFrameLength - root.userFrameToPivot
                )
                j_tail: Qt.vector3d(
                    -root.userTrackWidth/2,
                    root.userBeamSize + root.userFrameHeight,
                    root.userFrameLength - root.userFrameToPivot
                )

                leverAngle: root.rl_angle
                pistonPositionFromPython: root.userPistonPositionRL

                leverLength: root.userLeverLength
                rodPosition: root.userRodPosition
                cylinderLength: root.userCylinderLength
                boreHead: root.userBoreHead
                rodDiameter: root.userRodDiameter
                pistonThickness: root.userPistonThickness
                pistonRodLength: root.userPistonRodLength
                cylinderSegments: root.cylinderSegments
                cylinderRings: root.cylinderRings

                leverMaterial: materials.leverMat
                tailRodMaterial: materials.tailRodMat
                cylinderMaterial: materials.cylinderMat
                pistonBodyMaterial: materials.pistonBodyMat
                pistonRodMaterial: materials.pistonRodMat
                jointTailMaterial: materials.jointTailMat
                jointArmMaterial: materials.jointArmMat
                jointRodMaterial: materials.jointRodMat
            }

            SuspensionCorner {
                id: rrCorner

                j_arm: Qt.vector3d(
                    root.userTrackWidth/2,
                    root.userBeamSize,
                    root.userFrameLength - root.userFrameToPivot
                )
                j_tail: Qt.vector3d(
                    root.userTrackWidth/2,
                    root.userBeamSize + root.userFrameHeight,
                    root.userFrameLength - root.userFrameToPivot
                )

                leverAngle: root.rr_angle
                pistonPositionFromPython: root.userPistonPositionRR

                leverLength: root.userLeverLength
                rodPosition: root.userRodPosition
                cylinderLength: root.userCylinderLength
                boreHead: root.userBoreHead
                rodDiameter: root.userRodDiameter
                pistonThickness: root.userPistonThickness
                pistonRodLength: root.userPistonRodLength
                cylinderSegments: root.cylinderSegments
                cylinderRings: root.cylinderRings

                leverMaterial: materials.leverMat
                tailRodMaterial: materials.tailRodMat
                cylinderMaterial: materials.cylinderMat
                pistonBodyMaterial: materials.pistonBodyMat
                pistonRodMaterial: materials.pistonRodMat
                jointTailMaterial: materials.jointTailMat
                jointArmMaterial: materials.jointArmMat
                jointRodMaterial: materials.jointRodMat
            }
        }"""

    # ✅ STEP 3: Заменить пустой worldRoot на заполненный
    new_content = re.sub(pattern, geometry_integration, content)

    # ✅ STEP 4: Сохранить
    backup = main_qml.with_suffix(".qml.backup_geometry")
    print(f"💾 Creating backup: {backup}")
    backup.write_text(content, encoding="utf-8")

    print(f"✍️ Writing integrated version to {main_qml}")
    main_qml.write_text(new_content, encoding="utf-8")

    print("\n" + "=" * 60)
    print("✅ GEOMETRY INTEGRATION COMPLETE!")
    print("=" * 60)
    print("\n📊 CHANGES:")
    print("  ✅ Frame component added to worldRoot")
    print("  ✅ DirectionalLights added (Key, Fill, Rim)")
    print("  ✅ PointLights added (Accent)")
    print("  ✅ 4 SuspensionCorner instances added (FL, FR, RL, RR)")
    print("\n🎯 RESULT:")
    print("  - Geometry will now be VISIBLE in the scene!")
    print("  - Lighting will illuminate the model")
    print("  - 4 suspension corners will animate")
    print("\n🔄 NEXT STEPS:")
    print("  1. Run: py app.py")
    print("  2. Check if model is visible")
    print("  3. If errors occur, check console output")
    print("\n💡 TIP: Backup saved at:", backup.name)
    print("=" * 60)

    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 STARTING GEOMETRY MODULE INTEGRATION")
    print("=" * 60 + "\n")

    success = integrate_geometry_modules()

    if success:
        print("\n✅ SUCCESS: Refactoring COMPLETE!")
        print("   Run the app to see the model!")
    else:
        print("\n❌ FAILED: Check errors above")

    print("\n" + "=" * 60)
