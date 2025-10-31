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
import "../scene"
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

 // ---------------------------------------------
 // Свойства и сигнал для батч-обновлений из Python
 // ---------------------------------------------
 property var pendingPythonUpdates: null
signal batchUpdatesApplied(var summary)
signal animationToggled(bool running)

 // Состояние симуляции, управляется из Python (MainWindow)
 property bool isRunning: animationDefaults && animationDefaults.is_running !== undefined ? Boolean(animationDefaults.is_running) : false
 property var animationDefaults: typeof initialAnimationSettings !== "undefined" ? initialAnimationSettings : null
 property var sceneDefaults: typeof initialSceneSettings !== "undefined" ? initialSceneSettings : null
 property var geometryDefaults: typeof initialGeometrySettings !== "undefined" ? initialGeometrySettings : null
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
 property bool fallbackEnabled: isRunning && !pythonAnimationActive
 property real fallbackPhase: 0.0
 property real lastFallbackPhase: 0.0
 property real fallbackBaseTime: animationTime
 readonly property real fallbackCycleSeconds: Math.max(0.2, 1.0 / Math.max(userFrequency, 0.01))
 property real batchFlashOpacity: 0.0

 readonly property real defaultDofFocusDistanceM: effectsDefaultNumber(["dof_focus_distance"], 2.5)

 property bool reflectionProbeEnabled: true
 // Padding stored in metres; converted to scene units where required
 property real reflectionProbePaddingM: 0.15
 property int reflectionProbeQualityValue: ReflectionProbe.VeryHigh
 property int reflectionProbeRefreshModeValue: ReflectionProbe.EveryFrame
 property int reflectionProbeTimeSlicingValue: ReflectionProbe.IndividualFaces

 property bool signalTraceOverlayVisible: false
 property bool signalTraceRecordingEnabled: false
 property int signalTraceHistoryLimit: 200
 property bool signalTracePanelExpanded: false
 property var signalTraceHistory: []
 property bool _signalTraceSyncing: false
 property var shaderWarningMap: ({})
 property var shaderWarningList: []

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

 property var lightingState: ({
 key: {},
 fill: {},
 rim: {},
 point: {},
 spot: {},
 global: {}
 })

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

 onBatchUpdatesApplied: {
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
    var defaults = geometryDefaults || {}
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
 }

