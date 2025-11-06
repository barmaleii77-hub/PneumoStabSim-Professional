import QtQml 6.10
import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import QtQuick.Timeline 1.0
import QtQuick3D 6.10
import QtQuick3D.Helpers 6.10
import "../camera"
import "../components"
import "../effects"
import "../geometry"
import "../lighting"
import "../diagnostics/LogBridge.js" as Diagnostics
import scene 1.0 as Scene
import "../animation"

/*
 * PneumoStabSim - MAIN QML (v4.9.x)
 *
 * View3D + ExtendedSceneEnvironment (HDR/IBL), IBL Probe Loader,
 * ReflectionProbe для локальных отражений.
 * Полноценная анимированная схема (рама, рычаги, шарниры, цилиндры,
 * штоки, хвостовики, поршни). Без кнопок на канве.
 * Обновления приходят из панелей через apply*Updates и batched updates.
 */
 Item {
 id: root
 anchors.fill: parent

    property var sceneBridge: null
    readonly property var emptyDefaultsObject: Object.freeze({})
    readonly property var emptyGeometryDefaults: emptyDefaultsObject
    readonly property var emptyMaterialsDefaults: emptyDefaultsObject

 // ---------------------------------------------
 // Свойства и сигнал для батч-обновлений из Python
 // ---------------------------------------------
 property var pendingPythonUpdates: null
signal batchUpdatesApplied(var summary)
signal animationToggled(bool running)

    Component.onCompleted: {
        const hasBridge = sceneBridge !== null && sceneBridge !== undefined
        console.log("[SimulationRoot] Component completed; sceneBridge:", hasBridge ? "available" : "missing")
        if (typeof window !== "undefined" && window) {
            const identifier = typeof window.objectName === "string" && window.objectName.length > 0 ? window.objectName : "<anonymous>"
            console.log("[SimulationRoot] Window context ready:", identifier)
        } else {
            console.warn("[SimulationRoot] Window context missing; shader warnings will stay local")
        }
    }

 // Состояние симуляции, управляется из Python (MainWindow)
 property bool isRunning: animationDefaults && animationDefaults.is_running !== undefined ? Boolean(animationDefaults.is_running) : false
 property var animationDefaults: typeof initialAnimationSettings !== "undefined" ? initialAnimationSettings : null
 property var sceneDefaults: typeof initialSceneSettings !== "undefined" ? initialSceneSettings : null
 property var geometryDefaults: typeof initialGeometrySettings !== "undefined" && initialGeometrySettings ? initialGeometrySettings : emptyGeometryDefaults
 property var diagnosticsDefaults: typeof initialDiagnosticsSettings !== "undefined" ? initialDiagnosticsSettings : null
 property var cameraHudSettings: ({})
 property bool cameraHudEnabled: false
 property bool feedbackReady: false
 property real animationTime: animationDefaults && animationDefaults.animation_time !== undefined ? Number(animationDefaults.animation_time) :0.0 // сек, накапливается Python-таймером
 property bool pythonAnimationActive: false
 property bool pythonLeverAnglesActive: false
 property bool pythonPistonsActive: false
 property bool pythonFrameActive: false
 property bool pythonPressureActive: false
 property bool diagnosticsLoggingEnabled: false
 property bool fallbackEnabled: isRunning && !pythonAnimationActive
 property real fallbackPhase: 0.0
 property real lastFallbackPhase: 0.0
 property real fallbackBaseTime: animationTime
  readonly property real fallbackCycleSeconds: Math.max(0.2, 1.0 / Math.max(userFrequency, 0.01))
 property real batchFlashOpacity: 0.0

 function initializeRenderSettings() {
  if (sceneRenderSettings) {
   sceneRenderSettings.destroy();
   sceneRenderSettings = null;
  }

  var propertyExists = sceneView && typeof sceneView.renderSettings !== "undefined";
  if (typeof RenderSettings === "undefined" || !propertyExists) {
   renderSettingsSupported = false;
   console.warn("[SimulationRoot] RenderSettings type unavailable; using default View3D settings");
   return;
  }

  var qmlSource = "import QtQuick 6.10\n" +
                  "import QtQuick3D 6.10\n" +
                  "RenderSettings {\n" +
                  "    renderScale: Math.max(0.1, root.renderScale)\n" +
                  "    maximumFrameRate: root.frameRateLimit > 0 ? root.frameRateLimit : 0\n" +
                  "    renderPolicy: {\n" +
                  "        var key = root.renderPolicyKey || \\\"always\\\";\n" +
                  "        if (key === \\\"ondemand\\\")\n" +
                  "            return RenderSettings.OnDemand;\n" +
                  "        if (key === \\\"automatic\\\" && RenderSettings.Automatic !== undefined)\n" +
                  "            return RenderSettings.Automatic;\n" +
                  "        if (key === \\\"manual\\\" && RenderSettings.Manual !== undefined)\n" +
                  "            return RenderSettings.Manual;\n" +
                  "        return RenderSettings.Always;\n" +
                  "    }\n" +
                  "}\n";

  try {
   var created = Qt.createQmlObject(qmlSource, sceneView, "DynamicRenderSettings");
   if (created) {
    var depthPrepared = false;
    if (typeof DepthTextureActivator !== "undefined"
            && DepthTextureActivator
            && typeof DepthTextureActivator.prepareRenderSettings === "function") {
     depthPrepared = DepthTextureActivator.prepareRenderSettings(sceneView, created);
    } else {
     try {
      if ("depthPrePassEnabled" in created) {
       created.depthPrePassEnabled = true;
       depthPrepared = true;
      }
     } catch (error) {
      console.debug("[SimulationRoot] depthPrePassEnabled preconfigure failed", error);
     }
     try {
      if (typeof created.enableDepthBuffer === "function") {
       created.enableDepthBuffer();
       depthPrepared = true;
      }
     } catch (error) {
      console.debug("[SimulationRoot] enableDepthBuffer preconfigure failed", error);
     }
    }
    if (depthPrepared) {
     console.log("[SimulationRoot] RenderSettings depth pre-pass configured before assignment");
    }
    sceneView.renderSettings = created;
    sceneRenderSettings = created;
    renderSettingsSupported = true;
   } else {
    renderSettingsSupported = false;
    console.warn("[SimulationRoot] Failed to instantiate RenderSettings; defaults will be used");
   }
  } catch (error) {
   renderSettingsSupported = false;
   sceneRenderSettings = null;
   console.error("[SimulationRoot] initializeRenderSettings failed", error);
  }
 }

readonly property real defaultDofFocusDistanceM: effectsDefaultNumber(["dof_focus_distance"], 2.5)

readonly property var environmentDefaultsMap: environmentDefaultsMapFor(sceneDefaults)
property color environmentBackgroundColorDefault: environmentDefaultString(environmentDefaultsMap, ["background_color", "backgroundColor"], "#1f242c")
property string environmentBackgroundModeDefault: environmentDefaultString(environmentDefaultsMap, ["background_mode", "backgroundMode"], "skybox")
property bool environmentSkyboxEnabledDefault: environmentDefaultBool(environmentDefaultsMap, ["skybox_enabled", "skyboxEnabled"], true)
property bool environmentIblBackgroundEnabledDefault: environmentDefaultBool(environmentDefaultsMap, ["ibl_background_enabled", "iblBackgroundEnabled", "skybox_enabled", "skyboxEnabled"], true)
property bool environmentIblLightingEnabledDefault: environmentDefaultBool(environmentDefaultsMap, ["ibl_lighting_enabled", "iblLightingEnabled", "ibl_enabled", "iblEnabled"], true)
property bool environmentIblMasterEnabledDefault: environmentDefaultBool(environmentDefaultsMap, ["ibl_master_enabled", "iblMasterEnabled"], environmentIblLightingEnabledDefault || environmentIblBackgroundEnabledDefault)
property bool environmentIblBindToCameraDefault: environmentDefaultBool(environmentDefaultsMap, ["ibl_bind_to_camera", "iblBindToCamera"], false)
property real environmentIblIntensityDefault: environmentDefaultNumber(environmentDefaultsMap, ["ibl_intensity", "iblIntensity"], 1.3)
property real environmentSkyboxBrightnessDefault: environmentDefaultNumber(environmentDefaultsMap, ["skybox_brightness", "probe_brightness", "skyboxBrightness", "probeBrightness"], 1.0)
property real environmentProbeHorizonDefault: environmentDefaultNumber(environmentDefaultsMap, ["probe_horizon", "probeHorizon"], 0.0)
property real environmentIblRotationPitchDefault: environmentDefaultNumber(environmentDefaultsMap, ["ibl_offset_x", "iblRotationPitchDeg"], 0.0)
property real environmentIblRotationYawDefault: environmentDefaultNumber(environmentDefaultsMap, ["ibl_rotation", "iblRotationDeg"], 0.0)
property real environmentIblRotationRollDefault: environmentDefaultNumber(environmentDefaultsMap, ["ibl_offset_y", "iblRotationRollDeg"], 0.0)
property real environmentSkyboxBlurDefault: environmentDefaultNumber(environmentDefaultsMap, ["skybox_blur", "skyboxBlur"], 0.08)
property url environmentHdrSourceDefault: normalizeHdrSource(environmentDefaultString(environmentDefaultsMap, ["ibl_source", "hdr_source", "iblPrimary"], ""))

property bool reflectionProbeEnabled: environmentDefaultBool(environmentDefaultsMap, ["reflection_enabled", "reflectionEnabled"], true)
// Padding stored in metres; converted to scene units where required
property real reflectionProbePaddingM: environmentDefaultNumber(environmentDefaultsMap, ["reflection_padding_m", "reflectionPadding"], 0.15)
property int reflectionProbeQualityValue: reflectionProbeQualityFrom(environmentDefaultString(environmentDefaultsMap, ["reflection_quality", "reflectionQuality"], "veryhigh"))
property int reflectionProbeRefreshModeValue: reflectionProbeRefreshModeFrom(environmentDefaultString(environmentDefaultsMap, ["reflection_refresh_mode", "reflectionRefreshMode"], "everyframe"))
property int reflectionProbeTimeSlicingValue: reflectionProbeTimeSlicingFrom(environmentDefaultString(environmentDefaultsMap, ["reflection_time_slicing", "reflectionTimeSlicing"], "individualfaces"))

 property bool signalTraceOverlayVisible: false
 property bool signalTraceRecordingEnabled: false
 property int signalTraceHistoryLimit: 200
 property bool signalTracePanelExpanded: false
 property var signalTraceHistory: []
 property bool _signalTraceSyncing: false
 property var shaderWarningMap: ({})
 property var shaderWarningList: []

 function setDiagnosticsLoggingEnabled(enabled) {
  diagnosticsLoggingEnabled = !!enabled
 }

 function notifyPythonShaderEvent(handlerName, args) {
  if (!handlerName || !args)
   return false

  var potentialTargets = []
  if (typeof window !== "undefined" && window)
   potentialTargets.push(window)
  if (root.sceneBridge)
   potentialTargets.push(root.sceneBridge)

  for (var idx = 0; idx < potentialTargets.length; ++idx) {
   var target = potentialTargets[idx]
   var handler = target && typeof target[handlerName] === "function" ? target[handlerName] : null
   if (typeof handler === "function") {
    try {
     handler.apply(target, args)
     return true
    } catch (error) {
     console.debug("[SimulationRoot]", handlerName, "forwarding failed", error)
    }
   }
  }

  return false
 }

 // ---------------------------------------------
 // Shader compilation diagnostics
 // ---------------------------------------------
 function registerShaderWarning(effectId, message) {
  var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
  var normalizedMessage = message !== undefined && message !== null ? String(message) : qsTr("Shader compilation failed")

  var hadEntry = Object.prototype.hasOwnProperty.call(shaderWarningMap, normalizedId)
  var previousEntry = hadEntry ? shaderWarningMap[normalizedId] : null

  var nextMap = Object.assign({}, shaderWarningMap)
  nextMap[normalizedId] = {
   id: normalizedId,
   message: normalizedMessage,
   timestamp: Date.now()
  }

  shaderWarningMap = nextMap
  shaderWarningList = Object.values(nextMap).sort(function(a, b) { return a.timestamp - b.timestamp })
  console.warn("⚠️ Shader fallback activated for", normalizedId, "-", normalizedMessage)

  try {
   Diagnostics.forward(
    "shader_warning",
    normalizedId + ": " + normalizedMessage,
    typeof window !== "undefined" ? window : null,
    "SimulationRoot"
   )
  } catch (diagnosticsError) {
   console.debug("[SimulationRoot] Diagnostics.forward failed for shader warning", diagnosticsError)
  }

  var messageChanged = !previousEntry || previousEntry.message !== normalizedMessage
  if (messageChanged)
   notifyPythonShaderEvent("registerShaderWarning", [normalizedId, normalizedMessage])
 }

 function clearShaderWarning(effectId) {
  var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
  if (!Object.prototype.hasOwnProperty.call(shaderWarningMap, normalizedId))
   return

  var nextMap = Object.assign({}, shaderWarningMap)
  delete nextMap[normalizedId]
  shaderWarningMap = nextMap
  shaderWarningList = Object.values(nextMap).sort(function(a, b) { return a.timestamp - b.timestamp })
  console.log("✅ Shader restored for", normalizedId)

  try {
   Diagnostics.forward(
    "shader_warning_cleared",
    normalizedId,
    typeof window !== "undefined" ? window : null,
    "SimulationRoot"
   )
  } catch (diagnosticsError) {
   console.debug("[SimulationRoot] Diagnostics.forward failed for shader clear", diagnosticsError)
  }

  notifyPythonShaderEvent("clearShaderWarning", [normalizedId])
 }

 property real renderScale: 1.0
 property real frameRateLimit: 144.0
 property string renderPolicyKey: "always"
 property bool renderSettingsSupported: false
 property var sceneRenderSettings: null

 // -------- Геометрия подвески (СИ) --------
 property real userFrameLength: geometryDefaultNumber(["frameLength", "frame_length", "frame_length_m", "wheelbase"], 0.0)
 property real userFrameHeight: geometryDefaultNumber(["frameHeight", "frame_height", "frame_height_m"], 0.0)
 property real userBeamSize: geometryDefaultNumber(["beamSize", "frame_beam_size", "frame_beam_size_m"], 0.0)
 property real userLeverLength: geometryDefaultNumber(["leverLength", "lever_length", "lever_length_m"], 0.0)
 property real userCylinderLength: geometryDefaultNumber(["cylinderLength", "cylinder_length", "cylinder_body_length", "cylinder_body_length_m"], 0.0)
 property real userTrackWidth: geometryDefaultNumber(["trackWidth", "track", "track_width", "track_width_m"], 0.0)
 property real userFrameToPivot: geometryDefaultNumber(["frameToPivot", "frame_to_pivot", "frame_to_pivot_m"], 0.0)
 property real userRodPosition: geometryDefaultNumber(["rodPosition", "rod_position", "attachFrac"], 0.0)
 property real userBoreHead: geometryDefaultNumber(["boreHead", "bore", "bore_d", "cyl_diam", "cyl_diam_m"], 0.0)
 property real userRodDiameter: geometryDefaultNumber(["rodDiameter", "rod_diameter", "rod_diameter_m", "rod_diameter_rear_m"], 0.0)
 property real userPistonThickness: geometryDefaultNumber(["pistonThickness", "piston_thickness", "piston_thickness_m"], 0.0)
 property real userPistonRodLength: geometryDefaultNumber(["pistonRodLength", "piston_rod_length", "piston_rod_length_m"], 0.0)
 property real userTailRodLength: geometryDefaultNumber(["tailRodLength", "tail_rod_length", "tail_rod_length_m"], 0.0)
 property int userCylinderSegments: Math.max(3, Math.round(geometryDefaultNumber(["cylinderSegments"], 64)))
 property int userCylinderRings: Math.max(1, Math.round(geometryDefaultNumber(["cylinderRings"], 8)))

 readonly property var defaultCameraGeometryMeters: Object.freeze({
     frameLength: 1.6,
     frameHeight: 0.6,
     trackWidth: 1.2,
     beamSize: 0.25,
     frameToPivot: 0.8
 })

 property var lightingState: ({
 key: {},
 fill: {},
 rim: {},
 point: {},
 spot: {},
 global: {}
 })

 QtObject {
  id: lightingAccess
  function value(group, key, fallback) {
   var groupState = root.lightingState && root.lightingState[group];
   if (groupState && groupState[key] !== undefined)
    return groupState[key];
   return fallback;
  }
  function globalValue(key, fallback) {
   var globalState = root.lightingState && root.lightingState.global;
   if (!globalState)
    return fallback;
   if (globalState[key] !== undefined)
    return globalState[key];
   var alt = key.indexOf("_") >= 0
    ? key.replace(/_([a-z])/g, function(_, ch) { return ch.toUpperCase(); })
    : key.replace(/[A-Z]/g, function(ch) { return "_" + ch.toLowerCase(); });
   if (globalState[alt] !== undefined)
    return globalState[alt];
   return fallback;
  }
 }

 property var geometryState: ({
  frameLength: userFrameLength,
  frameHeight: userFrameHeight,
  beamSize: userBeamSize,
  trackWidth: userTrackWidth,
  frameToPivot: userFrameToPivot,
  leverLength: userLeverLength,
  rodPosition: userRodPosition,
  cylinderLength: userCylinderLength,
  boreHead: userBoreHead,
  rodDiameter: userRodDiameter,
  pistonThickness: userPistonThickness,
  pistonRodLength: userPistonRodLength,
  tailRodLength: userTailRodLength,
  cylinderSegments: userCylinderSegments,
  cylinderRings: userCylinderRings
 })

 function cameraGeometryPayloadMeters() {
  var defaults = defaultCameraGeometryMeters

  function resolveLength(value, fallback) {
   var numeric = Number(value)
   if (isFinite(numeric) && numeric > 0)
    return numeric
   return fallback
  }

  var payload = {
   frameLength: resolveLength(userFrameLength, defaults.frameLength),
   frameHeight: resolveLength(userFrameHeight, defaults.frameHeight),
   trackWidth: resolveLength(userTrackWidth, defaults.trackWidth),
   beamSize: resolveLength(userBeamSize, defaults.beamSize),
   frameToPivot: resolveLength(userFrameToPivot, defaults.frameToPivot)
  }

  if (!isFinite(payload.frameToPivot) || payload.frameToPivot <= 0) {
   payload.frameToPivot = payload.frameLength > 0 ? payload.frameLength / 2 : defaults.frameToPivot
  }

  return payload
 }

 function initializeCameraControllerGeometry() {
  if (!cameraController || typeof cameraController.updateGeometry !== "function")
   return

  var payload = cameraGeometryPayloadMeters()

  try {
   cameraController.updateGeometry(payload)
  } catch (error) {
   console.warn("[SimulationRoot] Failed to prime camera geometry", error)
  }
 }

onIsRunningChanged: {
 if (isRunning) {
  fallbackBaseTime = animationTime
  restartFallbackTimeline()
 } else {
  fallbackTimeline.running = false
  updateFallbackAngles()
 }
}

 onFallbackEnabledChanged: {
  if (fallbackEnabled) {
   fallbackBaseTime = animationTime
   lastFallbackPhase = fallbackPhase
   restartFallbackTimeline()
   updateFallbackAngles()
  } else {
   fallbackTimeline.running = false
  }
 }

 onPythonAnimationActiveChanged: {
  if (pythonAnimationActive) {
   fallbackTimeline.running = false
  } else if (fallbackEnabled) {
   fallbackBaseTime = animationTime
   lastFallbackPhase = fallbackPhase
   restartFallbackTimeline()
   updateFallbackAngles()
  }
 }

 onFallbackPhaseChanged: {
  if (!fallbackEnabled)
   return
  if (fallbackPhase < lastFallbackPhase)
   fallbackBaseTime += fallbackCycleSeconds
  animationTime = fallbackBaseTime + fallbackPhase * fallbackCycleSeconds
  lastFallbackPhase = fallbackPhase
  updateFallbackAngles()
 }

 onUserFrequencyChanged: {
  if (fallbackEnabled) {
   fallbackBaseTime = animationTime
   lastFallbackPhase = fallbackPhase
   restartFallbackTimeline()
  }
  updateFallbackAngles()
 }

 onUserAmplitudeChanged: updateFallbackAngles()
 onUserPhaseGlobalChanged: updateFallbackAngles()
 onUserPhaseFLChanged: updateFallbackAngles()
 onUserPhaseFRChanged: updateFallbackAngles()
 onUserPhaseRLChanged: updateFallbackAngles()
 onUserPhaseRRChanged: updateFallbackAngles()

 onBatchUpdatesApplied: function(summary) {
  feedbackReady = true
  batchFlash.restart()
 }

// Масштаб перевода метров в сцену Qt Quick3D (значение 1.0 = метры в сцене)
property real sceneScaleFactor: sceneDefaults && sceneDefaults.scale_factor !== undefined ? Number(sceneDefaults.scale_factor) : 1.0
 readonly property real effectiveSceneScaleFactor: (function() {
 var numeric = Number(sceneScaleFactor);
 if (!isFinite(numeric) || numeric <= 0)
 return 1.0;
 return numeric;
 })()

// Анимация рычагов (град)
 // Значения по умолчанию соответствуют current.animation секции (8°, 1 Гц, 0° фазовые сдвиги)
 property real userAmplitude: animationDefaultNumber(["amplitude"], 8.0)
 property real userFrequency: animationDefaultNumber(["frequency"], 1.0)
 property real userPhaseGlobal: animationDefaultNumber(["phase_global"], 0.0)
 property real userPhaseFL: animationDefaultNumber(["phase_fl"], 0.0)
 property real userPhaseFR: animationDefaultNumber(["phase_fr"], 0.0)
 property real userPhaseRL: animationDefaultNumber(["phase_rl"], 0.0)
 property real userPhaseRR: animationDefaultNumber(["phase_rr"], 0.0)

// Настройки сглаживания анимации
 readonly property string defaultSmoothingEasing: rigAnimation ? rigAnimation.defaultEasingName : "OutCubic" // соответствует animation.smoothing_easing
 property bool animationSmoothingEnabled: animationDefaultBool(["smoothing_enabled"], true)
 property real animationSmoothingDurationMs: animationDefaultNumber(["smoothing_duration_ms"], 120.0)
 property real animationSmoothingAngleSnapDeg: animationDefaultNumber(["smoothing_angle_snap_deg"], 65.0)
 property real animationSmoothingPistonSnapM: animationDefaultNumber(["smoothing_piston_snap_m"], 0.05)
 property string animationSmoothingEasing: animationDefaultString([
     "smoothing_easing",
     "smoothingEasing"
 ], defaultSmoothingEasing)

 RigAnimationController {
  id: rigAnimation
  smoothingEnabled: root.animationSmoothingEnabled
  smoothingDurationMs: root.animationSmoothingDurationMs
  angleSnapThresholdDeg: root.animationSmoothingAngleSnapDeg
  pistonSnapThresholdM: root.animationSmoothingPistonSnapM
  smoothingEasingName: root.animationSmoothingEasing
}

 // Данные симуляции в СИ
 property alias flAngleRad: rigAnimation.flAngleRad
 property alias frAngleRad: rigAnimation.frAngleRad
 property alias rlAngleRad: rigAnimation.rlAngleRad
 property alias rrAngleRad: rigAnimation.rrAngleRad
 property alias fl_angle: rigAnimation.flAngleDeg
 property alias fr_angle: rigAnimation.frAngleDeg
 property alias rl_angle: rigAnimation.rlAngleDeg
 property alias rr_angle: rigAnimation.rrAngleDeg
 property alias frameHeave: rigAnimation.frameHeave
 property alias frameRollRad: rigAnimation.frameRollRad
 property alias framePitchRad: rigAnimation.framePitchRad
 property alias frameRollDeg: rigAnimation.frameRollDeg
 property alias framePitchDeg: rigAnimation.framePitchDeg
 property alias pistonPositions: rigAnimation.pistonPositions
 property var linePressures: ({})
 property real tankPressure:0.0

 // Ссылки на основные контроллеры сцены
 readonly property alias environmentController: sceneEnvCtl
 readonly property alias cameraController: cameraController
 readonly property alias view3d: sceneView
 readonly property alias camera: cameraController.camera

 // ---------------------------------------------------------
 // Environment compatibility layer (legacy bindings support)
 // ---------------------------------------------------------
 property alias bloomEnabled: sceneEnvCtl.bloomEnabled
 property alias bloomIntensity: sceneEnvCtl.bloomIntensity
 property alias bloomThreshold: sceneEnvCtl.bloomThreshold
 property alias bloomSpread: sceneEnvCtl.bloomSpread
 property alias bloomGlowStrength: sceneEnvCtl.bloomGlowStrength
 property alias ssaoEnabled: sceneEnvCtl.ssaoEnabled
 property alias ssaoRadius: sceneEnvCtl.ssaoRadius
 property alias ssaoIntensity: sceneEnvCtl.ssaoIntensity
 property alias depthOfFieldEnabled: sceneEnvCtl.internalDepthOfFieldEnabled
 property alias dofFocusDistance: sceneEnvCtl.dofFocusDistance
 property alias dofFocusRange: sceneEnvCtl.dofFocusRange
 property alias tonemapActive: sceneEnvCtl.tonemapActive
 property alias tonemapModeName: sceneEnvCtl.tonemapModeName
 property alias tonemapExposure: sceneEnvCtl.tonemapExposure
 property alias tonemapWhitePoint: sceneEnvCtl.tonemapWhitePoint
 property alias fogEnabled: sceneEnvCtl.fogEnabled
 property alias fogColor: sceneEnvCtl.fogColor
 property alias fogDensity: sceneEnvCtl.fogDensity
 property alias vignetteEnabled: sceneEnvCtl.internalVignetteEnabled
 property alias vignetteStrength: sceneEnvCtl.internalVignetteStrength

 // -------- Материалы/вид --------
 property color defaultClearColor: sceneDefaults && sceneDefaults.default_clear_color ? sceneDefaults.default_clear_color : "#1a1a2e"
 property color modelBaseColor: sceneDefaults && sceneDefaults.model_base_color ? sceneDefaults.model_base_color : "#9ea4ab"
 property real modelRoughness: sceneDefaults && sceneDefaults.model_roughness !== undefined ? Number(sceneDefaults.model_roughness) :0.35
 property real modelMetalness: sceneDefaults && sceneDefaults.model_metalness !== undefined ? Number(sceneDefaults.model_metalness) :0.9

 // ---------------------------------------------
 // Основные3D-компоненты сцены
 // ---------------------------------------------

 function cloneMap(source) {
 if (!source || typeof source !== "object")
 return {}
 var result = {}
 for (var key in source) {
 if (source.hasOwnProperty(key))
 result[key] = source[key]
 }
 return result
 }

property var _defaultFallbackRegistry: ({})

function defaultDebugValue(value) {
    if (value === undefined)
        return "undefined"
    if (value === null)
        return "null"
    if (typeof value === "number" && !isFinite(value))
        return String(value)
    try {
        var text = JSON.stringify(value)
        if (text !== undefined)
            return text
    } catch (err) {
    }
    return String(value)
}

function recordDefaultFallback(scope, keyList, fallbackValue, reason) {
    var list = Array.isArray(keyList) ? keyList : [keyList]
    var token = scope + ":" + list.join("|")
    if (_defaultFallbackRegistry[token])
        return
    _defaultFallbackRegistry[token] = true
    var reasonText = reason ? " (" + reason + ")" : ""
    console.warn("[SimulationRoot] ⚠️ " + scope + " default for " + list.join(" | ") + " unavailable" + reasonText + "; using fallback " + defaultDebugValue(fallbackValue))
}

function geometryDefaultNumber(keys, fallback) {
    var defaults = geometryDefaults || emptyGeometryDefaults
    var list = Array.isArray(keys) ? keys : [keys]
    for (var i = 0; i < list.length; ++i) {
        var candidate = defaults[list[i]]
        if (candidate !== undefined && candidate !== null) {
            var numeric = Number(candidate)
            if (isFinite(numeric))
                return numeric
            recordDefaultFallback("geometry", [list[i]], fallback, "invalid value " + defaultDebugValue(candidate))
        }
    }
    var fallbackNumeric = Number(fallback)
    if (!isFinite(fallbackNumeric))
        fallbackNumeric = 0.0
    var reason = defaults && Object.keys(defaults).length ? "missing key" : "defaults unavailable"
    recordDefaultFallback("geometry", list, fallbackNumeric, reason)
    return fallbackNumeric
}

function environmentDefaultsMapFor(source) {
    if (!source || typeof source !== "object" || Array.isArray(source))
        return {}
    if (source.environment && typeof source.environment === "object" && !Array.isArray(source.environment))
        return source.environment
    return source
}

function environmentDefaultRaw(defaults, list) {
    if (!defaults || typeof defaults !== "object")
        return undefined
    for (var i = 0; i < list.length; ++i) {
        var key = list[i]
        if (Object.prototype.hasOwnProperty.call(defaults, key))
            return defaults[key]
        var alt = key.indexOf("_") >= 0
            ? key.replace(/_([a-z])/g, function(_, ch) { return ch.toUpperCase() })
            : key.replace(/[A-Z]/g, function(ch) { return "_" + ch.toLowerCase() })
        if (Object.prototype.hasOwnProperty.call(defaults, alt))
            return defaults[alt]
    }
    return undefined
}

function environmentDefaultNumber(defaults, keys, fallback) {
    var list = Array.isArray(keys) ? keys : [keys]
    var raw = environmentDefaultRaw(defaults, list)
    if (raw === undefined || raw === null) {
        var fallbackNumeric = Number(fallback)
        if (!isFinite(fallbackNumeric))
            fallbackNumeric = 0.0
        var reason = defaults && Object.keys(defaults).length ? "missing key" : "defaults unavailable"
        recordDefaultFallback("environment", list, fallbackNumeric, reason)
        return fallbackNumeric
    }
    var numeric = Number(raw)
    if (isFinite(numeric))
        return numeric
    var fallbackNumeric = Number(fallback)
    if (!isFinite(fallbackNumeric))
        fallbackNumeric = 0.0
    recordDefaultFallback("environment", list, fallbackNumeric, "invalid value " + defaultDebugValue(raw))
    return fallbackNumeric
}

function environmentDefaultBool(defaults, keys, fallback) {
    var list = Array.isArray(keys) ? keys : [keys]
    var raw = environmentDefaultRaw(defaults, list)
    if (raw === undefined || raw === null) {
        var fallbackBool = !!fallback
        var reason = defaults && Object.keys(defaults).length ? "missing key" : "defaults unavailable"
        recordDefaultFallback("environment", list, fallbackBool, reason)
        return fallbackBool
    }
    if (typeof raw === "boolean")
        return raw
    if (typeof raw === "number")
        return raw !== 0
    if (typeof raw === "string") {
        var token = raw.trim().toLowerCase()
        if (token === "true" || token === "yes" || token === "on")
            return true
        if (token === "false" || token === "no" || token === "off")
            return false
        var numeric = Number(raw)
        if (isFinite(numeric))
            return numeric !== 0
    }
    var fallbackBool = !!fallback
    recordDefaultFallback("environment", list, fallbackBool, "invalid value " + defaultDebugValue(raw))
    return fallbackBool
}

function environmentDefaultString(defaults, keys, fallback) {
    var list = Array.isArray(keys) ? keys : [keys]
    var raw = environmentDefaultRaw(defaults, list)
    if (raw === undefined || raw === null) {
        var fallbackText = fallback !== undefined && fallback !== null ? String(fallback) : ""
        var reason = defaults && Object.keys(defaults).length ? "missing key" : "defaults unavailable"
        recordDefaultFallback("environment", list, fallbackText, reason)
        return fallbackText
    }
    var text = String(raw)
    if (text.length)
        return text
    var fallbackText = fallback !== undefined && fallback !== null ? String(fallback) : ""
    recordDefaultFallback("environment", list, fallbackText, "empty string value")
    return fallbackText
}

function normalizeHdrSource(source) {
    if (source === undefined || source === null)
        return ""
    var resolved = String(source)
    if (!resolved.length)
        return ""
    if (typeof window !== "undefined" && window && typeof window.normalizeHdrPath === "function") {
        try {
            resolved = window.normalizeHdrPath(resolved)
        } catch (error) {
            console.warn("[SimulationRoot] HDR path normalization failed:", error)
        }
    }
    return resolved
}

function animationDefaultNumber(keys, fallback) {
    var defaults = animationDefaults || {}
    var list = Array.isArray(keys) ? keys : [keys]
    for (var i = 0; i < list.length; ++i) {
        var candidate = defaults[list[i]]
        if (candidate !== undefined && candidate !== null) {
            var numeric = Number(candidate)
            if (isFinite(numeric))
                return numeric
            recordDefaultFallback("animation", [list[i]], fallback, "invalid value " + defaultDebugValue(candidate))
        }
    }
    var fallbackNumeric = Number(fallback)
    if (!isFinite(fallbackNumeric))
        fallbackNumeric = 0.0
    var reason = defaults && Object.keys(defaults).length ? "missing key" : "defaults unavailable"
    recordDefaultFallback("animation", list, fallbackNumeric, reason)
    return fallbackNumeric
}

function animationDefaultBool(keys, fallback) {
    var defaults = animationDefaults || {}
    var list = Array.isArray(keys) ? keys : [keys]
    for (var i = 0; i < list.length; ++i) {
        var candidate = defaults[list[i]]
        if (candidate !== undefined && candidate !== null)
            return !!candidate
    }
    if (!defaults || !Object.keys(defaults).length)
        recordDefaultFallback("animation", list, !!fallback, "defaults unavailable")
    else
        recordDefaultFallback("animation", list, !!fallback, "missing key")
    return !!fallback
}

function animationDefaultString(keys, fallback) {
    var defaults = animationDefaults || {}
    var list = Array.isArray(keys) ? keys : [keys]
    for (var i = 0; i < list.length; ++i) {
        var candidate = defaults[list[i]]
        if (candidate !== undefined && candidate !== null) {
            var text = String(candidate)
            if (text.length)
                return text
            recordDefaultFallback("animation", [list[i]], fallback, "empty string value")
        }
    }
    if (fallback === undefined || fallback === null)
        return ""
    var fallbackText = String(fallback)
    var reason = defaults && Object.keys(defaults).length ? "missing key" : "defaults unavailable"
    recordDefaultFallback("animation", list, fallbackText, reason)
    return fallbackText
}

function effectsDefaults() {
    if (!sceneDefaults || !sceneDefaults.graphics)
        return {}
    var graphics = sceneDefaults.graphics
    if (!graphics || typeof graphics !== "object")
        return {}
    var effects = graphics.effects
    if (!effects || typeof effects !== "object")
        return {}
    return effects
}

function effectsDefaultNumber(keys, fallback) {
    var defaults = effectsDefaults()
    var list = Array.isArray(keys) ? keys : [keys]
    for (var i = 0; i < list.length; ++i) {
        var candidate = defaults[list[i]]
        if (candidate !== undefined && candidate !== null) {
            var numeric = Number(candidate)
            if (isFinite(numeric))
                return numeric
            recordDefaultFallback("effects", [list[i]], fallback, "invalid value " + defaultDebugValue(candidate))
        }
    }
    var fallbackNumeric = Number(fallback)
    if (!isFinite(fallbackNumeric))
        fallbackNumeric = 0.0
    var reason = defaults && Object.keys(defaults).length ? "missing key" : "defaults unavailable"
    recordDefaultFallback("effects", list, fallbackNumeric, reason)
    return fallbackNumeric
}

 function restartFallbackTimeline() {
 if (!fallbackEnabled)
 return
 fallbackPhase = 0.0
 lastFallbackPhase = 0.0
 fallbackBaseTime = animationTime
 fallbackTimeline.running = false
 fallbackTimeline.running = true
 }

 function updateFallbackAngles() {
 if (pythonLeverAnglesActive)
  return
 if (!isRunning) {
  rigAnimation.applyLeverAnglesRadians({ fl: 0.0, fr: 0.0, rl: 0.0, rr: 0.0 }, { immediate: true })
  return
 }
 var globalPhaseRad = userPhaseGlobal * Math.PI / 180.0
 var amplitudeRad = userAmplitude * Math.PI / 180.0
 var base = animationTime * userFrequency * 2.0 * Math.PI

 function angleFor(offsetDeg) {
  var offsetRad = offsetDeg * Math.PI / 180.0
  return amplitudeRad * Math.sin(base + globalPhaseRad + offsetRad)
 }

 rigAnimation.applyLeverAnglesRadians({
  fl: angleFor(userPhaseFL),
  fr: angleFor(userPhaseFR),
  rl: angleFor(userPhaseRL),
  rr: angleFor(userPhaseRR)
 })
 }

 function applyCameraHudSettings(payload) {
 if (!payload)
 return
 var current = cloneMap(cameraHudSettings)
 var updated = cloneMap(payload)
 for (var key in current) {
 if (current.hasOwnProperty(key) && updated[key] === undefined)
 updated[key] = current[key]
 }
 if (payload.enabled !== undefined)
 updated.enabled = !!payload.enabled
 cameraHudSettings = updated
 if (payload.enabled !== undefined)
 cameraHudEnabled = !!payload.enabled
 }

 function setCameraHudEnabled(enabled) {
 var flag = !!enabled
 if (cameraHudEnabled !== flag)
 cameraHudEnabled = flag
 var current = cloneMap(cameraHudSettings)
 if (current.enabled !== flag) {
 current.enabled = flag
 cameraHudSettings = current
 }
 }

function toggleCameraHud() {
 setCameraHudEnabled(!cameraHudEnabled)
}

function toggleAnimation() {
 var next = !isRunning
 isRunning = next
 pythonAnimationActive = false
 if (next) {
  fallbackBaseTime = animationTime
  restartFallbackTimeline()
 } else {
  fallbackTimeline.running = false
  updateFallbackAngles()
 }
 animationToggled(next)
}

 function applySignalTraceSettings(payload) {
  if (!payload)
   return
  _signalTraceSyncing = true
  try {
   if (payload.overlay_enabled !== undefined || payload.overlayEnabled !== undefined) {
    const overlayValue = payload.overlay_enabled !== undefined ? payload.overlay_enabled : payload.overlayEnabled
    signalTraceOverlayVisible = Boolean(overlayValue)
    if (!signalTraceOverlayVisible)
     signalTracePanelExpanded = false
   }
   if (payload.enabled !== undefined) {
    signalTraceRecordingEnabled = Boolean(payload.enabled)
   }
   if (payload.history_limit !== undefined || payload.historyLimit !== undefined) {
    const rawLimit = payload.history_limit !== undefined ? payload.history_limit : payload.historyLimit
    const limitNumber = Number(rawLimit)
    if (!isNaN(limitNumber) && isFinite(limitNumber)) {
     signalTraceHistoryLimit = Math.max(1, Math.floor(limitNumber))
    }
   }
  } finally {
   _signalTraceSyncing = false
  }
 }

 function handleDiagnosticsSettingChange(change) {
  if (!change || !change.path)
   return
  var pathStr = String(change.path)
  if (pathStr === "diagnostics.camera_hud") {
   applyCameraHudSettings(change.newValue)
   return
  }
  if (pathStr === "diagnostics.camera_hud.enabled") {
   setCameraHudEnabled(change.newValue)
   return
  }
  if (pathStr.indexOf("diagnostics.camera_hud.") ===0) {
   var key = pathStr.substring("diagnostics.camera_hud.".length)
   var patch = {}
   patch[key] = change.newValue
   applyCameraHudSettings(patch)
   return
  }
  if (pathStr === "diagnostics.signal_trace") {
   applySignalTraceSettings(change.newValue)
   return
  }
  if (
   pathStr === "diagnostics.signal_trace.overlay_enabled"
   || pathStr === "diagnostics.signal_trace.overlayEnabled"
  ) {
   applySignalTraceSettings({ overlay_enabled: change.newValue })
   return
  }
  if (pathStr === "diagnostics.signal_trace.enabled") {
   applySignalTraceSettings({ enabled: change.newValue })
   return
  }
  if (
   pathStr === "diagnostics.signal_trace.history_limit"
   || pathStr === "diagnostics.signal_trace.historyLimit"
  ) {
   applySignalTraceSettings({ history_limit: change.newValue })
  }
 }

SceneEnvironmentController {
 id: sceneEnvCtl
 objectName: "sceneEnvironmentController"
 sceneBridge: root.sceneBridge
 sceneScaleFactor: root.sceneScaleFactor
 diagnosticsLoggingEnabled: root.diagnosticsLoggingEnabled
 backgroundColor: root.environmentBackgroundColorDefault
 backgroundModeKey: root.environmentBackgroundModeDefault
 skyboxToggleFlag: root.environmentSkyboxEnabledDefault
 iblBackgroundEnabled: root.environmentIblBackgroundEnabledDefault
 iblLightingEnabled: root.environmentIblLightingEnabledDefault
 iblMasterEnabled: root.environmentIblMasterEnabledDefault
 iblBindToCamera: root.environmentIblBindToCameraDefault
 iblIntensity: root.environmentIblIntensityDefault
 skyboxBrightnessValue: root.environmentSkyboxBrightnessDefault
 probeHorizonValue: root.environmentProbeHorizonDefault
 iblRotationPitchDeg: root.environmentIblRotationPitchDefault
 iblRotationDeg: root.environmentIblRotationYawDefault
 iblRotationRollDeg: root.environmentIblRotationRollDefault
 skyboxBlurValue: root.environmentSkyboxBlurDefault
}

IblProbeLoader {
 id: iblLoader
 objectName: "iblProbeLoader"
 visible: false
 primarySource: root.environmentHdrSourceDefault
}

 SequentialAnimation {
 id: batchFlash
 running: false
 onStopped: batchFlashOpacity = 0.0

 PropertyAnimation {
 target: root
 property: "batchFlashOpacity"
 from: 0.0
 to: 0.6
 duration: 140
 easing.type: Easing.OutCubic
 }

 PauseAnimation { duration: 180 }

 PropertyAnimation {
 target: root
 property: "batchFlashOpacity"
 to: 0.0
 duration: 320
 easing.type: Easing.InOutQuad
 }
 }

// Таймлайн нужен только для непрерывности визуализации, когда Python временно
// перестает публиковать кадры. Он запускается строго при fallbackEnabled и не
// скрывает ошибки загрузки данных: при сбоях isRunning тоже выключается.
SequentialAnimation {
 id: fallbackTimeline
 running: fallbackEnabled
 loops: Animation.Infinite
 alwaysRunToEnd: false

 onRunningChanged: {
  if (!running) {
   root.fallbackPhase = 0.0
  }
 }

 NumberAnimation {
  target: root
  property: "fallbackPhase"
  from: 0.0
  to: 1.0
  duration: Math.max(16, fallbackCycleSeconds * 1000)
  easing.type: Easing.Linear
 }
}

 Timer {
 id: pythonAnimationTimeout
 interval: 800
 repeat: false
 onTriggered: pythonAnimationActive = false
 }

 Timer {
 id: pythonLeverAnglesTimeout
 interval: 800
 repeat: false
 onTriggered: {
 pythonLeverAnglesActive = false
 updateFallbackAngles()
 }
 }

 Timer {
 id: pythonPistonsTimeout
 interval: 800
 repeat: false
 onTriggered: pythonPistonsActive = false
 }

 Timer {
 id: pythonFrameTimeout
 interval: 800
 repeat: false
 onTriggered: pythonFrameActive = false
 }

 Timer {
 id: pythonPressureTimeout
 interval: 800
 repeat: false
 onTriggered: pythonPressureActive = false
 }

    PostEffects {
        id: postEffects
        anchors.fill: parent
        visible: false
        diagnosticsLoggingEnabled: root.diagnosticsLoggingEnabled
    }

    Connections {
        target: postEffects

        function onEffectCompilationError(effectId, errorLog) {
            root.registerShaderWarning(effectId, errorLog)
        }

        function onEffectCompilationRecovered(effectId) {
            root.clearShaderWarning(effectId)
        }
    }

      View3D {
          id: sceneView
          anchors.fill: parent
          environment: sceneEnvCtl

          Component.onCompleted: {
              initializeRenderSettings()
              var depthActivated = DepthTextureActivator.activate(sceneView)
              if (depthActivated) {
                  console.log("✅ SimulationRoot: DepthTextureActivator successfully applied")
              } else {
                  console.warn("⚠️ SimulationRoot: DepthTextureActivator returned false; logging status")
                  DepthTextureActivator.logStatus(sceneView)
              }
          }

        Scene.SharedMaterials {
            id: sharedMaterials
        }

 Node {
 id: worldRoot
 position: Qt.vector3d(0, frameHeave,0)
 eulerRotation: Qt.vector3d(framePitchDeg,0, frameRollDeg)

 DirectionalLights {
 id: directionalLights
 worldRoot: worldRoot
 cameraRig: cameraController.rig
    shadowsEnabled: !!lightingAccess.globalValue("shadows_enabled", lightingAccess.globalValue("shadowsEnabled", true))
    shadowResolution: {
        var raw = lightingAccess.globalValue(
                    "shadow_resolution",
                    lightingAccess.globalValue("shadowResolution", 4096)
                )
        var numeric = Number(raw)
        return isFinite(numeric) ? Math.round(numeric) : 4096
    }
 shadowFilterSamples: Number(lightingAccess.globalValue("shadow_filter_samples", lightingAccess.globalValue("shadowFilterSamples",32)))
 shadowBias: Number(lightingAccess.globalValue("shadow_bias", lightingAccess.globalValue("shadowBias",8.0)))
 shadowFactor: Number(lightingAccess.globalValue("shadow_factor", lightingAccess.globalValue("shadowFactor",80.0)))

 keyLightBrightness: Number(lightingAccess.value("key", "brightness",1.0))
 keyLightColor: lightingAccess.value("key", "color", "#ffffff")
 keyLightAngleX: Number(lightingAccess.value("key", "angle_x", 25.0))
 keyLightAngleY: Number(lightingAccess.value("key", "angle_y", 23.5))
 keyLightAngleZ: Number(lightingAccess.value("key", "angle_z",0.0))
 keyLightCastsShadow: !!lightingAccess.value("key", "cast_shadow", true)
 keyLightBindToCamera: !!lightingAccess.value("key", "bind_to_camera", false)
 keyLightPosX: Number(lightingAccess.value("key", "position_x",0))
 keyLightPosY: Number(lightingAccess.value("key", "position_y",0))
 keyLightPosZ: Number(lightingAccess.value("key", "position_z",0))

 fillLightBrightness: Number(lightingAccess.value("fill", "brightness",1.0))
 fillLightColor: lightingAccess.value("fill", "color", "#f1f4ff")
 fillLightAngleX: Number(lightingAccess.value("fill", "angle_x", 0.0))
 fillLightAngleY: Number(lightingAccess.value("fill", "angle_y", -45.0))
 fillLightAngleZ: Number(lightingAccess.value("fill", "angle_z",0.0))
 fillLightCastsShadow: !!lightingAccess.value("fill", "cast_shadow", false)
 fillLightBindToCamera: !!lightingAccess.value("fill", "bind_to_camera", false)
 fillLightPosX: Number(lightingAccess.value("fill", "position_x",0))
 fillLightPosY: Number(lightingAccess.value("fill", "position_y",0))
 fillLightPosZ: Number(lightingAccess.value("fill", "position_z",0))

 rimLightBrightness: Number(lightingAccess.value("rim", "brightness",1.1))
 rimLightColor: lightingAccess.value("rim", "color", "#ffe1bd")
 rimLightAngleX: Number(lightingAccess.value("rim", "angle_x",30.0))
 rimLightAngleY: Number(lightingAccess.value("rim", "angle_y",-135.0))
 rimLightAngleZ: Number(lightingAccess.value("rim", "angle_z",0.0))
 rimLightCastsShadow: !!lightingAccess.value("rim", "cast_shadow", false)
 rimLightBindToCamera: !!lightingAccess.value("rim", "bind_to_camera", false)
 rimLightPosX: Number(lightingAccess.value("rim", "position_x",0))
 rimLightPosY: Number(lightingAccess.value("rim", "position_y",0))
 rimLightPosZ: Number(lightingAccess.value("rim", "position_z",0))
 }

 PointLights {
 id: pointLights
 worldRoot: worldRoot
 cameraRig: cameraController.rig
 pointLightBrightness: Number(lightingAccess.value("point", "brightness",50.0))
 pointLightColor: lightingAccess.value("point", "color", "#fff7e0")
 pointLightX: Number(lightingAccess.value("point", "position_x",0.0))
 pointLightY: Number(lightingAccess.value("point", "position_y",2.6))
 pointLightZ: Number(lightingAccess.value("point", "position_z",1.5))
 pointLightRange: Number(lightingAccess.value("point", "range",3.6))
 constantFade: Number(lightingAccess.value("point", "constant_fade",1.0))
 linearFade: Number(lightingAccess.value("point", "linear_fade",0.01))
 quadraticFade: Number(lightingAccess.value("point", "quadratic_fade",1.0))
 pointLightCastsShadow: !!lightingAccess.value("point", "cast_shadow", false)
 pointLightBindToCamera: !!lightingAccess.value("point", "bind_to_camera", false)
 }

 Scene.SuspensionAssembly {
  id: suspensionAssembly
  worldRoot: worldRoot
  geometryState: geometryState
  geometryDefaults: root.geometryDefaults ? root.geometryDefaults : root.emptyGeometryDefaults
  emptyGeometryDefaults: root.emptyGeometryDefaults
  materialsDefaults: root.sceneDefaults && root.sceneDefaults.materials ? root.sceneDefaults.materials : root.emptyMaterialsDefaults
  sharedMaterials: sharedMaterials
  sceneScaleFactor: root.effectiveSceneScaleFactor
  leverAngles: ({
   fl: fl_angle,
   fr: fr_angle,
   rl: rl_angle,
   rr: rr_angle
  })
  pistonPositions: pistonPositions
  reflectionProbeEnabled: root.reflectionProbeEnabled
  reflectionProbePaddingM: root.reflectionProbePaddingM
  reflectionProbeQualityValue: root.reflectionProbeQualityValue
  reflectionProbeRefreshModeValue: root.reflectionProbeRefreshModeValue
  reflectionProbeTimeSlicingValue: root.reflectionProbeTimeSlicingValue
  rodWarningThreshold: 0.001
 }


 CameraController {
 id: cameraController
 objectName: "cameraController"
 anchors.fill: parent
 worldRoot: worldRoot
 view3d: sceneView
 sceneBridge: root.sceneBridge
 sceneScaleFactor: root.sceneScaleFactor
 hudSettings: root.cameraHudSettings
 hudVisible: root.cameraHudEnabled
 taaMotionAdaptive: sceneEnvCtl.taaMotionAdaptive
 frameLength: root.userFrameLength * metersToControllerUnits
 frameHeight: root.userFrameHeight * metersToControllerUnits
 trackWidth: root.userTrackWidth * metersToControllerUnits
 beamSize: root.userBeamSize * metersToControllerUnits
 frameToPivot: root.userFrameToPivot > 0
               ? root.userFrameToPivot * metersToControllerUnits
               : (root.userFrameLength > 0
                  ? root.userFrameLength * metersToControllerUnits / 2
                  : 0)
 onToggleAnimation: function() {
 if (typeof root.toggleAnimation === "function") {
 root.toggleAnimation()
 }
 }
 onHudToggleRequested: root.toggleCameraHud()
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

Binding {
    target: sceneEnvCtl
    property: "cameraClipNear"
    value: cameraController && cameraController.camera
            ? cameraController.camera.clipNear
            : sceneEnvCtl.cameraClipNear
}

Binding {
    target: sceneEnvCtl
    property: "cameraClipFar"
    value: cameraController && cameraController.camera
            ? cameraController.camera.clipFar
            : sceneEnvCtl.cameraClipFar
}

Binding {
    target: sceneEnvCtl
    property: "cameraFieldOfView"
    value: cameraController && cameraController.camera
            ? cameraController.camera.fieldOfView
            : sceneEnvCtl.cameraFieldOfView
}

Binding {
    target: sceneEnvCtl
    property: "cameraAspectRatio"
    value: cameraController && cameraController.camera
            ? cameraController.camera.aspectRatio
            : sceneEnvCtl.cameraAspectRatio
}

Binding {
    target: postEffects
    property: "cameraClipNear"
    value: cameraController && cameraController.camera ? cameraController.camera.clipNear : postEffects.cameraClipNear
}

Binding {
    target: postEffects
    property: "cameraClipFar"
    value: cameraController && cameraController.camera ? cameraController.camera.clipFar : postEffects.cameraClipFar
}

Binding {
    target: sceneEnvCtl
    property: "externalEffects"
    value: postEffects.effectList
}

Binding {
    target: sceneEnvCtl
    property: "autoFocusDistanceHint"
    value: {
        var scale = Number(root.effectiveSceneScaleFactor)
        if (!isFinite(scale) || scale <= 0)
            scale = 1.0
        var defaultDistanceM = Number(root.defaultDofFocusDistanceM)
        if (!isFinite(defaultDistanceM) || defaultDistanceM <= 0)
            defaultDistanceM = 2.5
        if (!cameraController) {
            var storedDistance = Number(sceneEnvCtl.dofFocusDistance)
            if (!isFinite(storedDistance) || storedDistance <= 0) {
                storedDistance = defaultDistanceM * scale
            }
            if (storedDistance > 50 * scale)
                storedDistance = (storedDistance / 1000.0) * scale
            return Math.max(0.05, storedDistance)
        }
        var unitsPerMeter = Number(cameraController.metersToControllerUnits)
        if (!isFinite(unitsPerMeter) || unitsPerMeter <= 0)
            unitsPerMeter = 1000
        var distanceUnits = Number(cameraController.distance)
        if (!isFinite(distanceUnits) || distanceUnits <= 0)
            distanceUnits = defaultDistanceM * unitsPerMeter
        var meters = distanceUnits / unitsPerMeter
        var focusMeters = Math.max(0.05, meters) * scale
        return focusMeters
    }
}

Binding {
    target: sceneEnvCtl
    property: "autoFocusRangeHint"
    value: {
        if (!cameraController)
            return sceneEnvCtl.dofFocusRange
        var unitsPerMeter = Number(cameraController.metersToControllerUnits)
        if (!isFinite(unitsPerMeter) || unitsPerMeter <= 0)
            unitsPerMeter = 1000
        var scale = Number(root.effectiveSceneScaleFactor)
        if (!isFinite(scale) || scale <= 0)
            scale = 1.0
        var defaultDistanceM = Number(root.defaultDofFocusDistanceM)
        if (!isFinite(defaultDistanceM) || defaultDistanceM <= 0)
            defaultDistanceM = 2.5
        var distanceUnits = Number(cameraController.distance)
        if (!isFinite(distanceUnits) || distanceUnits <= 0)
            distanceUnits = defaultDistanceM * unitsPerMeter
        var meters = distanceUnits / unitsPerMeter
        var focusMeters = Math.max(0.05, meters) * scale
        var fovDeg = Number(cameraController.fov)
        if (!isFinite(fovDeg) || fovDeg <= 0)
            fovDeg = 50
        var fovRad = fovDeg * Math.PI / 180.0
        var halfSpan = Math.tan(fovRad / 2) * focusMeters
        var rangeMeters = Math.max(focusMeters * 0.25, Math.abs(halfSpan))
        return Math.max(0.01, rangeMeters)
    }
}

 // ---------------------------------------------
 // Python bridge helpers
 // ---------------------------------------------
function invokeBatchHandler(handler, payload, category) {
    if (typeof handler !== "function") {
        console.warn("[SimulationRoot] Missing handler for " + category + " updates")
        return false
    }
    try {
        return handler.call(root, payload)
    } catch (error) {
        console.error("[SimulationRoot] " + category + " handler threw:", error)
        return false
    }
}

function safeApplyConfigChange(category, payload) {
    if (typeof window === "undefined" || !window || typeof window.applyQmlConfigChange !== "function")
        return
    try {
        window.applyQmlConfigChange(category, payload || {})
    } catch (error) {
        console.warn("[SimulationRoot] applyQmlConfigChange failed:", error)
    }
}

 function applySceneBridgeState() {
 if (!sceneBridge)
  return

 if (sceneBridge.geometry && Object.keys(sceneBridge.geometry).length)
  invokeBatchHandler(root.applyGeometryUpdatesInternal, sceneBridge.geometry, "geometry")
 if (sceneBridge.camera && Object.keys(sceneBridge.camera).length)
  invokeBatchHandler(root.applyCameraUpdates, sceneBridge.camera, "camera")
 if (sceneBridge.lighting && Object.keys(sceneBridge.lighting).length)
  invokeBatchHandler(root.applyLightingUpdates, sceneBridge.lighting, "lighting")
 if (sceneBridge.environment && Object.keys(sceneBridge.environment).length)
  invokeBatchHandler(root.applyEnvironmentUpdates, sceneBridge.environment, "environment")
 if (sceneBridge.scene && Object.keys(sceneBridge.scene).length)
  invokeBatchHandler(root.applySceneUpdates, sceneBridge.scene, "scene")
 if (sceneBridge.quality && Object.keys(sceneBridge.quality).length)
  invokeBatchHandler(root.applyQualityUpdates, sceneBridge.quality, "quality")
 if (sceneBridge.materials && Object.keys(sceneBridge.materials).length)
  invokeBatchHandler(root.applyMaterialUpdates, sceneBridge.materials, "materials")
 if (sceneBridge.effects && Object.keys(sceneBridge.effects).length)
  invokeBatchHandler(root.applyEffectsUpdates, sceneBridge.effects, "effects")
 if (sceneBridge.animation && Object.keys(sceneBridge.animation).length)
  invokeBatchHandler(root.applyAnimationUpdates, sceneBridge.animation, "animation")
 if (sceneBridge.threeD && Object.keys(sceneBridge.threeD).length)
  invokeBatchHandler(root.apply3DUpdates, sceneBridge.threeD, "threeD")
 if (sceneBridge.render && Object.keys(sceneBridge.render).length)
  invokeBatchHandler(root.applyRenderSettings, sceneBridge.render, "render")
 if (sceneBridge.simulation && Object.keys(sceneBridge.simulation).length)
  invokeBatchHandler(root.applySimulationUpdates, sceneBridge.simulation, "simulation")

 if (sceneBridge.latestUpdates && Object.keys(sceneBridge.latestUpdates).length) {
 var summary = {}
 for (var key in sceneBridge.latestUpdates) {
 if (sceneBridge.latestUpdates.hasOwnProperty(key))
 summary[key] = true
 }
 batchUpdatesApplied(summary)
 }
}

Connections {
 id: sceneBridgeLifecycle
 target: root

 function onSceneBridgeChanged() {
  applySceneBridgeState()
 }
}

 Column {
  id: shaderWarningOverlay
  anchors.top: parent.top
  anchors.right: parent.right
  anchors.margins: 16
  spacing: 8
  visible: shaderWarningList.length > 0
  z: 910

  Repeater {
   model: shaderWarningList
   delegate: Rectangle {
    width: 360
    radius: 8
    color: Qt.rgba(0.3, 0.05, 0.05, 0.92)
    border.width: 1
    border.color: Qt.rgba(0.9, 0.35, 0.35, 1)
    implicitHeight: warningLayout.implicitHeight + 16

    Column {
     id: warningLayout
     anchors.fill: parent
     anchors.margins: 8
     spacing: 4

     Text {
      text: qsTr("Shader fallback: %1").arg(modelData.id)
      color: "#ffd7d7"
      font.bold: true
      wrapMode: Text.WordWrap
     }

     Text {
      text: modelData.message
      color: "#ffbcbc"
      wrapMode: Text.WordWrap
      font.pixelSize: 12
     }
    }
   }
  }
 }

Rectangle {
 anchors.fill: parent
 color: "#66b1ff"
 opacity: batchFlashOpacity
 visible: opacity > 0.0
 z: 900
 border.width: 0
 }

Connections {
 id: sceneBridgeConnections
 target: sceneBridge
 enabled: !!sceneBridge

    function safeInvoke(handler, payload, category) {
        if (typeof handler !== "function")
            return
        try {
            handler.call(root, payload)
        } catch (error) {
            console.error("[SimulationRoot] " + category + " handler threw:", error)
        }
    }

    function onGeometryChanged(payload) {
        if (!payload)
            return
        safeInvoke(root.applyGeometryUpdatesInternal, payload, "geometry")
    }
 function onCameraChanged(payload) {
     if (!payload)
         return
     var handler = root.applyCameraUpdates
     if (typeof handler === "function")
         handler.call(root, payload)
 }
 function onLightingChanged(payload) {
     if (!payload)
         return
     var handler = root.applyLightingUpdates
     if (typeof handler === "function")
         handler.call(root, payload)
 }
 function onEnvironmentChanged(payload) {
     if (!payload)
         return
     var handler = root.applyEnvironmentUpdates
     if (typeof handler === "function")
         handler.call(root, payload)
 }
 function onQualityChanged(payload) {
     if (!payload)
         return
     var handler = root.applyQualityUpdates
     if (typeof handler === "function")
         handler.call(root, payload)
 }
 function onMaterialsChanged(payload) {
     if (!payload)
         return
     var handler = root.applyMaterialUpdates
     if (typeof handler === "function")
         handler.call(root, payload)
 }
 function onEffectsChanged(payload) {
     if (!payload)
         return
     var handler = root.applyEffectsUpdates
     if (typeof handler === "function")
         handler.call(root, payload)
 }
 function onAnimationChanged(payload) {
     if (!payload)
         return
     var handler = root.applyAnimationUpdates
     if (typeof handler === "function")
         handler.call(root, payload)
 }
 function onThreeDChanged(payload) {
     if (!payload)
         return
     var handler = root.apply3DUpdates
     if (typeof handler === "function")
         handler.call(root, payload)
 }
 function onRenderChanged(payload) {
     if (!payload)
         return
     var handler = root.applyRenderSettings
     if (typeof handler === "function")
         handler.call(root, payload)
 }
 function onSimulationChanged(payload) {
     if (!payload)
         return
     var handler = root.applySimulationUpdates
     if (typeof handler === "function")
         handler.call(root, payload)
 }

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
  console.log("✅ SimulationRoot initialized successfully")
  if (typeof signalTrace !== "undefined" && signalTrace && typeof signalTrace.registerSubscription === "function") {
   signalTrace.registerSubscription("settings.settingChanged","main.qml","qml")
   signalTrace.registerSubscription("settings.settingsBatchUpdated","main.qml","qml")
  }
  if (diagnosticsDefaults && diagnosticsDefaults.camera_hud) {
   applyCameraHudSettings(diagnosticsDefaults.camera_hud)
  } else {
   setCameraHudEnabled(cameraHudEnabled)
  }
  if (diagnosticsDefaults && diagnosticsDefaults.signal_trace) {
   applySignalTraceSettings(diagnosticsDefaults.signal_trace)
  }
  if (geometryDefaults && Object.keys(geometryDefaults).length) {
        invokeBatchHandler(root.applyGeometryUpdatesInternal, geometryDefaults, "geometry-defaults")
  }
  applySceneBridgeState()
  Qt.callLater(initializeCameraControllerGeometry)
 }

 Connections {
  target: typeof signalTrace !== "undefined" ? signalTrace : null

  function onTraceUpdated(snapshot) {
   if (snapshot && snapshot.config) {
    applySignalTraceSettings(snapshot.config)
   }
   if (typeof signalTrace !== "undefined" && signalTrace) {
    var history = signalTrace.historyEntries
    signalTraceHistory = history ? history : []
   } else {
    signalTraceHistory = []
   }
  }
 }

 DiagnosticsOverlay {
  id: diagnosticsOverlay
  anchors.fill: parent
  z: 1000
  traceOverlayVisible: signalTraceOverlayVisible
  recordingEnabled: signalTraceRecordingEnabled
  panelExpanded: signalTracePanelExpanded
  historyLimit: signalTraceHistoryLimit
  historyEntries: signalTraceHistory
  clearEnabled: signalTraceHistory.length > 0 && typeof signalTrace !== "undefined" && signalTrace && signalTrace.clearHistory
  profileService: typeof settingsProfiles !== "undefined" ? settingsProfiles : null
  overlayLabel: qsTr("Сигналы")

  onOverlayToggled: function(enabled) {
   if (_signalTraceSyncing)
    return
   signalTraceOverlayVisible = enabled
   if (!enabled)
    signalTracePanelExpanded = false
  safeApplyConfigChange("diagnostics.signal_trace", { overlay_enabled: enabled })
  }

  onRecordingToggled: function(enabled) {
   if (_signalTraceSyncing)
    return
   signalTraceRecordingEnabled = enabled
  safeApplyConfigChange("diagnostics.signal_trace", { enabled: enabled })
  }

  onPanelVisibilityToggled: function(expanded) {
   signalTracePanelExpanded = expanded
  }

  onClearHistoryRequested: {
   if (typeof signalTrace !== "undefined" && signalTrace && signalTrace.clearHistory) {
    signalTrace.clearHistory()
   }
  }
 }

 Connections {
 target: typeof settingsEvents !== "undefined" ? settingsEvents : null
 function onSettingChanged(change) {
 if (typeof signalTrace !== "undefined" && signalTrace && typeof signalTrace.recordObservation === "function") {
 signalTrace.recordObservation("settings.settingChanged", change, "qml")
 }
 handleDiagnosticsSettingChange(change)
 }

 function onSettingsBatchUpdated(payload) {
 if (typeof signalTrace !== "undefined" && signalTrace && typeof signalTrace.recordObservation === "function") {
 signalTrace.recordObservation("settings.settingsBatchUpdated", payload, "qml")
 }
 if (payload && payload.changes && payload.changes.length) {
 for (var i =0; i < payload.changes.length; ++i) {
 handleDiagnosticsSettingChange(payload.changes[i])
 }
 }
   }
   }

   }

// ---------------------------------------------
// Утилиты
// ---------------------------------------------

function setIfExists(obj, prop, value) {
    try {
        if (obj && (prop in obj || typeof obj[prop] !== "undefined")) {
            obj[prop] = value;
            return true;
        }
    } catch (e) {
        console.warn("setIfExists failed", prop, e);
    }
    return false;
}

function isPlainObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}

function warnInvalidBatch(category, reason, payload) {
    var message = "Ignoring " + category + " batch: " + reason;
    try {
        console.warn("[SimulationRoot]", message, payload !== undefined ? payload : "");
    } catch (e) {
        console.warn("[SimulationRoot]", message);
    }

    if (typeof window !== "undefined" && window) {
        try {
            if (typeof window.recordQmlBatchWarning === "function") {
                window.recordQmlBatchWarning(category, reason, payload);
            }
        } catch (err) {
        }
    }
}

function coerceBatchObject(category, payload) {
    if (payload === null || payload === undefined)
        return null;
    if (isPlainObject(payload))
        return payload;
    warnInvalidBatch(category, "payload must be an object", payload);
    return null;
}

function valueForKeys(map, keys) {
    if (!isPlainObject(map))
        return undefined;
    for (var i = 0; i < keys.length; ++i) {
        var key = keys[i];
        if (map.hasOwnProperty(key) && map[key] !== undefined)
            return map[key];
    }
    return undefined;
}

function clamp(value, minValue, maxValue) {
if (typeof value !== 'number' || !isFinite(value))
return minValue;
return Math.max(minValue, Math.min(maxValue, value));
}

function normalizeRenderPolicyKey(value) {
    var normalized = "";
    if (value !== undefined && value !== null)
        normalized = String(value).trim().toLowerCase();

    if (!normalized)
        return "always";

    if (normalized === "on demand" || normalized === "on-demand" || normalized === "on_demand")
        normalized = "ondemand";
    if (normalized === "auto")
        normalized = "automatic";

    var allowed = { always: true, ondemand: true };
    if (typeof RenderSettings !== "undefined" && RenderSettings.Automatic !== undefined)
        allowed.automatic = true;
    if (typeof RenderSettings !== "undefined" && RenderSettings.Manual !== undefined)
        allowed.manual = true;

    if (allowed[normalized])
        return normalized;

    return "always";
}

 function toSceneLength(meters) {
 var numeric = Number(meters);
 if (!isFinite(numeric))
 return 0.0;
 return numeric * effectiveSceneScaleFactor;
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
 return numeric;
 }

 function parseReflectionProbeEnum(value, mapping, fallback) {
  if (value === undefined || value === null)
   return fallback;
  if (typeof value === "number" && isFinite(value)) {
   var numeric = Number(value);
   for (var key in mapping) {
    if (mapping.hasOwnProperty(key) && mapping[key] === numeric)
     return numeric;
   }
   return numeric;
  }
  var token = String(value).toLowerCase();
  token = token.replace(/\s+/g, "");
  token = token.replace(/[-_]/g, "");
  if (mapping[token] !== undefined)
   return mapping[token];
  return fallback;
 }

 function reflectionProbeQualityFrom(value) {
  return parseReflectionProbeEnum(value, {
   veryhigh: ReflectionProbe.VeryHigh,
   ultra: ReflectionProbe.VeryHigh,
   high: ReflectionProbe.High,
   medium: ReflectionProbe.Medium,
   low: ReflectionProbe.Low
  }, ReflectionProbe.VeryHigh);
 }

 function reflectionProbeRefreshModeFrom(value) {
  return parseReflectionProbeEnum(value, {
   never: ReflectionProbe.Never,
   disabled: ReflectionProbe.Never,
   off: ReflectionProbe.Never,
   firstframe: ReflectionProbe.FirstFrame,
   first: ReflectionProbe.FirstFrame,
   startup: ReflectionProbe.FirstFrame,
   everyframe: ReflectionProbe.EveryFrame,
   always: ReflectionProbe.EveryFrame,
   realtime: ReflectionProbe.EveryFrame
  }, ReflectionProbe.EveryFrame);
 }

 function reflectionProbeTimeSlicingFrom(value) {
  return parseReflectionProbeEnum(value, {
   notimeslicing: ReflectionProbe.NoTimeSlicing,
   none: ReflectionProbe.NoTimeSlicing,
   allfacesatonce: ReflectionProbe.AllFacesAtOnce,
   allfaces: ReflectionProbe.AllFacesAtOnce,
   together: ReflectionProbe.AllFacesAtOnce,
   individualfaces: ReflectionProbe.IndividualFaces,
   perface: ReflectionProbe.IndividualFaces
  }, ReflectionProbe.IndividualFaces);
 }

function sanitizeReflectionProbePadding(value) {
 if (value === undefined || value === null)
  return reflectionProbePaddingM;
 var numeric = Number(value);
 if (!isFinite(numeric))
  return reflectionProbePaddingM;
 return Math.max(0, numeric);
}

 function emitConfigChange(category, payload) {
 if (!feedbackReady)
 return;
 if (typeof window === "undefined" || !window)
 return;
 try {
 if (typeof window.isQmlFeedbackSuppressed === "function" && window.isQmlFeedbackSuppressed())
 return;
 } catch (err) {
 }
 safeApplyConfigChange(category, payload);
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

 function cloneObject(source) {
 if (!source)
 return {};
 var copy = {};
 for (var key in source) {
 if (source.hasOwnProperty(key))
 copy[key] = source[key];
 }
 return copy;
 }

 function updateGeometryState(patch) {
 if (!patch)
 return;
 var next = cloneObject(geometryState);
 var changed = false;
 for (var key in patch) {
 if (!patch.hasOwnProperty(key))
 continue;
 if (next[key] !== patch[key]) {
 next[key] = patch[key];
 changed = true;
 }
 }
 if (changed)
 geometryState = next;
 }

 function geometryValue(key, fallback) {
 if (suspensionAssembly)
 return suspensionAssembly.geometryValue(key, fallback);
 var state = geometryState || {};
 if (state[key] !== undefined)
 return state[key];
 return fallback;
 }

 function cornerArmPosition(side) {
 if (suspensionAssembly)
 return suspensionAssembly.cornerArmPosition(side);
 var track = geometryValue("trackWidth", userTrackWidth);
 var beam = geometryValue("beamSize", userBeamSize);
 var isLeft = String(side).toLowerCase().charAt(1) === "l";
 var pivot = geometryValue("frameToPivot", userFrameToPivot);
 var frameLengthVal = geometryValue("frameLength", userFrameLength);
 var z = (String(side).toLowerCase().charAt(0) === "r") ? frameLengthVal - pivot : pivot;
 var x = (isLeft ? -1 :1) * track /2;
 return Qt.vector3d(x, beam, z);
 }

 function cornerTailPosition(side) {
 if (suspensionAssembly)
 return suspensionAssembly.cornerTailPosition(side);
 var base = cornerArmPosition(side);
 var beam = geometryValue("beamSize", userBeamSize);
 var frameHeightVal = geometryValue("frameHeight", userFrameHeight);
 return Qt.vector3d(base.x, beam + frameHeightVal, base.z);
 }

 function pistonPosition(side) {
 if (suspensionAssembly)
 return suspensionAssembly.pistonPositionFor(side);
 var store = pistonPositions || {};
 var key = String(side).toLowerCase();
 var value = store[key];
 var numeric = Number(value);
 if (!isFinite(numeric))
 return 0.0;
 return numeric;
 }

 function leverAngleFor(side) {
 if (suspensionAssembly)
 return suspensionAssembly.leverAngleFor(side);
 var key = String(side).toLowerCase();
 if (key === "fl")
 return fl_angle;
 if (key === "fr")
 return fr_angle;
 if (key === "rl")
 return rl_angle;
 if (key === "rr")
 return rr_angle;
 return 0.0;
 }

 function normalizeLightingValue(key, value) {
 var numericKeys = {
 brightness: true,
 angle_x: true,
 angle_y: true,
 angle_z: true,
 position_x: true,
 position_y: true,
 position_z: true,
 range: true,
 constant_fade: true,
 linear_fade: true,
 quadratic_fade: true,
    shadow_factor: true,
    shadow_resolution: true,
 shadow_bias: true,
 shadow_filter_samples: true
 };
 if (numericKeys[key]) {
 var num = Number(value);
 return isFinite(num) ? num : value;
 }
 var booleanKeys = {
 cast_shadow: true,
 bind_to_camera: true,
 shadows_enabled: true,
 pointLightCastsShadow: true,
 pointLightBindToCamera: true
 };
 if (booleanKeys[key])
 return !!value;
 return value;
 }

 function mergeLightingGroup(current, updates) {
 if (!updates)
 return current;
 var merged = cloneObject(current);
 var changed = false;
 for (var key in updates) {
 if (!updates.hasOwnProperty(key))
 continue;
 var normalized = normalizeLightingValue(key, updates[key]);
 if (merged[key] !== normalized) {
 merged[key] = normalized;
 changed = true;
 }
 }
 return changed ? merged : current;
 }

 function lightingValue(group, key, fallback) {
 return lightingAccess.value(group, key, fallback);
 }

 function lightingGlobal(key, fallback) {
 return lightingAccess.globalValue(key, fallback);
 }

// ---------------------------------------------
    // Применение батч-обновлений из Python
    // ---------------------------------------------
    Connections {
        target: root
        function safeInvoke(handler, payload, category) {
            if (typeof handler !== "function")
                return
            try {
                handler.call(root, payload)
            } catch (error) {
                console.error("[SimulationRoot] " + category + " handler threw:", error)
            }
        }
        function onPendingPythonUpdatesChanged() {
            if (!root.pendingPythonUpdates)
                return;
            var payload = root.pendingPythonUpdates;
            root.pendingPythonUpdates = null;
            safeInvoke(root.applyBatchedUpdates, payload, "batched");
        }
    }

function applyBatchedUpdates(updates) {
    if (!isPlainObject(updates)) {
        warnInvalidBatch("root", "batch payload must be an object", updates);
        var rejectedSummary = {
            timestamp: Date.now(),
            applied: {},
            failed: { root: "invalid-payload" },
            unknownKeys: [],
            meta: null,
            appliedCount: 0,
            failedCount: 1,
            success: false
        };
        batchUpdatesApplied(rejectedSummary);
        return rejectedSummary;
    }

    var summary = {
        timestamp: Date.now(),
        applied: {},
        failed: {},
        unknownKeys: [],
        meta: null
    };

    function recordUnknown(key) {
        if (summary.unknownKeys.indexOf(key) === -1)
            summary.unknownKeys.push(key);
    }

    function invokeHandler(key, payload, handler) {
        try {
            var result = handler(payload);
            if (result === false) {
                summary.failed[key] = "no-op";
            } else {
                summary.applied[key] = true;
            }
        } catch (error) {
            summary.failed[key] = error && error.message ? error.message : String(error);
            console.error("[SimulationRoot] Failed to apply", key, "batch:", error);
        }
    }

    var handlers = {
        geometry: function(payload) { return root.applyGeometryUpdates(payload); },
        camera: function(payload) { return root.applyCameraUpdates(payload); },
        lighting: function(payload) { return root.applyLightingUpdates(payload); },
        environment: function(payload) { return root.applyEnvironmentUpdates(payload); },
        scene: function(payload) { return root.applySceneUpdates(payload); },
        quality: function(payload) { return root.applyQualityUpdates(payload); },
        materials: function(payload) { return root.applyMaterialUpdates(payload); },
        effects: function(payload) { return root.applyEffectsUpdates(payload); },
        animation: function(payload) { return root.applyAnimationUpdates(payload); },
        threeD: function(payload) { return root.apply3DUpdates(payload); },
        render: function(payload) { return root.applyRenderSettings(payload); },
        simulation: function(payload) { return root.applySimulationUpdates(payload); }
    };

    for (var key in updates) {
        if (!updates.hasOwnProperty(key))
            continue;
        if (key === "_meta" || key === "meta") {
            if (summary.meta === null && isPlainObject(updates[key]))
                summary.meta = updates[key];
            if (summary.batchId === undefined && isPlainObject(updates[key])
                    && updates[key].batchId !== undefined)
                summary.batchId = updates[key].batchId;
            continue;
        }
        var handler = handlers[key];
        if (!handler) {
            recordUnknown(key);
            continue;
        }
        invokeHandler(key, updates[key], handler);
    }

    if (summary.unknownKeys.length) {
        console.debug(
            "[SimulationRoot] Unhandled batch categories:",
            summary.unknownKeys.join(", ")
        );
    }

    if (summary.meta !== null && summary.batchId === undefined
            && summary.meta && summary.meta.batchId !== undefined)
        summary.batchId = summary.meta.batchId;

    summary.appliedCount = Object.keys(summary.applied).length;
    summary.failedCount = Object.keys(summary.failed).length;
    summary.success = summary.failedCount === 0 && summary.unknownKeys.length === 0;

    batchUpdatesApplied(summary);
    return summary;
}

 // ---------------------------------------------
 // Реализации apply*Updates (минимально: geometry, camera, lighting, environment, quality, materials, effects, animation,3d)
 // ---------------------------------------------
function applyGeometryUpdatesInternal(params) {
 if (!params) return false;
 var changed = false;
 function pick(obj, keys, def) {
 for (var i =0; i < keys.length; i++) if (obj[keys[i]] !== undefined) return obj[keys[i]];
 return def;
 }
 var v;
 v = pick(params, ['frameLength','frame_length','frame_length_m','wheelbase','userFrameLength'], undefined);
 var geometryPatch = {};
 if (v !== undefined) { var frameLen = normalizeLengthMeters(v); if (frameLen !== undefined) { userFrameLength = frameLen; geometryPatch.frameLength = frameLen; } }
 v = pick(params, ['frameHeight','frame_height','frame_height_m','userFrameHeight'], undefined);
 if (v !== undefined) { var frameHeight = normalizeLengthMeters(v); if (frameHeight !== undefined) { userFrameHeight = frameHeight; geometryPatch.frameHeight = frameHeight; } }
 v = pick(params, ['frameBeamSize','beamSize','frame_beam_size','frame_beam_size_m','userBeamSize'], undefined);
 if (v !== undefined) { var beamSize = normalizeLengthMeters(v); if (beamSize !== undefined) { userBeamSize = beamSize; geometryPatch.beamSize = beamSize; } }
 v = pick(params, ['leverLength','lever_length','lever_length_m','userLeverLength'], undefined);
 if (v !== undefined) { var leverLen = normalizeLengthMeters(v); if (leverLen !== undefined) { userLeverLength = leverLen; geometryPatch.leverLength = leverLen; } }
 v = pick(params, ['cylinderBodyLength','cylinderLength','cylinder_length','cylinder_body_length','cylinder_body_length_m','userCylinderLength'], undefined);
 if (v !== undefined) { var cylLen = normalizeLengthMeters(v); if (cylLen !== undefined) { userCylinderLength = cylLen; geometryPatch.cylinderLength = cylLen; } }
 v = pick(params, ['trackWidth','track','track_width','track_width_m','userTrackWidth'], undefined);
 if (v !== undefined) { var track = normalizeLengthMeters(v); if (track !== undefined) { userTrackWidth = track; geometryPatch.trackWidth = track; } }
 v = pick(params, ['frameToPivot','frame_to_pivot','frame_to_pivot_m','userFrameToPivot'], undefined);
 if (v !== undefined) { var pivot = normalizeLengthMeters(v); if (pivot !== undefined) { userFrameToPivot = pivot; geometryPatch.frameToPivot = pivot; } }
 v = pick(params, ['rodPosition','rod_position','attachFrac','userRodPosition'], undefined);
 if (v !== undefined) { var rodPos = Number(v); if (isFinite(rodPos)) { userRodPosition = rodPos; geometryPatch.rodPosition = rodPos; } }
 v = pick(params, ['boreHead','bore','bore_d','bore_head','cyl_diam','cyl_diam_m','userBoreHead'], undefined);
 if (v !== undefined) { var bore = normalizeLengthMeters(v); if (bore !== undefined) { userBoreHead = bore; geometryPatch.boreHead = bore; } }
 v = pick(params, ['rod_d','rodDiameter','rod_diameter','rod_diameter_m','rod_diameter_rear_m','userRodDiameter'], undefined);
 if (v !== undefined) { var rodDia = normalizeLengthMeters(v); if (rodDia !== undefined) { userRodDiameter = rodDia; geometryPatch.rodDiameter = rodDia; } }
 v = pick(params, ['pistonThickness','piston_thickness','piston_thickness_m','userPistonThickness'], undefined);
 if (v !== undefined) { var pistonThick = normalizeLengthMeters(v); if (pistonThick !== undefined) { userPistonThickness = pistonThick; geometryPatch.pistonThickness = pistonThick; } }
 v = pick(params, ['pistonRodLength','piston_rod_length','piston_rod_length_m','userPistonRodLength'], undefined);
 if (v !== undefined) { var rodLen = normalizeLengthMeters(v); if (rodLen !== undefined) { userPistonRodLength = rodLen; geometryPatch.pistonRodLength = rodLen; } }
 v = pick(params, ['tailRodLength','tail_rod_length','tail_rod_length_m','userTailRodLength'], undefined);
 if (v !== undefined) { var tailLen = normalizeLengthMeters(v); if (tailLen !== undefined) { userTailRodLength = tailLen; geometryPatch.tailRodLength = tailLen; } }
 if (params.cylinderSegments !== undefined) {
 var seg = Number(params.cylinderSegments);
 if (isFinite(seg)) {
  userCylinderSegments = Math.max(3, Math.round(seg));
  geometryPatch.cylinderSegments = userCylinderSegments;
 }
}
 if (params.cylinderRings !== undefined) {
 var rings = Number(params.cylinderRings);
 if (isFinite(rings)) {
  userCylinderRings = Math.max(1, Math.round(rings));
  geometryPatch.cylinderRings = userCylinderRings;
 }
}
 if (Object.keys(geometryPatch).length) {
  updateGeometryState(geometryPatch);
  changed = true;
 }

 if (cameraController) {
 var cameraGeometryUpdate = {};
 if (geometryPatch.frameLength !== undefined)
     cameraGeometryUpdate.frameLength = geometryPatch.frameLength;
 if (geometryPatch.frameHeight !== undefined)
     cameraGeometryUpdate.frameHeight = geometryPatch.frameHeight;
 if (geometryPatch.trackWidth !== undefined)
     cameraGeometryUpdate.trackWidth = geometryPatch.trackWidth;
 if (geometryPatch.beamSize !== undefined)
     cameraGeometryUpdate.beamSize = geometryPatch.beamSize;
 if (geometryPatch.frameToPivot !== undefined)
     cameraGeometryUpdate.frameToPivot = geometryPatch.frameToPivot;

 if (Object.keys(cameraGeometryUpdate).length) {
     try {
      cameraController.updateGeometry(cameraGeometryUpdate);
      changed = true;
     } catch (err) {
      console.warn("cameraController.updateGeometry failed", err);
     }
 }
    }
 return changed;
}

 function applyGeometryUpdates(params) {
  params = coerceBatchObject("geometry", params);
  if (!params)
   return false;
  return applyGeometryUpdatesInternal(params);
 }
 function applyCameraUpdates(params) {
  params = coerceBatchObject("camera", params);
  if (!params)
   return false;

  if (cameraController && cameraController.applyCameraUpdates) {
   try {
    var controllerResult = cameraController.applyCameraUpdates(params);
    if (controllerResult !== undefined)
     return controllerResult !== false;
    return true;
   } catch (err) {
    console.warn("CameraController.applyCameraUpdates failed:", err);
   }
  }

  var changed = false;

  if (params.fov !== undefined) {
   if (setIfExists(camera, 'fieldOfView', Number(params.fov)))
    changed = true;
  }

  var clipNearMeters = params.clipNear !== undefined ? Number(params.clipNear) : undefined;
  if (clipNearMeters !== undefined && isFinite(clipNearMeters)) {
   var clipNearScene = Math.max(0.0001, toSceneLength(clipNearMeters));
   var clipNearAssigned = setIfExists(camera, 'clipNear', clipNearScene);
   try {
    camera.clipNear = clipNearScene;
    clipNearAssigned = true;
   } catch (e) {
    console.warn("Camera near clip update failed:", e);
   }
   if (clipNearAssigned)
    changed = true;
  }

  var clipFarMeters = params.clipFar !== undefined ? Number(params.clipFar) : undefined;
  if (clipFarMeters !== undefined && isFinite(clipFarMeters)) {
   var clipFarScene = toSceneLength(clipFarMeters);
   var clipFarAssigned = setIfExists(camera, 'clipFar', clipFarScene);
   try {
    camera.clipFar = clipFarScene;
    clipFarAssigned = true;
   } catch (e) {
    console.warn("Camera far clip update failed:", e);
   }
   if (clipFarAssigned)
    changed = true;
  }

  var positionVector = params.position ? toSceneVector3(params.position) : null;
  if (positionVector) {
   var positionAssigned = setIfExists(camera, 'position', positionVector);
   try {
    camera.position = positionVector;
    positionAssigned = true;
   } catch (e) {
    console.warn("Camera position update failed:", e);
   }
   if (positionAssigned)
    changed = true;
  }

  if (params.eulerRotation) {
   var r = params.eulerRotation;
   try {
    camera.eulerRotation = Qt.vector3d(Number(r.x||r[0]), Number(r.y||r[1]), Number(r.z||r[2]));
    changed = true;
   } catch(e) {
    console.warn("Camera rotation normalization failed:", e);
   }
  }

  return changed;
 }

function applyLightingUpdates(params) {
 params = coerceBatchObject("lighting", params);
 if (!params)
  return false;

  try {

 function normalizeGroupPayload(payload) {
 if (!isPlainObject(payload))
  return {};
 var normalized = {};
 var mutated = false;
 for (var key in payload) {
 if (!payload.hasOwnProperty(key))
 continue;
 var value = payload[key];
 if (key === "eulerRotation" && value) {
 normalized.angle_x = Number(value.x !== undefined ? value.x : value[0]);
 normalized.angle_y = Number(value.y !== undefined ? value.y : value[1]);
 normalized.angle_z = Number(value.z !== undefined ? value.z : value[2]);
 mutated = true;
 continue;
 }
 if (key === "position" && value) {
 normalized.position_x = Number(value.x !== undefined ? value.x : value[0]);
 normalized.position_y = Number(value.y !== undefined ? value.y : value[1]);
 normalized.position_z = Number(value.z !== undefined ? value.z : value[2]);
 mutated = true;
 continue;
 }
 if (key === "color" || key === "brightness") {
 normalized[key] = value;
 mutated = mutated || false;
 continue;
 }
 if (key === "castsShadow") {
 normalized.cast_shadow = !!value;
 mutated = true;
 continue;
 }
 if (key === "bindToCamera") {
 normalized.bind_to_camera = !!value;
 mutated = true;
 continue;
 }
 if (key === "positionX" || key === "posX") {
 normalized.position_x = Number(value);
 mutated = true;
 continue;
 }
 if (key === "positionY" || key === "posY") {
 normalized.position_y = Number(value);
 mutated = true;
 continue;
 }
 if (key === "positionZ" || key === "posZ") {
 normalized.position_z = Number(value);
 mutated = true;
 continue;
 }
 normalized[key] = value;
 }
 return mutated ? normalized : payload;
 }

 function mergeGroup(target, updates) {
 if (!isPlainObject(updates))
  return target;
 return mergeLightingGroup(target, normalizeGroupPayload(updates));
 }

 var next = {
 key: cloneObject(lightingState.key),
 fill: cloneObject(lightingState.fill),
 rim: cloneObject(lightingState.rim),
 point: cloneObject(lightingState.point),
 spot: cloneObject(lightingState.spot),
 global: cloneObject(lightingState.global)
 };

 function applyToGroup(groupName, payload) {
 next[groupName] = mergeGroup(next[groupName], payload);
 }

 var consumed = { key: true, fill: true, rim: true, point: true, spot: true, global: true };
 var aliasGroups = {
 key_light: "key",
 fill_light: "fill",
 rim_light: "rim",
 point_light: "point",
 spot_light: "spot"
 };

 function handleGroup(key, group) {
 if (isPlainObject(params[key]))
  applyToGroup(group, params[key]);
 consumed[key] = true;
 }

 handleGroup("key", "key");
 handleGroup("fill", "fill");
 handleGroup("rim", "rim");
 handleGroup("point", "point");
 handleGroup("spot", "spot");
 handleGroup("global", "global");

 for (var alias in aliasGroups) {
 if (!aliasGroups.hasOwnProperty(alias))
 continue;
 if (isPlainObject(params[alias]))
  applyToGroup(aliasGroups[alias], params[alias]);
 consumed[alias] = true;
 }

 var legacyKeyPatch = {};
 if (params.color !== undefined) {
 legacyKeyPatch.color = params.color;
 consumed.color = true;
 }
 if (params.brightness !== undefined) {
 legacyKeyPatch.brightness = params.brightness;
 consumed.brightness = true;
 }
 if (params.eulerRotation) {
 var euler = params.eulerRotation;
 legacyKeyPatch.angle_x = Number(euler.x !== undefined ? euler.x : euler[0]);
 legacyKeyPatch.angle_y = Number(euler.y !== undefined ? euler.y : euler[1]);
 legacyKeyPatch.angle_z = Number(euler.z !== undefined ? euler.z : euler[2]);
 consumed.eulerRotation = true;
 }
 if (params.position) {
 var position = params.position;
 legacyKeyPatch.position_x = Number(position.x !== undefined ? position.x : position[0]);
 legacyKeyPatch.position_y = Number(position.y !== undefined ? position.y : position[1]);
 legacyKeyPatch.position_z = Number(position.z !== undefined ? position.z : position[2]);
 consumed.position = true;
 }
 if (Object.keys(legacyKeyPatch).length)
 applyToGroup("key", legacyKeyPatch);

 var camelPropertyMap = {
 Brightness: "brightness",
 Color: "color",
 AngleX: "angle_x",
 AngleY: "angle_y",
 AngleZ: "angle_z",
 CastsShadow: "cast_shadow",
 BindToCamera: "bind_to_camera",
 PosX: "position_x",
 PosY: "position_y",
 PosZ: "position_z",
 Range: "range",
 ConstantFade: "constant_fade",
 LinearFade: "linear_fade",
 QuadraticFade: "quadratic_fade"
 };

 for (var rawKey in params) {
 if (!params.hasOwnProperty(rawKey) || consumed[rawKey])
 continue;

 var camelMatch = /^([a-z]+)Light([A-Z].*)$/.exec(rawKey);
 if (camelMatch) {
 var groupName = camelMatch[1].toLowerCase();
 var propertySuffix = camelMatch[2];
 var normalizedKey = camelPropertyMap[propertySuffix];
 if (normalizedKey && next[groupName] !== undefined) {
 var patch = {};
 patch[normalizedKey] = params[rawKey];
 applyToGroup(groupName, patch);
 consumed[rawKey] = true;
 continue;
 }
 }

 var normalizedGlobalKey = {
 shadowsEnabled: "shadows_enabled",
 shadowResolution: "shadow_resolution",
 shadowFilterSamples: "shadow_filter_samples",
 shadowBias: "shadow_bias",
 shadowFactor: "shadow_factor"
 }[rawKey];
 if (normalizedGlobalKey) {
 var globalPatchSingle = {};
 globalPatchSingle[normalizedGlobalKey] = params[rawKey];
 applyToGroup("global", globalPatchSingle);
 consumed[rawKey] = true;
 continue;
 }
 }

 var globalPatch = {};
 for (var remainingKey in params) {
 if (!params.hasOwnProperty(remainingKey) || consumed[remainingKey])
 continue;
 var value = params[remainingKey];
 if (isPlainObject(value)) {
 var targetState = lightingState[remainingKey];
 next[remainingKey] = mergeLightingGroup(cloneObject(targetState), normalizeGroupPayload(value));
 } else {
 globalPatch[remainingKey] = value;
 }
 }

 if (Object.keys(globalPatch).length)
 next.global = mergeLightingGroup(next.global, globalPatch);

 lightingState = next;
  return true;
 } catch (error) {
  console.error("[SimulationRoot] applyLightingUpdates failed", error);
 return false;
}
}

function applySceneUpdates(params) {
 params = coerceBatchObject("scene", params);
 if (!params)
  return false;

 var sourceDefaults = sceneDefaults;
 if (!sourceDefaults || typeof sourceDefaults !== "object")
  sourceDefaults = {};
 var nextDefaults = cloneObject(sourceDefaults);
 var changed = false;

 function assignDefault(key, value) {
  if (nextDefaults[key] === value)
   return;
  nextDefaults[key] = value;
  changed = true;
 }

 var scaleValue = valueForKeys(params, ["scale_factor", "scaleFactor"]);
 if (scaleValue !== undefined) {
  var numericScale = Number(scaleValue);
  if (isFinite(numericScale) && numericScale > 0)
   assignDefault("scale_factor", numericScale);
 }

 var exposureValue = valueForKeys(params, ["exposure"]);
 if (exposureValue !== undefined) {
  var numericExposure = Number(exposureValue);
  if (isFinite(numericExposure)) {
   assignDefault("exposure", numericExposure);
   setIfExists(sceneEnvCtl, "tonemapExposure", numericExposure);
  }
 }

 var clearColorValue = valueForKeys(
  params,
  ["default_clear_color", "defaultClearColor"]
 );
 if (clearColorValue !== undefined && clearColorValue !== null) {
  var resolvedClear = String(clearColorValue);
  assignDefault("default_clear_color", resolvedClear);
  setIfExists(sceneEnvCtl, "backgroundColor", resolvedClear);
 }

 var baseColorValue = valueForKeys(
  params,
  ["model_base_color", "modelBaseColor"]
 );
 if (baseColorValue !== undefined && baseColorValue !== null)
  assignDefault("model_base_color", String(baseColorValue));

 var roughnessValue = valueForKeys(
  params,
  ["model_roughness", "modelRoughness"]
 );
 if (roughnessValue !== undefined) {
  var numericRoughness = Number(roughnessValue);
  if (isFinite(numericRoughness))
   assignDefault("model_roughness", numericRoughness);
 }

 var metalnessValue = valueForKeys(
  params,
  ["model_metalness", "modelMetalness"]
 );
 if (metalnessValue !== undefined) {
  var numericMetalness = Number(metalnessValue);
  if (isFinite(numericMetalness))
   assignDefault("model_metalness", numericMetalness);
 }

 if (changed) {
  sceneDefaults = nextDefaults;
  return true;
 }

 return false;
}

function updateScene(params) {
 return applySceneUpdates(params);
}

 function applyEnvironmentUpdates(params) {
  params = coerceBatchObject("environment", params);
  if (!params)
   return false;

  try {
    var backgroundSection = isPlainObject(params.background) ? params.background : null;
    var iblSection = isPlainObject(params.ibl) ? params.ibl : null;
    var tonemapSection = isPlainObject(params.tonemap) ? params.tonemap : null;
    var fogSection = isPlainObject(params.fog) ? params.fog : null;
    var ssaoSection = isPlainObject(params.ssao) ? params.ssao : null;
    var ambientSection = isPlainObject(params.ambient_occlusion) ? params.ambient_occlusion : null;
    if (!ssaoSection && ambientSection)
        ssaoSection = ambientSection;
    var dofSection = isPlainObject(params.depthOfField) ? params.depthOfField : null;
    var vignetteSection = isPlainObject(params.vignette) ? params.vignette : null;
    var aaSection = isPlainObject(params.antialiasing) ? params.antialiasing : null;

    var controllerApplied = false;
    if (sceneEnvCtl && typeof sceneEnvCtl.applyEnvironmentPayload === "function") {
        try {
            sceneEnvCtl.applyEnvironmentPayload(params);
            controllerApplied = true;
        } catch (controllerError) {
            console.warn("[SimulationRoot] sceneEnvCtl.applyEnvironmentPayload failed", controllerError);
        }
    }

    if (!controllerApplied) {
        var bgColorVal = valueForKeys(params, ['backgroundColor', 'background_color']);
        if (bgColorVal === undefined && backgroundSection)
            bgColorVal = backgroundSection.color;
        if (bgColorVal === undefined)
            bgColorVal = valueForKeys(params, ['clearColor', 'clear_color']);
        if (bgColorVal !== undefined)
            setIfExists(sceneEnvCtl, 'backgroundColor', bgColorVal);

        var backgroundModeVal = valueForKeys(params, ['backgroundMode', 'background_mode']);
        if (backgroundModeVal === undefined && backgroundSection)
            backgroundModeVal = backgroundSection.mode;
        if (backgroundModeVal !== undefined)
            setIfExists(sceneEnvCtl, 'backgroundModeKey', String(backgroundModeVal));

        var skyboxFlagRaw = valueForKeys(
            params,
            ['iblBackgroundEnabled', 'ibl_background_enabled', 'skyboxEnabled', 'skybox_enabled']
        );
        if (skyboxFlagRaw === undefined && backgroundSection)
            skyboxFlagRaw = valueForKeys(backgroundSection, ['skybox_enabled', 'skybox']);
        if (skyboxFlagRaw !== undefined)
            setIfExists(sceneEnvCtl, 'skyboxToggleFlag', !!skyboxFlagRaw);

        var currentSkyboxState = false;
        if (sceneEnvCtl && sceneEnvCtl.skyboxToggleFlag !== undefined)
            currentSkyboxState = !!sceneEnvCtl.skyboxToggleFlag;
        var resolvedSkybox = skyboxFlagRaw !== undefined ? !!skyboxFlagRaw : currentSkyboxState;

        var iblEnabledRaw = valueForKeys(params, ['iblEnabled', 'ibl_enabled']);
        if (iblEnabledRaw === undefined && iblSection)
            iblEnabledRaw = valueForKeys(iblSection, ['enabled']);
        var iblLightingRaw = valueForKeys(params, ['iblLightingEnabled', 'ibl_lighting_enabled']);
        if (iblLightingRaw === undefined && iblSection)
            iblLightingRaw = valueForKeys(iblSection, ['lighting_enabled', 'lightingEnabled']);

        var resolvedLighting = false;
        if (sceneEnvCtl && sceneEnvCtl.iblLightingEnabled !== undefined)
            resolvedLighting = !!sceneEnvCtl.iblLightingEnabled;

        if (iblEnabledRaw !== undefined) {
            resolvedLighting = !!iblEnabledRaw;
            setIfExists(sceneEnvCtl, 'iblLightingEnabled', resolvedLighting);
        }

        if (iblLightingRaw !== undefined) {
            resolvedLighting = !!iblLightingRaw;
            setIfExists(sceneEnvCtl, 'iblLightingEnabled', resolvedLighting);
        }

        var masterEnabled = resolvedLighting || resolvedSkybox;
        setIfExists(sceneEnvCtl, 'iblMasterEnabled', masterEnabled);
        setIfExists(sceneEnvCtl, 'iblBackgroundEnabled', masterEnabled && resolvedSkybox);

        var directSkyboxBrightnessProvided = valueForKeys(
            params,
            ['skyboxBrightness', 'skybox_brightness']
        ) !== undefined;
        var directProbeBrightnessProvided = valueForKeys(
            params,
            ['probeBrightness', 'probe_brightness']
        ) !== undefined;
        var nestedSkyboxBrightnessProvided = false;
        var nestedProbeBrightnessProvided = false;
        if (iblSection) {
            nestedSkyboxBrightnessProvided = valueForKeys(
                iblSection,
                ['skyboxBrightness', 'skybox_brightness']
            ) !== undefined;
            nestedProbeBrightnessProvided = valueForKeys(
                iblSection,
                ['probeBrightness', 'probe_brightness']
            ) !== undefined;
        }
        var shouldMirrorIntensity = !(
            directSkyboxBrightnessProvided ||
            directProbeBrightnessProvided ||
            nestedSkyboxBrightnessProvided ||
            nestedProbeBrightnessProvided
        );

        var intensityVal = valueForKeys(params, ['iblIntensity', 'ibl_intensity']);
        if (intensityVal === undefined && iblSection)
            intensityVal = valueForKeys(iblSection, ['intensity']);
        if (intensityVal !== undefined) {
            var numericIntensity = Number(intensityVal);
            if (isFinite(numericIntensity)) {
                setIfExists(sceneEnvCtl, 'iblIntensity', numericIntensity);
                if (shouldMirrorIntensity) {
                    setIfExists(sceneEnvCtl, 'skyboxBrightnessValue', numericIntensity);
                }
            }
        }

        var skyboxBrightnessVal = valueForKeys(
            params,
            ['skyboxBrightness', 'skybox_brightness', 'probeBrightness', 'probe_brightness']
        );
        if (skyboxBrightnessVal === undefined && iblSection)
            skyboxBrightnessVal = valueForKeys(
                iblSection,
                ['skyboxBrightness', 'skybox_brightness', 'probeBrightness', 'probe_brightness']
            );
        if (skyboxBrightnessVal !== undefined) {
            var numericSkyboxBrightness = Number(skyboxBrightnessVal);
            if (isFinite(numericSkyboxBrightness)) {
                setIfExists(sceneEnvCtl, 'skyboxBrightnessValue', numericSkyboxBrightness);
            }
        }

        var probeHorizonVal = valueForKeys(params, ['probeHorizon', 'probe_horizon']);
        if (probeHorizonVal === undefined && iblSection)
            probeHorizonVal = valueForKeys(iblSection, ['probe_horizon', 'horizon']);
        if (probeHorizonVal !== undefined) {
            var numericHorizon = Number(probeHorizonVal);
            if (isFinite(numericHorizon))
                setIfExists(sceneEnvCtl, 'probeHorizonValue', numericHorizon);
        }

        var rotationYawVal = valueForKeys(params, ['iblRotationDeg', 'ibl_rotation']);
        if (rotationYawVal === undefined && iblSection)
            rotationYawVal = valueForKeys(iblSection, ['rotation', 'rotation_y']);
        if (rotationYawVal !== undefined) {
            var numericYaw = Number(rotationYawVal);
            if (isFinite(numericYaw))
                setIfExists(sceneEnvCtl, 'iblRotationDeg', numericYaw);
        }

        var rotationPitchVal = valueForKeys(params, ['iblRotationPitchDeg', 'ibl_offset_x']);
        if (rotationPitchVal === undefined && iblSection)
            rotationPitchVal = valueForKeys(iblSection, ['rotation_x']);
        if (rotationPitchVal !== undefined) {
            var numericPitch = Number(rotationPitchVal);
            if (isFinite(numericPitch))
                setIfExists(sceneEnvCtl, 'iblRotationPitchDeg', numericPitch);
        }

        var rotationRollVal = valueForKeys(params, ['iblRotationRollDeg', 'ibl_offset_y']);
        if (rotationRollVal === undefined && iblSection)
            rotationRollVal = valueForKeys(iblSection, ['rotation_z']);
        if (rotationRollVal !== undefined) {
            var numericRoll = Number(rotationRollVal);
            if (isFinite(numericRoll))
                setIfExists(sceneEnvCtl, 'iblRotationRollDeg', numericRoll);
        }

        var bindCameraVal = valueForKeys(params, ['iblBindToCamera', 'ibl_bind_to_camera']);
        if (bindCameraVal === undefined && iblSection)
            bindCameraVal = valueForKeys(iblSection, ['bind_to_camera']);
        if (bindCameraVal !== undefined)
            setIfExists(sceneEnvCtl, 'iblBindToCamera', !!bindCameraVal);

        var skyboxBlurVal = valueForKeys(params, ['skyboxBlur', 'skybox_blur']);
        if (skyboxBlurVal === undefined && iblSection)
            skyboxBlurVal = valueForKeys(iblSection, ['skybox_blur', 'blur']);
        if (skyboxBlurVal !== undefined) {
            var numericBlur = Number(skyboxBlurVal);
            if (isFinite(numericBlur))
                setIfExists(sceneEnvCtl, 'skyboxBlurValue', numericBlur);
        }

        var tonemapToggleVal = valueForKeys(
            params,
            ['tonemapEnabled', 'tonemap_enabled', 'tonemapActive', 'tonemap_active']
        );
        if (tonemapToggleVal === undefined && tonemapSection)
            tonemapToggleVal = valueForKeys(tonemapSection, ['enabled', 'active']);
        if (tonemapToggleVal !== undefined) {
            var tonemapFlag = !!tonemapToggleVal;
            setIfExists(sceneEnvCtl, 'tonemapActive', tonemapFlag);
            if (!tonemapFlag) {
                setIfExists(sceneEnvCtl, 'tonemapModeName', 'none');
            } else {
                var explicitModeProvided = valueForKeys(params, ['tonemapModeName', 'tonemap_mode']) !== undefined;
                if (!explicitModeProvided && tonemapSection)
                    explicitModeProvided = valueForKeys(tonemapSection, ['mode', 'name']) !== undefined;
                if (!explicitModeProvided) {
                    var storedMode = sceneEnvCtl.tonemapStoredModeName || sceneEnvCtl.tonemapModeName || 'filmic';
                    setIfExists(sceneEnvCtl, 'tonemapModeName', storedMode);
                }
            }
        }
    }
    var tonemapModeVal = valueForKeys(params, ['tonemapModeName', 'tonemap_mode']);
    if (tonemapModeVal === undefined && tonemapSection)
        tonemapModeVal = valueForKeys(tonemapSection, ['mode', 'name']);
    if (tonemapModeVal !== undefined)
        setIfExists(sceneEnvCtl, 'tonemapModeName', String(tonemapModeVal));

    var tonemapExposureVal = valueForKeys(params, ['tonemapExposure', 'tonemap_exposure']);
    if (tonemapExposureVal === undefined && tonemapSection)
        tonemapExposureVal = valueForKeys(tonemapSection, ['exposure']);
    if (tonemapExposureVal !== undefined)
        setIfExists(sceneEnvCtl, 'tonemapExposure', Number(tonemapExposureVal));

    var tonemapWhitePointVal = valueForKeys(params, ['tonemapWhitePoint', 'tonemap_white_point']);
    if (tonemapWhitePointVal === undefined && tonemapSection)
        tonemapWhitePointVal = valueForKeys(tonemapSection, ['white_point']);
    if (tonemapWhitePointVal !== undefined)
        setIfExists(sceneEnvCtl, 'tonemapWhitePoint', Number(tonemapWhitePointVal));

    var fogEnabledVal = valueForKeys(params, ['fogEnabled', 'fog_enabled']);
    if (fogEnabledVal === undefined && fogSection)
        fogEnabledVal = valueForKeys(fogSection, ['enabled']);
    if (fogEnabledVal !== undefined)
        setIfExists(sceneEnvCtl, 'fogEnabled', !!fogEnabledVal);

    var fogColorVal = valueForKeys(params, ['fogColor', 'fog_color']);
    if (fogColorVal === undefined && fogSection)
        fogColorVal = valueForKeys(fogSection, ['color']);
    if (fogColorVal !== undefined)
        setIfExists(sceneEnvCtl, 'fogColor', fogColorVal);

    var fogDensityVal = valueForKeys(params, ['fogDensity', 'fog_density']);
    if (fogDensityVal === undefined && fogSection)
        fogDensityVal = valueForKeys(fogSection, ['density']);
    if (fogDensityVal !== undefined) {
        var fogDensityNum = Number(fogDensityVal);
        if (isFinite(fogDensityNum))
            setIfExists(sceneEnvCtl, 'fogDensity', fogDensityNum);
    }

    var fogNearSource = valueForKeys(params, ['fogNear', 'fog_near']);
    if (fogNearSource === undefined && fogSection)
        fogNearSource = valueForKeys(fogSection, ['near']);
    if (fogNearSource !== undefined) {
        var fogNearVal = Number(fogNearSource);
        if (isFinite(fogNearVal))
            setIfExists(sceneEnvCtl, 'fogNear', toSceneLength(fogNearVal));
    }

    var fogFarSource = valueForKeys(params, ['fogFar', 'fog_far']);
    if (fogFarSource === undefined && fogSection)
        fogFarSource = valueForKeys(fogSection, ['far']);
    if (fogFarSource !== undefined) {
        var fogFarVal = Number(fogFarSource);
        if (isFinite(fogFarVal))
            setIfExists(sceneEnvCtl, 'fogFar', toSceneLength(fogFarVal));
    }

    var fogHeightEnabledVal = valueForKeys(params, ['fogHeightEnabled', 'fog_height_enabled']);
    if (fogHeightEnabledVal === undefined && fogSection)
        fogHeightEnabledVal = valueForKeys(fogSection, ['height_enabled']);
    if (fogHeightEnabledVal !== undefined)
        setIfExists(sceneEnvCtl, 'fogHeightEnabled', !!fogHeightEnabledVal);

    var fogLeastVal = valueForKeys(params, ['fogLeastIntenseY', 'fog_least_intense_y']);
    if (fogLeastVal === undefined && fogSection)
        fogLeastVal = valueForKeys(fogSection, ['least_intense_y']);
    if (fogLeastVal !== undefined) {
        var fogLeastNum = Number(fogLeastVal);
        if (isFinite(fogLeastNum))
            setIfExists(sceneEnvCtl, 'fogLeastIntenseY', toSceneLength(fogLeastNum));
    }

    var fogMostVal = valueForKeys(params, ['fogMostIntenseY', 'fog_most_intense_y']);
    if (fogMostVal === undefined && fogSection)
        fogMostVal = valueForKeys(fogSection, ['most_intense_y']);
    if (fogMostVal !== undefined) {
        var fogMostNum = Number(fogMostVal);
        if (isFinite(fogMostNum))
            setIfExists(sceneEnvCtl, 'fogMostIntenseY', toSceneLength(fogMostNum));
    }

    var fogHeightCurveVal = valueForKeys(params, ['fogHeightCurve', 'fog_height_curve']);
    if (fogHeightCurveVal === undefined && fogSection)
        fogHeightCurveVal = valueForKeys(fogSection, ['height_curve']);
    if (fogHeightCurveVal !== undefined) {
        var fogHeightCurveNum = Number(fogHeightCurveVal);
        if (isFinite(fogHeightCurveNum))
            setIfExists(sceneEnvCtl, 'fogHeightCurve', fogHeightCurveNum);
    }

    var fogTransmitEnabledVal = valueForKeys(params, ['fogTransmitEnabled', 'fog_transmit_enabled']);
    if (fogTransmitEnabledVal === undefined && fogSection)
        fogTransmitEnabledVal = valueForKeys(fogSection, ['transmit_enabled']);
    if (fogTransmitEnabledVal !== undefined)
        setIfExists(sceneEnvCtl, 'fogTransmitEnabled', !!fogTransmitEnabledVal);

    var fogTransmitCurveVal = valueForKeys(params, ['fogTransmitCurve', 'fog_transmit_curve']);
    if (fogTransmitCurveVal === undefined && fogSection)
        fogTransmitCurveVal = valueForKeys(fogSection, ['transmit_curve']);
    if (fogTransmitCurveVal !== undefined) {
        var fogTransmitCurveNum = Number(fogTransmitCurveVal);
        if (isFinite(fogTransmitCurveNum))
            setIfExists(sceneEnvCtl, 'fogTransmitCurve', fogTransmitCurveNum);
    }

    var ssaoEnabledVal = valueForKeys(params, ['ssaoEnabled', 'ssao_enabled', 'ao_enabled']);
    if (ssaoEnabledVal === undefined && ssaoSection)
        ssaoEnabledVal = valueForKeys(ssaoSection, ['enabled']);
    if (ssaoEnabledVal !== undefined)
        setIfExists(sceneEnvCtl, 'ssaoEnabled', !!ssaoEnabledVal);

    var ssaoRadiusVal = valueForKeys(params, ['ssaoRadius', 'ssao_radius', 'ao_radius']);
    if (ssaoRadiusVal === undefined && ssaoSection)
        ssaoRadiusVal = valueForKeys(ssaoSection, ['radius']);
    if (ssaoRadiusVal !== undefined) {
        var ssaoRadiusNum = Number(ssaoRadiusVal);
        if (isFinite(ssaoRadiusNum))
            setIfExists(sceneEnvCtl, 'ssaoRadius', ssaoRadiusNum);
    }

    var ssaoIntensityVal = valueForKeys(params, ['ssaoIntensity', 'ssao_intensity', 'ao_strength']);
    if (ssaoIntensityVal === undefined && ssaoSection)
        ssaoIntensityVal = valueForKeys(ssaoSection, ['intensity', 'strength']);
    if (ssaoIntensityVal !== undefined)
        setIfExists(sceneEnvCtl, 'ssaoIntensity', Number(ssaoIntensityVal));

    var ssaoSoftnessVal = valueForKeys(params, ['ssaoSoftness', 'ssao_softness', 'ao_softness']);
    if (ssaoSoftnessVal === undefined && ssaoSection)
        ssaoSoftnessVal = valueForKeys(ssaoSection, ['softness']);
    if (ssaoSoftnessVal !== undefined)
        setIfExists(sceneEnvCtl, 'ssaoSoftness', Number(ssaoSoftnessVal));

    var ssaoDitherVal = valueForKeys(params, ['ssaoDither', 'ssao_dither', 'ao_dither']);
    if (ssaoDitherVal === undefined && ssaoSection)
        ssaoDitherVal = valueForKeys(ssaoSection, ['dither']);
    if (ssaoDitherVal !== undefined)
        setIfExists(sceneEnvCtl, 'ssaoDither', !!ssaoDitherVal);

    var ssaoSampleRateVal = valueForKeys(params, ['ssaoSampleRate', 'ssao_sample_rate', 'ao_sample_rate']);
    if (ssaoSampleRateVal === undefined && ssaoSection)
        ssaoSampleRateVal = valueForKeys(ssaoSection, ['sample_rate']);
    if (ssaoSampleRateVal !== undefined) {
        var ssaoSampleNumeric = Number(ssaoSampleRateVal);
        if (isFinite(ssaoSampleNumeric))
            setIfExists(sceneEnvCtl, 'ssaoSampleRate', Math.max(1, Math.round(ssaoSampleNumeric)));
    }

    var dofEnabledVal = valueForKeys(
        params,
        ['depthOfFieldEnabled', 'depth_of_field_enabled', 'depth_of_field']
    );
    if (dofEnabledVal === undefined && dofSection)
        dofEnabledVal = valueForKeys(dofSection, ['enabled']);
    if (dofEnabledVal !== undefined)
        setIfExists(sceneEnvCtl, 'internalDepthOfFieldEnabled', !!dofEnabledVal);

    var dofAutoFocusVal = valueForKeys(params, ['depthOfFieldAutoFocus', 'dof_auto_focus']);
    if (dofAutoFocusVal === undefined && dofSection)
        dofAutoFocusVal = valueForKeys(dofSection, ['auto_focus']);
    if (dofAutoFocusVal !== undefined)
        setIfExists(sceneEnvCtl, 'depthOfFieldAutoFocus', !!dofAutoFocusVal);

    var dofFocusDistanceVal = valueForKeys(params, ['dofFocusDistance', 'dof_focus_distance']);
    if (dofFocusDistanceVal === undefined && dofSection)
        dofFocusDistanceVal = valueForKeys(dofSection, ['focus_distance']);
    if (dofFocusDistanceVal !== undefined) {
        var dofDist = Number(dofFocusDistanceVal);
        if (isFinite(dofDist))
            setIfExists(sceneEnvCtl, 'dofFocusDistance', toSceneLength(dofDist));
    }

    var dofFocusRangeVal = valueForKeys(params, ['dofFocusRange', 'dof_focus_range']);
    if (dofFocusRangeVal === undefined && dofSection)
        dofFocusRangeVal = valueForKeys(dofSection, ['focus_range']);
    if (dofFocusRangeVal !== undefined) {
        var dofRange = Number(dofFocusRangeVal);
        if (isFinite(dofRange))
            setIfExists(sceneEnvCtl, 'dofFocusRange', toSceneLength(dofRange));
    }

    var dofBlurAmountVal = valueForKeys(params, ['dofBlurAmount', 'dof_blur_amount']);
    if (dofBlurAmountVal === undefined && dofSection)
        dofBlurAmountVal = valueForKeys(dofSection, ['blur_amount']);
    if (dofBlurAmountVal !== undefined)
        setIfExists(sceneEnvCtl, 'dofBlurAmount', Number(dofBlurAmountVal));

    var vignetteEnabledVal = valueForKeys(params, ['vignetteEnabled', 'vignette_enabled']);
    if (vignetteEnabledVal === undefined && vignetteSection)
        vignetteEnabledVal = valueForKeys(vignetteSection, ['enabled']);
    if (vignetteEnabledVal !== undefined)
        setIfExists(sceneEnvCtl, 'internalVignetteEnabled', !!vignetteEnabledVal);

    var vignetteStrengthVal = valueForKeys(params, ['vignetteStrength', 'vignette_strength']);
    if (vignetteStrengthVal === undefined && vignetteSection)
        vignetteStrengthVal = valueForKeys(vignetteSection, ['strength']);
    if (vignetteStrengthVal !== undefined)
        setIfExists(sceneEnvCtl, 'internalVignetteStrength', Number(vignetteStrengthVal));

    var aaPrimaryVal = valueForKeys(params, ['aaPrimaryMode', 'aa_primary_mode']);
    if (aaPrimaryVal === undefined && aaSection)
        aaPrimaryVal = valueForKeys(aaSection, ['primary', 'mode']);
    if (aaPrimaryVal !== undefined)
        setIfExists(sceneEnvCtl, 'aaPrimaryMode', String(aaPrimaryVal));

    var aaQualityVal = valueForKeys(params, ['aaQualityLevel', 'aa_quality_level']);
    if (aaQualityVal === undefined && aaSection)
        aaQualityVal = valueForKeys(aaSection, ['quality']);
    if (aaQualityVal !== undefined)
        setIfExists(sceneEnvCtl, 'aaQualityLevel', String(aaQualityVal));

    var aaPostVal = valueForKeys(params, ['aaPostMode', 'aa_post_mode']);
    if (aaPostVal === undefined && aaSection)
        aaPostVal = valueForKeys(aaSection, ['post']);
    if (aaPostVal !== undefined)
        setIfExists(sceneEnvCtl, 'aaPostMode', String(aaPostVal));

    var taaEnabledVal = valueForKeys(params, ['taaEnabled', 'taa_enabled']);
    if (taaEnabledVal === undefined && aaSection)
        taaEnabledVal = valueForKeys(aaSection, ['taaEnabled', 'taa_enabled']);
    if (taaEnabledVal !== undefined)
        setIfExists(sceneEnvCtl, 'taaEnabled', !!taaEnabledVal);

    var taaStrengthVal = valueForKeys(params, ['taaStrength', 'taa_strength']);
    if (taaStrengthVal === undefined && aaSection)
        taaStrengthVal = valueForKeys(aaSection, ['taa_strength', 'strength']);
    if (taaStrengthVal !== undefined)
        setIfExists(sceneEnvCtl, 'taaStrength', Number(taaStrengthVal));

    var taaMotionVal = valueForKeys(params, ['taaMotionAdaptive', 'taa_motion_adaptive']);
    if (taaMotionVal === undefined && aaSection)
        taaMotionVal = valueForKeys(aaSection, ['taa_motion_adaptive']);
    if (taaMotionVal !== undefined)
        setIfExists(sceneEnvCtl, 'taaMotionAdaptive', !!taaMotionVal);

    var fxaaVal = valueForKeys(params, ['fxaaEnabled', 'fxaa_enabled']);
    if (fxaaVal === undefined && aaSection)
        fxaaVal = valueForKeys(aaSection, ['fxaa_enabled', 'fxaa']);
    if (fxaaVal !== undefined)
        setIfExists(sceneEnvCtl, 'fxaaEnabled', !!fxaaVal);

    var specularVal = valueForKeys(
        params,
        ['specularAAEnabled', 'specular_aa_enabled', 'specular_aa']
    );
    if (specularVal === undefined && aaSection)
        specularVal = valueForKeys(aaSection, ['specular', 'specular_aa']);
    if (specularVal !== undefined)
        setIfExists(sceneEnvCtl, 'specularAAEnabled', !!specularVal);

    var oitVal = valueForKeys(params, ['oitMode', 'oit_mode', 'oit']);
    if (oitVal === undefined && aaSection)
        oitVal = valueForKeys(aaSection, ['oit']);
    if (oitVal !== undefined)
        setIfExists(sceneEnvCtl, 'oitMode', String(oitVal));

    var ditheringVal = valueForKeys(params, ['ditheringEnabled', 'dithering']);
    if (ditheringVal === undefined && aaSection)
        ditheringVal = valueForKeys(aaSection, ['dithering']);
    if (ditheringVal !== undefined)
        setIfExists(sceneEnvCtl, 'ditheringEnabled', !!ditheringVal);

    var hdrSourceVal = valueForKeys(
        params,
        [
            'iblSource',
            'ibl_source',
            'iblPrimary',
            'ibl_primary',
            'hdrSource',
            'hdr_source'
        ]
    );
    if (hdrSourceVal === undefined && iblSection)
        hdrSourceVal = valueForKeys(iblSection, ['source', 'primary', 'hdr_source']);
    if (hdrSourceVal !== undefined) {
        var normalizedSource = normalizeHdrSource(hdrSourceVal);
        setIfExists(iblLoader, 'primarySource', normalizedSource);
    }

 if (postEffects && typeof postEffects.applyPayload === "function") {
  try {
   postEffects.applyPayload(params, sceneEnvCtl);
  } catch (effectError) {
   console.warn("[SimulationRoot] postEffects.applyPayload failed", effectError);
  }
 }

 return true;
  } catch (error) {
  console.error("[SimulationRoot] applyEnvironmentUpdates failed", error);
  return false;
  }
}
    function applyQualityUpdates(params) {
        params = coerceBatchObject("quality", params);
        if (!params)
            return false;

        try {

        var qualityPatch = {};

        function assignString(targetKey, value) {
            if (value === undefined || value === null)
                return;
            qualityPatch[targetKey] = String(value);
        }

 function assignBool(targetKey, value) {
  if (value === undefined || value === null)
   return;
  qualityPatch[targetKey] = !!value;
 }

 function assignNumber(targetKey, value) {
  if (value === undefined || value === null)
   return;
  var numeric = Number(value);
 if (isFinite(numeric))
  qualityPatch[targetKey] = numeric;
}

        var presetValue = valueForKeys(params, ['qualityPreset', 'quality_preset', 'preset']);
        assignString("qualityPreset", presetValue);

 var renderScaleValue = valueForKeys(params, ['renderScale', 'render_scale']);
 if (renderScaleValue !== undefined) {
  var renderScaleNumeric = Number(renderScaleValue);
  if (isFinite(renderScaleNumeric))
   renderScale = Math.max(0.1, renderScaleNumeric);
 }

 var frameLimitValue = valueForKeys(params, ['frameRateLimit', 'frame_rate_limit']);
 if (frameLimitValue !== undefined) {
  var frameLimitNumeric = Number(frameLimitValue);
  if (isFinite(frameLimitNumeric))
   frameRateLimit = Math.max(0, frameLimitNumeric);
 }

  var renderPolicyValue = valueForKeys(params, ['renderPolicy', 'render_policy']);
  if (renderPolicyValue !== undefined)
   renderPolicyKey = normalizeRenderPolicyKey(renderPolicyValue);

 var meshQualitySource = null;
 if (isPlainObject(params.meshQuality))
  meshQualitySource = params.meshQuality;
 else if (isPlainObject(params.mesh))
  meshQualitySource = params.mesh;

 if (meshQualitySource) {
  var meshPatch = {};
  if (meshQualitySource.cylinderSegments !== undefined)
   meshPatch.cylinderSegments = meshQualitySource.cylinderSegments;
  else if (meshQualitySource.cylinder_segments !== undefined)
   meshPatch.cylinderSegments = meshQualitySource.cylinder_segments;
  if (meshQualitySource.cylinderRings !== undefined)
   meshPatch.cylinderRings = meshQualitySource.cylinderRings;
  else if (meshQualitySource.cylinder_rings !== undefined)
   meshPatch.cylinderRings = meshQualitySource.cylinder_rings;
  if (Object.keys(meshPatch).length)
   applyGeometryUpdatesInternal(meshPatch);
 }

var shadowSource = null;
if (isPlainObject(params.shadowSettings))
 shadowSource = params.shadowSettings;
else if (isPlainObject(params.shadows))
 shadowSource = params.shadows;

 if (shadowSource) {
  var lightingPatch = {};
  if (shadowSource.enabled !== undefined)
   lightingPatch.shadows_enabled = !!shadowSource.enabled;
  var resolutionValue = shadowSource.resolution;
  if (resolutionValue === undefined && shadowSource.shadowResolution !== undefined)
   resolutionValue = shadowSource.shadowResolution;
  var resolutionNumeric = Number(resolutionValue);
  if (resolutionValue !== undefined && isFinite(resolutionNumeric))
   lightingPatch.shadow_resolution = Math.round(resolutionNumeric);
  var filterValue = shadowSource.filterSamples;
  if (filterValue === undefined && shadowSource.filter !== undefined)
   filterValue = shadowSource.filter;
  var filterNumeric = Number(filterValue);
  if (filterValue !== undefined && isFinite(filterNumeric))
   lightingPatch.shadow_filter_samples = Math.round(filterNumeric);
  var biasValue = shadowSource.bias;
  if (biasValue === undefined && shadowSource.shadowBias !== undefined)
   biasValue = shadowSource.shadowBias;
  var biasNumeric = Number(biasValue);
  if (biasValue !== undefined && isFinite(biasNumeric))
   lightingPatch.shadow_bias = biasNumeric;
  var factorValue = shadowSource.factor;
  if (factorValue === undefined && shadowSource.darkness !== undefined)
   factorValue = shadowSource.darkness;
  if (factorValue === undefined && shadowSource.shadowFactor !== undefined)
   factorValue = shadowSource.shadowFactor;
  var factorNumeric = Number(factorValue);
  if (factorValue !== undefined && isFinite(factorNumeric))
   lightingPatch.shadow_factor = factorNumeric;
  if (Object.keys(lightingPatch).length)
   applyLightingUpdates({ global: lightingPatch });
 }

 var aaSource = isPlainObject(params.antialiasing) ? params.antialiasing : null;

 assignString("aaPrimaryMode", params.aaPrimaryMode !== undefined ? params.aaPrimaryMode : aaSource && aaSource.primary);
 assignString("aaQualityLevel", params.aaQualityLevel !== undefined ? params.aaQualityLevel : aaSource && aaSource.quality);
 assignString("aaPostMode", params.aaPostMode !== undefined ? params.aaPostMode : aaSource && aaSource.post);

 var taaEnabledValue = params.taaEnabled;
 if (taaEnabledValue === undefined)
  taaEnabledValue = params.taa_enabled;
 assignBool("taaEnabled", taaEnabledValue);

 var taaStrengthValue = params.taaStrength;
 if (taaStrengthValue === undefined)
  taaStrengthValue = params.taa_strength;
 assignNumber("taaStrength", taaStrengthValue);

 var taaMotionValue = params.taaMotionAdaptive;
 if (taaMotionValue === undefined)
  taaMotionValue = params.taa_motion_adaptive;
 assignBool("taaMotionAdaptive", taaMotionValue);

 var fxaaValue = params.fxaaEnabled;
 if (fxaaValue === undefined)
  fxaaValue = params.fxaa_enabled;
 assignBool("fxaaEnabled", fxaaValue);

 var specularValue = params.specularAAEnabled;
 if (specularValue === undefined)
  specularValue = params.specular_aa;
 assignBool("specularAAEnabled", specularValue);

 var ditheringValue = params.ditheringEnabled;
 if (ditheringValue === undefined)
  ditheringValue = params.dithering;
 assignBool("ditheringEnabled", ditheringValue);

 var oitValue = params.oitMode;
 if (oitValue === undefined)
  oitValue = params.oit;
 if (oitValue !== undefined && oitValue !== null)
  qualityPatch.oitMode = String(oitValue);

        if (Object.keys(qualityPatch).length && sceneEnvCtl && typeof sceneEnvCtl.applyQualityPayload === "function") {
            try {
                sceneEnvCtl.applyQualityPayload(qualityPatch);
            } catch (err) {
                console.warn("applyQualityPayload failed", err);
            }
        }
        return true;
    } catch (error) {
        console.error("[SimulationRoot] applyQualityUpdates failed", error);
        return false;
    }
    }

  function applyMaterialUpdates(params) {
  if (!params)
  return false;

  try {
  var applied = false;

  var prefixMap = {
 frame: "frame",
 lever: "lever",
 tail: "tailRod",
 tail_rod: "tailRod",
 cylinder: "cylinder",
 piston_body: "pistonBody",
 piston_rod: "pistonRod",
 joint_tail: "jointTail",
 joint_arm: "jointArm",
 joint_rod: "jointRod"
 };

 var aliasMaterialKey = {
 metal: "lever",
 glass: "cylinder"
 };

 var propertySuffixMap = {
 base_color: "BaseColor",
 metalness: "Metalness",
 roughness: "Roughness",
 specular: "SpecularAmount",
 specular_amount: "SpecularAmount",
 specular_tint: "SpecularTint",
 clearcoat: "Clearcoat",
 clearcoat_roughness: "ClearcoatRoughness",
 transmission: "Transmission",
 opacity: "Opacity",
 ior: "Ior",
 attenuation_distance: "AttenuationDistance",
 attenuation_color: "AttenuationColor",
    emissive_color: "EmissiveColor",
    emissive_intensity: "EmissiveIntensity",
    normal_strength: "NormalStrength",
    occlusion_amount: "OcclusionAmount",
    thickness: "Thickness",
    alpha_mode: "AlphaMode",
    alpha_cutoff: "AlphaCutoff",
    texture_path: "TexturePath",
    warning_color: "WarningColor",
    ok_color: "OkColor",
    error_color: "ErrorColor"
};

 function canonicalMaterialKey(key) {
 var normalized = String(key || "").toLowerCase();
 if (aliasMaterialKey[normalized] !== undefined)
 return aliasMaterialKey[normalized];
 return normalized;
 }

  function applyMaterialProperty(prefix, propertyKey, value) {
  var suffix = propertySuffixMap[propertyKey];
  if (!suffix)
  return false;
  if (setIfExists(sharedMaterials, prefix + suffix, value)) {
  applied = true;
  return true;
  }
  return false;
  }

 function applyMaterialGroup(materialKey, values) {
 if (!values || typeof values !== "object")
 return;
 var prefix = prefixMap[materialKey];
 if (!prefix)
 return;

 for (var key in values) {
 if (!values.hasOwnProperty(key))
 continue;
 var normalizedKey = String(key).toLowerCase();
  if (!applyMaterialProperty(prefix, normalizedKey, values[key]) && materialKey === "joint_tail") {
  if (normalizedKey === "ok_color")
  applied = setIfExists(sharedMaterials, "jointRodOkColor", values[key]) || applied;
  if (normalizedKey === "error_color")
  applied = setIfExists(sharedMaterials, "jointRodErrorColor", values[key]) || applied;
  }
 }

  if (materialKey === "piston_body") {
  if (values.warning_color !== undefined)
  applied = setIfExists(sharedMaterials, "pistonBodyWarningColor", values.warning_color) || applied;
  }
  if (materialKey === "piston_rod") {
  if (values.warning_color !== undefined)
  applied = setIfExists(sharedMaterials, "pistonRodWarningColor", values.warning_color) || applied;
  }
  if (materialKey === "joint_rod") {
  if (values.ok_color !== undefined)
  applied = setIfExists(sharedMaterials, "jointRodOkColor", values.ok_color) || applied;
  if (values.error_color !== undefined)
  applied = setIfExists(sharedMaterials, "jointRodErrorColor", values.error_color) || applied;
  }
 }

 var consumedKeys = {};

 for (var materialKey in params) {
 if (!params.hasOwnProperty(materialKey))
 continue;
 var canonicalKey = canonicalMaterialKey(materialKey);
 if (prefixMap[canonicalKey] || canonicalKey === "joint_rod") {
 applyMaterialGroup(canonicalKey, params[materialKey]);
 consumedKeys[materialKey] = true;
 }
 }

 for (var rawKey in params) {
 if (!params.hasOwnProperty(rawKey) || consumedKeys[rawKey])
 continue;
 var directMatch = /^([a-z]+(?:_[a-z]+)*)_(.+)$/.exec(rawKey);
 if (!directMatch)
 continue;
 var materialPart = canonicalMaterialKey(directMatch[1]);
 var propertyPart = directMatch[2].toLowerCase();
 var prefix = prefixMap[materialPart];
 if (!prefix)
 continue;
  if (!applyMaterialProperty(prefix, propertyPart, params[rawKey]) && materialPart === "joint_rod") {
  if (propertyPart === "ok_color")
  applied = setIfExists(sharedMaterials, "jointRodOkColor", params[rawKey]) || applied;
  if (propertyPart === "error_color")
  applied = setIfExists(sharedMaterials, "jointRodErrorColor", params[rawKey]) || applied;
  }
  }

  return applied;
 } catch (error) {
  console.error("[SimulationRoot] applyMaterialUpdates failed", error);
  return false;
 }
 }

function applyEffectsUpdatesInternal(params) {
    if (!params)
        return false;

    try {
        var mergedPayload = cloneObject(params);
        var normalized = {};
        var hasUpdates = false;

        function recordValue(targetKey, value) {
            if (value === undefined)
                return;
            mergedPayload[targetKey] = value;
            normalized[targetKey] = value;
            hasUpdates = true;
        }

        function toBoolean(value) {
            if (value === undefined || value === null)
                return undefined;
            if (typeof value === "boolean")
                return value;
            if (typeof value === "number")
                return value !== 0;
            if (typeof value === "string") {
                var lowered = value.trim().toLowerCase();
                if (["true", "1", "yes", "on"].indexOf(lowered) !== -1)
                    return true;
                if (["false", "0", "no", "off"].indexOf(lowered) !== -1)
                    return false;
            }
            return !!value;
        }

        function toNumber(value) {
            if (value === undefined || value === null)
                return undefined;
            var numeric = Number(value);
            return isFinite(numeric) ? numeric : undefined;
        }

        function toInteger(value) {
            var numeric = toNumber(value);
            return numeric === undefined ? undefined : Math.round(numeric);
        }

        function keyList(candidate) {
            return Array.isArray(candidate) ? candidate : [candidate];
        }

        function valueFromKeys(source, keys) {
            if (!isPlainObject(source))
                return undefined;
            var list = keyList(keys);
            for (var i = 0; i < list.length; ++i) {
                var key = list[i];
                if (source.hasOwnProperty(key) && source[key] !== undefined)
                    return source[key];
            }
            return undefined;
        }

        function readValue(primaryKeys, nestedSources, nestedKeys) {
            var direct = valueFromKeys(params, primaryKeys);
            if (direct !== undefined)
                return direct;

            var sources = nestedSources || [];
            if (!Array.isArray(sources))
                sources = [sources];
            var nestedList = nestedKeys ? keyList(nestedKeys) : keyList(primaryKeys);

            for (var i = 0; i < sources.length; ++i) {
                var candidate = sources[i];
                if (!candidate)
                    continue;
                var nested = valueFromKeys(candidate, nestedList);
                if (nested !== undefined)
                    return nested;
            }

            return undefined;
        }

        function assignBool(targetKey, primaryKeys, nestedSources, nestedKeys) {
            var raw = readValue(primaryKeys, nestedSources, nestedKeys);
            var coerced = toBoolean(raw);
            if (coerced === undefined)
                return;
            recordValue(targetKey, coerced);
        }

        function assignNumber(targetKey, primaryKeys, nestedSources, nestedKeys) {
            var raw = readValue(primaryKeys, nestedSources, nestedKeys);
            var coerced = toNumber(raw);
            if (coerced === undefined)
                return;
            recordValue(targetKey, coerced);
        }

        function assignInteger(targetKey, primaryKeys, nestedSources, nestedKeys) {
            var raw = readValue(primaryKeys, nestedSources, nestedKeys);
            var coerced = toInteger(raw);
            if (coerced === undefined)
                return;
            recordValue(targetKey, coerced);
        }

        function assignString(targetKey, primaryKeys, nestedSources, nestedKeys) {
            var raw = readValue(primaryKeys, nestedSources, nestedKeys);
            if (raw === undefined || raw === null)
                return;
            recordValue(targetKey, String(raw));
        }

        function assignLensStretch(targetKey, primaryKeys, nestedSources, nestedKeys) {
            var raw = readValue(primaryKeys, nestedSources, nestedKeys);
            if (raw === undefined || raw === null)
                return;
            var numeric = toNumber(raw);
            if (numeric === undefined) {
                var boolValue = toBoolean(raw);
                if (boolValue === undefined)
                    return;
                recordValue(targetKey, boolValue ? 1.0 : 0.0);
                return;
            }
            recordValue(targetKey, numeric);
        }

        var bloomSection = isPlainObject(params.bloom) ? params.bloom : null;
        var bloomLegacySection = isPlainObject(params.bloom_settings) ? params.bloom_settings : null;
        var tonemapSection = isPlainObject(params.tonemap) ? params.tonemap : null;
        var ssaoSection = isPlainObject(params.ssao) ? params.ssao : null;
        var aoSection = isPlainObject(params.ao) ? params.ao : null;
        var dofSection = isPlainObject(params.depthOfField) ? params.depthOfField : null;
        if (!dofSection && isPlainObject(params.dof))
            dofSection = params.dof;
        var motionSection = isPlainObject(params.motion) ? params.motion : null;
        var motionBlurSection = isPlainObject(params.motionBlur) ? params.motionBlur : null;
        var lensFlareSection = isPlainObject(params.lensFlare) ? params.lensFlare : null;
        if (!lensFlareSection && isPlainObject(params.lens_flare))
            lensFlareSection = params.lens_flare;
        var vignetteSection = isPlainObject(params.vignette) ? params.vignette : null;
        var adjustmentsSection = isPlainObject(params.adjustments) ? params.adjustments : null;
        if (!adjustmentsSection && isPlainObject(params.color))
            adjustmentsSection = params.color;

        assignBool("bloomEnabled", ["bloomEnabled", "bloom_enabled"], [bloomSection, bloomLegacySection], ["enabled", "active"]);
        assignNumber("bloomIntensity", ["bloomIntensity", "bloom_intensity", "bloom_strength"], [bloomSection, bloomLegacySection], ["intensity", "strength"]);
        assignNumber("bloomThreshold", ["bloomThreshold", "bloom_threshold"], [bloomSection, bloomLegacySection], ["threshold"]);
        assignNumber("bloomSpread", ["bloomSpread", "bloom_spread", "bloom_blur", "bloom_blur_amount"], [bloomSection, bloomLegacySection], ["spread", "blur", "blur_amount"]);
        assignNumber("bloomGlowStrength", ["bloomGlowStrength", "bloom_glow_strength"], [bloomSection, bloomLegacySection], ["glow_strength"]);
        assignNumber("bloomHdrMax", ["bloomHdrMax", "bloom_hdr_max"], [bloomSection, bloomLegacySection], ["hdr_max"]);
        assignNumber("bloomHdrScale", ["bloomHdrScale", "bloom_hdr_scale"], [bloomSection, bloomLegacySection], ["hdr_scale"]);
        assignBool("bloomQualityHigh", ["bloomQualityHigh", "bloom_quality_high"], [bloomSection, bloomLegacySection], ["quality_high", "high_quality"]);
        assignBool("bloomBicubicUpscale", ["bloomBicubicUpscale", "bloom_bicubic_upscale"], [bloomSection, bloomLegacySection], ["bicubic_upscale"]);

        assignBool("tonemapEnabled", ["tonemapEnabled", "tonemap_enabled"], tonemapSection, ["enabled"]);
        assignString("tonemapModeName", ["tonemapModeName", "tonemapMode", "tonemap_mode"], tonemapSection, ["mode", "name"]);
        assignNumber("tonemapExposure", ["tonemapExposure", "tonemap_exposure"], tonemapSection, ["exposure"]);
        assignNumber("tonemapWhitePoint", ["tonemapWhitePoint", "tonemap_white_point"], tonemapSection, ["white_point"]);

        assignBool("ssaoEnabled", ["ssaoEnabled", "ssao_enabled", "ao_enabled"], [ssaoSection, aoSection], ["enabled", "active"]);
        assignNumber("ssaoIntensity", ["ssaoIntensity", "ssao_intensity", "ssao_strength", "ao_strength"], [ssaoSection, aoSection], ["intensity", "strength"]);
        assignNumber("ssaoRadius", ["ssaoRadius", "ssao_radius", "ao_radius"], [ssaoSection, aoSection], ["radius"]);
        assignNumber("ssaoBias", ["ssaoBias", "ssao_bias", "ao_bias"], [ssaoSection, aoSection], ["bias"]);
        assignNumber("ssaoSampleRate", ["ssaoSampleRate", "ssao_samples", "ssao_sample_rate", "ao_sample_rate"], [ssaoSection, aoSection], ["sample_rate", "samples"]);

        assignBool("depthOfFieldEnabled", ["depthOfFieldEnabled", "depth_of_field", "dof_enabled"], dofSection, ["enabled", "active"]);
        assignNumber("dofFocusDistance", ["dofFocusDistance", "dof_focus_distance", "focus_distance"], dofSection, ["focus_distance", "distance"]);
        assignNumber("dofFocusRange", ["dofFocusRange", "dof_focus_range", "focus_range"], dofSection, ["focus_range", "range"]);
        assignNumber("dofBlurAmount", ["dofBlurAmount", "dof_blur", "blur_amount"], dofSection, ["blur", "blur_amount"]);
        assignBool("dofAutoFocus", ["dofAutoFocus", "dof_auto_focus"], dofSection, ["auto_focus", "autofocus"]);

        assignBool("motionBlurEnabled", ["motionBlurEnabled", "motion_blur"], [motionSection, motionBlurSection], ["enabled", "active"]);
        assignNumber("motionBlurStrength", ["motionBlurStrength", "motion_blur_amount", "motion_blur_strength"], [motionSection, motionBlurSection], ["amount", "strength"]);
        assignInteger("motionBlurSamples", ["motionBlurSamples", "motion_blur_samples"], [motionSection, motionBlurSection], ["samples"]);

        assignBool("lensFlareEnabled", ["lensFlareEnabled", "lens_flare"], lensFlareSection, ["enabled", "active"]);
        assignInteger("lensFlareGhostCount", ["lensFlareGhostCount", "lens_flare_ghost_count"], lensFlareSection, ["ghost_count", "ghosts"]);
        assignNumber("lensFlareGhostDispersal", ["lensFlareGhostDispersal", "lens_flare_ghost_dispersal"], lensFlareSection, ["ghost_dispersal", "ghost_dispersal_factor"]);
        assignNumber("lensFlareHaloWidth", ["lensFlareHaloWidth", "lens_flare_halo_width"], lensFlareSection, ["halo_width"]);
        assignNumber("lensFlareBloomBias", ["lensFlareBloomBias", "lens_flare_bloom_bias"], lensFlareSection, ["bloom_bias"]);
        assignLensStretch("lensFlareStretchToAspect", ["lensFlareStretchToAspect", "lens_flare_stretch_to_aspect", "lens_flare_stretch"], lensFlareSection, ["stretch_to_aspect", "stretch"]);

        assignBool("vignetteEnabled", ["vignetteEnabled", "vignette", "vignette_enabled"], vignetteSection, ["enabled", "active"]);
        assignNumber("vignetteStrength", ["vignetteStrength", "vignette_strength"], vignetteSection, ["strength"]);
        assignNumber("vignetteRadius", ["vignetteRadius", "vignette_radius"], vignetteSection, ["radius"]);

        assignNumber("adjustmentBrightness", ["adjustmentBrightness", "adjustment_brightness", "color_brightness"], adjustmentsSection, ["brightness"]);
        assignNumber("adjustmentContrast", ["adjustmentContrast", "adjustment_contrast", "color_contrast"], adjustmentsSection, ["contrast"]);
        assignNumber("adjustmentSaturation", ["adjustmentSaturation", "adjustment_saturation", "color_saturation"], adjustmentsSection, ["saturation"]);

        var payloadKeys = Object.keys(mergedPayload);
        if (!payloadKeys.length)
            return false;

        var changed = false;

        if (sceneEnvCtl && typeof sceneEnvCtl.applyEffectsPayload === "function") {
            try {
                sceneEnvCtl.applyEffectsPayload(mergedPayload);
                changed = true;
            } catch (controllerError) {
                console.warn("[SimulationRoot] sceneEnvCtl.applyEffectsPayload failed", controllerError);
            }
        }

        if (postEffects && typeof postEffects.applyPayload === "function") {
            try {
                postEffects.applyPayload(mergedPayload, sceneEnvCtl);
                changed = true;
            } catch (effectError) {
                console.warn("[SimulationRoot] postEffects.applyPayload failed", effectError);
            }
        }

        return changed || hasUpdates;
    } catch (error) {
        console.error("[SimulationRoot] applyEffectsUpdates failed", error);
        return false;
    }
}

function applyEffectsUpdates(params) {
    params = coerceBatchObject("effects", params);
    if (!params)
        return false;
    return applyEffectsUpdatesInternal(params);
}

function applyAnimationUpdates(params) {
 if (!params)
  return false;

 var changed = false;
 try {
 if (params && Object.keys(params).length)
  changed = true;

 if (params.isRunning !== undefined) {
  isRunning = !!params.isRunning;
  changed = true;
 }

 if (params.simulationTime !== undefined) {
  animationTime = Number(params.simulationTime);
  pythonAnimationActive = true;
  pythonAnimationTimeout.restart();
  changed = true;
 }

 if (params.smoothingEnabled !== undefined)
  animationSmoothingEnabled = !!params.smoothingEnabled;
 else if (params.smoothing_enabled !== undefined)
  animationSmoothingEnabled = !!params.smoothing_enabled;

 if (params.smoothingDurationMs !== undefined)
  animationSmoothingDurationMs = Number(params.smoothingDurationMs);
 else if (params.smoothing_duration_ms !== undefined)
  animationSmoothingDurationMs = Number(params.smoothing_duration_ms);

 if (params.smoothingAngleSnapDeg !== undefined)
  animationSmoothingAngleSnapDeg = Number(params.smoothingAngleSnapDeg);
 else if (params.smoothing_angle_snap_deg !== undefined)
  animationSmoothingAngleSnapDeg = Number(params.smoothing_angle_snap_deg);

 if (params.smoothingPistonSnapM !== undefined)
  animationSmoothingPistonSnapM = Number(params.smoothingPistonSnapM);
 else if (params.smoothing_piston_snap_m !== undefined)
  animationSmoothingPistonSnapM = Number(params.smoothing_piston_snap_m);

 var easingValue = params.smoothingEasingName;
 if (easingValue === undefined && params.smoothingEasing !== undefined)
  easingValue = params.smoothingEasing;
 if (easingValue === undefined && params.smoothing_easing !== undefined)
  easingValue = params.smoothing_easing;
 if (easingValue !== undefined)
  animationSmoothingEasing = String(easingValue);

 if (params.amplitude !== undefined)
  userAmplitude = Number(params.amplitude);
 if (params.frequency !== undefined)
  userFrequency = Number(params.frequency);
 if (params.phase_global !== undefined)
  userPhaseGlobal = Number(params.phase_global);
 if (params.phase_fl !== undefined)
  userPhaseFL = Number(params.phase_fl);
 if (params.phase_fr !== undefined)
  userPhaseFR = Number(params.phase_fr);
 if (params.phase_rl !== undefined)
  userPhaseRL = Number(params.phase_rl);
 if (params.phase_rr !== undefined)
  userPhaseRR = Number(params.phase_rr);

 var globalImmediate = params.instant === true || params.immediate === true;

 if (params.frame) {
  var frame = params.frame;
  var framePayload = {};
  if (frame.heave !== undefined)
   framePayload.heave = Number(frame.heave);
  if (frame.roll !== undefined)
   framePayload.roll = Number(frame.roll);
  if (frame.pitch !== undefined)
   framePayload.pitch = Number(frame.pitch);
  if (Object.keys(framePayload).length) {
   rigAnimation.applyFrameMotion(framePayload, {
    immediate: globalImmediate || params.frameImmediate === true || frame.immediate === true
   });
   pythonFrameActive = true;
   pythonFrameTimeout.restart();
  }
 }

 var leverAnglesPayload = null;
 if (isPlainObject(params.leverAngles))
  leverAnglesPayload = params.leverAngles;
 else if (isPlainObject(params.lever_angles))
  leverAnglesPayload = params.lever_angles;
 if (leverAnglesPayload) {
  var anglesPayload = {};
  if (leverAnglesPayload.fl !== undefined)
   anglesPayload.fl = Number(leverAnglesPayload.fl);
  if (leverAnglesPayload.fr !== undefined)
   anglesPayload.fr = Number(leverAnglesPayload.fr);
  if (leverAnglesPayload.rl !== undefined)
   anglesPayload.rl = Number(leverAnglesPayload.rl);
  if (leverAnglesPayload.rr !== undefined)
   anglesPayload.rr = Number(leverAnglesPayload.rr);
  if (Object.keys(anglesPayload).length && rigAnimation && typeof rigAnimation.applyLeverAnglesRadians === "function") {
   try {
    rigAnimation.applyLeverAnglesRadians(anglesPayload, {
     immediate: globalImmediate || params.leverAnglesImmediate === true || leverAnglesPayload.immediate === true
    });
   } catch (err) {
    console.warn("applyLeverAnglesRadians failed", err);
   }
   pythonLeverAnglesActive = true;
   pythonLeverAnglesTimeout.restart();
  }
 }

 var pistonPayloadSource = null;
 if (isPlainObject(params.pistonPositions))
  pistonPayloadSource = params.pistonPositions;
 else if (isPlainObject(params.piston_positions))
  pistonPayloadSource = params.piston_positions;
 if (pistonPayloadSource) {
  var pistonPayload = {};
  if (pistonPayloadSource.fl !== undefined)
   pistonPayload.fl = Number(pistonPayloadSource.fl);
  if (pistonPayloadSource.fr !== undefined)
   pistonPayload.fr = Number(pistonPayloadSource.fr);
  if (pistonPayloadSource.rl !== undefined)
   pistonPayload.rl = Number(pistonPayloadSource.rl);
  if (pistonPayloadSource.rr !== undefined)
   pistonPayload.rr = Number(pistonPayloadSource.rr);
  if (Object.keys(pistonPayload).length && rigAnimation && typeof rigAnimation.applyPistonPositions === "function") {
   try {
    rigAnimation.applyPistonPositions(pistonPayload, {
     immediate: globalImmediate || params.pistonImmediate === true || pistonPayloadSource.immediate === true
    });
   } catch (err) {
    console.warn("applyPistonPositions failed", err);
   }
   pythonPistonsActive = true;
   pythonPistonsTimeout.restart();
  }
 }

 if (isPlainObject(params.linePressures)) {
  var lp = params.linePressures;
  var updatedPressures = Object.assign({}, linePressures || {});
  if (lp.a1 !== undefined)
   updatedPressures.a1 = Number(lp.a1);
  if (lp.b1 !== undefined)
   updatedPressures.b1 = Number(lp.b1);
  if (lp.a2 !== undefined)
   updatedPressures.a2 = Number(lp.a2);
  if (lp.b2 !== undefined)
   updatedPressures.b2 = Number(lp.b2);
  linePressures = updatedPressures;
  pythonPressureActive = true;
  pythonPressureTimeout.restart();
 }

 if (params.tankPressure !== undefined) {
  tankPressure = Number(params.tankPressure);
  pythonPressureActive = true;
  pythonPressureTimeout.restart();
 }

  if (!pythonLeverAnglesActive) {
  updateFallbackAngles();
  }
  return changed;
 } catch (error) {
  console.error("[SimulationRoot] applyAnimationUpdates failed", error);
  return false;
 }
}

function apply3DUpdates(params) {
 params = coerceBatchObject("threeD", params);
 if (!params)
  return false;
 var changed = false;
 try {
 if (params && Object.keys(params).length)
  changed = true;
 var globalImmediate = params.instant === true || params.immediate === true;
 if (isPlainObject(params.frame)) {
  var f = params.frame;
  var framePayload = {};
  if (f.heave !== undefined)
   framePayload.heave = Number(f.heave);
  if (f.roll !== undefined)
   framePayload.roll = Number(f.roll);
  if (f.pitch !== undefined)
   framePayload.pitch = Number(f.pitch);
  if (Object.keys(framePayload).length && rigAnimation && typeof rigAnimation.applyFrameMotion === "function") {
   try {
    rigAnimation.applyFrameMotion(framePayload, {
     immediate: globalImmediate || params.frameImmediate === true || f.immediate === true
    });
   } catch (err) {
    console.warn("applyFrameMotion failed", err);
   }
   pythonFrameActive = true;
   pythonFrameTimeout.restart();
  }
 }
 if (isPlainObject(params.wheels)) {
  var wheelData = params.wheels;
  var leverPatch = {};
  var pistonPatch = {};
  var leverImmediate = globalImmediate;
  var pistonImmediate = globalImmediate;

  function applyWheel(key, source) {
  if (!isPlainObject(source))
   return;
   if (source.leverAngle !== undefined)
    leverPatch[key] = Number(source.leverAngle);
   if (source.pistonPosition !== undefined)
    pistonPatch[key] = Number(source.pistonPosition);
   if (source.immediate === true) {
    leverImmediate = true;
    pistonImmediate = true;
   }
  }

  applyWheel("fl", wheelData.fl);
  applyWheel("fr", wheelData.fr);
  applyWheel("rl", wheelData.rl);
  applyWheel("rr", wheelData.rr);

  if (Object.keys(leverPatch).length && rigAnimation && typeof rigAnimation.applyLeverAnglesRadians === "function") {
   try {
    rigAnimation.applyLeverAnglesRadians(leverPatch, {
     immediate: leverImmediate || params.leverAnglesImmediate === true || params.wheelsImmediate === true
    });
   } catch (err) {
    console.warn("applyLeverAnglesRadians failed", err);
   }
   pythonLeverAnglesActive = true;
   pythonLeverAnglesTimeout.restart();
  }

  if (Object.keys(pistonPatch).length && rigAnimation && typeof rigAnimation.applyPistonPositions === "function") {
   try {
    rigAnimation.applyPistonPositions(pistonPatch, {
     immediate: pistonImmediate || params.pistonImmediate === true || params.wheelsImmediate === true
    });
   } catch (err) {
    console.warn("applyPistonPositions failed", err);
   }
   pythonPistonsActive = true;
   pythonPistonsTimeout.restart();
  }
 }
 if (isPlainObject(params.reflectionProbe)) {
  var rp = params.reflectionProbe;
  if (rp.enabled !== undefined)
   reflectionProbeEnabled = !!rp.enabled;
  if (rp.padding !== undefined)
   reflectionProbePaddingM = sanitizeReflectionProbePadding(rp.padding);
  if (rp.quality !== undefined)
   reflectionProbeQualityValue = reflectionProbeQualityFrom(rp.quality);
  if (rp.refreshMode !== undefined)
   reflectionProbeRefreshModeValue = reflectionProbeRefreshModeFrom(rp.refreshMode);
  if (rp.timeSlicing !== undefined)
   reflectionProbeTimeSlicingValue = reflectionProbeTimeSlicingFrom(rp.timeSlicing);
 }
 if (!pythonLeverAnglesActive) {
  updateFallbackAngles();
  }
 return changed;
 } catch (error) {
  console.error("[SimulationRoot] apply3DUpdates failed", error);
  return false;
 }
 }

    function applyRenderSettings(params) {
        if (!params)
            return false;

        var changed = false;
        try {
            if (params && Object.keys(params).length)
                changed = true;

        if (params.environment)
            sceneEnvCtl.applyEnvironmentPayload(params.environment);
        if (params.effects)
            sceneEnvCtl.applyEffectsPayload(params.effects);
        if (params.quality)
            applyQualityUpdates(params.quality);
        if (params.camera)
            applyCameraUpdates(params.camera);
        if (params.animation)
            root.applyAnimationUpdates(params.animation);
        if (params.threeD)
            root.apply3DUpdates(params.threeD);

        var environmentPatch = {};
        if (params.backgroundColor !== undefined)
            environmentPatch.backgroundColor = params.backgroundColor;
        var requestedTonemapMode = params.tonemapModeName || params.tonemap_mode;
        if (requestedTonemapMode !== undefined)
            environmentPatch.tonemapModeName = String(requestedTonemapMode);

        var tonemapToggle = null;
        if (params.tonemapEnabled !== undefined)
            tonemapToggle = !!params.tonemapEnabled;
        if (params.tonemapActive !== undefined)
            tonemapToggle = !!params.tonemapActive;
        if (tonemapToggle !== null) {
            environmentPatch.tonemapActive = tonemapToggle;
            if (!tonemapToggle) {
                environmentPatch.tonemapModeName = 'none';
            } else if (environmentPatch.tonemapModeName === undefined) {
                var restoredMode = sceneEnvCtl.tonemapStoredModeName || sceneEnvCtl.tonemapModeName || 'filmic';
                environmentPatch.tonemapModeName = restoredMode;
            }
        }
        if (params.tonemapExposure !== undefined)
            environmentPatch.tonemapExposure = Number(params.tonemapExposure);
        if (params.tonemapWhitePoint !== undefined)
            environmentPatch.tonemapWhitePoint = Number(params.tonemapWhitePoint);
        if (params.fogEnabled !== undefined)
            environmentPatch.fogEnabled = !!params.fogEnabled;
        if (params.fogColor)
            environmentPatch.fogColor = params.fogColor;
        if (params.fogNear !== undefined)
            environmentPatch.fogNear = Number(params.fogNear);
        if (params.fogFar !== undefined)
            environmentPatch.fogFar = Number(params.fogFar);

        if (Object.keys(environmentPatch).length)
            sceneEnvCtl.applyEnvironmentPayload(environmentPatch);

        var qualityPatch = {};
        if (params.aaPrimaryMode)
            qualityPatch.aaPrimaryMode = String(params.aaPrimaryMode);
        if (params.aaQualityLevel)
            qualityPatch.aaQualityLevel = String(params.aaQualityLevel);
        if (params.aaPostMode)
            qualityPatch.aaPostMode = String(params.aaPostMode);
        if (params.taaEnabled !== undefined)
            qualityPatch.taaEnabled = !!params.taaEnabled;
        if (params.taaStrength !== undefined)
            qualityPatch.taaStrength = Number(params.taaStrength);
        if (params.taaMotionAdaptive !== undefined)
            qualityPatch.taaMotionAdaptive = !!params.taaMotionAdaptive;
        if (params.fxaaEnabled !== undefined)
            qualityPatch.fxaaEnabled = !!params.fxaaEnabled;
        if (params.specularAAEnabled !== undefined)
            qualityPatch.specularAAEnabled = !!params.specularAAEnabled;
        if (params.ditheringEnabled !== undefined)
            qualityPatch.ditheringEnabled = !!params.ditheringEnabled;

        if (Object.keys(qualityPatch).length)
            applyQualityUpdates(qualityPatch);

        if (params.cameraIsMoving !== undefined)
            sceneEnvCtl.cameraIsMoving = !!params.cameraIsMoving;

        var viewTargets = params.view3D || params.view3d || params.view;
        if (viewTargets) {
            for (var key in viewTargets) {
                if (!viewTargets.hasOwnProperty(key))
                    continue;
                setIfExists(sceneView, key, viewTargets[key]);
            }
        }

        if (params.environmentController) {
            var envDirect = params.environmentController;
            for (var envKey in envDirect) {
                if (!envDirect.hasOwnProperty(envKey))
                    continue;
                setIfExists(sceneEnvCtl, envKey, envDirect[envKey]);
            }
        }

        var directRenderScale = valueForKeys(params, ['renderScale', 'render_scale']);
        if (directRenderScale !== undefined) {
            var directScaleNumeric = Number(directRenderScale);
            if (isFinite(directScaleNumeric))
                renderScale = Math.max(0.1, directScaleNumeric);
        }

        var directFrameLimit = valueForKeys(params, ['frameRateLimit', 'frame_rate_limit']);
        if (directFrameLimit !== undefined) {
            var directFrameNumeric = Number(directFrameLimit);
            if (isFinite(directFrameNumeric))
                frameRateLimit = Math.max(0, directFrameNumeric);
        }

        var directRenderPolicy = valueForKeys(params, ['renderPolicy', 'render_policy']);
        if (directRenderPolicy !== undefined)
            renderPolicyKey = normalizeRenderPolicyKey(directRenderPolicy);
        return changed;
    } catch (error) {
        console.error("[SimulationRoot] applyRenderSettings failed", error);
        return false;
    }
    }

    function applySimulationUpdates(params) {
        if (!params)
            return false;

        var changed = false;
        try {
            if (params && Object.keys(params).length)
                changed = true;

        if (params.animation)
            applyAnimationUpdates(params.animation);

        var directAnimationPatch = {};
        var animationKeys = [
            "isRunning",
            "simulationTime",
            "amplitude",
            "frequency",
            "phase_global",
            "phase_fl",
            "phase_fr",
            "phase_rl",
            "phase_rr",
            "frame",
            "leverAngles",
            "pistonPositions",
            "linePressures",
            "tankPressure",
        ];

        for (var i = 0; i < animationKeys.length; ++i) {
            var key = animationKeys[i];
            if (params[key] !== undefined)
                directAnimationPatch[key] = params[key];
        }

        if (Object.keys(directAnimationPatch).length)
            root.applyAnimationUpdates(directAnimationPatch);

        if (params.threeD)
            root.apply3DUpdates(params.threeD);

        if (params.environment)
            root.applyEnvironmentUpdates(params.environment);

        if (params.effects)
            root.applyEffectsUpdates(params.effects);

        if (params.quality)
            root.applyQualityUpdates(params.quality);

        if (params.camera)
            root.applyCameraUpdates(params.camera);

        if (params.render)
            root.applyRenderSettings(params.render);
        return changed;
    } catch (error) {
        console.error("[SimulationRoot] applySimulationUpdates failed", error);
        return false;
    }
    }

    // -----------------------------------------------------------------
    // Legacy compatibility shims (update* aliases)
    // -----------------------------------------------------------------
    function updateGeometry(params) {
        applyGeometryUpdatesInternal(params)
    }

    function updateAnimation(params) {
        root.applyAnimationUpdates(params)
    }

    function updateLighting(params) {
        root.applyLightingUpdates(params)
    }

    function updateMaterials(params) {
        root.applyMaterialUpdates(params)
    }

    function updateEnvironment(params) {
        root.applyEnvironmentUpdates(params)
    }

    function updateQuality(params) {
        root.applyQualityUpdates(params)
    }

    function updateCamera(params) {
        root.applyCameraUpdates(params)
    }

    function updateEffects(params) {
        params = coerceBatchObject("effects", params);
        if (!params)
            return false;
        return applyEffectsUpdatesInternal(params);
    }
}

}
