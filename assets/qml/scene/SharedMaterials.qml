import QtQuick
import QtQuick3D

/*
 * SharedMaterials - Централизованное управление материалами
 *
 * НАЗНАЧЕНИЕ:
 * - Единый источник всех PBR материалов для3D сцены
 * - Избежание дублирования материалов
 * - Централизованное управление через Python bindings
 *
 * USAGE:
 * ```qml
 * SharedMaterials {
 * id: sharedMaterials
 * frameBaseColor: root.frameBaseColor
 * // ... все остальные bindings
 * }
 *
 * Model {
 * materials: [sharedMaterials.frameMaterial]
 * }
 * ```
 */
QtObject {
    id: root

    property var initialSharedMaterials: null
    property var materialsDefaults: root.initialSharedMaterials

    function matValue(materialKey, propertyName, fallback) {
        if (root.materialsDefaults && root.materialsDefaults[materialKey] !== undefined) {
            const candidate = root.materialsDefaults[materialKey][propertyName]
            if (candidate !== undefined) {
                return candidate
            }
        }
        return fallback
    }

 // ===============================================================
 // FRAME MATERIAL PROPERTIES
 // ===============================================================

 // Painted steel chassis (dielectric with satin clearcoat)
 property color frameBaseColor: matValue("frame", "base_color", "#2d323c")
 property real frameMetalness: Number(matValue("frame", "metalness",0.0))
 property real frameRoughness: Number(matValue("frame", "roughness",0.58))
 property real frameSpecularAmount: Number(matValue("frame", "specular_amount",0.55))
 property real frameSpecularTint: Number(matValue("frame", "specular_tint",0.0))
 property real frameClearcoat: Number(matValue("frame", "clearcoat",0.35))
 property real frameClearcoatRoughness: Number(matValue("frame", "clearcoat_roughness",0.12))
 property real frameTransmission: Number(matValue("frame", "transmission",0.0))
 property real frameOpacity: Number(matValue("frame", "opacity",1.0))
 property real frameIor: Number(matValue("frame", "ior",1.5))
 property real frameAttenuationDistance: Number(matValue("frame", "attenuation_distance",10000.0))
 property color frameAttenuationColor: matValue("frame", "attenuation_color", "#ffffff")
 property color frameEmissiveColor: matValue("frame", "emissive_color", "#000000")
 property real frameEmissiveIntensity: Number(matValue("frame", "emissive_intensity",0.0))

 // ===============================================================
 // LEVER MATERIAL PROPERTIES
 // ===============================================================

 // Machined steel lever with brushed finish
 property color leverBaseColor: matValue("lever", "base_color", "#a7adb4")
 property real leverMetalness: Number(matValue("lever", "metalness",1.0))
 property real leverRoughness: Number(matValue("lever", "roughness",0.38))
 property real leverSpecularAmount: Number(matValue("lever", "specular_amount",1.0))
 property real leverSpecularTint: Number(matValue("lever", "specular_tint",0.0))
 property real leverClearcoat: Number(matValue("lever", "clearcoat",0.05))
 property real leverClearcoatRoughness: Number(matValue("lever", "clearcoat_roughness",0.05))
 property real leverTransmission: Number(matValue("lever", "transmission",0.0))
 property real leverOpacity: Number(matValue("lever", "opacity",1.0))
 property real leverIor: Number(matValue("lever", "ior",1.5))
 property real leverAttenuationDistance: Number(matValue("lever", "attenuation_distance",10000.0))
 property color leverAttenuationColor: matValue("lever", "attenuation_color", "#ffffff")
 property color leverEmissiveColor: matValue("lever", "emissive_color", "#000000")
 property real leverEmissiveIntensity: Number(matValue("lever", "emissive_intensity",0.0))

 // ===============================================================
 // TAIL ROD MATERIAL PROPERTIES
 // ===============================================================

 // Tail rod inherits mild roughness to catch highlights
 property color tailRodBaseColor: matValue("tail_rod", "base_color", "#d5d9df")
 property real tailRodMetalness: Number(matValue("tail_rod", "metalness",1.0))
 property real tailRodRoughness: Number(matValue("tail_rod", "roughness",0.32))
 property real tailRodSpecularAmount: Number(matValue("tail_rod", "specular_amount",1.0))
 property real tailRodSpecularTint: Number(matValue("tail_rod", "specular_tint",0.0))
 property real tailRodClearcoat: Number(matValue("tail_rod", "clearcoat",0.08))
 property real tailRodClearcoatRoughness: Number(matValue("tail_rod", "clearcoat_roughness",0.05))
 property real tailRodTransmission: Number(matValue("tail_rod", "transmission",0.0))
 property real tailRodOpacity: Number(matValue("tail_rod", "opacity",1.0))
 property real tailRodIor: Number(matValue("tail_rod", "ior",1.5))
 property real tailRodAttenuationDistance: Number(matValue("tail_rod", "attenuation_distance",10000.0))
 property color tailRodAttenuationColor: matValue("tail_rod", "attenuation_color", "#ffffff")
 property color tailRodEmissiveColor: matValue("tail_rod", "emissive_color", "#000000")
 property real tailRodEmissiveIntensity: Number(matValue("tail_rod", "emissive_intensity",0.0))

 // ===============================================================
 // CYLINDER MATERIAL PROPERTIES (GLASS)
 // ===============================================================

 property color cylinderBaseColor: matValue("cylinder", "base_color", "#e1f5ff")
 property real cylinderMetalness: Number(matValue("cylinder", "metalness",0.0))
 property real cylinderRoughness: Number(matValue("cylinder", "roughness",0.05))
 property real cylinderSpecularAmount: Number(matValue("cylinder", "specular_amount",1.0))
 property real cylinderSpecularTint: Number(matValue("cylinder", "specular_tint",0.0))
 property real cylinderClearcoat: Number(matValue("cylinder", "clearcoat",0.0))
 property real cylinderClearcoatRoughness: Number(matValue("cylinder", "clearcoat_roughness",0.0))
 property real cylinderTransmission: Number(matValue("cylinder", "transmission",1.0))
 property real cylinderOpacity: Number(matValue("cylinder", "opacity",1.0))
 property real cylinderIor: Number(matValue("cylinder", "ior",1.52))
 property real cylinderAttenuationDistance: Number(matValue("cylinder", "attenuation_distance",1800.0))
 property color cylinderAttenuationColor: matValue("cylinder", "attenuation_color", "#b7e7ff")
 property color cylinderEmissiveColor: matValue("cylinder", "emissive_color", "#000000")
 property real cylinderEmissiveIntensity: Number(matValue("cylinder", "emissive_intensity",0.0))

 // ===============================================================
 // PISTON BODY MATERIAL PROPERTIES
 // ===============================================================

 // Painted safety cap with strong clearcoat for highlights
 property color pistonBodyBaseColor: matValue("piston_body", "base_color", "#ff3c6e")
 property color pistonBodyWarningColor: matValue("piston_body", "warning_color", "#ff5454")
 property real pistonBodyMetalness: Number(matValue("piston_body", "metalness",0.0))
 property real pistonBodyRoughness: Number(matValue("piston_body", "roughness",0.45))
 property real pistonBodySpecularAmount: Number(matValue("piston_body", "specular_amount",0.6))
 property real pistonBodySpecularTint: Number(matValue("piston_body", "specular_tint",0.0))
 property real pistonBodyClearcoat: Number(matValue("piston_body", "clearcoat",0.42))
 property real pistonBodyClearcoatRoughness: Number(matValue("piston_body", "clearcoat_roughness",0.18))
 property real pistonBodyTransmission: Number(matValue("piston_body", "transmission",0.0))
 property real pistonBodyOpacity: Number(matValue("piston_body", "opacity",1.0))
 property real pistonBodyIor: Number(matValue("piston_body", "ior",1.5))
 property real pistonBodyAttenuationDistance: Number(matValue("piston_body", "attenuation_distance",10000.0))
 property color pistonBodyAttenuationColor: matValue("piston_body", "attenuation_color", "#ffffff")
 property color pistonBodyEmissiveColor: matValue("piston_body", "emissive_color", "#000000")
 property real pistonBodyEmissiveIntensity: Number(matValue("piston_body", "emissive_intensity",0.0))

 // ===============================================================
 // PISTON ROD MATERIAL PROPERTIES
 // ===============================================================

 // Highly polished chrome piston rod
 property color pistonRodBaseColor: matValue("piston_rod", "base_color", "#f0f0f0")
 property color pistonRodWarningColor: matValue("piston_rod", "warning_color", "#ff2a2a")
 property real pistonRodMetalness: Number(matValue("piston_rod", "metalness",1.0))
 property real pistonRodRoughness: Number(matValue("piston_rod", "roughness",0.12))
 property real pistonRodSpecularAmount: Number(matValue("piston_rod", "specular_amount",1.0))
 property real pistonRodSpecularTint: Number(matValue("piston_rod", "specular_tint",0.0))
 property real pistonRodClearcoat: Number(matValue("piston_rod", "clearcoat",0.05))
 property real pistonRodClearcoatRoughness: Number(matValue("piston_rod", "clearcoat_roughness",0.02))
 property real pistonRodTransmission: Number(matValue("piston_rod", "transmission",0.0))
 property real pistonRodOpacity: Number(matValue("piston_rod", "opacity",1.0))
 property real pistonRodIor: Number(matValue("piston_rod", "ior",1.5))
 property real pistonRodAttenuationDistance: Number(matValue("piston_rod", "attenuation_distance",10000.0))
 property color pistonRodAttenuationColor: matValue("piston_rod", "attenuation_color", "#ffffff")
 property color pistonRodEmissiveColor: matValue("piston_rod", "emissive_color", "#000000")
 property real pistonRodEmissiveIntensity: Number(matValue("piston_rod", "emissive_intensity",0.0))

 // ===============================================================
 // JOINT TAIL MATERIAL PROPERTIES
 // ===============================================================

 // Painted joint caps mimic powder-coated hardware
 property color jointTailBaseColor: matValue("joint_tail", "base_color", "#2a82ff")
 property real jointTailMetalness: Number(matValue("joint_tail", "metalness",0.0))
 property real jointTailRoughness: Number(matValue("joint_tail", "roughness",0.42))
 property real jointTailSpecularAmount: Number(matValue("joint_tail", "specular_amount",0.6))
 property real jointTailSpecularTint: Number(matValue("joint_tail", "specular_tint",0.0))
 property real jointTailClearcoat: Number(matValue("joint_tail", "clearcoat",0.28))
 property real jointTailClearcoatRoughness: Number(matValue("joint_tail", "clearcoat_roughness",0.16))
 property real jointTailTransmission: Number(matValue("joint_tail", "transmission",0.0))
 property real jointTailOpacity: Number(matValue("joint_tail", "opacity",1.0))
 property real jointTailIor: Number(matValue("joint_tail", "ior",1.5))
 property real jointTailAttenuationDistance: Number(matValue("joint_tail", "attenuation_distance",10000.0))
 property color jointTailAttenuationColor: matValue("joint_tail", "attenuation_color", "#ffffff")
 property color jointTailEmissiveColor: matValue("joint_tail", "emissive_color", "#000000")
 property real jointTailEmissiveIntensity: Number(matValue("joint_tail", "emissive_intensity",0.0))

 // ===============================================================
 // JOINT ARM MATERIAL PROPERTIES
 // ===============================================================

 property color jointArmBaseColor: matValue("joint_arm", "base_color", "#ff9c3a")
 property real jointArmMetalness: Number(matValue("joint_arm", "metalness",0.0))
 property real jointArmRoughness: Number(matValue("joint_arm", "roughness",0.4))
 property real jointArmSpecularAmount: Number(matValue("joint_arm", "specular_amount",0.65))
 property real jointArmSpecularTint: Number(matValue("joint_arm", "specular_tint",0.0))
 property real jointArmClearcoat: Number(matValue("joint_arm", "clearcoat",0.3))
 property real jointArmClearcoatRoughness: Number(matValue("joint_arm", "clearcoat_roughness",0.14))
 property real jointArmTransmission: Number(matValue("joint_arm", "transmission",0.0))
 property real jointArmOpacity: Number(matValue("joint_arm", "opacity",1.0))
 property real jointArmIor: Number(matValue("joint_arm", "ior",1.5))
 property real jointArmAttenuationDistance: Number(matValue("joint_arm", "attenuation_distance",10000.0))
 property color jointArmAttenuationColor: matValue("joint_arm", "attenuation_color", "#ffffff")
 property color jointArmEmissiveColor: matValue("joint_arm", "emissive_color", "#000000")
 property real jointArmEmissiveIntensity: Number(matValue("joint_arm", "emissive_intensity",0.0))

 // ===============================================================
 // JOINT ROD SPECIAL COLORS
 // ===============================================================

 property color jointRodOkColor: matValue("joint_rod", "ok_color", "#00ff55")
 property color jointRodErrorColor: matValue("joint_rod", "error_color", "#ff0000")

 // ===============================================================
 // HELPER FUNCTION
 // ===============================================================

 function emissiveVector(color, intensity) {
 if (intensity === undefined)
 intensity =1.0
 if (!color)
 return Qt.vector3d(0,0,0)
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

    readonly property PrincipledMaterial pistonBodyMaterial: PrincipledMaterial {
        baseColor: root.pistonBodyBaseColor
        metalness: root.pistonBodyMetalness
        roughness: root.pistonBodyRoughness
        clearcoatAmount: root.pistonBodyClearcoat
        clearcoatRoughnessAmount: root.pistonBodyClearcoatRoughness
        transmissionFactor: root.pistonBodyTransmission
        opacity: root.pistonBodyOpacity
        indexOfRefraction: root.pistonBodyIor
        attenuationDistance: root.pistonBodyAttenuationDistance
        attenuationColor: root.pistonBodyAttenuationColor
        emissiveFactor: root.emissiveVector(root.pistonBodyEmissiveColor, root.pistonBodyEmissiveIntensity)
    }

    readonly property PrincipledMaterial pistonRodMaterial: PrincipledMaterial {
        baseColor: root.pistonRodBaseColor
        metalness: root.pistonRodMetalness
        roughness: root.pistonRodRoughness
        clearcoatAmount: root.pistonRodClearcoat
        clearcoatRoughnessAmount: root.pistonRodClearcoatRoughness
        transmissionFactor: root.pistonRodTransmission
        opacity: root.pistonRodOpacity
        indexOfRefraction: root.pistonRodIor
        attenuationDistance: root.pistonRodAttenuationDistance
        attenuationColor: root.pistonRodAttenuationColor
        emissiveFactor: root.emissiveVector(root.pistonRodEmissiveColor, root.pistonRodEmissiveIntensity)
    }

 // ===============================================================
 // DYNAMIC MATERIALS (для поршня и штока с warning colors)
 // ===============================================================

 // Эти материалы создаются динамически в компонентах, так как зависят от rodLengthError
 // Но свойства для них доступны через root

 Component.onCompleted: {
 console.log("🎨 SharedMaterials initialized")
 console.log(" 📦7 static materials created")
 console.log(" 🔧 Dynamic piston/rod materials available")
 }
}
