import QtQuick
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
 * PneumoStabSim - ENHANCED WORKING VERSION
 * ✅ Геометрия, материалы, окружение (IBL), анимация, автообновление
 */
Item {
 id: root
 anchors.fill: parent

 // ===============================================================
 // МОСТ PYTHON → QML (батч-обновления)
 // ===============================================================
 property var pendingPythonUpdates: null
 signal batchUpdatesApplied(var summary)

 onPendingPythonUpdatesChanged: {
 if (!pendingPythonUpdates)
 return;
 try {
 applyBatchedUpdates(pendingPythonUpdates);
 } finally {
 pendingPythonUpdates = null; // очищаем после применения
 }
 }

 function setIfExists(obj, prop, value) {
 try {
 if (obj && (prop in obj || typeof obj[prop] !== 'undefined')) {
 obj[prop] = value;
 }
 } catch (e) { /* ignore */ }
 }

 // Универсальный clamp для безопасного приёма числовых значений из Python/UI
 function clamp(value, minValue, maxValue) {
 if (typeof value !== 'number' || !isFinite(value)) {
 return minValue;
 }
 return Math.max(minValue, Math.min(maxValue, value));
 }

 // Конвертация строкового режима тонемаппинга в enum Qt
 function tonemapModeFromString(mode) {
 if (typeof mode !== 'string' || !mode.length)
 throw new Error('Missing tonemap mode');
 switch (mode.toLowerCase()) {
 case 'filmic':
 return SceneEnvironment.TonemapModeFilmic;
 case 'aces':
 return SceneEnvironment.TonemapModeAces;
 case 'reinhard':
 return SceneEnvironment.TonemapModeReinhard;
 case 'gamma':
 return SceneEnvironment.TonemapModeGamma;
 case 'linear':
 return SceneEnvironment.TonemapModeLinear;
 case 'none':
 return SceneEnvironment.TonemapModeNone;
 default:
 throw new Error('Unsupported tonemap mode: ' + mode);
 }
}

function backgroundModeFromString(mode) {
 if (typeof mode !== 'string' || !mode.length)
 throw new Error('Missing background mode');
 switch (mode.toLowerCase()) {
 case 'color':
 return SceneEnvironment.Color;
 case 'transparent':
 return SceneEnvironment.Transparent;
 case 'skybox':
 return SceneEnvironment.SkyBox;
 default:
 throw new Error('Unsupported background mode: ' + mode);
 }
}

function alphaModeFromString(mode) {
 if (typeof mode !== 'string' || !mode.length)
 throw new Error('Missing alpha mode');
 switch (mode.toLowerCase()) {
 case 'mask':
 return PrincipledMaterial.Mask;
 case 'blend':
 return PrincipledMaterial.Blend;
 case 'default':
 return PrincipledMaterial.Default;
 default:
 throw new Error('Unsupported alpha mode: ' + mode);
 }
}

// Enhanced error handling and validation utilities
function requireDefinedSetting(name, value) {
    if (value === undefined || value === null)
    throw new Error('Missing required setting: ' + name);
    return value;
}

function requireObjectSetting(name, value) {
    var resolved = requireDefinedSetting(name, value);
    if (typeof resolved !== 'object')
   throw new Error('Invalid object for ' + name + ': ' + resolved);
return resolved;
}

function requireNumericSetting(name, value, minValue, maxValue) {
    var resolved = requireDefinedSetting(name, value);
var numeric = Number(resolved);
    if (!isFinite(numeric))
        throw new Error('Invalid numeric value for ' + name + ': ' + resolved);
    return clamp(numeric, minValue, maxValue);
}

function requireBooleanSetting(name, value) {
 var resolved = requireDefinedSetting(name, value);
 if (typeof resolved === 'boolean')
 return resolved;
 throw new Error('Invalid boolean value for ' + name + ': ' + resolved);
}

function requireStringSetting(name, value, allowEmpty) {
 var resolved = requireDefinedSetting(name, value);
 if (typeof resolved !== 'string')
 throw new Error('Invalid string value for ' + name + ': ' + resolved);
 if (!allowEmpty && resolved.length ===0)
 throw new Error('Empty string is not allowed for ' + name);
 return resolved;
 }

 function applyBatchedUpdates(updates) {
 if (!updates) return;
 var applied = {};
 if (updates.geometry) { applyGeometryUpdates(updates.geometry); applied.geometry = true; }
 if (updates.camera) { applyCameraUpdates(updates.camera); applied.camera = true; }
 if (updates.lighting) { applyLightingUpdates(updates.lighting); applied.lighting = true; }
 if (updates.environment) { applyEnvironmentUpdates(updates.environment); applied.environment = true; }
 if (updates.quality) { applyQualityUpdates(updates.quality); applied.quality = true; }
 if (updates.materials) { applyMaterialUpdates(updates.materials); applied.materials = true; }
 if (updates.effects) { applyEffectsUpdates(updates.effects); applied.effects = true; }
 if (updates.animation) { applyAnimationUpdates(updates.animation); applied.animation = true; }
 if (updates.threeD) { apply3DUpdates(updates.threeD); applied.threeD = true; }
 if (updates.render) { applyRenderSettings(updates.render); applied.render = true; }

 // Сводка изменений для Python
 var summary = {
 geometry: applied.geometry,
 camera: applied.camera,
 lighting: applied.lighting,
 environment: applied.environment,
 quality: applied.quality,
 materials: applied.materials,
 effects: applied.effects,
 animation: applied.animation,
 threeD: applied.threeD,
 render: applied.render,
 };

 // Упрощённая сводка с применёнными настройками
 var simplifiedSummary = {};
 for (var key in summary) {
 if (summary[key]) {
 var displayName = key.charAt(0).toUpperCase() + key.slice(1);
 simplifiedSummary[displayName] = true;
 }
 }

 // Уведомление об успешном применении батч-обновлений
 batchUpdatesApplied(simplifiedSummary);
 }

 // Инициализация
 Component.onCompleted: {
 //debugger;
 // Принудительное применение всех обновлений при старте
 applyBatchedUpdates({
 geometry: true,
 camera: true,
 lighting: true,
 environment: true,
 quality: true,
 materials: true,
 effects: true,
 animation: true,
 threeD: true,
 render: true,
 });
 }
}
