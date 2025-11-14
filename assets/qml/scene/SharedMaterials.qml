import QtQuick
import QtQuick3D
import "../components"
import "../components/MaterialCompat.js" as MaterialCompat
// qmllint disable import

pragma ComponentBehavior: Bound

// SharedMaterials — централизованные PBR материалы (минимальный набор Qt 6.10)
QtObject {
    id: root

    // --- ИНИЦИАЛЬНЫЕ ДАННЫЕ ---
    property var initialSharedMaterials: null
    property var materialsDefaults: root.initialSharedMaterials

    // --- TEXTURE LOADERS (using AssetsLoader for fallback support) ---
    property AssetsLoader frameBaseColorTexture: AssetsLoader {
        assetName: "frame"
        primarySource: resolveTextureSource(matValue("frame", "texture_path", ""))
        loggingEnabled: true
    }

    property AssetsLoader leverBaseColorTexture: AssetsLoader {
        assetName: "lever"
        primarySource: resolveTextureSource(matValue("lever", "texture_path", ""))
        loggingEnabled: true
    }

    property AssetsLoader tailRodBaseColorTexture: AssetsLoader {
        assetName: "tail_rod"
        primarySource: resolveTextureSource(matValue("tail_rod", "texture_path", ""))
        loggingEnabled: true
    }

    property AssetsLoader cylinderBaseColorTexture: AssetsLoader {
        assetName: "cylinder"
        primarySource: resolveTextureSource(matValue("cylinder", "texture_path", ""))
        loggingEnabled: true
    }

    property AssetsLoader pistonBodyBaseColorTexture: AssetsLoader {
        assetName: "piston_body"
        primarySource: resolveTextureSource(matValue("piston_body", "texture_path", ""))
        loggingEnabled: true
    }

    property AssetsLoader pistonRodBaseColorTexture: AssetsLoader {
        assetName: "piston_rod"
        primarySource: resolveTextureSource(matValue("piston_rod", "texture_path", ""))
        loggingEnabled: true
    }

    property AssetsLoader jointTailBaseColorTexture: AssetsLoader {
        assetName: "joint_tail"
        primarySource: resolveTextureSource(matValue("joint_tail", "texture_path", ""))
        loggingEnabled: true
    }

    property AssetsLoader jointArmBaseColorTexture: AssetsLoader {
        assetName: "joint_arm"
        primarySource: resolveTextureSource(matValue("joint_arm", "texture_path", ""))
        loggingEnabled: true
    }

    property AssetsLoader jointRodBaseColorTexture: AssetsLoader {
        assetName: "joint_rod"
        primarySource: resolveTextureSource(matValue("joint_rod", "texture_path", ""))
        loggingEnabled: true
    }

    // --- СЫРЬЕВЫЕ СВОЙСТВА (МИНИМАЛЬНЫЕ ПОДДЕРЖИВАЕМЫЕ PRINCIPLEDMATERIAL Qt 6.10) ---
    // FRAME
    property color frameBaseColor: "#ffffff"
    property real frameMetalness: 0.0
    property real frameRoughness: 0.4
    property real frameOpacity: 1.0
    property real frameClearcoat: 0.0
    property real frameClearcoatRoughness: 0.3
    property color frameEmissiveColor: "#000000"
    property real frameEmissiveIntensity: 0.0
    property real frameNormalStrength: 1.0
    property real frameOcclusionAmount: 1.0
    property string frameAlphaMode: "default"   // default|blend|mask
    property real frameAlphaCutoff: 0.5

    // LEVER
    property color leverBaseColor: "#cccccc"
    property real leverMetalness: 1.0
    property real leverRoughness: 0.28
    property real leverOpacity: 1.0
    property real leverClearcoat: 0.2
    property real leverClearcoatRoughness: 0.1
    property color leverEmissiveColor: "#000000"
    property real leverEmissiveIntensity: 0.0
    property real leverNormalStrength: 1.0
    property real leverOcclusionAmount: 1.0
    property string leverAlphaMode: "default"
    property real leverAlphaCutoff: 0.5

    // TAIL ROD
    property color tailRodBaseColor: "#d5d9df"
    property real tailRodMetalness: 1.0
    property real tailRodRoughness: 0.3
    property real tailRodOpacity: 1.0
    property real tailRodClearcoat: 0.0
    property real tailRodClearcoatRoughness: 0.0
    property color tailRodEmissiveColor: "#000000"
    property real tailRodEmissiveIntensity: 0.0
    property real tailRodNormalStrength: 1.0
    property real tailRodOcclusionAmount: 1.0
    property string tailRodAlphaMode: "default"
    property real tailRodAlphaCutoff: 0.5

    // CYLINDER (GLASS-LIKE)
    property color cylinderBaseColor: "#e1f5ff"
    property real cylinderMetalness: 0.0
    property real cylinderRoughness: 0.2
    property real cylinderOpacity: 0.3
    property color cylinderEmissiveColor: "#000000"
    property real cylinderEmissiveIntensity: 0.0
    property real cylinderNormalStrength: 1.0
    property real cylinderOcclusionAmount: 1.0
    property string cylinderAlphaMode: "blend"   // прозрачность включена
    property real cylinderAlphaCutoff: 0.5

    // PISTON BODY
    property color pistonBodyBaseColor: "#ff3c6e"
    property real pistonBodyMetalness: 1.0
    property real pistonBodyRoughness: 0.26
    property real pistonBodyOpacity: 1.0
    property real pistonBodyClearcoat: 0.15
    property real pistonBodyClearcoatRoughness: 0.08
    property color pistonBodyEmissiveColor: "#000000"
    property real pistonBodyEmissiveIntensity: 0.0
    property real pistonBodyNormalStrength: 1.0
    property real pistonBodyOcclusionAmount: 1.0
    property string pistonBodyAlphaMode: "default"
    property real pistonBodyAlphaCutoff: 0.5

    // PISTON ROD
    property color pistonRodBaseColor: "#ececec"
    property real pistonRodMetalness: 1.0
    property real pistonRodRoughness: 0.18
    property real pistonRodOpacity: 1.0
    property real pistonRodClearcoat: 0.1
    property real pistonRodClearcoatRoughness: 0.05
    property color pistonRodEmissiveColor: "#000000"
    property real pistonRodEmissiveIntensity: 0.0
    property real pistonRodNormalStrength: 1.0
    property real pistonRodOcclusionAmount: 1.0
    property string pistonRodAlphaMode: "default"
    property real pistonRodAlphaCutoff: 0.5

    // JOINT TAIL
    property color jointTailBaseColor: "#2a82ff"
    property real jointTailMetalness: 0.9
    property real jointTailRoughness: 0.35
    property real jointTailOpacity: 1.0
    property real jointTailClearcoat: 0.1
    property real jointTailClearcoatRoughness: 0.08
    property color jointTailEmissiveColor: "#000000"
    property real jointTailEmissiveIntensity: 0.0
    property real jointTailNormalStrength: 1.0
    property real jointTailOcclusionAmount: 1.0
    property string jointTailAlphaMode: "default"
    property real jointTailAlphaCutoff: 0.5

    // JOINT ARM
    property color jointArmBaseColor: "#ff9c3a"
    property real jointArmMetalness: 0.9
    property real jointArmRoughness: 0.32
    property real jointArmOpacity: 1.0
    property real jointArmClearcoat: 0.12
    property real jointArmClearcoatRoughness: 0.08
    property color jointArmEmissiveColor: "#000000"
    property real jointArmEmissiveIntensity: 0.0
    property real jointArmNormalStrength: 1.0
    property real jointArmOcclusionAmount: 1.0
    property string jointArmAlphaMode: "default"
    property real jointArmAlphaCutoff: 0.5

    // JOINT ROD (добавлен пропущенный материал)
    property color jointRodBaseColor: "#00ff55"
    property real jointRodMetalness: 0.9
    property real jointRodRoughness: 0.3
    property real jointRodOpacity: 1.0
    property real jointRodClearcoat: 0.05
    property real jointRodClearcoatRoughness: 0.08
    property color jointRodEmissiveColor: "#000000"
    property real jointRodEmissiveIntensity: 0.0
    property real jointRodNormalStrength: 1.0
    property real jointRodOcclusionAmount: 1.0
    property string jointRodAlphaMode: "default"
    property real jointRodAlphaCutoff: 0.5

    // JOINT ROD UI COLORS (для AnimatedRodMaterial)
    property color jointRodOkColor: matValue("joint_rod", "ok_color", "#00ff55")
    property color jointRodErrorColor: matValue("joint_rod", "error_color", "#ff0000")

    // --- АЛИАСЫ КЛЮЧЕЙ ---
    readonly property var materialKeyAliases: ({ tail: "tail_rod", tailrod: "tail_rod", glass: "cylinder", metal: "lever" })

    // --- АЛИАСЫ СВОЙСТВ (оставляем только поддерживаемые) ---
    readonly property var materialPropertyAliases: ({
        base_color: ["baseColor", "color"],
        normal_strength: ["normalStrength"],
        occlusion_amount: ["occlusionAmount"],
        alpha_mode: ["alphaMode"],
        alpha_cutoff: ["alphaCutoff"],
        texture_path: ["texturePath"],
        warning_color: ["warningColor"],
        ok_color: ["okColor"],
        error_color: ["errorColor"],
        metalness: ["metalness"],
        roughness: ["roughness"],
        opacity: ["opacity"],
        clearcoat: ["clearcoat"],
        clearcoat_roughness: ["clearcoatRoughness"],
        emissive_color: ["emissiveColor"],
        emissive_intensity: ["emissiveIntensity"]
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
        if (normalized !== canonical) names.push(normalized)
        var aliasList = root.materialPropertyAliases[normalized]
        if (aliasList) {
            for (var i = 0; i < aliasList.length; ++i) {
                var alias = aliasList[i]
                if (names.indexOf(alias) === -1) names.push(alias)
                var aliasLower = String(alias).toLowerCase()
                if (names.indexOf(aliasLower) === -1) names.push(aliasLower)
            }
        }
        return names
    }

    function matValue(materialKey, propertyName, fallback) {
        var canonicalKey = canonicalMaterialKey(materialKey)
        if (!root.materialsDefaults || root.materialsDefaults[canonicalKey] === undefined)
            return fallback
        var bucket = root.materialsDefaults[canonicalKey]
        if (!bucket) return fallback
        var candidates = candidatePropertyNames(propertyName)
        for (var i = 0; i < candidates.length; ++i) {
            var candidate = candidates[i]
            if (bucket[candidate] !== undefined) return bucket[candidate]
        }
        return fallback
    }

    // --- ХЕЛПЕРЫ ---
    function normalizedTexturePath(value) {
        if (value === undefined || value === null) return ""
        var text = String(value).trim()
        if (!text || text === "—") return ""
        return text.replace(/\\\\/g, "/")
    }
    function textureEnabled(path) { return path && String(path).trim() !== "" && String(path).trim() !== "—" }
    function resolveTextureSource(path) {
        if (!root.textureEnabled(path)) return ""
        var normalized = root.normalizedTexturePath(path)
        if (!normalized) return ""
        if (normalized.startsWith("qrc:/") || normalized.indexOf("://") > 0 || normalized.startsWith("data:")) return normalized
        return Qt.resolvedUrl(normalized)
    }
    function alphaModeValue(mode) {
        var text = String(mode || "").toLowerCase()
        switch (text) {
        case "mask": return PrincipledMaterial.Mask
        case "blend": return PrincipledMaterial.Blend
        case "opaque": return PrincipledMaterial.Opaque
        default: return PrincipledMaterial.Default
        }
    }

    // Реактивное применение PBR к материалу (унифицировано)
    function _applyPbrTo(mat, props) { try { MaterialCompat.applyPbr(mat, props) } catch (e) {} }

    // --- СБОР СВОЙСТВ ---
    function _frameProps() { return ({ baseColor: root.frameBaseColor, metalness: root.frameMetalness, roughness: root.frameRoughness, opacity: root.frameOpacity, clearcoatAmount: root.frameClearcoat, clearcoatRoughnessAmount: root.frameClearcoatRoughness, emissiveColor: root.frameEmissiveColor, emissiveIntensity: root.frameEmissiveIntensity, normalStrength: root.frameNormalStrength, occlusionAmount: root.frameOcclusionAmount, alphaMode: root.frameAlphaMode, alphaCutoff: root.frameAlphaCutoff }) }
    function _leverProps() { return ({ baseColor: root.leverBaseColor, metalness: root.leverMetalness, roughness: root.leverRoughness, opacity: root.leverOpacity, clearcoatAmount: root.leverClearcoat, clearcoatRoughnessAmount: root.leverClearcoatRoughness, emissiveColor: root.leverEmissiveColor, emissiveIntensity: root.leverEmissiveIntensity, normalStrength: root.leverNormalStrength, occlusionAmount: root.leverOcclusionAmount, alphaMode: root.leverAlphaMode, alphaCutoff: root.leverAlphaCutoff }) }
    function _tailRodProps() { return ({ baseColor: root.tailRodBaseColor, metalness: root.tailRodMetalness, roughness: root.tailRodRoughness, opacity: root.tailRodOpacity, clearcoatAmount: root.tailRodClearcoat, clearcoatRoughnessAmount: root.tailRodClearcoatRoughness, emissiveColor: root.tailRodEmissiveColor, emissiveIntensity: root.tailRodEmissiveIntensity, normalStrength: root.tailRodNormalStrength, occlusionAmount: root.tailRodOcclusionAmount, alphaMode: root.tailRodAlphaMode, alphaCutoff: root.tailRodAlphaCutoff }) }
    function _cylinderProps() { return ({ baseColor: root.cylinderBaseColor, metalness: root.cylinderMetalness, roughness: root.cylinderRoughness, opacity: root.cylinderOpacity, emissiveColor: root.cylinderEmissiveColor, emissiveIntensity: root.cylinderEmissiveIntensity, normalStrength: root.cylinderNormalStrength, occlusionAmount: root.cylinderOcclusionAmount, alphaMode: root.cylinderAlphaMode, alphaCutoff: root.cylinderAlphaCutoff }) }
    function _pistonBodyProps() { return ({ baseColor: root.pistonBodyBaseColor, metalness: root.pistonBodyMetalness, roughness: root.pistonBodyRoughness, opacity: root.pistonBodyOpacity, clearcoatAmount: root.pistonBodyClearcoat, clearcoatRoughnessAmount: root.pistonBodyClearcoatRoughness, emissiveColor: root.pistonBodyEmissiveColor, emissiveIntensity: root.pistonBodyEmissiveIntensity, normalStrength: root.pistonBodyNormalStrength, occlusionAmount: root.pistonBodyOcclusionAmount, alphaMode: root.pistonBodyAlphaMode, alphaCutoff: root.pistonBodyAlphaCutoff }) }
    function _pistonRodProps() { return ({ baseColor: root.pistonRodBaseColor, metalness: root.pistonRodMetalness, roughness: root.pistonRodRoughness, opacity: root.pistonRodOpacity, clearcoatAmount: root.pistonRodClearcoat, clearcoatRoughnessAmount: root.pistonRodClearcoatRoughness, emissiveColor: root.pistonRodEmissiveColor, emissiveIntensity: root.pistonRodEmissiveIntensity, normalStrength: root.pistonRodNormalStrength, occlusionAmount: root.pistonRodOcclusionAmount, alphaMode: root.pistonRodAlphaMode, alphaCutoff: root.pistonRodAlphaCutoff }) }
    function _jointTailProps() { return ({ baseColor: root.jointTailBaseColor, metalness: root.jointTailMetalness, roughness: root.jointTailRoughness, opacity: root.jointTailOpacity, clearcoatAmount: root.jointTailClearcoat, clearcoatRoughnessAmount: root.jointTailClearcoatRoughness, emissiveColor: root.jointTailEmissiveColor, emissiveIntensity: root.jointTailEmissiveIntensity, normalStrength: root.jointTailNormalStrength, occlusionAmount: root.jointTailOcclusionAmount, alphaMode: root.jointTailAlphaMode, alphaCutoff: root.jointTailAlphaCutoff }) }
    function _jointArmProps() { return ({ baseColor: root.jointArmBaseColor, metalness: root.jointArmMetalness, roughness: root.jointArmRoughness, opacity: root.jointArmOpacity, clearcoatAmount: root.jointArmClearcoat, clearcoatRoughnessAmount: root.jointArmClearcoatRoughness, emissiveColor: root.jointArmEmissiveColor, emissiveIntensity: root.jointArmEmissiveIntensity, normalStrength: root.jointArmNormalStrength, occlusionAmount: root.jointArmOcclusionAmount, alphaMode: root.jointArmAlphaMode, alphaCutoff: root.jointArmAlphaCutoff }) }
    function _jointRodProps() { return ({ baseColor: root.jointRodBaseColor, metalness: root.jointRodMetalness, roughness: root.jointRodRoughness, opacity: root.jointRodOpacity, clearcoatAmount: root.jointRodClearcoat, clearcoatRoughnessAmount: root.jointRodClearcoatRoughness, emissiveColor: root.jointRodEmissiveColor, emissiveIntensity: root.jointRodEmissiveIntensity, normalStrength: root.jointRodNormalStrength, occlusionAmount: root.jointRodOcclusionAmount, alphaMode: root.jointRodAlphaMode, alphaCutoff: root.jointRodAlphaCutoff }) }

    // --- ПРИМЕНЕНИЕ ---
    function _applyFrameMaterial(mat) { _applyPbrTo(mat, _frameProps()); MaterialCompat.applyEmissive(mat, root.frameEmissiveColor, root.frameEmissiveIntensity) }
    function _applyLeverMaterial(mat) { _applyPbrTo(mat, _leverProps()); MaterialCompat.applyEmissive(mat, root.leverEmissiveColor, root.leverEmissiveIntensity) }
    function _applyTailRodMaterial(mat) { _applyPbrTo(mat, _tailRodProps()); MaterialCompat.applyEmissive(mat, root.tailRodEmissiveColor, root.tailRodEmissiveIntensity) }
    function _applyCylinderMaterial(mat) { _applyPbrTo(mat, _cylinderProps()); MaterialCompat.applyEmissive(mat, root.cylinderEmissiveColor, root.cylinderEmissiveIntensity) }
    function _applyPistonBodyMaterial(mat) { _applyPbrTo(mat, _pistonBodyProps()); MaterialCompat.applyEmissive(mat, root.pistonBodyEmissiveColor, root.pistonBodyEmissiveIntensity) }
    function _applyPistonRodMaterial(mat) { _applyPbrTo(mat, _pistonRodProps()); MaterialCompat.applyEmissive(mat, root.pistonRodEmissiveColor, root.pistonRodEmissiveIntensity) }
    function _applyJointTailMaterial(mat) { _applyPbrTo(mat, _jointTailProps()); MaterialCompat.applyEmissive(mat, root.jointTailEmissiveColor, root.jointTailEmissiveIntensity) }
    function _applyJointArmMaterial(mat) { _applyPbrTo(mat, _jointArmProps()); MaterialCompat.applyEmissive(mat, root.jointArmEmissiveColor, root.jointArmEmissiveIntensity) }
    function _applyJointRodMaterial(mat) { _applyPbrTo(mat, _jointRodProps()); MaterialCompat.applyEmissive(mat, root.jointRodEmissiveColor, root.jointRodEmissiveIntensity) }

    // --- МАТЕРИАЛЫ --- (идентификаторы; свойства применяются через compat)
    property PrincipledMaterial frameMaterial: PrincipledMaterial { id: frameMaterial; Component.onCompleted: _applyFrameMaterial(this) }
    property PrincipledMaterial leverMaterial: PrincipledMaterial { id: leverMaterial; Component.onCompleted: _applyLeverMaterial(this) }
    property PrincipledMaterial tailRodMaterial: PrincipledMaterial { id: tailRodMaterial; Component.onCompleted: _applyTailRodMaterial(this) }
    property PrincipledMaterial cylinderMaterial: PrincipledMaterial { id: cylinderMaterial; Component.onCompleted: _applyCylinderMaterial(this) }
    property PrincipledMaterial pistonBodyMaterial: PrincipledMaterial { id: pistonBodyMaterial; Component.onCompleted: _applyPistonBodyMaterial(this) }
    property PrincipledMaterial pistonRodMaterial: PrincipledMaterial { id: pistonRodMaterial; Component.onCompleted: _applyPistonRodMaterial(this) }
    property PrincipledMaterial jointTailMaterial: PrincipledMaterial { id: jointTailMaterial; Component.onCompleted: _applyJointTailMaterial(this) }
    property PrincipledMaterial jointArmMaterial: PrincipledMaterial { id: jointArmMaterial; Component.onCompleted: _applyJointArmMaterial(this) }
    property PrincipledMaterial jointRodMaterial: PrincipledMaterial { id: jointRodMaterial; Component.onCompleted: _applyJointRodMaterial(this) }

    // --- ТРИГГЕРЫ ОБНОВЛЕНИЯ ---
    onFrameBaseColorChanged: _applyFrameMaterial(frameMaterial)
    onFrameMetalnessChanged: _applyFrameMaterial(frameMaterial)
    onFrameRoughnessChanged: _applyFrameMaterial(frameMaterial)
    onFrameClearcoatChanged: _applyFrameMaterial(frameMaterial)
    onFrameClearcoatRoughnessChanged: _applyFrameMaterial(frameMaterial)
    onFrameEmissiveColorChanged: _applyFrameMaterial(frameMaterial)
    onFrameEmissiveIntensityChanged: _applyFrameMaterial(frameMaterial)
    onFrameNormalStrengthChanged: _applyFrameMaterial(frameMaterial)
    onFrameOcclusionAmountChanged: _applyFrameMaterial(frameMaterial)
    onFrameAlphaModeChanged: _applyFrameMaterial(frameMaterial)
    onFrameAlphaCutoffChanged: _applyFrameMaterial(frameMaterial)

    onLeverBaseColorChanged: _applyLeverMaterial(leverMaterial)
    onLeverMetalnessChanged: _applyLeverMaterial(leverMaterial)
    onLeverRoughnessChanged: _applyLeverMaterial(leverMaterial)
    onLeverClearcoatChanged: _applyLeverMaterial(leverMaterial)
    onLeverClearcoatRoughnessChanged: _applyLeverMaterial(leverMaterial)
    onLeverEmissiveColorChanged: _applyLeverMaterial(leverMaterial)
    onLeverEmissiveIntensityChanged: _applyLeverMaterial(leverMaterial)
    onLeverNormalStrengthChanged: _applyLeverMaterial(leverMaterial)
    onLeverOcclusionAmountChanged: _applyLeverMaterial(leverMaterial)
    onLeverAlphaModeChanged: _applyLeverMaterial(leverMaterial)
    onLeverAlphaCutoffChanged: _applyLeverMaterial(leverMaterial)

    onTailRodBaseColorChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodMetalnessChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodRoughnessChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodClearcoatChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodClearcoatRoughnessChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodEmissiveColorChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodEmissiveIntensityChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodNormalStrengthChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodOcclusionAmountChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodAlphaModeChanged: _applyTailRodMaterial(tailRodMaterial)
    onTailRodAlphaCutoffChanged: _applyTailRodMaterial(tailRodMaterial)

    onCylinderBaseColorChanged: _applyCylinderMaterial(cylinderMaterial)
    onCylinderMetalnessChanged: _applyCylinderMaterial(cylinderMaterial)
    onCylinderRoughnessChanged: _applyCylinderMaterial(cylinderMaterial)
    onCylinderOpacityChanged: _applyCylinderMaterial(cylinderMaterial)
    onCylinderEmissiveColorChanged: _applyCylinderMaterial(cylinderMaterial)
    onCylinderEmissiveIntensityChanged: _applyCylinderMaterial(cylinderMaterial)
    onCylinderNormalStrengthChanged: _applyCylinderMaterial(cylinderMaterial)
    onCylinderOcclusionAmountChanged: _applyCylinderMaterial(cylinderMaterial)
    onCylinderAlphaModeChanged: _applyCylinderMaterial(cylinderMaterial)
    onCylinderAlphaCutoffChanged: _applyCylinderMaterial(cylinderMaterial)

    onPistonBodyBaseColorChanged: _applyPistonBodyMaterial(pistonBodyMaterial)
    onPistonBodyMetalnessChanged: _applyPistonBodyMaterial(pistonBodyMaterial)
    onPistonBodyRoughnessChanged: _applyPistonBodyMaterial(pistonBodyMaterial)
    onPistonBodyClearcoatChanged: _applyPistonBodyMaterial(pistonBodyMaterial)
    onPistonBodyClearcoatRoughnessChanged: _applyPistonBodyMaterial(pistonBodyMaterial)
    onPistonBodyEmissiveColorChanged: _applyPistonBodyMaterial(pistonBodyMaterial)
    onPistonBodyEmissiveIntensityChanged: _applyPistonBodyMaterial(pistonBodyMaterial)

    onPistonRodBaseColorChanged: _applyPistonRodMaterial(pistonRodMaterial)
    onPistonRodMetalnessChanged: _applyPistonRodMaterial(pistonRodMaterial)
    onPistonRodRoughnessChanged: _applyPistonRodMaterial(pistonRodMaterial)
    onPistonRodClearcoatChanged: _applyPistonRodMaterial(pistonRodMaterial)
    onPistonRodClearcoatRoughnessChanged: _applyPistonRodMaterial(pistonRodMaterial)
    onPistonRodEmissiveColorChanged: _applyPistonRodMaterial(pistonRodMaterial)
    onPistonRodEmissiveIntensityChanged: _applyPistonRodMaterial(pistonRodMaterial)

    onJointTailBaseColorChanged: _applyJointTailMaterial(jointTailMaterial)
    onJointTailMetalnessChanged: _applyJointTailMaterial(jointTailMaterial)
    onJointTailRoughnessChanged: _applyJointTailMaterial(jointTailMaterial)
    onJointTailClearcoatChanged: _applyJointTailMaterial(jointTailMaterial)
    onJointTailClearcoatRoughnessChanged: _applyJointTailMaterial(jointTailMaterial)
    onJointTailEmissiveColorChanged: _applyJointTailMaterial(jointTailMaterial)
    onJointTailEmissiveIntensityChanged: _applyJointTailMaterial(jointTailMaterial)

    onJointArmBaseColorChanged: _applyJointArmMaterial(jointArmMaterial)
    onJointArmMetalnessChanged: _applyJointArmMaterial(jointArmMaterial)
    onJointArmRoughnessChanged: _applyJointArmMaterial(jointArmMaterial)
    onJointArmClearcoatChanged: _applyJointArmMaterial(jointArmMaterial)
    onJointArmClearcoatRoughnessChanged: _applyJointArmMaterial(jointArmMaterial)
    onJointArmEmissiveColorChanged: _applyJointArmMaterial(jointArmMaterial)
    onJointArmEmissiveIntensityChanged: _applyJointArmMaterial(jointArmMaterial)

    onJointRodBaseColorChanged: _applyJointRodMaterial(jointRodMaterial)
    onJointRodMetalnessChanged: _applyJointRodMaterial(jointRodMaterial)
    onJointRodRoughnessChanged: _applyJointRodMaterial(jointRodMaterial)
    onJointRodClearcoatChanged: _applyJointRodMaterial(jointRodMaterial)
    onJointRodClearcoatRoughnessChanged: _applyJointRodMaterial(jointRodMaterial)
    onJointRodEmissiveColorChanged: _applyJointRodMaterial(jointRodMaterial)
    onJointRodEmissiveIntensityChanged: _applyJointRodMaterial(jointRodMaterial)

    Component.onCompleted: {
        console.log("SharedMaterials initialized (минимизированный слой Qt 6.10 + MaterialCompat)")
    }
}
