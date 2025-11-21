#pragma ComponentBehavior: Bound

import QtQuick
import QtQml 2.15
import QtQuick.Window 2.15
import QtQuick3D 6.10
// qmllint disable unused-imports
import QtQuick3D.Effects 6.10
import QtQuick3D.Helpers 6.10
// qmllint enable unused-imports
import "../components/ShaderProfileHelper.js" as SPH

Item {
    id: root
    property bool verboseLogging: false
    readonly property var shaderMetrics: SPH.ShaderProfileHelper.metricsSnapshot()

    // When true, the effect chain is bypassed to keep the scene visible even if shaders fail
    property bool effectsBypass: false
    property string effectsBypassReason: ""
    property var persistentEffectFailures: ({})
    property bool simplifiedFallbackActive: false
    property string simplifiedFallbackReason: ""
    property var shaderStatusCache: ({})

    // ── Троттлинг логов ──
    property var _logLastTs: ({})
    readonly property int _logMinIntervalMs: 1200
    function throttledLog(key, fn) {
        var now = Date.now()
        var last = _logLastTs[key] || 0
        if (now - last < _logMinIntervalMs) return
        _logLastTs[key] = now
        try { fn() } catch(e) {}
    }

    onEffectsBypassChanged: {
        if (effectsBypass) {
            var reason = effectsBypassReason && effectsBypassReason.length
                    ? effectsBypassReason
                    : "unknown shader failure"
            throttledLog('bypass_warn', function(){ console.warn("⚠️ PostEffects: bypassing post-processing due to persistent shader errors", reason) })
        } else {
            throttledLog('bypass_clear', function(){ console.log("✅ PostEffects: shader bypass cleared; post-processing restored") })
        }
    }

    function logDiagnostics(eventName, params, environment) {
        if (!diagnosticsLoggingEnabled)
            return
        var windowRef = null
        try {
            if (typeof globalThis !== 'undefined' && globalThis.window)
                windowRef = globalThis.window
        } catch (globalError) {
            windowRef = null
        }
        if (windowRef && typeof windowRef.logQmlEvent === "function") {
            try { windowRef.logQmlEvent("function_called", eventName) } catch (error) {
                if (verboseLogging) console.debug("PostEffects", eventName, "window.logQmlEvent failed", error)
            }
        }
        function ownKeys(value) {
            if (!value || typeof value !== "object") return []
            var keys = []
            for (var key in value) if (objectHasOwn.call(value, key)) keys.push(key)
            return keys
        }
        var payload = {
            level: "info",
            logger: "qml.post_effects",
            event: eventName,
            paramsKeys: ownKeys(params),
            environmentKeys: ownKeys(environment),
            timestamp: new Date().toISOString()
        }
        throttledLog('diagnostics_'+eventName, function(){ console.log(JSON.stringify(payload)) })
    }

    function shaderStatusSnapshot(reasonOverride) {
        var snapshot = {
            timestamp: Date.now(),
            effectsBypass: !!effectsBypass,
            effectsBypassReason: effectsBypassReason,
            simplifiedFallbackActive: !!simplifiedFallbackActive,
            simplifiedFallbackReason: simplifiedFallbackReason,
            persistentEffectFailures: {},
            shaderStatus: {}
        }
        if (reasonOverride !== undefined && reasonOverride !== null && !snapshot.effectsBypassReason)
            snapshot.effectsBypassReason = String(reasonOverride)
        var failures = persistentEffectFailures
        if (failures && typeof failures === "object") {
            var failureCopy = {}
            for (var key in failures) if (objectHasOwn.call(failures, key)) failureCopy[key] = failures[key]
            snapshot.persistentEffectFailures = failureCopy
        }
        var cache = shaderStatusCache
        if (cache && typeof cache === "object") {
            var shaderCopy = {}
            for (var shaderKey in cache) if (objectHasOwn.call(cache, shaderKey)) shaderCopy[shaderKey] = cache[shaderKey]
            snapshot.shaderStatus = shaderCopy
        }
        return snapshot
    }

    function dumpShaderStatus(reasonOverride) {
        var snapshot = shaderStatusSnapshot(reasonOverride)
        if (diagnosticsLoggingEnabled)
            logDiagnostics("PostEffects.shaderStatusDump", snapshot, null)
        return snapshot
    }

    function notifyEffectCompilation(effectId, fallbackActive, errorLog) {
        var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
        if (fallbackActive) {
            var message = (errorLog !== undefined && errorLog !== null) ? String(errorLog) : ""
            if (!message.length) message = qsTr("%1: fallback shader active").arg(normalizedId)
            effectCompilationError(normalizedId, message)
        } else {
            effectCompilationRecovered(normalizedId)
        }
    }

    function updateEffectsBypassState(nextState) {
        persistentEffectFailures = nextState
        var keys = []
        for (var key in nextState) if (objectHasOwn.call(nextState, key)) keys.push(key)
        var active = keys.length > 0
        var reason = ""
        if (active) {
            for (var i = 0; i < keys.length; ++i) {
                var value = nextState[keys[i]]
                if (value !== undefined && value !== null) {
                    var normalized = String(value)
                    if (normalized.length) { reason = normalized; break }
                }
            }
        }
        if (effectsBypassReason !== reason) effectsBypassReason = reason
        if (effectsBypass !== active) effectsBypass = active
        updateSimplifiedFallbackState(active, reason)
    }

    function updateSimplifiedFallbackState(active, reason) {
        var normalizedReason = reason && reason.length ? reason : qsTr("Rendering pipeline failure")
        if (active) {
            var reasonChanged = simplifiedFallbackReason !== normalizedReason
            if (!simplifiedFallbackActive) {
                simplifiedFallbackActive = true
                simplifiedFallbackReason = normalizedReason
                throttledLog('simplified_fallback_on', function(){ console.warn("⚠️ PostEffects: requesting simplified rendering fallback ->", normalizedReason) })
                simplifiedRenderingRequested(normalizedReason)
            } else if (reasonChanged) {
                simplifiedFallbackReason = normalizedReason
                throttledLog('simplified_fallback_update', function(){ console.warn("⚠️ PostEffects: simplified rendering reason updated ->", normalizedReason) })
                simplifiedRenderingRequested(normalizedReason)
            }
        } else {
            if (simplifiedFallbackActive) {
                simplifiedFallbackActive = false
                simplifiedFallbackReason = ""
                throttledLog('simplified_fallback_off', function(){ console.log("✅ PostEffects: simplified rendering fallback cleared") })
                simplifiedRenderingRecovered()
            } else if (simplifiedFallbackReason.length) {
                simplifiedFallbackReason = ""
            }
        }
    }

    function setEffectPersistentFailure(effectId, active, reason) {
        var normalizedId = effectId !== undefined && effectId !== null ? String(effectId) : "unknown"
        var state = persistentEffectFailures || ({})
        var nextState = ({})
        for (var key in state) if (objectHasOwn.call(state, key)) nextState[key] = state[key]
        if (active) {
            var normalizedReason = ""
            if (reason !== undefined && reason !== null) normalizedReason = String(reason).trim()
            if (!normalizedReason.length) normalizedReason = qsTr("%1: persistent shader failure").arg(normalizedId)
            else if (normalizedReason.indexOf(normalizedId) !== 0) normalizedReason = normalizedId + ": " + normalizedReason
            nextState[normalizedId] = normalizedReason
        } else if (objectHasOwn.call(nextState, normalizedId)) {
            delete nextState[normalizedId]
        }
        updateEffectsBypassState(nextState)
    }

    function trySetEffectProperty(effectItem, propertyName, value) {
        if (!effectItem || !propertyName) return false
        // Обновлённый список legacy (не исключаем requiresDepthTexture / requiresVelocityTexture)
        var legacy = ["explicitDepthTextureEnabled","explicitVelocityTextureEnabled"]
        if (legacy.indexOf(propertyName) !== -1) {
            if (verboseLogging) console.debug("PostEffects: legacy property skipped", propertyName)
            return false
        }
        try { effectItem[propertyName] = value; return true } catch (error) {}
        try { if (typeof effectItem.setProperty === "function") { effectItem.setProperty(propertyName, value); return true } } catch (error) {}
        if (verboseLogging) console.debug("⚠️", effectItem, "property assignment failed for", propertyName)
        return false
    }

    // Shader profile selection
    property bool forceDesktopShaderProfile: false
    readonly property bool preferDesktopShaderProfile: SPH.ShaderProfileHelper.preferDesktopProfile(forceDesktopShaderProfile, false, normalizedRendererGraphicsApi, reportedGlesContext, (function(){ try { return qtGraphicsApiRequiresDesktopShaders } catch(e){ return undefined } })(), GraphicsInfo)
    readonly property bool useGlesShaders: reportedGlesContext && !preferDesktopShaderProfile

    onForceDesktopShaderProfileChanged: { shaderVariantSelectionCache = ({}); resetShaderCaches(); SPH.ShaderProfileHelper.markProfileSwitch(); if (verboseLogging) console.log('[PostEffects] profile override desktop=', forceDesktopShaderProfile) }
    onUseGlesShadersChanged: { shaderVariantSelectionCache = ({}); resetShaderCaches(); SPH.ShaderProfileHelper.markProfileSwitch(); if (verboseLogging) console.log('[PostEffects] useGlesShaders ->', useGlesShaders) }

    readonly property string rendererGraphicsApi: {
        try { if (typeof qtGraphicsApiName === "string") return qtGraphicsApiName } catch (error) {}
        switch (GraphicsInfo.api) {
        case GraphicsInfo.OpenGL: return "opengl"
        case GraphicsInfo.Direct3D11: return "direct3d11"
        case GraphicsInfo.Vulkan: return "vulkan"
        case GraphicsInfo.Metal: return "metal"
        case GraphicsInfo.Software: return "software"
        default: return "unknown"
        }
    }
    readonly property string normalizedRendererGraphicsApi: { var apiName = rendererGraphicsApi; if (!apiName || typeof apiName !== "string") return ""; return apiName.trim().toLowerCase() }
    readonly property string openGlVersionLabel: { if (GraphicsInfo.api !== GraphicsInfo.OpenGL) return ""; var major = Number(GraphicsInfo.majorVersion); if (!isFinite(major) || major <= 0) return ""; var minorValue = Number(GraphicsInfo.minorVersion); var minor = isFinite(minorValue) && minorValue >= 0 ? minorValue : 0; return major + "." + minor }
    readonly property bool enforceLegacyFallbackShaders: { if (GraphicsInfo.api !== GraphicsInfo.OpenGL) return false; var major = Number(GraphicsInfo.majorVersion); if (!isFinite(major) || major <= 0) return false; if (major < 3) return true; if (major === 3) { var minorValue = Number(GraphicsInfo.minorVersion); if (!isFinite(minorValue)) return false; return minorValue <= 2 } return false }
    readonly property string legacyFallbackReason: enforceLegacyFallbackShaders ? qsTr("Legacy OpenGL profile detected (OpenGL %1); forcing GLSL 330 fallback shaders.").arg(openGlVersionLabel.length ? openGlVersionLabel : "3.3") : ""
    readonly property bool reportedGlesContext: {
        if (forceDesktopShaderProfile) return false
        try { if (GraphicsInfo.renderableType === GraphicsInfo.SurfaceFormatOpenGLES) return true } catch (error) {}
        try {
            var normalized = normalizedRendererGraphicsApi
            if (!normalized.length) return false
            var normalizedCondensed = normalized.replace(/[\s_-]+/g, "")
            var normalizedWithSpaces = normalized.replace(/[_-]+/g, " ")
            if (normalized.indexOf("rhi") !== -1 && normalized.indexOf("opengl") !== -1 && normalizedCondensed.indexOf("gles") === -1) return false
            if (normalizedWithSpaces.indexOf("opengl es") !== -1) return true
            if (normalizedCondensed.indexOf("opengles") !== -1) return true
            if (normalizedCondensed.indexOf("gles") !== -1) return true
            if (GraphicsInfo.api === GraphicsInfo.Direct3D11 && normalized.indexOf("angle") !== -1) return true
        } catch (error) {}
        return false
    }

    readonly property url shaderResourceDirectory: Qt.resolvedUrl("../../shaders/effects/")
    readonly property url legacyShaderResourceDirectory: Qt.resolvedUrl("../../shaders/effects/")
    readonly property url glesShaderResourceDirectory: Qt.resolvedUrl("../../shaders/effects/")
    readonly property url shaderRootUrl: Qt.resolvedUrl("../../shaders/")
    readonly property var shaderResourceDirectories: {
        var directories = []
        function appendDirectory(path) { if (!path || !path.length) return; if (directories.indexOf(path) !== -1) return; directories.push(path) }
        if (useGlesShaders) { appendDirectory(glesShaderResourceDirectory); appendDirectory(shaderResourceDirectory) } else { appendDirectory(shaderResourceDirectory); appendDirectory(glesShaderResourceDirectory) }
        appendDirectory(legacyShaderResourceDirectory)
        return directories
    }
    readonly property var desktopShaderSuffixes: ["_glsl450", "_desktop", "_core"]
    readonly property var glesShaderSuffixes: ["_es", "_gles", "_300es"]
    // qmllint disable unqualified
    readonly property var shaderResourceManifest: typeof effectShaderManifest !== "undefined" ? effectShaderManifest : ({})
    // qmllint enable unqualified
    property var shaderResourceAvailabilityCache: ({})
    property var shaderSanitizationCache: ({})
    property var shaderSanitizationWarnings: ({})
    property var shaderVariantSelectionCache: ({})
    property var shaderProfileMismatchWarnings: ({})
    property var shaderCompatibilityOverrides: ({})
    property var shaderVariantMissingWarnings: ({})
    // LRU кеш для resolveShaders
    property var _resolveCache: ({})
    property var _resolveCacheOrder: []
    readonly property int _resolveCacheLimit: 32
    function _cacheResolve(key, value) {
        if (!_resolveCache[key]) {
            _resolveCache[key] = value
            _resolveCacheOrder.push(key)
            if (_resolveCacheOrder.length > _resolveCacheLimit) {
                var evicted = _resolveCacheOrder.shift()
                delete _resolveCache[evicted]
            }
        } else {
            _resolveCache[key] = value
        }
    }

    function shaderCompilationMessage(shaderItem) {
        if (!shaderItem) return ""
        try { if ("log" in shaderItem && shaderItem.log) return shaderItem.log } catch (error) {}
        try { if ("compilationLog" in shaderItem && shaderItem.compilationLog) return shaderItem.compilationLog } catch (error) {}
        return ""
    }

    function attachShaderLogHandler(shaderItem, shaderId) {
        if (!shaderItem) return false
        function emitLog() { root.handleShaderCompilationLog(shaderId, shaderCompilationMessage(shaderItem)) }
        try { if (typeof shaderItem.logChanged === "function") { shaderItem.logChanged.connect(emitLog); emitLog(); return true } } catch (error) {}
        try { if (typeof shaderItem.compilationLogChanged === "function") { shaderItem.compilationLogChanged.connect(emitLog); emitLog(); return true } } catch (error) {}
        return false
    }

    function resolvedShaderUrl(resourceName, resourceDirectory) {
        var baseDirectory = resourceDirectory && resourceDirectory.length ? resourceDirectory : (useGlesShaders ? glesShaderResourceDirectory : shaderResourceDirectory)
        var final = baseDirectory + resourceName
        return Qt.resolvedUrl(final)
    }

    function shaderResourceExists(url, resourceName, suppressErrors, manifest) {
        if (!url) return false
        if (objectHasOwn.call(shaderResourceAvailabilityCache, url)) return shaderResourceAvailabilityCache[url]
        // manifest check
        if (manifest && resourceName && objectHasOwn.call(manifest, resourceName)) {
            var entry = manifest[resourceName]
            if (entry === false) {
                if (!suppressErrors) throttledLog('shader_disabled_'+resourceName, function(){ console.warn('❌ PostEffects: shader disabled by manifest', resourceName) })
                shaderResourceAvailabilityCache[url] = false
                return false
            }
        }
        // simple heuristic: if suffix profile mismatch
        if (useGlesShaders && resourceName.indexOf('_glsl450') !== -1) {
            throttledLog('profile_mismatch_'+resourceName, function(){ console.warn('⚠️ PostEffects: desktop suffix on GLES profile', resourceName) })
        }
        shaderResourceAvailabilityCache[url] = true
        return true
    }

    function shaderPath(key) {
        return SPH.ShaderProfileHelper.resolveVariant(
                    key,
                    useGlesShaders,
                    false,
                    desktopShaderSuffixes,
                    glesShaderSuffixes,
                    shaderResourceDirectories,
                    shaderResourceManifest,
                    shaderResourceExists,
                    function(name, directory){ return resolvedShaderUrl(name, directory) },
                    verboseLogging)
    }

    function resetShaderCaches() {
        shaderResourceAvailabilityCache = ({})
        shaderSanitizationCache = ({})
        shaderSanitizationWarnings = ({})
        shaderVariantSelectionCache = ({})
        shaderProfileMismatchWarnings = ({})
        shaderCompatibilityOverrides = ({})
        shaderVariantMissingWarnings = ({})
        _resolveCache = ({})
        _resolveCacheOrder = []
        SPH.ShaderProfileHelper.resetCaches()
        if (verboseLogging) console.log('[PostEffects] caches reset; metrics=', JSON.stringify(shaderMetrics))
    }

    // Effects enable flags & aliases
    property bool bloomEnabled: false
    property alias bloomIntensity: bloomEffect.intensity
    property alias bloomThreshold: bloomEffect.threshold
    property alias bloomBlurAmount: bloomEffect.blurAmount

    property bool ssaoEnabled: false
    property alias ssaoIntensity: ssaoEffect.intensity
    property alias ssaoRadius: ssaoEffect.radius
    property alias ssaoBias: ssaoEffect.bias
    property alias ssaoSamples: ssaoEffect.samples
    property alias ssaoDither: ssaoEffect.dither

    property bool depthOfFieldEnabled: false
    // Унифицируем единицы: считаем что вход в метрах
    property alias dofFocusDistance: dofEffect.focusDistance
    property alias dofFocusRange: dofEffect.focusRange
    property alias dofBlurAmount: dofEffect.blurAmount
    property alias depthOfFieldFallbackActive: dofEffect.fallbackActive
    property alias depthOfFieldFallbackDueToRequirements: dofEffect.fallbackDueToRequirements
    property alias depthOfFieldDepthTextureAvailable: dofEffect.depthTextureAvailable

    property real cameraClipNear: 0.1
    property real cameraClipFar: 1000.0 // уменьшено до 1000 м для согласованности

    property bool motionBlurEnabled: false
    property alias motionBlurStrength: motionBlurEffect.strength
    property alias motionBlurSamples: motionBlurEffect.samples

    // Cached resolveShaders
    function resolveShaders(isEnabled, effectItem, activeShader, fallbackShader, shaderBaseName) {
        var cacheKey = (effectItem ? effectItem.objectName || shaderBaseName || "" : shaderBaseName || "") + '|' + (isEnabled?'1':'0') + '|' + (root.effectsBypass?'b':'n') + '|' + (effectItem && effectItem.fallbackActive ? 'f':'p')
        if (_resolveCache[cacheKey]) return _resolveCache[cacheKey]
        const hasFallback = fallbackShader !== undefined && fallbackShader !== null
        if (root.effectsBypass) { _cacheResolve(cacheKey, []); return [] }
        var persistentFailureActive = false
        try { persistentFailureActive = !!effectItem.persistentFailure } catch (error) {}
        if (persistentFailureActive) { _cacheResolve(cacheKey, []); return [] }
        if (!isEnabled) {
            trySetEffectProperty(effectItem, "fallbackActive", false)
            trySetEffectProperty(effectItem, "fallbackForcedByCompatibility", false)
            _cacheResolve(cacheKey, [])
            return []
        }
        var compatibilityOverrideActive = false
        if (useGlesShaders && shaderBaseName && objectHasOwn.call(shaderCompatibilityOverrides, shaderBaseName)) compatibilityOverrideActive = !!shaderCompatibilityOverrides[shaderBaseName]
        if (!compatibilityOverrideActive) {
            trySetEffectProperty(effectItem, "fallbackForcedByCompatibility", false)
            var fallbackLocked = false
            try { if (effectItem.fallbackDueToCompilation) fallbackLocked = true } catch (error) {}
            if (!fallbackLocked) { try { if (effectItem.fallbackDueToRequirements) fallbackLocked = true } catch (error) {} }
            if (!fallbackLocked && effectItem.fallbackActive) trySetEffectProperty(effectItem, "fallbackActive", false)
        }
        if (compatibilityOverrideActive) {
            trySetEffectProperty(effectItem, "fallbackForcedByCompatibility", true)
            trySetEffectProperty(effectItem, "fallbackActive", true)
            if (hasFallback) { var r = [fallbackShader]; _cacheResolve(cacheKey, r); return r }
            throttledLog('missing_fallback_'+shaderBaseName, function(){ console.warn("⚠️", effectItem, "missing fallback shader for", shaderBaseName, "– disabling effect") })
            _cacheResolve(cacheKey, [])
            return []
        }
        if (effectItem.fallbackActive) { var rf = hasFallback ? [fallbackShader] : []; _cacheResolve(cacheKey, rf); return rf }
        var ra = [activeShader]; _cacheResolve(cacheKey, ra); return ra
    }

    function ensureEffectRequirement(effectItem, propertyName, value, successLog, failureLog) {
        if (trySetEffectProperty(effectItem, propertyName, value)) { if (successLog && successLog.length > 0) throttledLog('req_'+propertyName+'_ok', function(){ console.log("✅", successLog) }); return true }
        var capabilityKeys = ["requiresDepthTexture", "requiresNormalTexture", "requiresVelocityTexture"]
        var isCapability = capabilityKeys.indexOf(propertyName) !== -1
        if (isCapability) {
            var desktopLike = (!useGlesShaders) || preferDesktopShaderProfile || normalizedRendererGraphicsApi.indexOf("opengl") !== -1
            if (desktopLike && value === true) { if (successLog && successLog.length > 0) throttledLog('req_'+propertyName+'_ok_desktop', function(){ console.log("✅", successLog) }); return true }
        }
        const message = failureLog && failureLog.length > 0 ? failureLog : `Effect requirement '${propertyName}' is not supported`
        throttledLog('req_'+propertyName+'_fail', function(){ console.warn("⚠️", message) })
        return false
    }

    Component.onCompleted: {
        console.log("🎨 Post Effects Collection loaded")
        console.log("   Graphics API:", rendererGraphicsApi)
        if (normalizedRendererGraphicsApi.length) console.log("   Normalized API:", normalizedRendererGraphicsApi)
        console.log("   Shader profile:", useGlesShaders ? "OpenGL ES (GLSL 300 es)" : "Desktop (GLSL 450 core)")
        console.log("   Profile decision flags ->", "preferDesktop:", preferDesktopShaderProfile, "reportedGles:", reportedGlesContext, "forceDesktopOverride:", forceDesktopShaderProfile)
        if (legacyFallbackReason.length) throttledLog('legacy_fallback', function(){ console.warn("⚠️ PostEffects:", legacyFallbackReason) })
        console.log("   Available effects: Bloom, SSAO, DOF, Motion Blur")
    }

    // Bloom Effect
    Effect { id: bloomEffect
        Binding { target: bloomEffect; property: "enabled"; value: root.bloomEnabled }
        property bool fallbackActive: false; property string lastErrorLog: ""; property bool componentCompleted: false; property bool fallbackDueToCompilation: false; property string compilationErrorLog: ""; property bool fallbackForcedByCompatibility: false; property bool persistentFailure: false
        readonly property string fallbackMessage: qsTr("Bloom: fallback shader active")
        readonly property string compatibilityFallbackMessage: { var versionLabel = root.openGlVersionLabel.length ? root.openGlVersionLabel : "3.3"; return qsTr("Bloom: forcing GLSL 330 fallback shader for OpenGL %1").arg(versionLabel) }
        Component.onCompleted: {
            if (root.enforceLegacyFallbackShaders && !fallbackForcedByCompatibility) {
                fallbackForcedByCompatibility = true
                var compatibilityLog = compatibilityFallbackMessage.length ? compatibilityFallbackMessage : root.legacyFallbackReason
                if ((!lastErrorLog || !lastErrorLog.length) && compatibilityLog.length) lastErrorLog = compatibilityLog
                fallbackActive = true
                if (compatibilityLog.length) throttledLog('bloom_fallback', function(){ console.warn("⚠️", compatibilityLog) })
            }
            if (fallbackActive && !lastErrorLog) lastErrorLog = fallbackMessage; else if (!fallbackActive && lastErrorLog) lastErrorLog = ""
            root.notifyEffectCompilation("bloom", fallbackActive, lastErrorLog)
            componentCompleted = true
        }
        onFallbackActiveChanged: { if (!componentCompleted) return; if (fallbackActive && !lastErrorLog) lastErrorLog = fallbackMessage; else if (!fallbackActive && lastErrorLog) lastErrorLog = ""; root.notifyEffectCompilation("bloom", fallbackActive, lastErrorLog) }
        property real intensity: 0.3; property real threshold: 0.7; property real blurAmount: 1.0
        onBlurAmountChanged: { if (blurAmount < 0.0) blurAmount = 0.0 }
        Shader { id: bloomFragmentShader; stage: Shader.Fragment; property real uIntensity: bloomEffect.intensity; property real uThreshold: bloomEffect.threshold; property real uBlurAmount: bloomEffect.blurAmount; shader: root.shaderPath("bloom.frag"); Component.onCompleted: { if (!root.attachShaderLogHandler(bloomFragmentShader, "bloom.frag")) if (verboseLogging) console.debug("PostEffects: shader log handler unavailable for bloom.frag") } }
        Connections { target: bloomFragmentShader; ignoreUnknownSignals: true; function onStatusChanged(status) { root.handleEffectShaderStatusChange("bloom", bloomEffect, bloomFragmentShader, "bloom.frag", false) } }
        Shader { id: bloomFallbackShader; stage: Shader.Fragment; shader: root.shaderPath("bloom_fallback.frag"); Component.onCompleted: { if (!root.attachShaderLogHandler(bloomFallbackShader, "bloom_fallback.frag")) if (verboseLogging) console.debug("PostEffects: shader log handler unavailable for bloom_fallback.frag") } }
        Connections { target: bloomFallbackShader; ignoreUnknownSignals: true; function onStatusChanged() { root.handleEffectShaderStatusChange("bloom", bloomEffect, bloomFallbackShader, "bloom_fallback.frag", true) } }
        passes: [ Pass { shaders: root.resolveShaders(root.bloomEnabled, bloomEffect, bloomFragmentShader, bloomFallbackShader, "bloom.frag") } ] }

    // SSAO Effect (only localization fix inside requirementFallbackLog)
    Effect { id: ssaoEffect
        Binding { target: ssaoEffect; property: "enabled"; value: root.ssaoEnabled }
        property bool fallbackActive: false; property string lastErrorLog: ""; property bool depthTextureAvailable: false; property bool normalTextureAvailable: false; property bool componentCompleted: false; property bool fallbackDueToCompilation: false; property bool fallbackDueToRequirements: false; property string compilationErrorLog: ""; property string requirementFallbackLog: ""; property bool fallbackForcedByCompatibility: false; property bool persistentFailure: false
        readonly property string fallbackMessage: qsTr("SSAO: fallback shader active")
        readonly property string compatibilityFallbackMessage: { var versionLabel = root.openGlVersionLabel.length ? root.openGlVersionLabel : "3.3"; return qsTr("SSAO: forcing GLSL 330 fallback shader for OpenGL %1").arg(versionLabel) }
        Component.onCompleted: {
            depthTextureAvailable = root.ensureEffectRequirement(
                        ssaoEffect,
                        "requiresDepthTexture",
                        true,
                        "SSAO: depth texture support enabled",
                        "SSAO: depth texture buffer is not supported; disabling advanced SSAO")
            normalTextureAvailable = root.ensureEffectRequirement(
                        ssaoEffect,
                        "requiresNormalTexture",
                        true,
                        "SSAO: normal texture support enabled",
                        "SSAO: normal texture buffer is not supported; disabling advanced SSAO")

            fallbackDueToCompilation = false
            compilationErrorLog = ""
            var requiresFallback = !depthTextureAvailable || !normalTextureAvailable
            fallbackDueToRequirements = requiresFallback
            if (requiresFallback) {
                if (!depthTextureAvailable && !normalTextureAvailable)
                    requirementFallbackLog = qsTr("SSAO: depth and normal textures unavailable in this runtime; enabling compatibility SSAO")
                else if (!depthTextureAvailable)
                    requirementFallbackLog = qsTr("SSAO: depth texture unavailable in this runtime; enabling compatibility SSAO")
                else
                    requirementFallbackLog = qsTr("SSAO: normal texture unavailable в данной среде выполнения; включение совместимого SSAO")
                lastErrorLog = requirementFallbackLog
                console.warn("⚠️ SSAO: switching to passthrough fallback due to missing textures")
                fallbackActive = true
            } else {
                requirementFallbackLog = ""
                lastErrorLog = ""
                fallbackActive = false
            }

            if (root.enforceLegacyFallbackShaders && !fallbackForcedByCompatibility) {
                fallbackForcedByCompatibility = true
                var compatibilityLog = compatibilityFallbackMessage.length
                        ? compatibilityFallbackMessage
                        : root.legacyFallbackReason
                if (compatibilityLog.length) {
                    if (lastErrorLog.length) {
                        if (lastErrorLog.indexOf(compatibilityLog) === -1)
                            lastErrorLog = lastErrorLog + " | " + compatibilityLog
                    } else {
                        lastErrorLog = compatibilityLog
                    }
                    console.warn("⚠️", compatibilityLog)
                }
                fallbackActive = true
            }

            root.notifyEffectCompilation("ssao", fallbackActive, lastErrorLog)
            componentCompleted = true
        }

        onFallbackActiveChanged: { if (!componentCompleted) return; if (fallbackActive && !lastErrorLog) lastErrorLog = fallbackMessage; else if (!fallbackActive && lastErrorLog) lastErrorLog = ""; root.notifyEffectCompilation("ssao", fallbackActive, lastErrorLog) }
        property real intensity: 0.5; property real radius: 2.0; property real bias: 0.025; property bool dither: true; property int samples: 16
        onSamplesChanged: { if (samples < 1) samples = 1 }
        Shader { id: ssaoFragmentShader; stage: Shader.Fragment; property real uIntensity: ssaoEffect.intensity; property real uRadius: ssaoEffect.radius; property real uBias: ssaoEffect.bias; property int uSamples: ssaoEffect.samples; property real uDitherToggle: ssaoEffect.dither ? 1.0 : 0.0; shader: root.shaderPath("ssao.frag"); Component.onCompleted: { if (!root.attachShaderLogHandler(ssaoFragmentShader, "ssao.frag")) if (verboseLogging) console.debug("PostEffects: shader log handler unavailable for ssao.frag") } }
        Connections { target: ssaoFragmentShader; ignoreUnknownSignals: true; function onStatusChanged(status) { root.handleEffectShaderStatusChange("ssao", ssaoEffect, ssaoFragmentShader, "ssao.frag", false) } }
        Shader { id: ssaoFallbackShader; stage: Shader.Fragment; shader: root.shaderPath("ssao_fallback.frag"); Component.onCompleted: { if (!root.attachShaderLogHandler(ssaoFallbackShader, "ssao_fallback.frag")) if (verboseLogging) console.debug("PostEffects: shader log handler unavailable for ssao_fallback.frag") } }
        Connections { target: ssaoFallbackShader; ignoreUnknownSignals: true; function onStatusChanged(status) { root.handleEffectShaderStatusChange("ssao", ssaoEffect, ssaoFallbackShader, "ssao_fallback.frag", true) } }
        passes: [ Pass { shaders: root.resolveShaders(root.ssaoEnabled, ssaoEffect, ssaoFragmentShader, ssaoFallbackShader, "ssao.frag") } ]
    }

    // Depth of Field Effect (units unified to meters)
    Effect { id: dofEffect
        Binding { target: dofEffect; property: "enabled"; value: root.depthOfFieldEnabled }
        // Эффект глубины резкости использует буфер глубины сцены
        property bool fallbackActive: false; property string lastErrorLog: ""; property bool depthTextureAvailable: false; property bool componentCompleted: false; property bool fallbackDueToCompilation: false; property bool fallbackDueToRequirements: false; property string compilationErrorLog: ""; property string requirementFallbackLog: ""; property bool fallbackForcedByCompatibility: false; property bool persistentFailure: false
        readonly property string fallbackMessage: qsTr("Depth of Field: fallback shader active")
        readonly property string compatibilityFallbackMessage: { var versionLabel = root.openGlVersionLabel.length ? root.openGlVersionLabel : "3.3"; return qsTr("Depth of Field: forcing GLSL 330 fallback shader for OpenGL %1").arg(versionLabel) }
        property real focusDistance: 2.0;  // Расстояние фокуса (м)
        property real focusRange: 1.0;     // Диапазон фокуса (м)
        property real blurAmount: 1.0      // Сила размытия
        property real cameraNear: root.cameraClipNear
        property real cameraFar: root.cameraClipFar

        onBlurAmountChanged: { if (blurAmount < 0.0) blurAmount = 0.0 }
        Component.onCompleted: {
            depthTextureAvailable = root.ensureEffectRequirement(
                        dofEffect,
                        "requiresDepthTexture",
                        true,
                        "Depth of Field: depth texture support enabled",
                        "Depth of Field: depth texture unavailable; using fallback shader")

            fallbackDueToCompilation = false
            compilationErrorLog = ""
            var requiresFallback = !depthTextureAvailable
            fallbackDueToRequirements = requiresFallback
            if (requiresFallback) {
                requirementFallbackLog = qsTr("Depth of Field: depth texture unavailable; using fallback shader")
                lastErrorLog = requirementFallbackLog
                console.warn("⚠️ Depth of Field: switching to passthrough fallback due to missing depth texture")
                fallbackActive = true
            } else {
                requirementFallbackLog = ""
                lastErrorLog = ""
                fallbackActive = false
            }

            if (root.enforceLegacyFallbackShaders && !fallbackForcedByCompatibility) {
                fallbackForcedByCompatibility = true
                var compatibilityLog = compatibilityFallbackMessage.length
                        ? compatibilityFallbackMessage
                        : root.legacyFallbackReason
                if (compatibilityLog.length) {
                    if (lastErrorLog.length) {
                        if (lastErrorLog.indexOf(compatibilityLog) === -1)
                            lastErrorLog = lastErrorLog + " | " + compatibilityLog
                    } else {
                        lastErrorLog = compatibilityLog
                    }
                    console.warn("⚠️", compatibilityLog)
                }
                fallbackActive = true
            }

            root.notifyEffectCompilation("depthOfField", fallbackActive, lastErrorLog)
            componentCompleted = true
        }

        onFallbackActiveChanged: { if (!componentCompleted) return; if (fallbackActive && !lastErrorLog) lastErrorLog = fallbackMessage; else if (!fallbackActive && lastErrorLog) lastErrorLog = ""; root.notifyEffectCompilation("depthOfField", fallbackActive, lastErrorLog) }
        Shader { id: dofFragmentShader; stage: Shader.Fragment; property real uFocusDistance: dofEffect.focusDistance; property real uFocusRange: dofEffect.focusRange; property real uBlurAmount: dofEffect.blurAmount; property real uCameraNear: dofEffect.cameraNear; property real uCameraFar: dofEffect.cameraFar; shader: root.shaderPath("dof.frag"); Component.onCompleted: { if (!root.attachShaderLogHandler(dofFragmentShader, "dof.frag")) if (verboseLogging) console.debug("PostEffects: shader log handler unavailable for dof.frag") } }
        Connections { target: dofFragmentShader; ignoreUnknownSignals: true; function onStatusChanged(status) { root.handleEffectShaderStatusChange("depthOfField", dofEffect, dofFragmentShader, "dof.frag", false) } }
        Shader { id: dofFallbackShader; stage: Shader.Fragment; shader: root.shaderPath("dof_fallback.frag"); Component.onCompleted: { if (!root.attachShaderLogHandler(dofFallbackShader, "dof_fallback.frag")) if (verboseLogging) console.debug("PostEffects: shader log handler unavailable for dof_fallback.frag") } }
        Connections { target: dofFallbackShader; ignoreUnknownSignals: true; function onStatusChanged() { root.handleEffectShaderStatusChange("depthOfField", dofEffect, dofFallbackShader, "dof_fallback.frag", true) } }
        passes: [ Pass { shaders: root.resolveShaders(root.depthOfFieldEnabled, dofEffect, dofFragmentShader, dofFallbackShader, "dof.frag") } ]
    }

    // Motion Blur Effect (typo fix velocity texture unavailable)
    Effect { id: motionBlurEffect
        Binding { target: motionBlurEffect; property: "enabled"; value: root.motionBlurEnabled }
        // Эффект размытия движения читает текстуру скоростей
        property bool fallbackActive: false; property string lastErrorLog: ""; property bool velocityTextureAvailable: false; property bool componentCompleted: false; property bool fallbackDueToCompilation: false; property bool fallbackDueToRequirements: false; property string compilationErrorLog: ""; property string requirementFallbackLog: ""; property bool fallbackForcedByCompatibility: false; property bool persistentFailure: false
        readonly property string fallbackMessage: qsTr("Motion Blur: fallback shader active")
        readonly property string compatibilityFallbackMessage: { var versionLabel = root.openGlVersionLabel.length ? root.openGlVersionLabel : "3.3"; return qsTr("Motion Blur: forcing GLSL 330 fallback shader for OpenGL %1").arg(versionLabel) }
        property real strength: 0.5;      // Сила размытия движения
        property int samples: 8          // Количество сэмплов
        onSamplesChanged: { if (samples < 1) samples = 1 }
        Component.onCompleted: {
            velocityTextureAvailable = root.ensureEffectRequirement(
                        motionBlurEffect,
                        "requiresVelocityTexture",
                        true,
                        "Motion Blur: velocity texture support enabled",
                        "Motion Blur: velocity textureUnavailable; using fallback shader")

            fallbackDueToCompilation = false
            compilationErrorLog = ""
            var requiresFallback = !velocityTextureAvailable
            fallbackDueToRequirements = requiresFallback
            if (requiresFallback) {
                requirementFallbackLog = qsTr("Motion Blur: velocity texture unavailable; using fallback shader")
                lastErrorLog = requirementFallbackLog
                console.warn("⚠️ Motion Blur: switching to passthrough fallback due to missing velocity texture")
                fallbackActive = true
            } else {
                requirementFallbackLog = ""
                lastErrorLog = ""
                fallbackActive = false
            }

            if (root.enforceLegacyFallbackShaders && !fallbackForcedByCompatibility) {
                fallbackForcedByCompatibility = true
                var compatibilityLog = compatibilityFallbackMessage.length
                        ? compatibilityFallbackMessage
                        : root.legacyFallbackReason
                if (compatibilityLog.length) {
                    if (lastErrorLog.length) {
                        if (lastErrorLog.indexOf(compatibilityLog) === -1)
                            lastErrorLog = lastErrorLog + " | " + compatibilityLog
                    } else {
                        lastErrorLog = compatibilityLog
                    }
                    console.warn("⚠️", compatibilityLog)
                }
                fallbackActive = true
            }

            root.notifyEffectCompilation("motionBlur", fallbackActive, lastErrorLog)
            componentCompleted = true
        }

        onFallbackActiveChanged: { if (!componentCompleted) return; if (fallbackActive && !lastErrorLog) lastErrorLog = fallbackMessage; else if (!fallbackActive && lastErrorLog) lastErrorLog = ""; root.notifyEffectCompilation("motionBlur", fallbackActive, lastErrorLog) }
        Shader { id: motionBlurFragmentShader; stage: Shader.Fragment; property real uStrength: motionBlurEffect.strength; property int uSamples: motionBlurEffect.samples; shader: root.shaderPath("motion_blur.frag"); Component.onCompleted: { if (!root.attachShaderLogHandler(motionBlurFragmentShader, "motion_blur.frag")) if (verboseLogging) console.debug("PostEffects: shader log handler unavailable for motion_blur.frag") } }
        Connections { target: motionBlurFragmentShader; ignoreUnknownSignals: true; function onStatusChanged(status) { root.handleEffectShaderStatusChange("motionBlur", motionBlurEffect, motionBlurFragmentShader, "motion_blur.frag", false) } }
        Shader { id: motionBlurFallbackShader; stage: Shader.Fragment; shader: root.shaderPath("motion_blur_fallback.frag"); Component.onCompleted: { if (!root.attachShaderLogHandler(motionBlurFallbackShader, "motion_blur_fallback.frag")) if (verboseLogging) console.debug("PostEffects: shader log handler unavailable for motion_blur_fallback.frag") } }
        Connections { target: motionBlurFallbackShader; ignoreUnknownSignals: true; function onStatusChanged() { root.handleEffectShaderStatusChange("motionBlur", motionBlurEffect, motionBlurFallbackShader, "motion_blur_fallback.frag", true) } }
        passes: [ Pass { shaders: root.resolveShaders(root.motionBlurEnabled, motionBlurEffect, motionBlurFragmentShader, motionBlurFallbackShader, "motion_blur.frag") } ]
    }

    // Canonical shader map
    readonly property var _canonicalEffectShaderMap: ({ bloomFrag: 'effects/bloom.frag', fogFrag: 'effects/fog.frag' })
    readonly property bool _legacyPathsEnabled: (function(){ try { return String((typeof globalThis !== 'undefined' && globalThis.PSS_ENABLE_LEGACY_POST_EFFECTS_PATHS) || '').toLowerCase() in ['1','true','yes','on'] } catch(e){ return false } })()
}
