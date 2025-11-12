// MaterialCompat.js - совместимые присвоения для PBR материалов
// Цель: динамически применять свойства, которые могут отсутствовать в данной сборке Qt Quick 3D.
// Использует безопасный setProperty с подавлением исключений вместо прямого объявления
// свойств в QML для избежания parse-ошибок.

function _normalizeColor(value) {
    if (!value)
        return Qt.rgba(0, 0, 0, 1)
    try {
        if (typeof value === 'string') {
            // Попытка превратить строку в цвет через Qt.darker без изменения
            return Qt.darker(value, 1.0)
        }
        return Qt.rgba(value.r, value.g, value.b, (value.a !== undefined ? value.a : 1))
    } catch (e) {
        return Qt.rgba(0, 0, 0, 1)
    }
}

function _colorToVector3(color, intensity) {
    var c = _normalizeColor(color)
    var i = Number(intensity === undefined ? 1.0 : intensity)
    if (!isFinite(i)) i = 1.0
    return Qt.vector3d(c.r * i, c.g * i, c.b * i)
}

function _safeSetProperty(obj, name, val) {
    try {
        if (!obj)
            return false
        if (typeof obj.setProperty === 'function') {
            var result = obj.setProperty(name, val)
            return result === undefined ? true : Boolean(result)
        }
        obj[name] = val
        return true
    } catch (e) {
        return false
    }
}

// Применяем эмиссию, если ключевые поля доступны
function applyEmissive(material, color, factor) {
    if (!material)
        return
    var normalizedColor = _normalizeColor(color)
    var numericFactor = Number(factor)
    if (!isFinite(numericFactor)) numericFactor = 0.0

    // Свойства emissiveColor/emissiveFactor встречаются не во всех сборках.
    var okColor = _safeSetProperty(material, 'emissiveColor', normalizedColor)
    var okFactor = _safeSetProperty(material, 'emissiveFactor', numericFactor)

    if (!okColor)
        _safeSetProperty(material, 'emissive_color', normalizedColor)
    if (!okFactor)
        _safeSetProperty(material, 'emissive_factor', numericFactor)
}

function alphaMode(modeText) {
    var t = String(modeText || '').toLowerCase()
    switch (t) {
    case 'blend': return PrincipledMaterial.Blend
    case 'mask': return PrincipledMaterial.Mask
    case 'opaque': return PrincipledMaterial.Opaque
    default: return PrincipledMaterial.Default
    }
}

// Унифицированное применение набора PBR-свойств (только если присутствуют в сборке)
function applyPbr(material, props) {
    if (!material || !props) return

    // Базовые гарантированные свойства можно назначать напрямую
    if (props.baseColor !== undefined) {
        _safeSetProperty(material, 'baseColor', _normalizeColor(props.baseColor))
    }
    if (props.metalness !== undefined) _safeSetProperty(material, 'metalness', Number(props.metalness))
    if (props.roughness !== undefined) _safeSetProperty(material, 'roughness', Number(props.roughness))
    if (props.opacity !== undefined) _safeSetProperty(material, 'opacity', Number(props.opacity))

    // Альфа режим/порог
    if (props.alphaMode !== undefined) _safeSetProperty(material, 'alphaMode', alphaMode(props.alphaMode))
    if (props.alphaCutoff !== undefined) _safeSetProperty(material, 'alphaCutoff', Number(props.alphaCutoff))

    // Clearcoat (имена в разных версиях)
    if (props.clearcoatAmount !== undefined) {
        if (!_safeSetProperty(material, 'clearcoatAmount', Number(props.clearcoatAmount))) {
            _safeSetProperty(material, 'clearcoat', Number(props.clearcoatAmount))
        }
    }
    if (props.clearcoatRoughnessAmount !== undefined) {
        if (!_safeSetProperty(material, 'clearcoatRoughnessAmount', Number(props.clearcoatRoughnessAmount))) {
            _safeSetProperty(material, 'clearcoatRoughness', Number(props.clearcoatRoughnessAmount))
        }
    }

    // Прозрачность / физическая передача света
    if (props.transmissionFactor !== undefined) _safeSetProperty(material, 'transmissionFactor', Number(props.transmissionFactor))
    if (props.indexOfRefraction !== undefined) _safeSetProperty(material, 'indexOfRefraction', Number(props.indexOfRefraction))
    if (props.thicknessFactor !== undefined) _safeSetProperty(material, 'thicknessFactor', Number(props.thicknessFactor))

    // Аттенюация (цвет/дистанция для ослабления света внутри среды)
    if (props.attenuationDistance !== undefined) _safeSetProperty(material, 'attenuationDistance', Number(props.attenuationDistance))
    if (props.attenuationColor !== undefined) _safeSetProperty(material, 'attenuationColor', _normalizeColor(props.attenuationColor))

    // Нормали / AO
    if (props.normalStrength !== undefined) _safeSetProperty(material, 'normalStrength', Number(props.normalStrength))
    if (props.occlusionAmount !== undefined) _safeSetProperty(material, 'occlusionAmount', Number(props.occlusionAmount))

    // Эмиссия из (emissiveColor + emissiveIntensity) либо emissiveFactor в векторном виде
    if (props.emissiveColor !== undefined || props.emissiveIntensity !== undefined) {
        var eColor = props.emissiveColor !== undefined ? props.emissiveColor : Qt.rgba(0,0,0,1)
        var eIntensity = props.emissiveIntensity !== undefined ? props.emissiveIntensity : 0.0
        // Пытаемся сначала emissiveColor/emissiveFactor
        applyEmissive(material, eColor, eIntensity)
        // Если доступен emissiveFactor в векторном формате (некоторые билды) — пробуем вычислить.
        _safeSetProperty(material, 'emissiveFactor', _colorToVector3(eColor, eIntensity))
    }
}

var MaterialCompat = {
    applyEmissive: applyEmissive,
    applyPbr: applyPbr,
    alphaMode: alphaMode
}

function __dummy() {}
