import QtQuick
import QtQuick3D

/*
 * SharedMaterials - Централизованное управление материалами
 *
 * НАЗНАЧЕНИЕ:
 * - Единый источник всех PBR материалов для3D сцены
 * - Избежание дублирования материалов
 * - Централизованное управление через Python bindings
 * - Исключительно параметрические материалы (без внешних текстур),
 *   чтобы репозиторий оставался текстовым и предсказуемым для CI
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

    readonly property var materialKeyAliases: ({
        tail: "tail_rod",
        tailrod: "tail_rod",
        glass: "cylinder",
        metal: "lever"
    })

    readonly property var materialPropertyAliases: ({
        base_color: ["baseColor"],
        specular: ["specular_amount", "specularAmount"],
        specular_amount: ["specular", "specularAmount"],
        specular_tint: ["specularTint"],
        clearcoat_roughness: ["clearcoatRoughness"],
        transmission: ["transmissionFactor"],
        ior: ["indexOfRefraction"],
        thickness: ["thicknessFactor"],
        attenuation_distance: ["attenuationDistance"],
        attenuation_color: ["attenuationColor"],
        emissive_color: ["emissiveColor"],
        emissive_intensity: ["emissiveIntensity"],
        normal_strength: ["normalStrength"],
        occlusion_amount: ["occlusionAmount"],
        alpha_mode: ["alphaMode"],
        alpha_cutoff: ["alphaCutoff"],
        texture_path: ["texturePath"],
        warning_color: ["warningColor"],
        ok_color: ["okColor"],
        error_color: ["errorColor"]
    })

    function canonicalMaterialKey(key) {
        var normalized = String(key || "").toLowerCase()
        if (root.materialKeyAliases[normalized] !== undefined)
            return root.materialKeyAliases[normalized]
        return normalized
    }

    function candidatePropertyNames(propertyName) {
        var canonical = String(propertyName || "")
        var names = [canonical]
        var normalized = canonical.toLowerCase()
        if (normalized !== canonical)
            names.push(normalized)
        var aliasList = root.materialPropertyAliases[normalized]
        if (aliasList) {
            for (var i = 0; i < aliasList.length; ++i) {
                var alias = aliasList[i]
                if (names.indexOf(alias) === -1)
                    names.push(alias)
                var aliasLower = String(alias).toLowerCase()
                if (names.indexOf(aliasLower) === -1)
                    names.push(aliasLower)
            }
        }
        return names
    }

    function matValue(materialKey, propertyName, fallback) {
        var canonicalKey = canonicalMaterialKey(materialKey)
        if (!root.materialsDefaults || root.materialsDefaults[canonicalKey] === undefined)
            return fallback
        var bucket = root.materialsDefaults[canonicalKey]
        if (!bucket)
            return fallback
        var candidates = candidatePropertyNames(propertyName)
        for (var i = 0; i < candidates.length; ++i) {
            var candidate = candidates[i]
            if (bucket[candidate] !== undefined)
                return bucket[candidate]
        }
        return fallback
    }

    function normalizedTexturePath(value) {
        if (value === undefined || value === null)
            return ""
        var text = String(value).trim()
        if (!text || text === "—")
            return ""
        return text.replace(/\\\\/g, "/")
    }

    function textureEnabled(path) {
        return path !== undefined && path !== null && String(path).trim() !== "" && String(path).trim() !== "—"
    }

    function resolveTextureSource(path) {
        if (!root.textureEnabled(path))
            return ""
        var normalized = root.normalizedTexturePath(path)
        if (!normalized)
            return ""
        if (normalized.startsWith("qrc:/") || normalized.indexOf("://") > 0 || normalized.startsWith("data:"))
            return normalized
        return Qt.resolvedUrl(normalized)
    }

    function alphaModeValue(mode) {
        var text = String(mode || "").toLowerCase()
        switch (text) {
        case "mask":
            return PrincipledMaterial.Mask
        case "blend":
            return PrincipledMaterial.Blend
        case "opaque":
            return PrincipledMaterial.Opaque
        default:
            return PrincipledMaterial.Default
        }
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
 property real frameThickness: Number(matValue("frame", "thickness",0.0))
 property real frameAttenuationDistance: Number(matValue("frame", "attenuation_distance",10000.0))
 property color frameAttenuationColor: matValue("frame", "attenuation_color", "#ffffff")
 property color frameEmissiveColor: matValue("frame", "emissive_color", "#000000")
 property real frameEmissiveIntensity: Number(matValue("frame", "emissive_intensity",0.0))
 property real frameNormalStrength: Number(matValue("frame", "normal_strength",0.0))
 property real frameOcclusionAmount: Number(matValue("frame", "occlusion_amount",0.0))
 property string frameAlphaMode: String(matValue("frame", "alpha_mode", "default"))
 property real frameAlphaCutoff: Number(matValue("frame", "alpha_cutoff",0.0))
 property string frameTexturePath: normalizedTexturePath(matValue("frame", "texture_path", ""))

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
 property real leverThickness: Number(matValue("lever", "thickness",0.0))
 property real leverAttenuationDistance: Number(matValue("lever", "attenuation_distance",10000.0))
 property color leverAttenuationColor: matValue("lever", "attenuation_color", "#ffffff")
 property color leverEmissiveColor: matValue("lever", "emissive_color", "#000000")
 property real leverEmissiveIntensity: Number(matValue("lever", "emissive_intensity",0.0))
 property real leverNormalStrength: Number(matValue("lever", "normal_strength",0.0))
 property real leverOcclusionAmount: Number(matValue("lever", "occlusion_amount",0.0))
 property string leverAlphaMode: String(matValue("lever", "alpha_mode", "default"))
 property real leverAlphaCutoff: Number(matValue("lever", "alpha_cutoff",0.0))
 property string leverTexturePath: normalizedTexturePath(matValue("lever", "texture_path", ""))

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
 property real tailRodThickness: Number(matValue("tail_rod", "thickness",0.0))
 property real tailRodAttenuationDistance: Number(matValue("tail_rod", "attenuation_distance",10000.0))
 property color tailRodAttenuationColor: matValue("tail_rod", "attenuation_color", "#ffffff")
 property color tailRodEmissiveColor: matValue("tail_rod", "emissive_color", "#000000")
 property real tailRodEmissiveIntensity: Number(matValue("tail_rod", "emissive_intensity",0.0))
 property real tailRodNormalStrength: Number(matValue("tail_rod", "normal_strength",0.0))
 property real tailRodOcclusionAmount: Number(matValue("tail_rod", "occlusion_amount",0.0))
 property string tailRodAlphaMode: String(matValue("tail_rod", "alpha_mode", "default"))
 property real tailRodAlphaCutoff: Number(matValue("tail_rod", "alpha_cutoff",0.0))
 property string tailRodTexturePath: normalizedTexturePath(matValue("tail_rod", "texture_path", ""))

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
 property real cylinderThickness: Number(matValue("cylinder", "thickness",0.0))
 property real cylinderAttenuationDistance: Number(matValue("cylinder", "attenuation_distance",1800.0))
 property color cylinderAttenuationColor: matValue("cylinder", "attenuation_color", "#b7e7ff")
 property color cylinderEmissiveColor: matValue("cylinder", "emissive_color", "#000000")
 property real cylinderEmissiveIntensity: Number(matValue("cylinder", "emissive_intensity",0.0))
 property real cylinderNormalStrength: Number(matValue("cylinder", "normal_strength",0.0))
 property real cylinderOcclusionAmount: Number(matValue("cylinder", "occlusion_amount",0.0))
 property string cylinderAlphaMode: String(matValue("cylinder", "alpha_mode", "blend"))
 property real cylinderAlphaCutoff: Number(matValue("cylinder", "alpha_cutoff",0.0))
 property string cylinderTexturePath: normalizedTexturePath(matValue("cylinder", "texture_path", ""))

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
 property real pistonBodyThickness: Number(matValue("piston_body", "thickness",0.0))
 property real pistonBodyAttenuationDistance: Number(matValue("piston_body", "attenuation_distance",10000.0))
 property color pistonBodyAttenuationColor: matValue("piston_body", "attenuation_color", "#ffffff")
 property color pistonBodyEmissiveColor: matValue("piston_body", "emissive_color", "#000000")
 property real pistonBodyEmissiveIntensity: Number(matValue("piston_body", "emissive_intensity",0.0))
 property real pistonBodyNormalStrength: Number(matValue("piston_body", "normal_strength",0.0))
 property real pistonBodyOcclusionAmount: Number(matValue("piston_body", "occlusion_amount",0.0))
 property string pistonBodyAlphaMode: String(matValue("piston_body", "alpha_mode", "default"))
 property real pistonBodyAlphaCutoff: Number(matValue("piston_body", "alpha_cutoff",0.0))
 property string pistonBodyTexturePath: normalizedTexturePath(matValue("piston_body", "texture_path", ""))

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
 property real pistonRodThickness: Number(matValue("piston_rod", "thickness",0.0))
 property real pistonRodAttenuationDistance: Number(matValue("piston_rod", "attenuation_distance",10000.0))
 property color pistonRodAttenuationColor: matValue("piston_rod", "attenuation_color", "#ffffff")
 property color pistonRodEmissiveColor: matValue("piston_rod", "emissive_color", "#000000")
 property real pistonRodEmissiveIntensity: Number(matValue("piston_rod", "emissive_intensity",0.0))
 property real pistonRodNormalStrength: Number(matValue("piston_rod", "normal_strength",0.0))
 property real pistonRodOcclusionAmount: Number(matValue("piston_rod", "occlusion_amount",0.0))
 property string pistonRodAlphaMode: String(matValue("piston_rod", "alpha_mode", "default"))
 property real pistonRodAlphaCutoff: Number(matValue("piston_rod", "alpha_cutoff",0.0))
 property string pistonRodTexturePath: normalizedTexturePath(matValue("piston_rod", "texture_path", ""))

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
 property real jointTailThickness: Number(matValue("joint_tail", "thickness",0.0))
 property real jointTailAttenuationDistance: Number(matValue("joint_tail", "attenuation_distance",10000.0))
 property color jointTailAttenuationColor: matValue("joint_tail", "attenuation_color", "#ffffff")
 property color jointTailEmissiveColor: matValue("joint_tail", "emissive_color", "#000000")
 property real jointTailEmissiveIntensity: Number(matValue("joint_tail", "emissive_intensity",0.0))
 property real jointTailNormalStrength: Number(matValue("joint_tail", "normal_strength",0.0))
 property real jointTailOcclusionAmount: Number(matValue("joint_tail", "occlusion_amount",0.0))
 property string jointTailAlphaMode: String(matValue("joint_tail", "alpha_mode", "default"))
 property real jointTailAlphaCutoff: Number(matValue("joint_tail", "alpha_cutoff",0.0))
 property string jointTailTexturePath: normalizedTexturePath(matValue("joint_tail", "texture_path", ""))

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
 property real jointArmThickness: Number(matValue("joint_arm", "thickness",0.0))
 property real jointArmAttenuationDistance: Number(matValue("joint_arm", "attenuation_distance",10000.0))
 property color jointArmAttenuationColor: matValue("joint_arm", "attenuation_color", "#ffffff")
 property color jointArmEmissiveColor: matValue("joint_arm", "emissive_color", "#000000")
 property real jointArmEmissiveIntensity: Number(matValue("joint_arm", "emissive_intensity",0.0))
 property real jointArmNormalStrength: Number(matValue("joint_arm", "normal_strength",0.0))
 property real jointArmOcclusionAmount: Number(matValue("joint_arm", "occlusion_amount",0.0))
 property string jointArmAlphaMode: String(matValue("joint_arm", "alpha_mode", "default"))
 property real jointArmAlphaCutoff: Number(matValue("joint_arm", "alpha_cutoff",0.0))
 property string jointArmTexturePath: normalizedTexturePath(matValue("joint_arm", "texture_path", ""))

 // ===============================================================
 // JOINT ROD SPECIAL COLORS
 // ===============================================================

 property color jointRodOkColor: matValue("joint_rod", "ok_color", "#00ff55")
 property color jointRodErrorColor: matValue("joint_rod", "error_color", "#ff0000")

 // ===============================================================
 // HELPER FUNCTION
 // ===============================================================

 function emissiveVector(color, intensity) {
 var parsed = color
 if (parsed === undefined || parsed === null || parsed === "")
 parsed = Qt.darker("#000000", 1.0)
 else if (typeof parsed === "string")
 parsed = Qt.darker(parsed, 1.0)
 var factor = Number(intensity === undefined ? 1.0 : intensity)
 if (!isFinite(factor))
 factor = 1.0
 return Qt.vector3d(parsed.r * factor, parsed.g * factor, parsed.b * factor)
 }

// ===============================================================
// TEXTURE RESOURCES
// ===============================================================

readonly property Texture frameBaseColorTexture: Texture {
    source: root.resolveTextureSource(root.frameTexturePath)
    generateMipmaps: true
    minFilter: Texture.Linear
    magFilter: Texture.Linear
    tilingModeHorizontal: Texture.ClampToEdge
    tilingModeVertical: Texture.ClampToEdge
}

readonly property Texture leverBaseColorTexture: Texture {
    source: root.resolveTextureSource(root.leverTexturePath)
    generateMipmaps: true
    minFilter: Texture.Linear
    magFilter: Texture.Linear
    tilingModeHorizontal: Texture.ClampToEdge
    tilingModeVertical: Texture.ClampToEdge
}

readonly property Texture tailRodBaseColorTexture: Texture {
    source: root.resolveTextureSource(root.tailRodTexturePath)
    generateMipmaps: true
    minFilter: Texture.Linear
    magFilter: Texture.Linear
    tilingModeHorizontal: Texture.ClampToEdge
    tilingModeVertical: Texture.ClampToEdge
}

readonly property Texture cylinderBaseColorTexture: Texture {
    source: root.resolveTextureSource(root.cylinderTexturePath)
    generateMipmaps: true
    minFilter: Texture.Linear
    magFilter: Texture.Linear
    tilingModeHorizontal: Texture.ClampToEdge
    tilingModeVertical: Texture.ClampToEdge
}

readonly property Texture pistonBodyBaseColorTexture: Texture {
    source: root.resolveTextureSource(root.pistonBodyTexturePath)
    generateMipmaps: true
    minFilter: Texture.Linear
    magFilter: Texture.Linear
    tilingModeHorizontal: Texture.ClampToEdge
    tilingModeVertical: Texture.ClampToEdge
}

readonly property Texture pistonRodBaseColorTexture: Texture {
    source: root.resolveTextureSource(root.pistonRodTexturePath)
    generateMipmaps: true
    minFilter: Texture.Linear
    magFilter: Texture.Linear
    tilingModeHorizontal: Texture.ClampToEdge
    tilingModeVertical: Texture.ClampToEdge
}

readonly property Texture jointTailBaseColorTexture: Texture {
    source: root.resolveTextureSource(root.jointTailTexturePath)
    generateMipmaps: true
    minFilter: Texture.Linear
    magFilter: Texture.Linear
    tilingModeHorizontal: Texture.ClampToEdge
    tilingModeVertical: Texture.ClampToEdge
}

readonly property Texture jointArmBaseColorTexture: Texture {
    source: root.resolveTextureSource(root.jointArmTexturePath)
    generateMipmaps: true
    minFilter: Texture.Linear
    magFilter: Texture.Linear
    tilingModeHorizontal: Texture.ClampToEdge
    tilingModeVertical: Texture.ClampToEdge
}

// ===============================================================
// MATERIAL INSTANCES
// ===============================================================

readonly property PrincipledMaterial frameMaterial: PrincipledMaterial {
    baseColor: root.frameBaseColor
    metalness: root.frameMetalness
    roughness: root.frameRoughness
    specularAmount: root.frameSpecularAmount
    specularTint: root.frameSpecularTint
    clearcoatAmount: root.frameClearcoat
    clearcoatRoughnessAmount: root.frameClearcoatRoughness
    transmissionFactor: root.frameTransmission
    opacity: root.frameOpacity
    indexOfRefraction: root.frameIor
    thicknessFactor: root.frameThickness
    attenuationDistance: root.frameAttenuationDistance
    attenuationColor: root.frameAttenuationColor
    emissiveFactor: root.emissiveVector(root.frameEmissiveColor, root.frameEmissiveIntensity)
    normalStrength: root.frameNormalStrength
    occlusionAmount: root.frameOcclusionAmount
    alphaMode: root.alphaModeValue(root.frameAlphaMode)
    alphaCutoff: root.frameAlphaCutoff
    baseColorMap: root.textureEnabled(root.frameTexturePath) ? root.frameBaseColorTexture : null
}

readonly property PrincipledMaterial leverMaterial: PrincipledMaterial {
    baseColor: root.leverBaseColor
    metalness: root.leverMetalness
    roughness: root.leverRoughness
    specularAmount: root.leverSpecularAmount
    specularTint: root.leverSpecularTint
    clearcoatAmount: root.leverClearcoat
    clearcoatRoughnessAmount: root.leverClearcoatRoughness
    transmissionFactor: root.leverTransmission
    opacity: root.leverOpacity
    indexOfRefraction: root.leverIor
    thicknessFactor: root.leverThickness
    attenuationDistance: root.leverAttenuationDistance
    attenuationColor: root.leverAttenuationColor
    emissiveFactor: root.emissiveVector(root.leverEmissiveColor, root.leverEmissiveIntensity)
    normalStrength: root.leverNormalStrength
    occlusionAmount: root.leverOcclusionAmount
    alphaMode: root.alphaModeValue(root.leverAlphaMode)
    alphaCutoff: root.leverAlphaCutoff
    baseColorMap: root.textureEnabled(root.leverTexturePath) ? root.leverBaseColorTexture : null
}

readonly property PrincipledMaterial tailRodMaterial: PrincipledMaterial {
    baseColor: root.tailRodBaseColor
    metalness: root.tailRodMetalness
    roughness: root.tailRodRoughness
    specularAmount: root.tailRodSpecularAmount
    specularTint: root.tailRodSpecularTint
    clearcoatAmount: root.tailRodClearcoat
    clearcoatRoughnessAmount: root.tailRodClearcoatRoughness
    transmissionFactor: root.tailRodTransmission
    opacity: root.tailRodOpacity
    indexOfRefraction: root.tailRodIor
    thicknessFactor: root.tailRodThickness
    attenuationDistance: root.tailRodAttenuationDistance
    attenuationColor: root.tailRodAttenuationColor
    emissiveFactor: root.emissiveVector(root.tailRodEmissiveColor, root.tailRodEmissiveIntensity)
    normalStrength: root.tailRodNormalStrength
    occlusionAmount: root.tailRodOcclusionAmount
    alphaMode: root.alphaModeValue(root.tailRodAlphaMode)
    alphaCutoff: root.tailRodAlphaCutoff
    baseColorMap: root.textureEnabled(root.tailRodTexturePath) ? root.tailRodBaseColorTexture : null
}

readonly property PrincipledMaterial cylinderMaterial: PrincipledMaterial {
    baseColor: root.cylinderBaseColor
    metalness: root.cylinderMetalness
    roughness: root.cylinderRoughness
    specularAmount: root.cylinderSpecularAmount
    specularTint: root.cylinderSpecularTint
    clearcoatAmount: root.cylinderClearcoat
    clearcoatRoughnessAmount: root.cylinderClearcoatRoughness
    transmissionFactor: root.cylinderTransmission
    opacity: root.cylinderOpacity
    indexOfRefraction: root.cylinderIor
    thicknessFactor: root.cylinderThickness
    attenuationDistance: root.cylinderAttenuationDistance
    attenuationColor: root.cylinderAttenuationColor
    emissiveFactor: root.emissiveVector(root.cylinderEmissiveColor, root.cylinderEmissiveIntensity)
    normalStrength: root.cylinderNormalStrength
    occlusionAmount: root.cylinderOcclusionAmount
    alphaMode: root.alphaModeValue(root.cylinderAlphaMode)
    alphaCutoff: root.cylinderAlphaCutoff
    baseColorMap: root.textureEnabled(root.cylinderTexturePath) ? root.cylinderBaseColorTexture : null
}

readonly property PrincipledMaterial jointTailMaterial: PrincipledMaterial {
    baseColor: root.jointTailBaseColor
    metalness: root.jointTailMetalness
    roughness: root.jointTailRoughness
    specularAmount: root.jointTailSpecularAmount
    specularTint: root.jointTailSpecularTint
    clearcoatAmount: root.jointTailClearcoat
    clearcoatRoughnessAmount: root.jointTailClearcoatRoughness
    transmissionFactor: root.jointTailTransmission
    opacity: root.jointTailOpacity
    indexOfRefraction: root.jointTailIor
    thicknessFactor: root.jointTailThickness
    attenuationDistance: root.jointTailAttenuationDistance
    attenuationColor: root.jointTailAttenuationColor
    emissiveFactor: root.emissiveVector(root.jointTailEmissiveColor, root.jointTailEmissiveIntensity)
    normalStrength: root.jointTailNormalStrength
    occlusionAmount: root.jointTailOcclusionAmount
    alphaMode: root.alphaModeValue(root.jointTailAlphaMode)
    alphaCutoff: root.jointTailAlphaCutoff
    baseColorMap: root.textureEnabled(root.jointTailTexturePath) ? root.jointTailBaseColorTexture : null
}

readonly property PrincipledMaterial jointArmMaterial: PrincipledMaterial {
    baseColor: root.jointArmBaseColor
    metalness: root.jointArmMetalness
    roughness: root.jointArmRoughness
    specularAmount: root.jointArmSpecularAmount
    specularTint: root.jointArmSpecularTint
    clearcoatAmount: root.jointArmClearcoat
    clearcoatRoughnessAmount: root.jointArmClearcoatRoughness
    transmissionFactor: root.jointArmTransmission
    opacity: root.jointArmOpacity
    indexOfRefraction: root.jointArmIor
    thicknessFactor: root.jointArmThickness
    attenuationDistance: root.jointArmAttenuationDistance
    attenuationColor: root.jointArmAttenuationColor
    emissiveFactor: root.emissiveVector(root.jointArmEmissiveColor, root.jointArmEmissiveIntensity)
    normalStrength: root.jointArmNormalStrength
    occlusionAmount: root.jointArmOcclusionAmount
    alphaMode: root.alphaModeValue(root.jointArmAlphaMode)
    alphaCutoff: root.jointArmAlphaCutoff
    baseColorMap: root.textureEnabled(root.jointArmTexturePath) ? root.jointArmBaseColorTexture : null
}

    readonly property PrincipledMaterial pistonBodyMaterial: PrincipledMaterial {
        baseColor: root.pistonBodyBaseColor
        metalness: root.pistonBodyMetalness
        roughness: root.pistonBodyRoughness
        specularAmount: root.pistonBodySpecularAmount
        specularTint: root.pistonBodySpecularTint
        clearcoatAmount: root.pistonBodyClearcoat
        clearcoatRoughnessAmount: root.pistonBodyClearcoatRoughness
        transmissionFactor: root.pistonBodyTransmission
        opacity: root.pistonBodyOpacity
        indexOfRefraction: root.pistonBodyIor
        thicknessFactor: root.pistonBodyThickness
        attenuationDistance: root.pistonBodyAttenuationDistance
        attenuationColor: root.pistonBodyAttenuationColor
        emissiveFactor: root.emissiveVector(root.pistonBodyEmissiveColor, root.pistonBodyEmissiveIntensity)
        normalStrength: root.pistonBodyNormalStrength
        occlusionAmount: root.pistonBodyOcclusionAmount
        alphaMode: root.alphaModeValue(root.pistonBodyAlphaMode)
        alphaCutoff: root.pistonBodyAlphaCutoff
        baseColorMap: root.textureEnabled(root.pistonBodyTexturePath) ? root.pistonBodyBaseColorTexture : null
    }

    readonly property PrincipledMaterial pistonRodMaterial: PrincipledMaterial {
        baseColor: root.pistonRodBaseColor
        metalness: root.pistonRodMetalness
        roughness: root.pistonRodRoughness
        specularAmount: root.pistonRodSpecularAmount
        specularTint: root.pistonRodSpecularTint
        clearcoatAmount: root.pistonRodClearcoat
        clearcoatRoughnessAmount: root.pistonRodClearcoatRoughness
        transmissionFactor: root.pistonRodTransmission
        opacity: root.pistonRodOpacity
        indexOfRefraction: root.pistonRodIor
        thicknessFactor: root.pistonRodThickness
        attenuationDistance: root.pistonRodAttenuationDistance
        attenuationColor: root.pistonRodAttenuationColor
        emissiveFactor: root.emissiveVector(root.pistonRodEmissiveColor, root.pistonRodEmissiveIntensity)
        normalStrength: root.pistonRodNormalStrength
        occlusionAmount: root.pistonRodOcclusionAmount
        alphaMode: root.alphaModeValue(root.pistonRodAlphaMode)
        alphaCutoff: root.pistonRodAlphaCutoff
        baseColorMap: root.textureEnabled(root.pistonRodTexturePath) ? root.pistonRodBaseColorTexture : null
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
