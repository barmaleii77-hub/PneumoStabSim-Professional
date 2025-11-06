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
import scene 1.0 as Scene
import "../animation"
import "../diagnostics/LogBridge.js" as Diagnostics

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
    property var postEffects: null
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

    function diagnosticsWindow() {
        return typeof window !== "undefined" && window ? window : null
    }

    function forwardShaderDiagnostics(eventType, effectId, message) {
        if (!Diagnostics || typeof Diagnostics.forward !== "function")
            return

        var normalizedId = effectId !== undefined && effectId !== null
                ? String(effectId)
                : "unknown"
        var normalizedMessage = message !== undefined && message !== null
                ? String(message)
                : ""

        var label = normalizedId
        if (normalizedMessage.length)
            label = normalizedId + ": " + normalizedMessage

        try {
            Diagnostics.forward(eventType, label, diagnosticsWindow(), "SimulationRoot")
        } catch (error) {
            console.warn("[SimulationRoot] Diagnostics forwarding failed", error)
        }
    }

    function registerShaderWarning(effectId, message) {
        var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
        var normalizedMessage = message !== undefined && message !== null ? String(message) : ""

        forwardShaderDiagnostics("shader_warning", normalizedId, normalizedMessage)

        if (!sceneBridge)
            return

        var bridgeId = effectId !== undefined && effectId !== null ? effectId : normalizedId
        var bridgeMessage = message !== undefined && message !== null ? message : normalizedMessage

        try {
            if (typeof sceneBridge.registerShaderWarning === "function")
                sceneBridge.registerShaderWarning(bridgeId, bridgeMessage)
        } catch (error) {
            console.debug("[SimulationRoot] sceneBridge.registerShaderWarning failed", error)
        }
    }

    function clearShaderWarning(effectId) {
        var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"

        forwardShaderDiagnostics("shader_warning_cleared", normalizedId, "")

        if (!sceneBridge)
            return

        var bridgeId = effectId !== undefined && effectId !== null ? effectId : normalizedId

        try {
            if (typeof sceneBridge.clearShaderWarning === "function")
                sceneBridge.clearShaderWarning(bridgeId)
        } catch (error) {
            console.debug("[SimulationRoot] sceneBridge.clearShaderWarning failed", error)
        }
    }

    Connections {
        id: postEffectsSignals
        target: root.postEffects
        enabled: !!target

        function onEffectCompilationError(effectId, status, message) {
            var resolvedMessage = message

            if (resolvedMessage === undefined || resolvedMessage === null || resolvedMessage === "") {
                if (typeof status === "string") {
                    resolvedMessage = status
                } else if (status === true) {
                    resolvedMessage = "Compilation failed"
                }
            }

            registerShaderWarning(effectId, resolvedMessage)
        }

        function onEffectCompilationRecovered(effectId, _) {
            clearShaderWarning(effectId)
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

}

