#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создание SharedMaterials.qml для централизованного управления материалами
"""

SHARED_MATERIALS_CONTENT = r"""import QtQuick
import QtQuick3D

/*
 * SharedMaterials - Централизованное управление материалами
 *
 * НАЗНАЧЕНИЕ:
 * - Единый источник всех PBR материалов для 3D сцены
 * - Избежание дублирования материалов
 * - Централизованное управление через Python bindings
 *
 * USAGE:
 * ```qml
 * SharedMaterials {
 *     id: sharedMaterials
 *     frameBaseColor: root.frameBaseColor
 *     // ... все остальные bindings
 * }
 *
 * Model {
 *     materials: [sharedMaterials.frameMaterial]
 * }
 * ```
 */
QtObject {
    id: root

    // ===============================================================
    // FRAME MATERIAL PROPERTIES
    // ===============================================================

    property color frameBaseColor: "#c53030"
    property real frameMetalness: 0.85
    property real frameRoughness: 0.35
    property real frameSpecularAmount: 1.0
    property real frameSpecularTint: 0.0
    property real frameClearcoat: 0.22
    property real frameClearcoatRoughness: 0.1
    property real frameTransmission: 0.0
    property real frameOpacity: 1.0
    property real frameIor: 1.5
    property real frameAttenuationDistance: 10000.0
    property color frameAttenuationColor: "#ffffff"
    property color frameEmissiveColor: "#000000"
    property real frameEmissiveIntensity: 0.0

    // ===============================================================
    // LEVER MATERIAL PROPERTIES
    // ===============================================================

    property color leverBaseColor: "#9ea4ab"
    property real leverMetalness: 1.0
    property real leverRoughness: 0.28
    property real leverSpecularAmount: 1.0
    property real leverSpecularTint: 0.0
    property real leverClearcoat: 0.3
    property real leverClearcoatRoughness: 0.08
    property real leverTransmission: 0.0
    property real leverOpacity: 1.0
    property real leverIor: 1.5
    property real leverAttenuationDistance: 10000.0
    property color leverAttenuationColor: "#ffffff"
    property color leverEmissiveColor: "#000000"
    property real leverEmissiveIntensity: 0.0

    // ===============================================================
    // TAIL ROD MATERIAL PROPERTIES
    // ===============================================================

    property color tailRodBaseColor: "#d5d9df"
    property real tailRodMetalness: 1.0
    property real tailRodRoughness: 0.3
    property real tailRodSpecularAmount: 1.0
    property real tailRodSpecularTint: 0.0
    property real tailRodClearcoat: 0.0
    property real tailRodClearcoatRoughness: 0.0
    property real tailRodTransmission: 0.0
    property real tailRodOpacity: 1.0
    property real tailRodIor: 1.5
    property real tailRodAttenuationDistance: 10000.0
    property color tailRodAttenuationColor: "#ffffff"
    property color tailRodEmissiveColor: "#000000"
    property real tailRodEmissiveIntensity: 0.0

    // ===============================================================
    // CYLINDER MATERIAL PROPERTIES (GLASS)
    // ===============================================================

    property color cylinderBaseColor: "#e1f5ff"
    property real cylinderMetalness: 0.0
    property real cylinderRoughness: 0.05
    property real cylinderSpecularAmount: 1.0
    property real cylinderSpecularTint: 0.0
    property real cylinderClearcoat: 0.0
    property real cylinderClearcoatRoughness: 0.0
    property real cylinderTransmission: 1.0
    property real cylinderOpacity: 1.0
    property real cylinderIor: 1.52
    property real cylinderAttenuationDistance: 1800.0
    property color cylinderAttenuationColor: "#b7e7ff"
    property color cylinderEmissiveColor: "#000000"
    property real cylinderEmissiveIntensity: 0.0

    // ===============================================================
    // PISTON BODY MATERIAL PROPERTIES
    // ===============================================================

    property color pistonBodyBaseColor: "#ff3c6e"
    property color pistonBodyWarningColor: "#ff5454"
    property real pistonBodyMetalness: 1.0
    property real pistonBodyRoughness: 0.26
    property real pistonBodySpecularAmount: 1.0
    property real pistonBodySpecularTint: 0.0
    property real pistonBodyClearcoat: 0.18
    property real pistonBodyClearcoatRoughness: 0.06
    property real pistonBodyTransmission: 0.0
    property real pistonBodyOpacity: 1.0
    property real pistonBodyIor: 1.5
    property real pistonBodyAttenuationDistance: 10000.0
    property color pistonBodyAttenuationColor: "#ffffff"
    property color pistonBodyEmissiveColor: "#000000"
    property real pistonBodyEmissiveIntensity: 0.0

    // ===============================================================
    // PISTON ROD MATERIAL PROPERTIES
    // ===============================================================

    property color pistonRodBaseColor: "#ececec"
    property color pistonRodWarningColor: "#ff2a2a"
    property real pistonRodMetalness: 1.0
    property real pistonRodRoughness: 0.18
    property real pistonRodSpecularAmount: 1.0
    property real pistonRodSpecularTint: 0.0
    property real pistonRodClearcoat: 0.12
    property real pistonRodClearcoatRoughness: 0.05
    property real pistonRodTransmission: 0.0
    property real pistonRodOpacity: 1.0
    property real pistonRodIor: 1.5
    property real pistonRodAttenuationDistance: 10000.0
    property color pistonRodAttenuationColor: "#ffffff"
    property color pistonRodEmissiveColor: "#000000"
    property real pistonRodEmissiveIntensity: 0.0

    // ===============================================================
    // JOINT TAIL MATERIAL PROPERTIES
    // ===============================================================

    property color jointTailBaseColor: "#2a82ff"
    property real jointTailMetalness: 0.9
    property real jointTailRoughness: 0.35
    property real jointTailSpecularAmount: 1.0
    property real jointTailSpecularTint: 0.0
    property real jointTailClearcoat: 0.1
    property real jointTailClearcoatRoughness: 0.08
    property real jointTailTransmission: 0.0
    property real jointTailOpacity: 1.0
    property real jointTailIor: 1.5
    property real jointTailAttenuationDistance: 10000.0
    property color jointTailAttenuationColor: "#ffffff"
    property color jointTailEmissiveColor: "#000000"
    property real jointTailEmissiveIntensity: 0.0

    // ===============================================================
    // JOINT ARM MATERIAL PROPERTIES
    // ===============================================================

    property color jointArmBaseColor: "#ff9c3a"
    property real jointArmMetalness: 0.9
    property real jointArmRoughness: 0.32
    property real jointArmSpecularAmount: 1.0
    property real jointArmSpecularTint: 0.0
    property real jointArmClearcoat: 0.12
    property real jointArmClearcoatRoughness: 0.08
    property real jointArmTransmission: 0.0
    property real jointArmOpacity: 1.0
    property real jointArmIor: 1.5
    property real jointArmAttenuationDistance: 10000.0
    property color jointArmAttenuationColor: "#ffffff"
    property color jointArmEmissiveColor: "#000000"
    property real jointArmEmissiveIntensity: 0.0

    // ===============================================================
    // JOINT ROD SPECIAL COLORS
    // ===============================================================

    property color jointRodOkColor: "#00ff55"
    property color jointRodErrorColor: "#ff0000"

    // ===============================================================
    // HELPER FUNCTION
    // ===============================================================

    function emissiveVector(color, intensity) {
        if (intensity === undefined)
            intensity = 1.0
        if (!color)
            return Qt.vector3d(0, 0, 0)
        return Qt.vector3d(color.r * intensity, color.g * intensity, color.b * intensity)
    }

    // ===============================================================
    // MATERIAL INSTANCES
    // ===============================================================

    readonly property PrincipledMaterial frameMaterial: PrincipledMaterial {
        baseColor: root.frameBaseColor
        metalness: root.frameMetalness
        roughness: root.frameRoughness
        clearcoatAmount: root.frameClearcoat
        clearcoatRoughnessAmount: root.frameClearcoatRoughness
        transmissionFactor: root.frameTransmission
        opacity: root.frameOpacity
        indexOfRefraction: root.frameIor
        attenuationDistance: root.frameAttenuationDistance
        attenuationColor: root.frameAttenuationColor
        emissiveFactor: root.emissiveVector(root.frameEmissiveColor, root.frameEmissiveIntensity)
    }

    readonly property PrincipledMaterial leverMaterial: PrincipledMaterial {
        baseColor: root.leverBaseColor
        metalness: root.leverMetalness
        roughness: root.leverRoughness
        clearcoatAmount: root.leverClearcoat
        clearcoatRoughnessAmount: root.leverClearcoatRoughness
        transmissionFactor: root.leverTransmission
        opacity: root.leverOpacity
        indexOfRefraction: root.leverIor
        attenuationDistance: root.leverAttenuationDistance
        attenuationColor: root.leverAttenuationColor
        emissiveFactor: root.emissiveVector(root.leverEmissiveColor, root.leverEmissiveIntensity)
    }

    readonly property PrincipledMaterial tailRodMaterial: PrincipledMaterial {
        baseColor: root.tailRodBaseColor
        metalness: root.tailRodMetalness
        roughness: root.tailRodRoughness
        clearcoatAmount: root.tailRodClearcoat
        clearcoatRoughnessAmount: root.tailRodClearcoatRoughness
        transmissionFactor: root.tailRodTransmission
        opacity: root.tailRodOpacity
        indexOfRefraction: root.tailRodIor
        attenuationDistance: root.tailRodAttenuationDistance
        attenuationColor: root.tailRodAttenuationColor
        emissiveFactor: root.emissiveVector(root.tailRodEmissiveColor, root.tailRodEmissiveIntensity)
    }

    readonly property PrincipledMaterial cylinderMaterial: PrincipledMaterial {
        baseColor: root.cylinderBaseColor
        metalness: root.cylinderMetalness
        roughness: root.cylinderRoughness
        clearcoatAmount: root.cylinderClearcoat
        clearcoatRoughnessAmount: root.cylinderClearcoatRoughness
        transmissionFactor: root.cylinderTransmission
        opacity: root.cylinderOpacity
        indexOfRefraction: root.cylinderIor
        attenuationDistance: root.cylinderAttenuationDistance
        attenuationColor: root.cylinderAttenuationColor
        emissiveFactor: root.emissiveVector(root.cylinderEmissiveColor, root.cylinderEmissiveIntensity)
        alphaMode: PrincipledMaterial.Blend
    }

    readonly property PrincipledMaterial jointTailMaterial: PrincipledMaterial {
        baseColor: root.jointTailBaseColor
        metalness: root.jointTailMetalness
        roughness: root.jointTailRoughness
        clearcoatAmount: root.jointTailClearcoat
        clearcoatRoughnessAmount: root.jointTailClearcoatRoughness
        transmissionFactor: root.jointTailTransmission
        opacity: root.jointTailOpacity
        indexOfRefraction: root.jointTailIor
        attenuationDistance: root.jointTailAttenuationDistance
        attenuationColor: root.jointTailAttenuationColor
        emissiveFactor: root.emissiveVector(root.jointTailEmissiveColor, root.jointTailEmissiveIntensity)
    }

    readonly property PrincipledMaterial jointArmMaterial: PrincipledMaterial {
        baseColor: root.jointArmBaseColor
        metalness: root.jointArmMetalness
        roughness: root.jointArmRoughness
        clearcoatAmount: root.jointArmClearcoat
        clearcoatRoughnessAmount: root.jointArmClearcoatRoughness
        transmissionFactor: root.jointArmTransmission
        opacity: root.jointArmOpacity
        indexOfRefraction: root.jointArmIor
        attenuationDistance: root.jointArmAttenuationDistance
        attenuationColor: root.jointArmAttenuationColor
        emissiveFactor: root.emissiveVector(root.jointArmEmissiveColor, root.jointArmEmissiveIntensity)
    }

    // ===============================================================
    // DYNAMIC MATERIALS (для поршня и штока с warning colors)
    // ===============================================================

    // Эти материалы создаются динамически в компонентах, так как зависят от rodLengthError
    // Но свойства для них доступны через root

    Component.onCompleted: {
        console.log("🎨 SharedMaterials initialized")
        console.log("   📦 7 static materials created")
        console.log("   🔧 Dynamic piston/rod materials available")
    }
}
"""


def main():
    from pathlib import Path

    file_path = Path("assets/qml/scene/SharedMaterials.qml")

    print(f"📝 Создание {file_path}...")

    file_path.write_text(SHARED_MATERIALS_CONTENT, encoding="utf-8")

    print(f"✅ Файл создан: {file_path}")
    print(f"   Размер: {len(SHARED_MATERIALS_CONTENT)} символов")
    print(
        "   Материалов: 7 (frame, lever, tailRod, cylinder, jointTail, jointArm + dynamic)"
    )


if __name__ == "__main__":
    main()
