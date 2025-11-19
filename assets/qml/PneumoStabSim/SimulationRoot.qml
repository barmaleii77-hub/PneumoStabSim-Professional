#pragma ComponentBehavior: Bound

import QtQml 6.10
import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import QtQuick3D 6.10
import QtQuick3D.Helpers 6.10
import "../camera"
import "../components"
import "../effects" as Effects
import "../geometry"
import "../lighting"
import scene 1.0 as Scene
import "../animation"
import "../diagnostics/LogBridge.js" as Diagnostics

// Восстановленная функциональная версия SimulationRoot с расширенной логикой bypass + backup
Item {
    id: root
    objectName: "simulationRoot"
    anchors.fill: parent

    // Bridge
    property var sceneBridge: null
    property var sceneSharedMaterials: null
    property var sceneDirectionalLights: null
    property var scenePointLights: null
    property var sceneFrameNode: null
    property var postEffects: null
    property var sceneView: null

    // Post-processing bypass
    property bool effectsBypassRequested: false
    property string effectsBypassReason: ""
    property bool postProcessingBypassed: false
    property string postProcessingBypassReason: ""
    property var postProcessingEffectBackup: []
    property bool _effectsBackupTaken: false

    // Simplified fallback
    property bool simpleFallbackActive: false
    property string simpleFallbackReason: ""
    signal simpleFallbackRequested(string reason)
    signal simpleFallbackRecovered()

    // Shader diagnostics
    signal shaderWarningRegistered(string effectId, string message)
    signal shaderWarningCleared(string effectId)
    signal shaderStatusDumpRequested(var payload)
    property var shaderWarningState: ({})

    // Core state mirrors
    property var geometryState: ({})
    property var simulationState: ({})
    property var materialsState: ({})
    property var previousMaterialsState: ({})
    property var threeDState: ({})
    property var flowTelemetry: ({})
    property var receiverTelemetry: ({})

    property bool geometryStateReceived: false
    property bool simulationStateReceived: false
    property int sceneBridgeDispatchCount: 0

    readonly property bool sceneBridgeAvailable: sceneBridge !== null && sceneBridge !== undefined
    readonly property bool geometryStateReady: !_isEmptyMap(geometryState)
    readonly property bool simulationStateReady: !_isEmptyMap(simulationState)

    // SSAO properties (mirrored)
    property bool ssaoEnabled: true
    property real ssaoRadius: 0.008
    property real ssaoIntensity: 1.0
    property real ssaoSoftness: 20.0
    property real ssaoBias: 0.025
    property bool ssaoDither: true
    property int ssaoSampleRate: 4

    // Batch updates
    property var pendingPythonUpdates: null
    property var lastUpdateByCategory: ({})
    signal geometryUpdatesApplied(var payload)
    signal batchUpdatesApplied(var summary)
    signal animationToggled(bool running)

    onPendingPythonUpdatesChanged: { if (!pendingPythonUpdates || typeof pendingPythonUpdates !== "object") return; try { applyBatchedUpdates(pendingPythonUpdates) } finally { pendingPythonUpdates = null } }

    // Render related state
    property real renderScale: 1.0
    property int frameRateLimit: 0
    property string renderPolicyKey: "always"
    property var renderState: ({})
    property var qualityState: ({})
    property var sceneRenderDefaults: ({})
    property var sceneQualityDefaults: ({})
    property var environmentState: ({})
    property bool fogDepthEnabled: true
    property real fogDepthNear: 2.0
    property real fogDepthFar: 20.0
    property real fogDepthCurve: 1.0
    property var effectsState: ({})
    property var cameraStateSnapshot: ({})

    // Reflection probe state
    property bool reflectionProbeDefaultsWarningIssued: false
    property list<string> reflectionProbeMissingKeys: []
    property bool reflectionProbeEnabledState: true
    property bool reflectionProbeEnabledOverrideActive: false
    property bool reflectionProbeEnabledOverride: true
    property bool reflectionProbeEnabled: reflectionProbeEnabledOverrideActive ? reflectionProbeEnabledOverride : reflectionProbeEnabledState
    property real reflectionProbePaddingM: 0.0
    property string reflectionProbeQualitySetting: "medium"
    property string reflectionProbeRefreshModeSetting: "static"
    property string reflectionProbeTimeSlicingSetting: "allfaces"

    // Scene defaults
    property real sceneScaleFactor: 1.0
    property real suspensionRodWarningThresholdM: 0.001

    // Animation flags
    property bool pythonAnimationActive: false
    property bool pythonFrameActive: false
    property bool pythonLeverAnglesActive: false
    property bool pythonPistonsActive: false
    property bool isRunning: false
    property real animationTime: 0.0
    property real batchFlashOpacity: 0.0

    // Helpers --------------------------------------------------
    function _isPlainObject(v){ return v && typeof v === 'object' && !Array.isArray(v) }
    function _cloneObject(v){ if(!_isPlainObject(v)) return ({}); var c={}; for(var k in v) if(Object.prototype.hasOwnProperty.call(v,k)) c[k]=_isPlainObject(v[k])?_cloneObject(v[k]):v[k]; return c }
    function _deepMerge(base,payload){ var r=_cloneObject(base); if(_isPlainObject(payload)) for(var k in payload) if(Object.prototype.hasOwnProperty.call(payload,k)) r[k]=_isPlainObject(payload[k])?_deepMerge(r[k],payload[k]):payload[k]; return r }
    function _normaliseState(v){ if(!v||typeof v!=="object") return ({}); var c={}; for(var k in v) if(Object.prototype.hasOwnProperty.call(v,k)) c[k]=v[k]; return c }
    function _isEmptyMap(v){ if(!v||typeof v!== "object") return true; for(var k in v) if(Object.prototype.hasOwnProperty.call(v,k)) return false; return true }
    function _storeLastUpdate(cat,payload){ var snap=_cloneObject(lastUpdateByCategory); snap[cat]= payload && typeof payload === 'object' ? _normaliseState(payload) : payload; lastUpdateByCategory = snap }
    function _ack(categories){ if(categories&&categories.length) batchFlashOpacity=1.0; batchUpdatesApplied({ timestamp: Date.now(), categories: categories.slice(), source: "python" }) }

    // Batch dispatcher ------------------------------------------
    function applyBatchedUpdates(updates){ if(!updates||typeof updates!=='object') return; var cats=[]; if(updates.geometry!==undefined){ cats.push('geometry'); applyGeometryUpdates(updates.geometry) } if(updates.animation!==undefined){ cats.push('animation'); applyAnimationUpdates(updates.animation) } if(updates.lighting!==undefined){ cats.push('lighting'); applyLightingUpdates(updates.lighting) } if(updates.materials!==undefined){ cats.push('materials'); applyMaterialUpdates(updates.materials) } if(updates.environment!==undefined){ cats.push('environment'); applyEnvironmentUpdates(updates.environment) } if(updates.scene!==undefined){ cats.push('scene'); applySceneUpdates(updates.scene) } if(updates.quality!==undefined){ cats.push('quality'); applyQualityUpdates(updates.quality) } if(updates.camera!==undefined){ cats.push('camera'); applyCameraUpdates(updates.camera) } if(updates.effects!==undefined){ cats.push('effects'); applyEffectsUpdates(updates.effects) } if(updates.render!==undefined){ cats.push('render'); applyRenderSettings(updates.render) } if(updates.simulation!==undefined){ cats.push('simulation'); applySimulationUpdates(updates.simulation) } if(updates.threeD!==undefined){ cats.push('threeD'); applyThreeDUpdates(updates.threeD) } _ack(cats) }

    // Category handlers -----------------------------------------
    function applyGeometryUpdates(p){ var n=_normaliseState(p); if(!_isEmptyMap(n)){ geometryState=_deepMerge(geometryState,n); geometryStateReceived=true } _storeLastUpdate('geometry', n); geometryUpdatesApplied(n) }
    function applySimulationUpdates(p){ var n=_normaliseState(p); if(!_isEmptyMap(n)){ simulationState=_deepMerge(simulationState,n); simulationStateReceived=true } if(n.animation) applyAnimationUpdates(n.animation); if(n.threeD) applyThreeDUpdates(n.threeD); _storeLastUpdate('simulation', n) }
    function applyAnimationUpdates(p){ var d=p||{}; var prev=isRunning; function _num(v,f){ if(v===undefined||v===null) return f; var c=Number(v); return isNaN(c)?f:c } function _bool(v,f){ if(v===undefined||v===null) return f; return !!v } animationTime=_num(d.animation_time, animationTime); animationTime=_num(d.animationTime, animationTime); isRunning=_bool(d.is_running, isRunning); isRunning=_bool(d.isRunning, isRunning); pythonAnimationActive=_bool(d.python_driven, pythonAnimationActive); pythonAnimationActive=_bool(d.pythonDriven, pythonAnimationActive); if(isRunning!==prev) animationToggled(isRunning); _storeLastUpdate('animation', d) }
    function applyLightingUpdates(p){ _storeLastUpdate('lighting', _normaliseState(p)) }
    function applyMaterialUpdates(p){ var n=_normaliseState(p); previousMaterialsState=_cloneObject(materialsState); materialsState=_deepMerge(materialsState,n); _storeLastUpdate('materials', n); return materialsState }
    function applyEnvironmentUpdates(p){ var n=_normaliseState(p); var base=environmentState&&typeof environmentState==='object'? environmentState : {}; var merged={}; for(var bk in base) if(Object.prototype.hasOwnProperty.call(base,bk)) merged[bk]=base[bk]; for(var nk in n) if(Object.prototype.hasOwnProperty.call(nk)) merged[nk]=n[nk]; environmentState = Object.keys(base).length===0 ? p : merged; if(n.reflection_enabled!==undefined) { envController.reflectionProbeEnabled=!!n.reflection_enabled; _applyReflectionProbeEnabledOverride(n.reflection_enabled) } _storeLastUpdate('environment', n); _refreshReflectionProbeObject() }
    function applySceneUpdates(p){ _storeLastUpdate('scene', p||{}) }
    function applyQualityUpdates(p){ var n=_normaliseState(p); qualityState=_deepMerge(qualityState,n); _syncRenderSettingsState(); _storeLastUpdate('quality', n) }
    function applyCameraUpdates(p){ var n=_normaliseState(p); cameraStateSnapshot=_deepMerge(cameraStateSnapshot,n); _storeLastUpdate('camera', n) }
    function applyEffectsUpdates(p){ var n=_normaliseState(p); effectsState=_deepMerge(effectsState,n); if(n.effects_bypass!==undefined) _applyEffectsBypassOverride(n.effects_bypass, n.effects_bypass_reason); else if(n.effects_bypass_reason!==undefined) _applyEffectsBypassOverride(effectsBypassRequested, n.effects_bypass_reason); _storeLastUpdate('effects', n) }
    function rollbackMaterials(){ if(_isEmptyMap(previousMaterialsState)) return materialsState; materialsState=_cloneObject(previousMaterialsState); _storeLastUpdate('materials', materialsState); return materialsState }
    function applyRenderSettings(p){ var d=p||{}; if(d.environment) applyEnvironmentUpdates(d.environment); if(d.quality) applyQualityUpdates(d.quality); if(d.effects) applyEffectsUpdates(d.effects); if(d.camera) applyCameraUpdates(d.camera); var direct=_normaliseState(d.render); if(!_isEmptyMap(direct)) renderState=_deepMerge(renderState,direct); _syncRenderSettingsState(); _storeLastUpdate('render', d) }
    function applyThreeDUpdates(p){ var n=_normaliseState(p); threeDState=_deepMerge(threeDState,n); flowTelemetry=_normaliseState(n.flowNetwork||n.flownetwork); receiverTelemetry=_resolveReceiverTelemetry(n); var reflectionNode=n.reflectionProbe||n.reflection_probe||n.reflection; if(_isPlainObject(reflectionNode)){ if(reflectionNode.enabled!==undefined) _applyReflectionProbeEnabledOverride(reflectionNode.enabled); if(reflectionNode.padding!==undefined) reflectionProbePaddingM = sanitizeReflectionProbePadding(reflectionNode.padding); if(reflectionNode.quality!==undefined) reflectionProbeQualitySetting=String(reflectionNode.quality).toLowerCase(); if(reflectionNode.refreshMode||reflectionNode.refresh_mode) reflectionProbeRefreshModeSetting=String(reflectionNode.refreshMode||reflectionNode.refresh_mode).toLowerCase(); if(reflectionNode.timeSlicing||reflectionNode.time_slicing) reflectionProbeTimeSlicingSetting=String(reflectionNode.timeSlicing||reflectionNode.time_slicing).toLowerCase() } _storeLastUpdate('threeD', n); _refreshReflectionProbeObject() }
    function apply3DUpdates(p){ applyThreeDUpdates(p) }

    // Legacy aliases
    function updateGeometry(p){ applyGeometryUpdates(p) }
    function updateAnimation(p){ applyAnimationUpdates(p) }
    function updateLighting(p){ applyLightingUpdates(p) }
    function updateMaterials(p){ applyMaterialUpdates(p) }
    function updateEnvironment(p){ applyEnvironmentUpdates(p) }
    function updateScene(p){ applySceneUpdates(p) }
    function updateQuality(p){ applyQualityUpdates(p) }
    function updateCamera(p){ applyCameraUpdates(p) }
    function updateEffects(p){ applyEffectsUpdates(p) }
    function updateRender(p){ applyRenderSettings(p) }
    function updateThreeD(p){ applyThreeDUpdates(p) }

    // Render sync ------------------------------------------------
    function _renderSources(){ return [renderState||({}), qualityState||({}), sceneRenderDefaults||({}), sceneQualityDefaults||({})] }
    function _syncRenderSettingsState(){ var sources=_renderSources(); function _first(keys){ for(var i=0;i<sources.length;++i){ var s=sources[i]; if(!s||typeof s!=="object") continue; for(var k=0;k<keys.length;++k){ var n=keys[k]; if(s[n]!==undefined) return s[n] } } return undefined } function _num(v,f){ var n=Number(v); return isFinite(n)? n : f } function _policy(v){ if(v===undefined||v===null) return renderPolicyKey; var t=String(v).toLowerCase().trim(); if(t==="on_demand"||t==="on-demand") t="ondemand"; return ["always","ondemand","automatic","manual"].indexOf(t)!==-1? t : renderPolicyKey } var scaleCandidate=_first(["renderScale","render_scale","sceneScaleFactor","scene_scale_factor"]); var frameCandidate=_first(["frameRateLimit","frame_rate_limit","frameLimit","frame_limit"]); var policyCandidate=_first(["renderPolicy","render_policy","renderMode","render_mode"]); if(scaleCandidate!==undefined){ var sc=_num(scaleCandidate, renderScale); if(isFinite(sc)&&sc>0) renderScale=sc } if(frameCandidate!==undefined){ var fr=_num(frameCandidate, frameRateLimit); if(isFinite(fr)&&fr>=0) frameRateLimit=fr } if(policyCandidate!==undefined){ renderPolicyKey=_policy(policyCandidate) } }
    function _applyReflectionProbeEnabledOverride(c){ if(c===undefined||c===null) return; var coerced=!!c; var needs=!reflectionProbeEnabledOverrideActive || reflectionProbeEnabledOverride!==coerced; if(needs) reflectionProbeEnabledOverride=coerced; if(!reflectionProbeEnabledOverrideActive || needs) reflectionProbeEnabledOverrideActive=true }
    function sanitizeReflectionProbePadding(v){ var n=Number(v); return isFinite(n)&&n>=0? n : 0.0 }
    function _resolveReceiverTelemetry(src){ var st=_normaliseState(src); if(_isEmptyMap(st)) return ({}); if(st.receiver){ var direct=_normaliseState(st.receiver); if(!_isEmptyMap(direct)) return direct } var net=st.flowNetwork||st.flownetwork; if(net&&net.receiver) return _normaliseState(net.receiver); return ({}) }

    // Shader diagnostics
    function registerShaderWarning(effectId,message){ var id=String(effectId||"unknown"); var msg=String(message||""); var prev=shaderWarningState; var next=_cloneObject(prev); if(next[id]!==msg) next[id]=msg; shaderWarningState=next; shaderWarningRegistered(id,msg); if(sceneBridge && typeof sceneBridge.registerShaderWarning==="function") { try{ sceneBridge.registerShaderWarning(effectId,message) }catch(e){} } }
    function clearShaderWarning(effectId){ var id=String(effectId||"unknown"); var prev=shaderWarningState; var next=_cloneObject(prev); if(Object.prototype.hasOwnProperty.call(next,id)) delete next[id]; shaderWarningState=next; shaderWarningCleared(id); if(sceneBridge && typeof sceneBridge.clearShaderWarning==="function") { try{ sceneBridge.clearShaderWarning(effectId) }catch(e){} } }

    Connections { target: sceneBridge; enabled: !!target; function onGeometryChanged(payload){ applyGeometryUpdates(payload) } function onSimulationChanged(payload){ applySimulationUpdates(payload) } function onUpdatesDispatched(payload){ if(payload && typeof payload === 'object'){ sceneBridgeDispatchCount += 1 } } }

    // Effects bypass / shader warnings from postEffects
    Connections {
        target: postEffects
        enabled: !!target
        ignoreUnknownSignals: true
        function onEffectsBypassChanged(active, reasonText){ if(!postEffects) return; try { var bypass = active !== undefined ? !!active : !!postEffects.effectsBypass; var reason = reasonText !== undefined && reasonText !== null ? String(reasonText) : String(postEffects.effectsBypassReason || ""); if(postProcessingBypassed !== bypass) postProcessingBypassed = bypass; if(postProcessingBypassReason !== reason) postProcessingBypassReason = reason; if(bypass){ if(sceneView){ try{ postProcessingEffectBackup = sceneView.effects && typeof sceneView.effects.slice === 'function' ? sceneView.effects.slice() : []; sceneView.effects = [] }catch(e){} } shaderStatusDumpRequested({ effectsBypass: true, effectsBypassReason: reason }) } else { var restore = postProcessingEffectBackup && postProcessingEffectBackup.length ? postProcessingEffectBackup : []; if(sceneView){ try{ sceneView.effects = restore }catch(e){} } shaderStatusDumpRequested({ effectsBypass: false, effectsBypassReason: "" }) } } catch(err){ console.error("[SimulationRoot] effectsBypassChanged failed", err) } }
        function onEffectCompilationError(effectId, fallbackActive, message){ try { registerShaderWarning(effectId, message); shaderStatusDumpRequested({ effectsBypass: postProcessingBypassed, effectsBypassReason: String(message||"") }) } catch(e){ console.debug('[SimulationRoot] onEffectCompilationError failed', e) } }
        function onEffectCompilationRecovered(effectId, wasFallbackActive){ try { clearShaderWarning(effectId); shaderStatusDumpRequested({ effectsBypass: postProcessingBypassed, effectsBypassReason: postProcessingBypassReason }) } catch(e){ console.debug('[SimulationRoot] onEffectCompilationRecovered failed', e) } }
    }

    function _ensureEffectsBackup(){ try { if(_effectsBackupTaken) return; if(!sceneView || !postEffects) return; var list= postEffects.effectList; if(list && typeof list === 'object'){ postProcessingEffectBackup = typeof list.slice==='function'? list.slice(): list; _effectsBackupTaken = true; if(sceneView){ try{ sceneView.effects = list }catch(e){} } } } catch(e){ console.debug('[SimulationRoot] _ensureEffectsBackup failed', e) } }
    onSceneViewChanged: _ensureEffectsBackup()
    onPostEffectsChanged: _ensureEffectsBackup()

    Component.onCompleted: { console.log('[SimulationRoot] Component completed; bridge:', sceneBridge? 'available':'missing'); _applyBridgeSnapshot(sceneBridge); _refreshReflectionProbeObject() }
    onSceneBridgeChanged: { _applyBridgeSnapshot(sceneBridge) }

    function _applyBridgeSnapshot(t){ if(!t){ geometryState=({}); simulationState=({}); threeDState=({}); renderState=({}); flowTelemetry=({}); receiverTelemetry=({}); geometryStateReceived=false; simulationStateReceived=false; return } try{ geometryState=_normaliseState(t.geometry) }catch(e){ geometryState=({}) } try{ simulationState=_normaliseState(t.simulation) }catch(e){ simulationState=({}) } geometryStateReceived=!_isEmptyMap(geometryState); simulationStateReceived=!_isEmptyMap(simulationState) }

    // Environment controller (reflection probe integration + SSAO sync)
    Effects.SceneEnvironmentController { id: envController; objectName: "sceneEnvironment"; fogEnabled:false; fogDensity:0.0; iblLightingEnabled:false; skyboxToggleFlag:false; reflectionProbeEnabled: root.reflectionProbeEnabled; ssaoEnabled: root.ssaoEnabled; ssaoRadius: root.ssaoRadius; ssaoIntensity: root.ssaoIntensity; ssaoSoftness: root.ssaoSoftness; ssaoBias: root.ssaoBias; ssaoDither: root.ssaoDither; ssaoSampleRate: root.ssaoSampleRate }
    Connections { target: envController; function onSsaoEnabledChanged(){ if(ssaoEnabled !== envController.ssaoEnabled) ssaoEnabled = envController.ssaoEnabled } function onSsaoRadiusChanged(){ if(ssaoRadius !== envController.ssaoRadius) ssaoRadius = envController.ssaoRadius } function onSsaoIntensityChanged(){ if(ssaoIntensity !== envController.ssaoIntensity) ssaoIntensity = envController.ssaoIntensity } function onSsaoSoftnessChanged(){ if(ssaoSoftness !== envController.ssaoSoftness) ssaoSoftness = envController.ssaoSoftness } function onSsaoBiasChanged(){ if(ssaoBias !== envController.ssaoBias) ssaoBias = envController.ssaoBias } function onSsaoDitherChanged(){ if(ssaoDither !== envController.ssaoDither) ssaoDither = envController.ssaoDither } function onSsaoSampleRateChanged(){ if(ssaoSampleRate !== envController.ssaoSampleRate) ssaoSampleRate = envController.ssaoSampleRate } }

    QtObject { id: suspensionAssembly; objectName: "sceneSuspensionAssembly"; property bool reflectionProbeEnabled: root.reflectionProbeEnabled; property real reflectionProbePaddingM: root.reflectionProbePaddingM; property real sceneScaleFactor: root.sceneScaleFactor; property real rodWarningThreshold: root.suspensionRodWarningThresholdM; property QtObject reflectionProbe: QtObject { property bool enabled: suspensionAssembly.reflectionProbeEnabled; property bool visible: enabled; property int quality: 0; property int refreshMode: 0; property int timeSlicing: 0 } }
    property alias sceneEnvironment: envController
    property alias sceneSuspensionAssembly: suspensionAssembly

    function _refreshReflectionProbeObject(){ suspensionAssembly.reflectionProbe.enabled = suspensionAssembly.reflectionProbeEnabled; suspensionAssembly.reflectionProbe.visible = suspensionAssembly.reflectionProbeEnabled; suspensionAssembly.reflectionProbe.quality = _qualityToInt(reflectionProbeQualitySetting); suspensionAssembly.reflectionProbe.refreshMode = (function(m){ switch(String(m).toLowerCase()){ case 'firstframe': return 1; case 'everyframe': return 2; default: return 0 } })(reflectionProbeRefreshModeSetting); suspensionAssembly.reflectionProbe.timeSlicing = (function(m){ switch(String(m).toLowerCase()){ case 'allfaces': return 1; case 'allfacesatonce': return 2; case 'individualfaces': return 3; default: return 0 } })(reflectionProbeTimeSlicingSetting); suspensionAssembly.reflectionProbePaddingM = reflectionProbePaddingM; _syncReflectionProbeEnvironmentState() }
    function _syncReflectionProbeEnvironmentState(){ var reflectionState={ reflection_enabled: !!suspensionAssembly.reflectionProbeEnabled, reflection_padding_m: reflectionProbePaddingM, reflection_quality: reflectionProbeQualitySetting, reflection_refresh_mode: reflectionProbeRefreshModeSetting, reflection_time_slicing: reflectionProbeTimeSlicingSetting }; var normalized=_normaliseState(environmentState); var merged=_deepMerge(normalized, reflectionState); try{ environmentState = JSON.parse(JSON.stringify(merged)) } catch(e){ environmentState = merged } }
    function _qualityToInt(q){ switch(String(q||"").toLowerCase()){ case 'low': return 1; case 'medium': return 2; case 'high': return 3; case 'veryhigh': return 4; default: return 0 } }
}
