import QtQuick
import QtQuick3D
import QtQuick.Controls
import QtQuick3D.Helpers
import "components"
import "effects"

/*
 * PneumoStabSim - MAIN QML (v4.9.x)
 *
 * View3D + ExtendedSceneEnvironment (HDR/IBL), IBL Probe Loader.
 * Реальная упрощённая схема (рама, рычаги, цилиндр). Без кнопок на канве.
 * Обновления приходят из панелей через apply*Updates и batched updates.
 */
Item {
 id: root
 anchors.fill: parent

 // ---------------------------------------------
 // Свойства и сигнал для батч-обновлений из Python
 // ---------------------------------------------
 property var pendingPythonUpdates: null
 signal batchUpdatesApplied(var summary)

 // Состояние симуляции, управляется из Python (MainWindow)
 property bool isRunning: false
 property real animationTime:0.0 // сек, накапливается Python-таймером

 // -------- Геометрия подвески (СИ) --------
 property real userFrameLength:3.2
 property real userFrameHeight:0.65
 property real userBeamSize:0.12
 property real userLeverLength:0.8
 property real userCylinderLength:0.5
 property real userTrackWidth:1.6
 property real userFrameToPivot:0.6
 property real userRodPosition:0.6
 property real userBoreHead:0.08
 property real userRodDiameter:0.035
 property real userPistonThickness:0.025
 property real userPistonRodLength:0.2

 // Анимация рычагов (град)
 property real userAmplitude:8.0
 property real userFrequency:1.0
 property real userPhaseGlobal:0.0
 property real userPhaseFL:0.0
 property real userPhaseFR:0.0
 property real userPhaseRL:0.0
 property real userPhaseRR:0.0

 // Вычисляемые углы (SLERP handled by Qt)
 property real fl_angle: isRunning ? userAmplitude * Math.sin(animationTime * userFrequency *2 * Math.PI + (userPhaseGlobal + userPhaseFL) * Math.PI /180) :0.0
 property real fr_angle: isRunning ? userAmplitude * Math.sin(animationTime * userFrequency *2 * Math.PI + (userPhaseGlobal + userPhaseFR) * Math.PI /180) :0.0
 property real rl_angle: isRunning ? userAmplitude * Math.sin(animationTime * userFrequency *2 * Math.PI + (userPhaseGlobal + userPhaseRL) * Math.PI /180) :0.0
 property real rr_angle: isRunning ? userAmplitude * Math.sin(animationTime * userFrequency *2 * Math.PI + (userPhaseGlobal + userPhaseRR) * Math.PI /180) :0.0

 // -------- Материалы/вид --------
 property color defaultClearColor: "#1a1a2e"
 property color modelBaseColor: "#9ea4ab"
 property real modelRoughness:0.35
 property real modelMetalness:0.9

 // ---------------------------------------------
 // Утилиты
 // ---------------------------------------------
 function setIfExists(obj, prop, value) {
 try {
 if (obj && (prop in obj || typeof obj[prop] !== 'undefined')) {
 obj[prop] = value;
 }
 } catch (e) { /* ignore */ }
 }

 function clamp(value, minValue, maxValue) {
 if (typeof value !== 'number' || !isFinite(value))
 return minValue;
 return Math.max(minValue, Math.min(maxValue, value));
 }

 // ---------------------------------------------
 // Применение батч-обновлений из Python
 // ---------------------------------------------
 onPendingPythonUpdatesChanged: {
 if (!pendingPythonUpdates)
 return;
 try {
 applyBatchedUpdates(pendingPythonUpdates);
 } finally {
 pendingPythonUpdates = null; // очистка после применения
 }
 }

 function applyBatchedUpdates(updates) {
 if (!updates)
 return;
 var applied = {};
 if (updates.geometry) { applyGeometryUpdates(updates.geometry); applied.geometry = true; }
 if (updates.camera) { applyCameraUpdates(updates.camera); applied.camera = true; }
 if (updates.lighting) { applyLightingUpdates(updates.lighting); applied.lighting = true; }
 if (updates.environment){ applyEnvironmentUpdates(updates.environment); applied.environment = true; }
 if (updates.quality) { applyQualityUpdates(updates.quality); applied.quality = true; }
 if (updates.materials) { applyMaterialUpdates(updates.materials); applied.materials = true; }
 if (updates.effects) { applyEffectsUpdates(updates.effects); applied.effects = true; }
 if (updates.animation) { applyAnimationUpdates(updates.animation); applied.animation = true; }
 if (updates.threeD) { apply3DUpdates(updates.threeD); applied.threeD = true; }
 if (updates.render) { applyRenderSettings(updates.render); applied.render = true; }

 batchUpdatesApplied(applied);
 }

 // ---------------------------------------------
 // Реализации apply*Updates
 // ---------------------------------------------
 function applyGeometryUpdates(params) {
 if (!params) return;
 // Поддерживаем несколько алиасов из Python панелей
 function pick(obj, keys, def) {
 for (var i=0;i<keys.length;i++) if (obj[keys[i]] !== undefined) return obj[keys[i]];
 return def;
 }
 var v;
 v = pick(params, ['frameLength','frame_length','userFrameLength'], undefined); if (v!==undefined) userFrameLength = Number(v);
 v = pick(params, ['frameHeight','frame_height','userFrameHeight'], undefined); if (v!==undefined) userFrameHeight = Number(v);
 v = pick(params, ['frameBeamSize','beamSize','userBeamSize'], undefined); if (v!==undefined) userBeamSize = Number(v);
 v = pick(params, ['leverLength','userLeverLength'], undefined); if (v!==undefined) userLeverLength = Number(v);
 v = pick(params, ['cylinderBodyLength','cylinderLength','userCylinderLength'], undefined); if (v!==undefined) userCylinderLength = Number(v);
 v = pick(params, ['trackWidth','track','userTrackWidth'], undefined); if (v!==undefined) userTrackWidth = Number(v);
 v = pick(params, ['frameToPivot','frame_to_pivot','userFrameToPivot'], undefined); if (v!==undefined) userFrameToPivot = Number(v);
 v = pick(params, ['rodPosition','attachFrac','userRodPosition'], undefined); if (v!==undefined) userRodPosition = Number(v);
 v = pick(params, ['boreHead','bore','bore_d','userBoreHead'], undefined); if (v!==undefined) userBoreHead = Number(v);
 v = pick(params, ['rod_d','rodDiameter','userRodDiameter'], undefined); if (v!==undefined) userRodDiameter = Number(v);
 v = pick(params, ['pistonThickness','userPistonThickness'], undefined); if (v!==undefined) userPistonThickness = Number(v);
 v = pick(params, ['pistonRodLength','userPistonRodLength'], undefined); if (v!==undefined) userPistonRodLength = Number(v);
 }

 function applyCameraUpdates(params) {
 if (!params) return;
 if (params.fov !== undefined) setIfExists(camera, 'fieldOfView', Number(params.fov));
 if (params.clipNear !== undefined) setIfExists(camera, 'clipNear', Number(params.clipNear));
 if (params.clipFar !== undefined) setIfExists(camera, 'clipFar', Number(params.clipFar));
 if (params.position) {
 var p = params.position;
 try { camera.position = Qt.vector3d(Number(p.x||p[0]), Number(p.y||p[1]), Number(p.z||p[2])); } catch(e) {}
 }
 if (params.eulerRotation) {
 var r = params.eulerRotation;
 try { camera.eulerRotation = Qt.vector3d(Number(r.x||r[0]), Number(r.y||r[1]), Number(r.z||r[2])); } catch(e) {}
 }
 // Обработка ошибок установки камеры
 try {
 if (params.fov !== undefined) camera.fieldOfView = Number(params.fov);
 if (params.clipNear !== undefined) camera.clipNear = Number(params.clipNear);
 if (params.clipFar !== undefined) camera.clipFar = Number(params.clipFar);
 if (params.position) {
 var p = params.position;
 camera.position = Qt.vector3d(Number(p.x||p[0]), Number(p.y||p[1]), Number(p.z||p[2]));
 }
 if (params.eulerRotation) {
 var r = params.eulerRotation;
 camera.eulerRotation = Qt.vector3d(Number(r.x||r[0]), Number(r.y||r[1]), Number(r.z||r[2]));
 }
 } catch(e) {
 console.warn("Camera update error:", e);
 }
 }

 function applyLightingUpdates(params) {
 if (!params) return;
 if (params.color) setIfExists(keyLight, 'color', params.color);
 if (params.brightness !== undefined) setIfExists(keyLight, 'brightness', Number(params.brightness));
 if (params.eulerRotation) {
 var r = params.eulerRotation;
 try { keyLight.eulerRotation = Qt.vector3d(Number(r.x||r[0]), Number(r.y||r[1]), Number(r.z||r[2])); } catch(e) {}
 }
 // Обработка ошибок установки освещения
 try {
 if (params.color) keyLight.color = params.color;
 if (params.brightness !== undefined) keyLight.brightness = Number(params.brightness);
 if (params.eulerRotation) {
 var r = params.eulerRotation;
 keyLight.eulerRotation = Qt.vector3d(Number(r.x||r[0]), Number(r.y||r[1]), Number(r.z||r[2]));
 }
 } catch(e) {
 console.warn("Lighting update error:", e);
 }
 }

 function applyEnvironmentUpdates(params) {
 if (!params) return;
 // Бэкграунд/цвет
 if (params.clearColor) setIfExists(sceneEnvCtl, 'backgroundColor', params.clearColor);
 if (params.backgroundColor) setIfExists(sceneEnvCtl, 'backgroundColor', params.backgroundColor);
 // IBL флаги и параметры
 if (params.iblBackgroundEnabled !== undefined) setIfExists(sceneEnvCtl, 'iblBackgroundEnabled', !!params.iblBackgroundEnabled);
 if (params.iblLightingEnabled !== undefined) setIfExists(sceneEnvCtl, 'iblLightingEnabled', !!params.iblLightingEnabled);
 if (params.iblIntensity !== undefined) setIfExists(sceneEnvCtl, 'iblIntensity', Number(params.iblIntensity));
 if (params.iblRotationDeg !== undefined) setIfExists(sceneEnvCtl, 'iblRotationDeg', Number(params.iblRotationDeg));
 // Источники HDR
 if (params.iblPrimary || params.hdrSource || params.iblSource) {
 var src = params.iblPrimary || params.hdrSource || params.iblSource;
 if (typeof window !== 'undefined' && window && typeof window.normalizeHdrPath === 'function') {
 try { src = window.normalizeHdrPath(String(src)); } catch(e) {}
 }
 setIfExists(iblLoader, 'primarySource', src);
 }
 if (params.iblFallback) setIfExists(iblLoader, 'fallbackSource', params.iblFallback);
 // Тонемап
 if (params.tonemapEnabled !== undefined) setIfExists(sceneEnvCtl, 'tonemapEnabled', !!params.tonemapEnabled);
 if (params.tonemapModeName) setIfExists(sceneEnvCtl, 'tonemapModeName', String(params.tonemapModeName));
 if (params.tonemapExposure !== undefined) setIfExists(sceneEnvCtl, 'tonemapExposure', Number(params.tonemapExposure));
 if (params.tonemapWhitePoint !== undefined) setIfExists(sceneEnvCtl, 'tonemapWhitePoint', Number(params.tonemapWhitePoint));
 // Туман
 if (params.fogEnabled !== undefined) setIfExists(sceneEnvCtl, 'fogEnabled', !!params.fogEnabled);
 if (params.fogColor) setIfExists(sceneEnvCtl, 'fogColor', params.fogColor);
 if (params.fogNear !== undefined) setIfExists(sceneEnvCtl, 'fogNear', Number(params.fogNear));
 if (params.fogFar !== undefined) setIfExists(sceneEnvCtl, 'fogFar', Number(params.fogFar));
 // SSAO
 if (params.ssaoEnabled !== undefined) setIfExists(sceneEnvCtl, 'ssaoEnabled', !!params.ssaoEnabled);
 if (params.ssaoRadius !== undefined) setIfExists(sceneEnvCtl, 'ssaoRadius', Number(params.ssaoRadius));
 if (params.ssaoIntensity !== undefined) setIfExists(sceneEnvCtl, 'ssaoIntensity', Number(params.ssaoIntensity));
 // DoF
 if (params.depthOfFieldEnabled !== undefined) setIfExists(sceneEnvCtl, 'internalDepthOfFieldEnabled', !!params.depthOfFieldEnabled);
 if (params.dofFocusDistance !== undefined) setIfExists(sceneEnvCtl, 'dofFocusDistance', Number(params.dofFocusDistance));
 if (params.dofBlurAmount !== undefined) setIfExists(sceneEnvCtl, 'dofBlurAmount', Number(params.dofBlurAmount));
 // Vignette
 if (params.vignetteEnabled !== undefined) setIfExists(sceneEnvCtl, 'internalVignetteEnabled', !!params.vignetteEnabled);
 if (params.vignetteStrength !== undefined) setIfExists(sceneEnvCtl, 'internalVignetteStrength', Number(params.vignetteStrength));
 // AA/качество
 if (params.aaPrimaryMode) setIfExists(sceneEnvCtl, 'aaPrimaryMode', String(params.aaPrimaryMode));
 if (params.aaQualityLevel) setIfExists(sceneEnvCtl, 'aaQualityLevel', String(params.aaQualityLevel));
 if (params.aaPostMode) setIfExists(sceneEnvCtl, 'aaPostMode', String(params.aaPostMode));
 if (params.taaEnabled !== undefined) setIfExists(sceneEnvCtl, 'taaEnabled', !!params.taaEnabled);
 if (params.taaStrength !== undefined) setIfExists(sceneEnvCtl, 'taaStrength', Number(params.taaStrength));
 if (params.taaMotionAdaptive !== undefined) setIfExists(sceneEnvCtl, 'taaMotionAdaptive', !!params.taaMotionAdaptive);
 if (params.fxaaEnabled !== undefined) setIfExists(sceneEnvCtl, 'fxaaEnabled', !!params.fxaaEnabled);
 if (params.specularAAEnabled !== undefined) setIfExists(sceneEnvCtl, 'specularAAEnabled', !!params.specularAAEnabled);
 // OIT
 if (params.oitMode) setIfExists(sceneEnvCtl, 'oitMode', String(params.oitMode));
 // Dithering
 if (params.ditheringEnabled !== undefined) setIfExists(sceneEnvCtl, 'ditheringEnabled', !!params.ditheringEnabled);
 }

 function applyQualityUpdates(params) {
 if (!params) return;
 if (params.aaPrimaryMode) setIfExists(sceneEnvCtl, 'aaPrimaryMode', String(params.aaPrimaryMode));
 if (params.aaQualityLevel) setIfExists(sceneEnvCtl, 'aaQualityLevel', String(params.aaQualityLevel));
 if (params.ditheringEnabled !== undefined) setIfExists(sceneEnvCtl, 'ditheringEnabled', !!params.ditheringEnabled);
 }

 function applyMaterialUpdates(params) {
 if (!params) return;
 // Упрощённо: применять к металлу рычагов
 if (params.baseColor) modelBaseColor = params.baseColor;
 if (params.roughness !== undefined) modelRoughness = clamp(Number(params.roughness),0.0,1.0);
 if (params.metalness !== undefined) modelMetalness = clamp(Number(params.metalness),0.0,1.0);
 }

 function applyEffectsUpdates(params) {
 if (!params) return;
 // Эффекты уже настраиваются через applyEnvironmentUpdates
 }

 function applyAnimationUpdates(params) {
 if (!params) return;
 if (params.isRunning !== undefined) isRunning = !!params.isRunning;
 if (params.amplitude !== undefined) userAmplitude = Number(params.amplitude);
 if (params.frequency !== undefined) userFrequency = Number(params.frequency);
 if (params.phase_global !== undefined) userPhaseGlobal = Number(params.phase_global);
 if (params.phase_fl !== undefined) userPhaseFL = Number(params.phase_fl);
 if (params.phase_fr !== undefined) userPhaseFR = Number(params.phase_fr);
 if (params.phase_rl !== undefined) userPhaseRL = Number(params.phase_rl);
 if (params.phase_rr !== undefined) userPhaseRR = Number(params.phase_rr);
 }

 function apply3DUpdates(params) {
 }

 function applyRenderSettings(params) {
 }

 // ---------------------------------------------
 // IBL Loader (загрузка HDR probe)
 // ---------------------------------------------
 IblProbeLoader {
 id: iblLoader
 }

 // ---------------------------------------------
 //3D сцена + ExtendedSceneEnvironment с IBL
 // ---------------------------------------------
 View3D {
 id: view3d
 anchors.fill: parent

 environment: SceneEnvironmentController {
 id: sceneEnvCtl
 iblProbe: iblLoader.probe
 backgroundColor: root.defaultClearColor
 }

 PerspectiveCamera {
 id: camera
 position: Qt.vector3d(0,0,600)
 fieldOfView:60
 clipNear:1
 clipFar:50000
 }

 DirectionalLight {
 id: keyLight
 eulerRotation.x: -30
 eulerRotation.y: -30
 brightness:1.6
 color: "#ffffff"
 }

 // === Рама (центральная балка) ===
 Model {
 id: mainFrame
 position: Qt.vector3d(0, root.userBeamSize/2, root.userFrameLength/2)
 source: "#Cube"
 scale: Qt.vector3d(root.userTrackWidth/100, root.userBeamSize/100, root.userFrameLength/100)
 materials: PrincipledMaterial { baseColor: "#4a4a4a"; metalness:0.85; roughness:0.3 }
 }

 // === Рычаги ===
 Model { id: frontLeftLever; position: Qt.vector3d(-root.userTrackWidth/2, root.userBeamSize, root.userFrameToPivot); source: "#Cube"; scale: Qt.vector3d(root.userLeverLength/100,8,8); eulerRotation: Qt.vector3d(0,0, root.fl_angle); materials: PrincipledMaterial { baseColor: root.modelBaseColor; metalness: root.modelMetalness; roughness: root.modelRoughness } }
 Model { id: frontRightLever; position: Qt.vector3d( root.userTrackWidth/2, root.userBeamSize, root.userFrameToPivot); source: "#Cube"; scale: Qt.vector3d(root.userLeverLength/100,8,8); eulerRotation: Qt.vector3d(0,0, root.fr_angle); materials: PrincipledMaterial { baseColor: root.modelBaseColor; metalness: root.modelMetalness; roughness: root.modelRoughness } }
 Model { id: rearLeftLever; position: Qt.vector3d(-root.userTrackWidth/2, root.userBeamSize, root.userFrameLength - root.userFrameToPivot); source: "#Cube"; scale: Qt.vector3d(root.userLeverLength/100,8,8); eulerRotation: Qt.vector3d(0,0, root.rl_angle); materials: PrincipledMaterial { baseColor: root.modelBaseColor; metalness: root.modelMetalness; roughness: root.modelRoughness } }
 Model { id: rearRightLever; position: Qt.vector3d( root.userTrackWidth/2, root.userBeamSize, root.userFrameLength - root.userFrameToPivot); source: "#Cube"; scale: Qt.vector3d(root.userLeverLength/100,8,8); eulerRotation: Qt.vector3d(0,0, root.rr_angle); materials: PrincipledMaterial { baseColor: root.modelBaseColor; metalness: root.modelMetalness; roughness: root.modelRoughness } }

 // === Простой цилиндр (визуальная верификация) ===
 Model {
 id: cylinderFL
 position: Qt.vector3d(-root.userTrackWidth/4, root.userBeamSize + root.userFrameHeight/2, root.userFrameToPivot)
 source: "#Cylinder"
 scale: Qt.vector3d(root.userBoreHead/100, root.userCylinderLength/100, root.userBoreHead/100)
 materials: PrincipledMaterial { baseColor: "#bcd7ff"; metalness:0.0; roughness:0.08; transmissionFactor:0.6; opacity:0.8; indexOfRefraction:1.52; alphaMode: PrincipledMaterial.Blend }
 }
 }

 // Принудительное первичное применение категорий (без данных)
 Component.onCompleted: {
 applyBatchedUpdates({
 geometry: true,
 camera: true,
 lighting: true,
 environment: { backgroundColor: defaultClearColor },
 quality: true,
 materials: { baseColor: modelBaseColor, roughness: modelRoughness, metalness: modelMetalness },
 effects: true,
 animation: { isRunning: isRunning, amplitude: userAmplitude, frequency: userFrequency },
 threeD: true,
 render: true,
 });
 }
}
