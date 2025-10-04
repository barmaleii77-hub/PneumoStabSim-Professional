// Materials.qml - PBR материалы для визуализации
pragma Singleton
import QtQuick
import QtQuick3D

QtObject {
    // Красный металлик для рамы
    readonly property PrincipledMaterial redMetal: PrincipledMaterial {
        baseColor: "#d01515"
        metalness: 1.0
        roughness: 0.28
        clearcoatAmount: 0.25
        clearcoatRoughnessAmount: 0.1
    }

    // Сталь (рычаги/крышки/хвостовик/поршень)
    readonly property PrincipledMaterial steel: PrincipledMaterial {
        baseColor: "#9fa5ad"
        metalness: 0.9
        roughness: 0.35
    }

    // Тонкая сталь (крышки)
    readonly property PrincipledMaterial steelThin: PrincipledMaterial {
        baseColor: "#b9c0c8"
        metalness: 0.8
        roughness: 0.25
    }

    // Хром (шток)
    readonly property PrincipledMaterial chrome: PrincipledMaterial {
        baseColor: "#e6e6e6"
        metalness: 1.0
        roughness: 0.12
    }

    // Стекло для корпуса цилиндра
    readonly property PrincipledMaterial glass: PrincipledMaterial {
        baseColor: "#ffffff"
        metalness: 0.0
        roughness: 0.05
        opacity: 0.35
        alphaMode: PrincipledMaterial.Blend
        cullMode: Material.BackFaceCulling
    }

    // Сфера массы (полупрозрачная голубая)
    readonly property PrincipledMaterial massSphere: PrincipledMaterial {
        baseColor: "#a0d8ff"
        metalness: 0.2
        roughness: 0.6
        opacity: 0.55
        alphaMode: PrincipledMaterial.Blend
    }
}
