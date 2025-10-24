import QtQuick
import QtQuick3D
import QtQuick.Controls
import QtQuick3D.Helpers
import "../camera"
import "../components"
import "../effects"

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

 required property var sceneBridge

 // ---------------------------------------------
 // Свойства и сигнал для батч-обновлений из Python
 // ---------------------------------------------
 property var pendingPythonUpdates: null
 signal batchUpdatesApplied(var summary)

 // Состояние симуляции, управляется из Python (MainWindow)
 property bool isRunning: false
 property var animationDefaults: typeof initialAnimationSettings !== "undefined" ? initialAnimationSettings : null
 property var sceneDefaults: typeof initialSceneSettings !== "undefined" ? initialSceneSettings : null
 property bool feedbackReady: false
 property real animationTime: animationDefaults && animationDefaults.animation_time !== undefined ? Number(animationDefaults.animation_time) :0.0 // сек, накапливается Python-таймером

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

 // Масштаб перевода метров в сцену Qt Quick3D (исторически миллиметры)
 property real sceneScaleFactor: sceneDefaults && sceneDefaults.scale_factor !== undefined ? Number(sceneDefaults.scale_factor) :1000.0

 // Анимация рычагов (град)
 property real userAmplitude: animationDefaults && animationDefaults.amplitude !== undefined ? Number(animationDefaults.amplitude) :8.0
 property real userFrequency: animationDefaults && animationDefaults.frequency !== undefined ? Number(animationDefaults.frequency) :1.0
 property real userPhaseGlobal: animationDefaults && animationDefaults.phase_global !== undefined ? Number(animationDefaults.phase_global) :0.0
 property real userPhaseFL: animationDefaults && animationDefaults.phase_fl !== undefined ? Number(animationDefaults.phase_fl) :0.0
 property real userPhaseFR: animationDefaults && animationDefaults.phase_fr !== undefined ? Number(animationDefaults.phase_fr) :0.0
 property real userPhaseRL: animationDefaults && animationDefaults.phase_rl !== undefined ? Number(animationDefaults.phase_rl) :0.0
 property real userPhaseRR: animationDefaults && animationDefaults.phase_rr !== undefined ? Number(animationDefaults.phase_rr) :0.0

 // Данные симуляции в СИ
 property real flAngleRad:0.0
 property real frAngleRad:0.0
 property real rlAngleRad:0.0
 property real rrAngleRad:0.0
 property real fl_angle: flAngleRad *180 / Math.PI
 property real fr_angle: frAngleRad *180 / Math.PI
 property real rl_angle: rlAngleRad *180 / Math.PI
 property real rr_angle: rrAngleRad *180 / Math.PI
 property real frameHeave:0.0
 property real frameRollRad:0.0
 property real framePitchRad:0.0
 property real frameRollDeg: frameRollRad *180 / Math.PI
 property real framePitchDeg: framePitchRad *180 / Math.PI
 property var pistonPositions: ({ fl:0.0, fr:0.0, rl:0.0, rr:0.0 })
 property var linePressures: ({})
 property real tankPressure:0.0

 // Ссылки на основные контроллеры сцены
 readonly property alias environmentController: sceneEnvCtl
 readonly property alias cameraController: cameraController
 readonly property alias view3d: sceneView
 readonly property alias camera: cameraController.camera

 // -------- Материалы/вид --------
 property color defaultClearColor: sceneDefaults && sceneDefaults.default_clear_color ? sceneDefaults.default_clear_color : "#1a1a2e"
 property color modelBaseColor: sceneDefaults && sceneDefaults.model_base_color ? sceneDefaults.model_base_color : "#9ea4ab"
 property real modelRoughness: sceneDefaults && sceneDefaults.model_roughness !== undefined ? Number(sceneDefaults.model_roughness) :0.35
 property real modelMetalness: sceneDefaults && sceneDefaults.model_metalness !== undefined ? Number(sceneDefaults.model_metalness) :0.9

 // ---------------------------------------------
 // Основные3D-компоненты сцены
 // ---------------------------------------------

 SceneEnvironmentController {
 id: sceneEnvCtl
 objectName: "sceneEnvironmentController"
 sceneBridge: root.sceneBridge
 }

 IblProbeLoader {
 id: iblLoader
 objectName: "iblProbeLoader"
 visible: false
 }

 View3D {
 id: sceneView
 anchors.fill: parent
 environment: sceneEnvCtl

 Node {
 id: worldRoot

 DirectionalLight {
 id: keyLight
 brightness:500
 color: "#ffffff"
 eulerRotation: Qt.vector3d(-45,60,0)
 }
 }
 }

 CameraController {
 id: cameraController
 objectName: "cameraController"
 anchors.fill: parent
 worldRoot: worldRoot
 view3d: sceneView
 sceneBridge: root.sceneBridge
 taaMotionAdaptive: sceneEnvCtl.taaMotionAdaptive
 onToggleAnimation: function() {
 if (typeof root.toggleAnimation === "function") {
 root.toggleAnimation()
 }
 }
 }

 Binding {
 target: sceneView
 property: "camera"
 value: cameraController.camera
 }

 Binding {
 target: sceneEnvCtl
 property: "iblProbe"
 value: iblLoader.probe
 }

 Binding {
 target: sceneEnvCtl
 property: "cameraIsMoving"
 value: cameraController ? cameraController.isMoving : false
 }

 // ---------------------------------------------
 // Python bridge helpers
 // ---------------------------------------------
 function applySceneBridgeState() {
 if (!sceneBridge)
 return

 if (sceneBridge.geometry && Object.keys(sceneBridge.geometry).length)
 applyGeometryUpdates(sceneBridge.geometry)
 if (sceneBridge.camera && Object.keys(sceneBridge.camera).length)
 applyCameraUpdates(sceneBridge.camera)
 if (sceneBridge.lighting && Object.keys(sceneBridge.lighting).length)
 applyLightingUpdates(sceneBridge.lighting)
 if (sceneBridge.environment && Object.keys(sceneBridge.environment).length)
 applyEnvironmentUpdates(sceneBridge.environment)
 if (sceneBridge.quality && Object.keys(sceneBridge.quality).length)
 applyQualityUpdates(sceneBridge.quality)
 if (sceneBridge.materials && Object.keys(sceneBridge.materials).length)
 applyMaterialUpdates(sceneBridge.materials)
 if (sceneBridge.effects && Object.keys(sceneBridge.effects).length)
 applyEffectsUpdates(sceneBridge.effects)
 if (sceneBridge.animation && Object.keys(sceneBridge.animation).length)
 applyAnimationUpdates(sceneBridge.animation)
 if (sceneBridge.threeD && Object.keys(sceneBridge.threeD).length)
 apply3DUpdates(sceneBridge.threeD)
 if (sceneBridge.render && Object.keys(sceneBridge.render).length)
 applyRenderSettings(sceneBridge.render)
 if (sceneBridge.simulation && Object.keys(sceneBridge.simulation).length)
 applySimulationUpdates(sceneBridge.simulation)

 if (sceneBridge.latestUpdates && Object.keys(sceneBridge.latestUpdates).length) {
 var summary = {}
 for (var key in sceneBridge.latestUpdates) {
 if (sceneBridge.latestUpdates.hasOwnProperty(key))
 summary[key] = true
 }
 batchUpdatesApplied(summary)
 }
 }

 onSceneBridgeChanged: applySceneBridgeState()

 Connections {
 id: sceneBridgeConnections
 target: sceneBridge
 enabled: !!sceneBridge

 function onGeometryChanged(payload) { if (payload) applyGeometryUpdates(payload) }
 function onCameraChanged(payload) { if (payload) applyCameraUpdates(payload) }
 function onLightingChanged(payload) { if (payload) applyLightingUpdates(payload) }
 function onEnvironmentChanged(payload) { if (payload) applyEnvironmentUpdates(payload) }
 function onQualityChanged(payload) { if (payload) applyQualityUpdates(payload) }
 function onMaterialsChanged(payload) { if (payload) applyMaterialUpdates(payload) }
 function onEffectsChanged(payload) { if (payload) applyEffectsUpdates(payload) }
 function onAnimationChanged(payload) { if (payload) applyAnimationUpdates(payload) }
 function onThreeDChanged(payload) { if (payload) apply3DUpdates(payload) }
 function onRenderChanged(payload) { if (payload) applyRenderSettings(payload) }
 function onSimulationChanged(payload) { if (payload) applySimulationUpdates(payload) }

 function onUpdatesDispatched(payload) {
 pendingPythonUpdates = payload
 if (!payload)
 return

 var summary = {}
 for (var key in payload) {
 if (payload.hasOwnProperty(key))
 summary[key] = true
 }
 batchUpdatesApplied(summary)
 }
 }

 Component.onCompleted: {
 if (signalTrace && signalTrace.registerSubscription) {
 signalTrace.registerSubscription("settings.settingChanged","main.qml","qml")
 signalTrace.registerSubscription("settings.settingsBatchUpdated","main.qml","qml")
 }
 applySceneBridgeState()
 }

 Connections {
 target: settingsEvents
 function onSettingChanged(change) {
 if (signalTrace && signalTrace.recordObservation) {
 signalTrace.recordObservation("settings.settingChanged", change, "qml")
 }
 }

 function onSettingsBatchUpdated(payload) {
 if (signalTrace && signalTrace.recordObservation) {
 signalTrace.recordObservation("settings.settingsBatchUpdated", payload, "qml")
 }
 }
 }

 // ---------------------------------------------
 // Утилиты
 // ---------------------------------------------
 function setIfExists(obj, prop, value) {
 try {
 if (obj && (prop in obj || typeof obj[prop] !== 'undefined')) {
 obj[prop] = value;
 }
 } catch (e) {
 console.warn("setIfExists failed", prop, e);
 }
 }

 function clamp(value, minValue, maxValue) {
 if (typeof value !== 'number' || !isFinite(value))
 return minValue;
 return Math.max(minValue, Math.min(maxValue, value));
 }

 function toSceneLength(meters) {
 var numeric = Number(meters);
 if (!isFinite(numeric))
 return0;
 return numeric * sceneScaleFactor;
 }

 function toSceneScale(meters) {
 return toSceneLength(meters) /100.0;
 }

 function normalizeLengthMeters(value) {
 if (value === undefined || value === null)
 return undefined;
 var numeric = Number(value);
 if (!isFinite(numeric))
 return undefined;
 if (Math.abs(numeric) >10.0)
 return numeric /1000.0;
 return numeric;
 }

 function emitConfigChange(category, payload) {
 if (!feedbackReady)
 return;
 if (!window)
 return;
 try {
 if (typeof window.isQmlFeedbackSuppressed === "function" && window.isQmlFeedbackSuppressed())
 return;
 } catch (err) {
 }
 if (typeof window.applyQmlConfigChange === "function")
 window.applyQmlConfigChange(category, payload);
 }

 function toSceneVector3(position) {
 if (!position)
 return null;
 var x = position.x !== undefined ? position.x : position[0];
 var y = position.y !== undefined ? position.y : position[1];
 var z = position.z !== undefined ? position.z : position[2];
 if (x === undefined || y === undefined || z === undefined)
 return null;
 return Qt.vector3d(
 toSceneLength(Number(x)),
 toSceneLength(Number(y)),
 toSceneLength(Number(z))
 );
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
 if (updates.simulation) { applySimulationUpdates(updates.simulation); applied.simulation = true; }

 batchUpdatesApplied(applied);
 }

 // ---------------------------------------------
 // Реализации apply*Updates (минимально: geometry, camera, lighting, environment, quality, materials, effects, animation,3d)
 // ---------------------------------------------
 function applyGeometryUpdates(params) {
 if (!params) return;
 function pick(obj, keys, def) {
 for (var i=0;i<keys.length;i++) if (obj[keys[i]] !== undefined) return obj[keys[i]];
 return def;
 }
 var v;
 v = pick(params, ['frameLength','frame_length','userFrameLength'], undefined);
 if (v !== undefined) { var frameLen = normalizeLengthMeters(v); if (frameLen !== undefined) userFrameLength = frameLen; }
 v = pick(params, ['frameHeight','frame_height','userFrameHeight'], undefined);
 if (v !== undefined) { var frameHeight = normalizeLengthMeters(v); if (frameHeight !== undefined) userFrameHeight = frameHeight; }
 v = pick(params, ['frameBeamSize','beamSize','userBeamSize'], undefined);
 if (v !== undefined) { var beamSize = normalizeLengthMeters(v); if (beamSize !== undefined) userBeamSize = beamSize; }
 v = pick(params, ['leverLength','userLeverLength'], undefined);
 if (v !== undefined) { var leverLen = normalizeLengthMeters(v); if (leverLen !== undefined) userLeverLength = leverLen; }
 v = pick(params, ['cylinderBodyLength','cylinderLength','userCylinderLength'], undefined);
 if (v !== undefined) { var cylLen = normalizeLengthMeters(v); if (cylLen !== undefined) userCylinderLength = cylLen; }
 v = pick(params, ['trackWidth','track','userTrackWidth'], undefined);
 if (v !== undefined) { var track = normalizeLengthMeters(v); if (track !== undefined) userTrackWidth = track; }
 v = pick(params, ['frameToPivot','frame_to_pivot','userFrameToPivot'], undefined);
 if (v !== undefined) { var pivot = normalizeLengthMeters(v); if (pivot !== undefined) userFrameToPivot = pivot; }
 v = pick(params, ['rodPosition','attachFrac','userRodPosition'], undefined);
 if (v !== undefined) { var rodPos = Number(v); if (isFinite(rodPos)) userRodPosition = rodPos; }
 v = pick(params, ['boreHead','bore','bore_d','userBoreHead'], undefined);
 if (v !== undefined) { var bore = normalizeLengthMeters(v); if (bore !== undefined) userBoreHead = bore; }
 v = pick(params, ['rod_d','rodDiameter','userRodDiameter'], undefined);
 if (v !== undefined) { var rodDia = normalizeLengthMeters(v); if (rodDia !== undefined) userRodDiameter = rodDia; }
 v = pick(params, ['pistonThickness','userPistonThickness'], undefined);
 if (v !== undefined) { var pistonThick = normalizeLengthMeters(v); if (pistonThick !== undefined) userPistonThickness = pistonThick; }
 v = pick(params, ['pistonRodLength','userPistonRodLength'], undefined);
 if (v !== undefined) { var rodLen = normalizeLengthMeters(v); if (rodLen !== undefined) userPistonRodLength = rodLen; }
 }

 function applyCameraUpdates(params) {
 if (!params) return;
 if (params.fov !== undefined)
 setIfExists(camera, 'fieldOfView', Number(params.fov));
 var clipNearMeters = params.clipNear !== undefined ? Number(params.clipNear) : undefined;
 if (clipNearMeters !== undefined && isFinite(clipNearMeters)) {
 var clipNearScene = Math.max(0.0001, toSceneLength(clipNearMeters));
 setIfExists(camera, 'clipNear', clipNearScene);
 try { camera.clipNear = clipNearScene; } catch (e) { console.warn("Camera near clip update failed:", e); }
 }
 var clipFarMeters = params.clipFar !== undefined ? Number(params.clipFar) : undefined;
 if (clipFarMeters !== undefined && isFinite(clipFarMeters)) {
 var clipFarScene = toSceneLength(clipFarMeters);
 setIfExists(camera, 'clipFar', clipFarScene);
 try { camera.clipFar = clipFarScene; } catch (e) { console.warn("Camera far clip update failed:", e); }
 }
 var positionVector = params.position ? toSceneVector3(params.position) : null;
 if (positionVector) {
 setIfExists(camera, 'position', positionVector);
 try { camera.position = positionVector; } catch (e) { console.warn("Camera position update failed:", e); }
 }
 if (params.eulerRotation) {
 var r = params.eulerRotation;
 try { camera.eulerRotation = Qt.vector3d(Number(r.x||r[0]), Number(r.y||r[1]), Number(r.z||r[2])); } catch(e) { console.warn("Camera rotation normalization failed:", e); }
 }
 }

 function applyLightingUpdates(params) {
 if (!params) return;
 if (params.color) setIfExists(keyLight, 'color', params.color);
 if (params.brightness !== undefined) setIfExists(keyLight, 'brightness', Number(params.brightness));
 if (params.eulerRotation) { var r = params.eulerRotation; try { keyLight.eulerRotation = Qt.vector3d(Number(r.x||r[0]), Number(r.y||r[1]), Number(r.z||r[2])); } catch(e) { console.warn("Lighting rotation normalization failed:", e); } }
 try {
 if (params.color) keyLight.color = params.color;
 if (params.brightness !== undefined) keyLight.brightness = Number(params.brightness);
 if (params.eulerRotation) { var r2 = params.eulerRotation; keyLight.eulerRotation = Qt.vector3d(Number(r2.x||r2[0]), Number(r2.y||r2[1]), Number(r2.z||r2[2])); }
 } catch(e2) { console.warn("Lighting update error:", e2); }
 }

 function applyEnvironmentUpdates(params) {
 if (!params) return;
 if (params.clearColor) setIfExists(sceneEnvCtl, 'backgroundColor', params.clearColor);
 if (params.backgroundColor) setIfExists(sceneEnvCtl, 'backgroundColor', params.backgroundColor);
 if (params.iblBackgroundEnabled !== undefined) setIfExists(sceneEnvCtl, 'iblBackgroundEnabled', !!params.iblBackgroundEnabled);
 if (params.iblLightingEnabled !== undefined) setIfExists(sceneEnvCtl, 'iblLightingEnabled', !!params.iblLightingEnabled);
 if (params.iblIntensity !== undefined) setIfExists(sceneEnvCtl, 'iblIntensity', Number(params.iblIntensity));
 if (params.iblRotationDeg !== undefined) setIfExists(sceneEnvCtl, 'iblRotationDeg', Number(params.iblRotationDeg));
 if (params.iblPrimary || params.hdrSource || params.iblSource) { var src = params.iblPrimary || params.hdrSource || params.iblSource; if (typeof window !== 'undefined' && window && typeof window.normalizeHdrPath === 'function') { try { src = window.normalizeHdrPath(String(src)); } catch(e) { console.warn("HDR path normalization failed:", e); } } setIfExists(iblLoader, 'primarySource', src); }
 if (params.iblFallback) setIfExists(iblLoader, 'fallbackSource', params.iblFallback);
 if (params.tonemapEnabled !== undefined) setIfExists(sceneEnvCtl, 'tonemapEnabled', !!params.tonemapEnabled);
 if (params.tonemapModeName) setIfExists(sceneEnvCtl, 'tonemapModeName', String(params.tonemapModeName));
 if (params.tonemapExposure !== undefined) setIfExists(sceneEnvCtl, 'tonemapExposure', Number(params.tonemapExposure));
 if (params.tonemapWhitePoint !== undefined) setIfExists(sceneEnvCtl, 'tonemapWhitePoint', Number(params.tonemapWhitePoint));
 if (params.fogEnabled !== undefined) setIfExists(sceneEnvCtl, 'fogEnabled', !!params.fogEnabled);
 if (params.fogColor) setIfExists(sceneEnvCtl, 'fogColor', params.fogColor);
 if (params.fogNear !== undefined) { var fogNearVal = Number(params.fogNear); if (isFinite(fogNearVal)) setIfExists(sceneEnvCtl, 'fogNear', toSceneLength(fogNearVal)); }
 if (params.fogFar !== undefined) { var fogFarVal = Number(params.fogFar); if (isFinite(fogFarVal)) setIfExists(sceneEnvCtl, 'fogFar', toSceneLength(fogFarVal)); }
 if (params.ssaoEnabled !== undefined) setIfExists(sceneEnvCtl, 'ssaoEnabled', !!params.ssaoEnabled);
 if (params.ssaoRadius !== undefined) setIfExists(sceneEnvCtl, 'ssaoRadius', Number(params.ssaoRadius));
 if (params.ssaoIntensity !== undefined) setIfExists(sceneEnvCtl, 'ssaoIntensity', Number(params.ssaoIntensity));
 if (params.depthOfFieldEnabled !== undefined) setIfExists(sceneEnvCtl, 'internalDepthOfFieldEnabled', !!params.depthOfFieldEnabled);
 if (params.dofFocusDistance !== undefined) { var dofDist = Number(params.dofFocusDistance); if (isFinite(dofDist)) setIfExists(sceneEnvCtl, 'dofFocusDistance', toSceneLength(dofDist)); }
 if (params.dofBlurAmount !== undefined) setIfExists(sceneEnvCtl, 'dofBlurAmount', Number(params.dofBlurAmount));
 if (params.vignetteEnabled !== undefined) setIfExists(sceneEnvCtl, 'internalVignetteEnabled', !!params.vignetteEnabled);
 if (params.vignetteStrength !== undefined) setIfExists(sceneEnvCtl, 'internalVignetteStrength', Number(params.vignetteStrength));
 if (params.aaPrimaryMode) setIfExists(sceneEnvCtl, 'aaPrimaryMode', String(params.aaPrimaryMode));
 if (params.aaQualityLevel) setIfExists(sceneEnvCtl, 'aaQualityLevel', String(params.aaQualityLevel));
 if (params.aaPostMode) setIfExists(sceneEnvCtl, 'aaPostMode', String(params.aaPostMode));
 if (params.taaEnabled !== undefined) setIfExists(sceneEnvCtl, 'taaEnabled', !!params.taaEnabled);
 if (params.taaStrength !== undefined) setIfExists(sceneEnvCtl, 'taaStrength', Number(params.taaStrength));
 if (params.taaMotionAdaptive !== undefined) setIfExists(sceneEnvCtl, 'taaMotionAdaptive', !!params.taaMotionAdaptive);
 if (params.fxaaEnabled !== undefined) setIfExists(sceneEnvCtl, 'fxaaEnabled', !!params.fxaaEnabled);
 if (params.specularAAEnabled !== undefined) setIfExists(sceneEnvCtl, 'specularAAEnabled', !!params.specularAAEnabled);
 if (params.oitMode) setIfExists(sceneEnvCtl, 'oitMode', String(params.oitMode));
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
 if (params.simulationTime !== undefined) animationTime = Number(params.simulationTime);
 if (params.amplitude !== undefined) userAmplitude = Number(params.amplitude);
 if (params.frequency !== undefined) userFrequency = Number(params.frequency);
 if (params.phase_global !== undefined) userPhaseGlobal = Number(params.phase_global);
 if (params.phase_fl !== undefined) userPhaseFL = Number(params.phase_fl);
 if (params.phase_fr !== undefined) userPhaseFR = Number(params.phase_fr);
 if (params.phase_rl !== undefined) userPhaseRL = Number(params.phase_rl);
 if (params.phase_rr !== undefined) userPhaseRR = Number(params.phase_rr);
 if (params.frame) { var frame = params.frame; if (frame.heave !== undefined) frameHeave = Number(frame.heave); if (frame.roll !== undefined) frameRollRad = Number(frame.roll); if (frame.pitch !== undefined) framePitchRad = Number(frame.pitch); }
 if (params.leverAngles) { var angles = params.leverAngles; if (angles.fl !== undefined) flAngleRad = Number(angles.fl); if (angles.fr !== undefined) frAngleRad = Number(angles.fr); if (angles.rl !== undefined) rlAngleRad = Number(angles.rl); if (angles.rr !== undefined) rrAngleRad = Number(angles.rr); }
 if (params.pistonPositions) { var pist = params.pistonPositions; var updatedPistons = Object.assign({}, pistonPositions || {}); if (pist.fl !== undefined) updatedPistons.fl = Number(pist.fl); if (pist.fr !== undefined) updatedPistons.fr = Number(pist.fr); if (pist.rl !== undefined) updatedPistons.rl = Number(pist.rl); if (pist.rr !== undefined) updatedPistons.rr = Number(pist.rr); pistonPositions = updatedPistons; }
 if (params.linePressures) { var lp = params.linePressures; var updatedPressures = Object.assign({}, linePressures || {}); if (lp.a1 !== undefined) updatedPressures.a1 = Number(lp.a1); if (lp.b1 !== undefined) updatedPressures.b1 = Number(lp.b1); if (lp.a2 !== undefined) updatedPressures.a2 = Number(lp.a2); if (lp.b2 !== undefined) updatedPressures.b2 = Number(lp.b2); linePressures = updatedPressures; }
 if (params.tankPressure !== undefined) tankPressure = Number(params.tankPressure);
 }

 function apply3DUpdates(params) {
 if (!params) return;
 if (params.frame) { var f = params.frame; if (f.heave !== undefined) frameHeave = Number(f.heave); if (f.roll !== undefined) frameRollRad = Number(f.roll); if (f.pitch !== undefined) framePitchRad = Number(f.pitch); }
 if (params.wheels) { var wheelData = params.wheels; var pist = Object.assign({}, pistonPositions || {}); if (wheelData.fl) { if (wheelData.fl.leverAngle !== undefined) flAngleRad = Number(wheelData.fl.leverAngle); if (wheelData.fl.pistonPosition !== undefined) pist.fl = Number(wheelData.fl.pistonPosition); }
 if (wheelData.fr) { if (wheelData.fr.leverAngle !== undefined) frAngleRad = Number(wheelData.fr.leverAngle); if (wheelData.fr.pistonPosition !== undefined) pist.fr = Number(wheelData.fr.pistonPosition); }
 if (wheelData.rl) { if (wheelData.rl.leverAngle !== undefined) rlAngleRad = Number(wheelData.rl.leverAngle); if (wheelData.rl.pistonPosition !== undefined) pist.rl = Number(wheelData.rl.pistonPosition); }
 if (wheelData.rr) { if (wheelData.rr.leverAngle !== undefined) rrAngleRad = Number(wheelData.rr.leverAngle); if (wheelData.rr.pistonPosition !== undefined) pist.rr = Number(wheelData.rr.pistonPosition); }
 pistonPositions = pist; }
 }
