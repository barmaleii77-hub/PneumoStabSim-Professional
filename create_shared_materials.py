#!/usr/bin/env python3
"""
Создание SharedMaterials.qml для централизованного управления материалами

Актуализировано под минимальный набор Qt 6.10 (PrincipledMaterial):
Оставлены только поддерживаемые поля: baseColor, metalness, roughness,
clearcoatAmount, clearcoatRoughnessAmount, opacity, emissiveFactor, alphaMode (где нужно).
Удалены устаревшие / неиспользуемые генератором поля: specular*, transmission*,
indexOfRefraction/ior, attenuationDistance/attenuationColor.
Добавлен jointRodMaterial (ранее отсутствовал в генераторе).
"""

SHARED_MATERIALS_CONTENT = r"""import QtQuick
import QtQuick3D

/*
 * SharedMaterials - Централизованное управление материалами (минимальный набор Qt 6.10)
 *
 * Удалены legacy поля (specular/transmission/ior/attenuation). Генератор синхронизирован
 * с боевой версией scene/SharedMaterials.qml.
 */
QtObject {
    id: root

    // === FRAME ===
    property color frameBaseColor: "#c53030"
    property real frameMetalness: 0.85
    property real frameRoughness: 0.35
    property real frameClearcoat: 0.22
    property real frameClearcoatRoughness: 0.10
    property real frameOpacity: 1.0
    property color frameEmissiveColor: "#000000"
    property real frameEmissiveIntensity: 0.0

    // === LEVER ===
    property color leverBaseColor: "#9ea4ab"
    property real leverMetalness: 1.0
    property real leverRoughness: 0.28
    property real leverClearcoat: 0.30
    property real leverClearcoatRoughness: 0.08
    property real leverOpacity: 1.0
    property color leverEmissiveColor: "#000000"
    property real leverEmissiveIntensity: 0.0

    // === TAIL ROD ===
    property color tailRodBaseColor: "#d5d9df"
    property real tailRodMetalness: 1.0
    property real tailRodRoughness: 0.30
    property real tailRodClearcoat: 0.0
    property real tailRodClearcoatRoughness: 0.0
    property real tailRodOpacity: 1.0
    property color tailRodEmissiveColor: "#000000"
    property real tailRodEmissiveIntensity: 0.0

    // === CYLINDER (GLASS-LIKE) ===
    property color cylinderBaseColor: "#e1f5ff"
    property real cylinderMetalness: 0.0
    property real cylinderRoughness: 0.20
    property real cylinderOpacity: 0.30    // используется как alpha при blend
    property color cylinderEmissiveColor: "#000000"
    property real cylinderEmissiveIntensity: 0.0

    // === PISTON BODY ===
    property color pistonBodyBaseColor: "#ff3c6e"
    property real pistonBodyMetalness: 1.0
    property real pistonBodyRoughness: 0.26
    property real pistonBodyClearcoat: 0.15
    property real pistonBodyClearcoatRoughness: 0.08
    property real pistonBodyOpacity: 1.0
    property color pistonBodyEmissiveColor: "#000000"
    property real pistonBodyEmissiveIntensity: 0.0

    // === PISTON ROD ===
    property color pistonRodBaseColor: "#ececec"
    property real pistonRodMetalness: 1.0
    property real pistonRodRoughness: 0.18
    property real pistonRodClearcoat: 0.10
    property real pistonRodClearcoatRoughness: 0.05
    property real pistonRodOpacity: 1.0
    property color pistonRodEmissiveColor: "#000000"
    property real pistonRodEmissiveIntensity: 0.0

    // === JOINT TAIL ===
    property color jointTailBaseColor: "#2a82ff"
    property real jointTailMetalness: 0.9
    property real jointTailRoughness: 0.35
    property real jointTailClearcoat: 0.10
    property real jointTailClearcoatRoughness: 0.08
    property real jointTailOpacity: 1.0
    property color jointTailEmissiveColor: "#000000"
    property real jointTailEmissiveIntensity: 0.0

    // === JOINT ARM ===
    property color jointArmBaseColor: "#ff9c3a"
    property real jointArmMetalness: 0.9
    property real jointArmRoughness: 0.32
    property real jointArmClearcoat: 0.12
    property real jointArmClearcoatRoughness: 0.08
    property real jointArmOpacity: 1.0
    property color jointArmEmissiveColor: "#000000"
    property real jointArmEmissiveIntensity: 0.0

    // === JOINT ROD STATIC (base) ===
    property color jointRodBaseColor: "#00ff55"
    property real jointRodMetalness: 0.9
    property real jointRodRoughness: 0.30
    property real jointRodClearcoat: 0.05
    property real jointRodClearcoatRoughness: 0.08
    property real jointRodOpacity: 1.0
    property color jointRodEmissiveColor: "#000000"
    property real jointRodEmissiveIntensity: 0.0

    // Special UI colors (warning/ok) for AnimatedRodMaterial
    property color jointRodOkColor: "#00ff55"
    property color jointRodErrorColor: "#ff0000"

    function emissiveVector(color, intensity) {
        if (intensity === undefined) intensity = 1.0
        if (!color) return Qt.vector3d(0,0,0)
        return Qt.vector3d(color.r * intensity, color.g * intensity, color.b * intensity)
    }

    // === MATERIAL INSTANCES ===
    readonly property PrincipledMaterial frameMaterial: PrincipledMaterial {
        baseColor: root.frameBaseColor
        metalness: root.frameMetalness
        roughness: root.frameRoughness
        clearcoatAmount: root.frameClearcoat
        clearcoatRoughnessAmount: root.frameClearcoatRoughness
        opacity: root.frameOpacity
        emissiveFactor: root.emissiveVector(root.frameEmissiveColor, root.frameEmissiveIntensity)
    }
    readonly property PrincipledMaterial leverMaterial: PrincipledMaterial {
        baseColor: root.leverBaseColor
        metalness: root.leverMetalness
        roughness: root.leverRoughness
        clearcoatAmount: root.leverClearcoat
        clearcoatRoughnessAmount: root.leverClearcoatRoughness
        opacity: root.leverOpacity
        emissiveFactor: root.emissiveVector(root.leverEmissiveColor, root.leverEmissiveIntensity)
    }
    readonly property PrincipledMaterial tailRodMaterial: PrincipledMaterial {
        baseColor: root.tailRodBaseColor
        metalness: root.tailRodMetalness
        roughness: root.tailRodRoughness
        clearcoatAmount: root.tailRodClearcoat
        clearcoatRoughnessAmount: root.tailRodClearcoatRoughness
        opacity: root.tailRodOpacity
        emissiveFactor: root.emissiveVector(root.tailRodEmissiveColor, root.tailRodEmissiveIntensity)
    }
    readonly property PrincipledMaterial cylinderMaterial: PrincipledMaterial {
        baseColor: root.cylinderBaseColor
        metalness: root.cylinderMetalness
        roughness: root.cylinderRoughness
        opacity: root.cylinderOpacity
        emissiveFactor: root.emissiveVector(root.cylinderEmissiveColor, root.cylinderEmissiveIntensity)
        alphaMode: PrincipledMaterial.Blend
    }
    readonly property PrincipledMaterial pistonBodyMaterial: PrincipledMaterial {
        baseColor: root.pistonBodyBaseColor
        metalness: root.pistonBodyMetalness
        roughness: root.pistonBodyRoughness
        clearcoatAmount: root.pistonBodyClearcoat
        clearcoatRoughnessAmount: root.pistonBodyClearcoatRoughness
        opacity: root.pistonBodyOpacity
        emissiveFactor: root.emissiveVector(root.pistonBodyEmissiveColor, root.pistonBodyEmissiveIntensity)
    }
    readonly property PrincipledMaterial pistonRodMaterial: PrincipledMaterial {
        baseColor: root.pistonRodBaseColor
        metalness: root.pistonRodMetalness
        roughness: root.pistonRodRoughness
        clearcoatAmount: root.pistonRodClearcoat
        clearcoatRoughnessAmount: root.pistonRodClearcoatRoughness
        opacity: root.pistonRodOpacity
        emissiveFactor: root.emissiveVector(root.pistonRodEmissiveColor, root.pistonRodEmissiveIntensity)
    }
    readonly property PrincipledMaterial jointTailMaterial: PrincipledMaterial {
        baseColor: root.jointTailBaseColor
        metalness: root.jointTailMetalness
        roughness: root.jointTailRoughness
        clearcoatAmount: root.jointTailClearcoat
        clearcoatRoughnessAmount: root.jointTailClearcoatRoughness
        opacity: root.jointTailOpacity
        emissiveFactor: root.emissiveVector(root.jointTailEmissiveColor, root.jointTailEmissiveIntensity)
    }
    readonly property PrincipledMaterial jointArmMaterial: PrincipledMaterial {
        baseColor: root.jointArmBaseColor
        metalness: root.jointArmMetalness
        roughness: root.jointArmRoughness
        clearcoatAmount: root.jointArmClearcoat
        clearcoatRoughnessAmount: root.jointArmClearcoatRoughness
        opacity: root.jointArmOpacity
        emissiveFactor: root.emissiveVector(root.jointArmEmissiveColor, root.jointArmEmissiveIntensity)
    }
    readonly property PrincipledMaterial jointRodMaterial: PrincipledMaterial {
        baseColor: root.jointRodBaseColor
        metalness: root.jointRodMetalness
        roughness: root.jointRodRoughness
        clearcoatAmount: root.jointRodClearcoat
        clearcoatRoughnessAmount: root.jointRodClearcoatRoughness
        opacity: root.jointRodOpacity
        emissiveFactor: root.emissiveVector(root.jointRodEmissiveColor, root.jointRodEmissiveIntensity)
    }

    Component.onCompleted: {
        console.log("SharedMaterials (generator) initialized: minimal Qt 6.10 property set")
    }
}
"""


def main():
    from pathlib import Path

    file_path = Path("assets/qml/scene/SharedMaterials.qml")
    print(f"📝 Обновление {file_path} (минимальный набор Qt 6.10)...")
    file_path.write_text(SHARED_MATERIALS_CONTENT, encoding="utf-8")
    print("✅ SharedMaterials.qml обновлён: legacy поля удалены, jointRodMaterial добавлен")


if __name__ == "__main__":
    main()
