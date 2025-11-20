// BatchDispatch.js - унифицированные утилиты батч-обновлений
// Русские комментарии + английские термины.

function isPlainObject(value) {
    return value && typeof value === 'object' && !Array.isArray(value);
}

function cloneObject(value) {
    if (!isPlainObject(value)) return {};
    const clone = {};
    for (const key in value) {
        if (Object.prototype.hasOwnProperty.call(value, key)) {
            const v = value[key];
            clone[key] = isPlainObject(v) ? cloneObject(v) : v;
        }
    }
    return clone;
}

function deepMerge(base, payload) {
    const result = cloneObject(base);
    if (isPlainObject(payload)) {
        for (const key in payload) {
            if (Object.prototype.hasOwnProperty.call(payload, key)) {
                const pv = payload[key];
                result[key] = isPlainObject(pv) ? deepMerge(result[key], pv) : pv;
            }
        }
    }
    return result;
}

function normaliseState(value) {
    if (!value || typeof value !== 'object') return {};
    const out = {};
    for (const k in value) if (Object.prototype.hasOwnProperty.call(value, k)) out[k] = value[k];
    return out;
}

function isEmptyMap(value) {
    if (!value || typeof value !== 'object') return true;
    for (const k in value) if (Object.prototype.hasOwnProperty.call(value, k)) return false;
    return true;
}

// Маска категорий через битовые флаги для уменьшения GC
const CategoryFlags = {
    geometry:      1 << 0,
    animation:     1 << 1,
    lighting:      1 << 2,
    materials:     1 << 3,
    environment:   1 << 4,
    scene:         1 << 5,
    quality:       1 << 6,
    camera:        1 << 7,
    effects:       1 << 8,
    render:        1 << 9,
    simulation:    1 << 10,
    threeD:        1 << 11,
};

function collectCategoriesMask(updates) {
    let mask = 0;
    if (!updates || typeof updates !== 'object') return mask;
    for (const key in updates) {
        if (!Object.prototype.hasOwnProperty.call(updates, key)) continue;
        if (CategoryFlags[key] !== undefined) mask |= CategoryFlags[key];
    }
    return mask;
}

function expandMask(mask) {
    const list = [];
    for (const name in CategoryFlags) {
        if (CategoryFlags[name] & mask) list.push(name);
    }
    return list;
}

// Нормализация списка эффектов (удаление дубликатов)
function dedupeEffects(list) {
    if (!Array.isArray(list)) return [];
    const seen = new Set();
    const out = [];
    for (let i = 0; i < list.length; ++i) {
        const entry = list[i];
        if (entry === undefined || entry === null) continue;
        const str = String(entry);
        if (seen.has(str)) continue;
        seen.add(str);
        out.push(entry);
    }
    return out;
}

// Экспортируем API
export { isPlainObject, cloneObject, deepMerge, normaliseState, isEmptyMap, CategoryFlags, collectCategoriesMask, expandMask, dedupeEffects };