IblProbeLoader {
 id: iblLoader
 objectName: "iblProbeLoader"
 visible: false
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
        onEffectCompilationError: registerShaderWarning(effectId, errorLog)
        onEffectCompilationRecovered: clearShaderWarning(effectId)
    }

    View3D {
        id: sceneView
        anchors.fill: parent
        environment: sceneEnvCtl

        SharedMaterials {
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
    shadowsEnabled: !!root.lightingGlobal("shadows_enabled", root.lightingGlobal("shadowsEnabled", true))
    shadowResolution: {
        var raw = root.lightingGlobal(
                    "shadow_resolution",
                    root.lightingGlobal("shadowResolution", 4096)
                )
        var numeric = Number(raw)
        return isFinite(numeric) ? Math.round(numeric) : 4096
    }
 shadowFilterSamples: Number(root.lightingGlobal("shadow_filter_samples", root.lightingGlobal("shadowFilterSamples",32)))
 shadowBias: Number(root.lightingGlobal("shadow_bias", root.lightingGlobal("shadowBias",8.0)))
 shadowFactor: Number(root.lightingGlobal("shadow_factor", root.lightingGlobal("shadowFactor",80.0)))

 keyLightBrightness: Number(root.lightingValue("key", "brightness",1.0))
 keyLightColor: root.lightingValue("key", "color", "#ffffff")
 keyLightAngleX: Number(root.lightingValue("key", "angle_x", 25.0))
 keyLightAngleY: Number(root.lightingValue("key", "angle_y", 23.5))
 keyLightAngleZ: Number(root.lightingValue("key", "angle_z",0.0))
 keyLightCastsShadow: !!root.lightingValue("key", "cast_shadow", true)
 keyLightBindToCamera: !!root.lightingValue("key", "bind_to_camera", false)
 keyLightPosX: Number(root.lightingValue("key", "position_x",0))
 keyLightPosY: Number(root.lightingValue("key", "position_y",0))
 keyLightPosZ: Number(root.lightingValue("key", "position_z",0))

 fillLightBrightness: Number(root.lightingValue("fill", "brightness",1.0))
 fillLightColor: root.lightingValue("fill", "color", "#f1f4ff")
 fillLightAngleX: Number(root.lightingValue("fill", "angle_x", 0.0))
 fillLightAngleY: Number(root.lightingValue("fill", "angle_y", -45.0))
 fillLightAngleZ: Number(root.lightingValue("fill", "angle_z",0.0))
 fillLightCastsShadow: !!root.lightingValue("fill", "cast_shadow", false)
 fillLightBindToCamera: !!root.lightingValue("fill", "bind_to_camera", false)
 fillLightPosX: Number(root.lightingValue("fill", "position_x",0))
 fillLightPosY: Number(root.lightingValue("fill", "position_y",0))
 fillLightPosZ: Number(root.lightingValue("fill", "position_z",0))

 rimLightBrightness: Number(root.lightingValue("rim", "brightness",1.1))
 rimLightColor: root.lightingValue("rim", "color", "#ffe1bd")
 rimLightAngleX: Number(root.lightingValue("rim", "angle_x",30.0))
 rimLightAngleY: Number(root.lightingValue("rim", "angle_y",-135.0))
 rimLightAngleZ: Number(root.lightingValue("rim", "angle_z",0.0))
 rimLightCastsShadow: !!root.lightingValue("rim", "cast_shadow", false)
 rimLightBindToCamera: !!root.lightingValue("rim", "bind_to_camera", false)
 rimLightPosX: Number(root.lightingValue("rim", "position_x",0))
 rimLightPosY: Number(root.lightingValue("rim", "position_y",0))
 rimLightPosZ: Number(root.lightingValue("rim", "position_z",0))
 }

 PointLights {
 id: pointLights
 worldRoot: worldRoot
 cameraRig: cameraController.rig
 pointLightBrightness: Number(root.lightingValue("point", "brightness",50.0))
 pointLightColor: root.lightingValue("point", "color", "#fff7e0")
 pointLightX: Number(root.lightingValue("point", "position_x",0.0))
 pointLightY: Number(root.lightingValue("point", "position_y",2.6))
 pointLightZ: Number(root.lightingValue("point", "position_z",1.5))
 pointLightRange: Number(root.lightingValue("point", "range",3.6))
 constantFade: Number(root.lightingValue("point", "constant_fade",1.0))
 linearFade: Number(root.lightingValue("point", "linear_fade",0.01))
 quadraticFade: Number(root.lightingValue("point", "quadratic_fade",1.0))
 pointLightCastsShadow: !!root.lightingValue("point", "cast_shadow", false)
 pointLightBindToCamera: !!root.lightingValue("point", "bind_to_camera", false)
 }

 SuspensionAssembly {
  id: suspensionAssembly
  worldRoot: worldRoot
  geometryState: geometryState
  geometryDefaults: geometryDefaults || ({})
  materialsDefaults: sceneDefaults && sceneDefaults.materials ? sceneDefaults.materials : ({})
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
    target: sceneView
    property: "clearColor"
    value: sceneEnvCtl.resolvedClearColor
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
 function applySceneBridgeState() {
 if (!sceneBridge)
 return

 if (sceneBridge.geometry && Object.keys(sceneBridge.geometry).length)
            root.applyGeometryUpdates(sceneBridge.geometry)
 if (sceneBridge.camera && Object.keys(sceneBridge.camera).length)
 root.applyCameraUpdates(sceneBridge.camera)
 if (sceneBridge.lighting && Object.keys(sceneBridge.lighting).length)
 root.applyLightingUpdates(sceneBridge.lighting)
 if (sceneBridge.environment && Object.keys(sceneBridge.environment).length)
 root.applyEnvironmentUpdates(sceneBridge.environment)
 if (sceneBridge.quality && Object.keys(sceneBridge.quality).length)
 root.applyQualityUpdates(sceneBridge.quality)
 if (sceneBridge.materials && Object.keys(sceneBridge.materials).length)
 root.applyMaterialUpdates(sceneBridge.materials)
 if (sceneBridge.effects && Object.keys(sceneBridge.effects).length)
 root.applyEffectsUpdates(sceneBridge.effects)
 if (sceneBridge.animation && Object.keys(sceneBridge.animation).length)
 root.applyAnimationUpdates(sceneBridge.animation)
 if (sceneBridge.threeD && Object.keys(sceneBridge.threeD).length)
 root.apply3DUpdates(sceneBridge.threeD)
 if (sceneBridge.render && Object.keys(sceneBridge.render).length)
 root.applyRenderSettings(sceneBridge.render)
 if (sceneBridge.simulation && Object.keys(sceneBridge.simulation).length)
 root.applySimulationUpdates(sceneBridge.simulation)

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

    function onGeometryChanged(payload) {
        if (!payload)
            return
        root.applyGeometryUpdates(payload)
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
        root.applyGeometryUpdates(geometryDefaults)
  }
  applySceneBridgeState()
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
   if (typeof window !== "undefined" && window && window.applyQmlConfigChange) {
    window.applyQmlConfigChange("diagnostics.signal_trace", { overlay_enabled: enabled })
   }
  }

  onRecordingToggled: function(enabled) {
   if (_signalTraceSyncing)
    return
   signalTraceRecordingEnabled = enabled
   if (typeof window !== "undefined" && window && window.applyQmlConfigChange) {
    window.applyQmlConfigChange("diagnostics.signal_trace", { enabled: enabled })
   }
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

function registerShaderWarning(effectId, errorLog) {
 var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
 var message = errorLog !== undefined && errorLog !== null ? String(errorLog) : qsTr("Shader compilation failed")
 var nextMap = Object.assign({}, shaderWarningMap)
 nextMap[normalizedId] = {
  id: normalizedId,
  message: message,
  timestamp: Date.now()
 }
 shaderWarningMap = nextMap
 shaderWarningList = Object.values(nextMap).sort(function(a, b) { return a.timestamp - b.timestamp })
 console.warn("⚠️ Shader fallback activated for", normalizedId, "-", message)
}

function clearShaderWarning(effectId) {
 var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
 if (!shaderWarningMap.hasOwnProperty(normalizedId))
  return
 var nextMap = Object.assign({}, shaderWarningMap)
 delete nextMap[normalizedId]
 shaderWarningMap = nextMap
 shaderWarningList = Object.values(nextMap).sort(function(a, b) { return a.timestamp - b.timestamp })
 console.log("✅ Shader restored for", normalizedId)
}

function setIfExists(obj, prop, value) {
try {
if (obj && (prop in obj || typeof obj[prop] !== 'undefined')) {
obj[prop] = value;
}
} catch (e) {
console.warn("setIfExists failed", prop, e);
}
}

function valueForKeys(map, keys) {
    if (!map)
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
 var state = lightingState && lightingState[group];
 if (state && state[key] !== undefined)
 return state[key];
 return fallback;
 }

 function lightingGlobal(key, fallback) {
 var state = lightingState && lightingState.global;
 if (state) {
 if (state[key] !== undefined)
 return state[key];
 var alt = key.indexOf("_") >=0
 ? key.replace(/_([a-z])/g, function(_, ch) { return ch.toUpperCase(); })
 : key.replace(/[A-Z]/g, function(ch) { return "_" + ch.toLowerCase(); });
 if (state[alt] !== undefined)
 return state[alt];
 }
 return fallback;
 }

    // ---------------------------------------------
    // Применение батч-обновлений из Python
    // ---------------------------------------------
    Connections {
        target: root
        function onPendingPythonUpdatesChanged() {
            // fixed: apply incoming UI updates immediately for instant redraw
            if (!root.pendingPythonUpdates)
                return;
            try {
                root.applyBatchedUpdates(root.pendingPythonUpdates);
            } finally {
                root.pendingPythonUpdates = null; // очистка после применения
            }
        }
    }

 function applyBatchedUpdates(updates) {
 if (!updates)
 return;
 var applied = {};
    if (updates.geometry) {
        root.applyGeometryUpdates(updates.geometry)
        applied.geometry = true
    }
 if (updates.camera) { root.applyCameraUpdates(updates.camera); applied.camera = true; }
 if (updates.lighting) { root.applyLightingUpdates(updates.lighting); applied.lighting = true; }
 if (updates.environment){ root.applyEnvironmentUpdates(updates.environment); applied.environment = true; }
 if (updates.quality) { root.applyQualityUpdates(updates.quality); applied.quality = true; }
 if (updates.materials) { root.applyMaterialUpdates(updates.materials); applied.materials = true; }
 if (updates.effects) { root.applyEffectsUpdates(updates.effects); applied.effects = true; }
 if (updates.animation) { root.applyAnimationUpdates(updates.animation); applied.animation = true; }
 if (updates.threeD) { root.apply3DUpdates(updates.threeD); applied.threeD = true; }
 if (updates.render) { root.applyRenderSettings(updates.render); applied.render = true; }
 if (updates.simulation) { root.applySimulationUpdates(updates.simulation); applied.simulation = true; }

 batchUpdatesApplied(applied);
 }

 // ---------------------------------------------
 // Реализации apply*Updates (минимально: geometry, camera, lighting, environment, quality, materials, effects, animation,3d)
 // ---------------------------------------------
 function applyGeometryUpdates(params) {
 if (!params) return;
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
 updateGeometryState(geometryPatch);

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

 if (Object.keys(cameraGeometryUpdate).length)
     cameraController.updateGeometry(cameraGeometryUpdate);
    }
}

 function applyCameraUpdates(params) {
 if (!params)
  return;

 var controllerHandled = false;
 if (cameraController && cameraController.applyCameraUpdates) {
  try {
   cameraController.applyCameraUpdates(params);
   controllerHandled = true;
  } catch (err) {
   console.warn("CameraController.applyCameraUpdates failed:", err);
  }
 }

 if (controllerHandled)
  return;

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
 if (!params)
 return;

 function normalizeGroupPayload(payload) {
 if (!payload)
 return payload;
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
 if (!updates || typeof updates !== "object")
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
 if (params[key] !== undefined)
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
 if (params[alias] !== undefined)
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
 if (typeof value === "object" && value !== null) {
 var targetState = lightingState[remainingKey];
 next[remainingKey] = mergeLightingGroup(cloneObject(targetState), normalizeGroupPayload(value));
 } else {
 globalPatch[remainingKey] = value;
 }
 }

 if (Object.keys(globalPatch).length)
 next.global = mergeLightingGroup(next.global, globalPatch);

 lightingState = next;
 }

 function applyEnvironmentUpdates(params) {
 if (!params) return;
 var bgColorVal = valueForKeys(params, ['backgroundColor', 'background_color']);
 if (bgColorVal !== undefined) setIfExists(sceneEnvCtl, 'backgroundColor', bgColorVal);
 if (params.clearColor) setIfExists(sceneEnvCtl, 'backgroundColor', params.clearColor);
 if (params.background && params.background.color) setIfExists(sceneEnvCtl, 'backgroundColor', params.background.color);

    var backgroundModeVal = valueForKeys(params, ['backgroundMode', 'background_mode']);
    if (backgroundModeVal !== undefined) setIfExists(sceneEnvCtl, 'backgroundModeKey', String(backgroundModeVal));

    var skyboxFlagRaw = valueForKeys(
        params,
        ['iblBackgroundEnabled', 'ibl_background_enabled', 'skyboxEnabled', 'skybox_enabled']
    );
    if (skyboxFlagRaw !== undefined)
        setIfExists(sceneEnvCtl, 'skyboxToggleFlag', !!skyboxFlagRaw);

    var currentSkyboxState = false;
    if (sceneEnvCtl && sceneEnvCtl.skyboxToggleFlag !== undefined)
        currentSkyboxState = !!sceneEnvCtl.skyboxToggleFlag;
    var resolvedSkybox = skyboxFlagRaw !== undefined ? !!skyboxFlagRaw : currentSkyboxState;

    var iblEnabledRaw = valueForKeys(params, ['iblEnabled', 'ibl_enabled']);
    var iblLightingRaw = valueForKeys(params, ['iblLightingEnabled', 'ibl_lighting_enabled']);

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
    if (params.ibl && typeof params.ibl === 'object') {
        nestedSkyboxBrightnessProvided = valueForKeys(
            params.ibl,
            ['skyboxBrightness', 'skybox_brightness']
        ) !== undefined;
        nestedProbeBrightnessProvided = valueForKeys(
            params.ibl,
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
    if (skyboxBrightnessVal !== undefined) {
        var numericSkyboxBrightness = Number(skyboxBrightnessVal);
        if (isFinite(numericSkyboxBrightness)) {
            setIfExists(sceneEnvCtl, 'skyboxBrightnessValue', numericSkyboxBrightness);
        }
    }

 var probeHorizonVal = valueForKeys(params, ['probeHorizon', 'probe_horizon']);
 if (probeHorizonVal !== undefined) {
     var numericHorizon = Number(probeHorizonVal);
     if (isFinite(numericHorizon)) setIfExists(sceneEnvCtl, 'probeHorizonValue', numericHorizon);
 }

 var rotationYawVal = valueForKeys(params, ['iblRotationDeg', 'ibl_rotation']);
 if (rotationYawVal !== undefined) {
     var numericYaw = Number(rotationYawVal);
     if (isFinite(numericYaw)) setIfExists(sceneEnvCtl, 'iblRotationDeg', numericYaw);
 }

 var rotationPitchVal = valueForKeys(params, ['iblRotationPitchDeg', 'ibl_offset_x']);
 if (rotationPitchVal !== undefined) {
     var numericPitch = Number(rotationPitchVal);
     if (isFinite(numericPitch)) setIfExists(sceneEnvCtl, 'iblRotationPitchDeg', numericPitch);
 }

 var rotationRollVal = valueForKeys(params, ['iblRotationRollDeg', 'ibl_offset_y']);
 if (rotationRollVal !== undefined) {
     var numericRoll = Number(rotationRollVal);
     if (isFinite(numericRoll)) setIfExists(sceneEnvCtl, 'iblRotationRollDeg', numericRoll);
 }

 var bindCameraVal = valueForKeys(params, ['iblBindToCamera', 'ibl_bind_to_camera']);
 if (bindCameraVal !== undefined) setIfExists(sceneEnvCtl, 'iblBindToCamera', !!bindCameraVal);

 var skyboxBlurVal = valueForKeys(params, ['skyboxBlur', 'skybox_blur']);
 if (skyboxBlurVal !== undefined) {
     var numericBlur = Number(skyboxBlurVal);
     if (isFinite(numericBlur)) setIfExists(sceneEnvCtl, 'skyboxBlurValue', numericBlur);
 }
 if (params.iblPrimary || params.hdrSource || params.iblSource) { var src = params.iblPrimary || params.hdrSource || params.iblSource; if (typeof window !== 'undefined' && window && typeof window.normalizeHdrPath === 'function') { try { src = window.normalizeHdrPath(String(src)); } catch(e) { console.warn("HDR path normalization failed:", e); } } setIfExists(iblLoader, 'primarySource', src); }
 if (params.tonemapEnabled !== undefined) {
     var tonemapEnabledFlag = !!params.tonemapEnabled;
     setIfExists(sceneEnvCtl, 'tonemapActive', tonemapEnabledFlag);
     if (!tonemapEnabledFlag) {
         setIfExists(sceneEnvCtl, 'tonemapModeName', 'none');
     } else if (!params.tonemapModeName && !params.tonemap_mode) {
         var storedMode = sceneEnvCtl.tonemapStoredModeName || sceneEnvCtl.tonemapModeName || 'filmic';
         setIfExists(sceneEnvCtl, 'tonemapModeName', storedMode);
     }
 }
 if (params.tonemapActive !== undefined) {
     var tonemapActiveFlag = !!params.tonemapActive;
     setIfExists(sceneEnvCtl, 'tonemapActive', tonemapActiveFlag);
     if (!tonemapActiveFlag) {
         setIfExists(sceneEnvCtl, 'tonemapModeName', 'none');
     } else if (!params.tonemapModeName && !params.tonemap_mode) {
         var activeStored = sceneEnvCtl.tonemapStoredModeName || sceneEnvCtl.tonemapModeName || 'filmic';
         setIfExists(sceneEnvCtl, 'tonemapModeName', activeStored);
     }
 }
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
        if (!params)
            return;

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

 var shadowSource = null;
 if (params.shadowSettings && typeof params.shadowSettings === "object")
  shadowSource = params.shadowSettings;
 else if (params.shadows && typeof params.shadows === "object")
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

 var qualityPatch = {};
 var aaSource = (params.antialiasing && typeof params.antialiasing === "object") ? params.antialiasing : null;

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

 if (Object.keys(qualityPatch).length)
  sceneEnvCtl.applyQualityPayload(qualityPatch);
 }

 function applyMaterialUpdates(params) {
 if (!params)
 return;

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
 setIfExists(sharedMaterials, prefix + suffix, value);
 return true;
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
 setIfExists(sharedMaterials, "jointRodOkColor", values[key]);
 if (normalizedKey === "error_color")
 setIfExists(sharedMaterials, "jointRodErrorColor", values[key]);
 }
 }

 if (materialKey === "piston_body") {
 if (values.warning_color !== undefined)
 setIfExists(sharedMaterials, "pistonBodyWarningColor", values.warning_color);
 }
 if (materialKey === "piston_rod") {
 if (values.warning_color !== undefined)
 setIfExists(sharedMaterials, "pistonRodWarningColor", values.warning_color);
 }
 if (materialKey === "joint_rod") {
 if (values.ok_color !== undefined)
 setIfExists(sharedMaterials, "jointRodOkColor", values.ok_color);
 if (values.error_color !== undefined)
 setIfExists(sharedMaterials, "jointRodErrorColor", values.error_color);
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
 setIfExists(sharedMaterials, "jointRodOkColor", params[rawKey]);
 if (propertyPart === "error_color")
 setIfExists(sharedMaterials, "jointRodErrorColor", params[rawKey]);
 }
 }
 }

 function applyEffectsUpdates(params) {
 if (!params)
 return;
 // Делегируем контроллеру окружения для консистентности
 sceneEnvCtl.applyEffectsPayload(params);
 if (postEffects && typeof postEffects.applyPayload === "function")
 postEffects.applyPayload(params, sceneEnvCtl);
 }

function applyAnimationUpdates(params) {
 if (!params)
  return;

 if (params.isRunning !== undefined)
  isRunning = !!params.isRunning;

 if (params.simulationTime !== undefined) {
  animationTime = Number(params.simulationTime);
  pythonAnimationActive = true;
  pythonAnimationTimeout.restart();
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
 if (params.leverAngles)
  leverAnglesPayload = params.leverAngles;
 else if (params.lever_angles)
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
  if (Object.keys(anglesPayload).length) {
   rigAnimation.applyLeverAnglesRadians(anglesPayload, {
    immediate: globalImmediate || params.leverAnglesImmediate === true || leverAnglesPayload.immediate === true
   });
   pythonLeverAnglesActive = true;
   pythonLeverAnglesTimeout.restart();
  }
 }

 var pistonPayloadSource = null;
 if (params.pistonPositions)
  pistonPayloadSource = params.pistonPositions;
 else if (params.piston_positions)
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
  if (Object.keys(pistonPayload).length) {
   rigAnimation.applyPistonPositions(pistonPayload, {
    immediate: globalImmediate || params.pistonImmediate === true || pistonPayloadSource.immediate === true
   });
   pythonPistonsActive = true;
   pythonPistonsTimeout.restart();
  }
 }

 if (params.linePressures) {
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
}

function apply3DUpdates(params) {
 if (!params) return;
 var globalImmediate = params.instant === true || params.immediate === true;
 if (params.frame) {
  var f = params.frame;
  var framePayload = {};
  if (f.heave !== undefined)
   framePayload.heave = Number(f.heave);
  if (f.roll !== undefined)
   framePayload.roll = Number(f.roll);
  if (f.pitch !== undefined)
   framePayload.pitch = Number(f.pitch);
  if (Object.keys(framePayload).length) {
   rigAnimation.applyFrameMotion(framePayload, {
    immediate: globalImmediate || params.frameImmediate === true || f.immediate === true
   });
   pythonFrameActive = true;
   pythonFrameTimeout.restart();
  }
 }
 if (params.wheels) {
  var wheelData = params.wheels;
  var leverPatch = {};
  var pistonPatch = {};
  var leverImmediate = globalImmediate;
  var pistonImmediate = globalImmediate;

  function applyWheel(key, source) {
   if (!source)
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

  if (Object.keys(leverPatch).length) {
   rigAnimation.applyLeverAnglesRadians(leverPatch, {
    immediate: leverImmediate || params.leverAnglesImmediate === true || params.wheelsImmediate === true
   });
   pythonLeverAnglesActive = true;
   pythonLeverAnglesTimeout.restart();
  }

  if (Object.keys(pistonPatch).length) {
   rigAnimation.applyPistonPositions(pistonPatch, {
    immediate: pistonImmediate || params.pistonImmediate === true || params.wheelsImmediate === true
   });
   pythonPistonsActive = true;
   pythonPistonsTimeout.restart();
  }
 }
 if (params.reflectionProbe) {
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
}

    function applyRenderSettings(params) {
        if (!params)
            return;

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
    }

    function applySimulationUpdates(params) {
        if (!params)
            return;

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
    }

    // -----------------------------------------------------------------
    // Legacy compatibility shims (update* aliases)
    // -----------------------------------------------------------------
    function updateGeometry(params) {
        root.applyGeometryUpdates(params)
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
        root.applyEffectsUpdates(params)
    }
}

}
