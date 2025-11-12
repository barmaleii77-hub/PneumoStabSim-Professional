pragma ComponentBehavior: Bound

import QtQuick
import QtQml 2.15
import QtQuick.Window 2.15
import QtQuick3D 6.4
// qmllint disable unused-imports
import QtQuick3D.Effects 6.4
import QtQuick3D.Helpers 6.4
// qmllint enable unused-imports

// qmllint disable property

/*
 * Коллекция пост-эффектов для улучшенной визуализации
 * Collection of post-effects for enhanced visualization
 */
Item {
    id: root

    readonly property var objectHasOwn: ({}).hasOwnProperty

    signal effectCompilationError(var effectId, string errorLog)
    signal effectCompilationRecovered(var effectId)
    signal simplifiedRenderingRequested(string reason)
    signal simplifiedRenderingRecovered()

    // Structured diagnostics (opt-in from Python)
    property bool diagnosticsLoggingEnabled: false

    // When true, the effect chain is bypassed to keep the scene visible even if shaders fail
    property bool effectsBypass: false
    property string effectsBypassReason: ""
    property var persistentEffectFailures: ({})
    property bool simplifiedFallbackActive: false
    property string simplifiedFallbackReason: ""
    property var shaderStatusCache: ({})

    onEffectsBypassChanged: {
        if (effectsBypass) {
            var reason = effectsBypassReason && effectsBypassReason.length
                    ? effectsBypassReason
                    : "unknown shader failure"
            console.warn("⚠️ PostEffects: bypassing post-processing due to persistent shader errors", reason)
        } else {
            console.log("✅ PostEffects: shader bypass cleared; post-processing restored")
        }
    }

    function logDiagnostics(eventName, params, environment) {
        if (!diagnosticsLoggingEnabled)
            return

        var windowRef = null
        try {
            var globalScope = Function("return this")()
            if (globalScope && globalScope.window)
                windowRef = globalScope.window
        } catch (globalError) {
            windowRef = null
        }
        if (windowRef && typeof windowRef.logQmlEvent === "function") {
            try {
                windowRef.logQmlEvent("function_called", eventName)
            } catch (error) {
                console.debug("PostEffects", eventName, "window.logQmlEvent failed", error)
            }
        }

        function ownKeys(value) {
            if (!value || typeof value !== "object")
                return []
            var keys = []
            for (var key in value) {
                if (objectHasOwn.call(value, key))
                    keys.push(key)
            }
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

        console.log(JSON.stringify(payload))
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
            for (var key in failures) {
                if (objectHasOwn.call(failures, key))
                    failureCopy[key] = failures[key]
            }
            snapshot.persistentEffectFailures = failureCopy
        }
        var cache = shaderStatusCache
        if (cache && typeof cache === "object") {
            var shaderCopy = {}
            for (var shaderKey in cache) {
                if (objectHasOwn.call(cache, shaderKey))
                    shaderCopy[shaderKey] = cache[shaderKey]
            }
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
        var normalizedId = effectId !== undefined && effectId !== null
                ? String(effectId)
                : "unknown"
        if (fallbackActive) {
            var message = ""
            if (errorLog !== undefined && errorLog !== null)
                message = String(errorLog)
            if (!message.length)
                message = qsTr("%1: fallback shader active").arg(normalizedId)
            effectCompilationError(normalizedId, message)
        } else {
            effectCompilationRecovered(normalizedId)
        }
    }

    function updateEffectsBypassState(nextState) {
        persistentEffectFailures = nextState
        var keys = []
        for (var key in nextState) {
            if (objectHasOwn.call(nextState, key))
                keys.push(key)
        }
        var active = keys.length > 0
        if (effectsBypass !== active)
            effectsBypass = active
        var reason = ""
        if (active) {
            for (var i = 0; i < keys.length; ++i) {
                var value = nextState[keys[i]]
                if (value !== undefined && value !== null) {
                    var normalized = String(value)
                    if (normalized.length) {
                        reason = normalized
                        break
                    }
                }
            }
        }
        if (effectsBypassReason !== reason)
            effectsBypassReason = reason
        updateSimplifiedFallbackState(active, reason)
    }

    function updateSimplifiedFallbackState(active, reason) {
        var normalizedReason = reason && reason.length
                ? reason
                : qsTr("Rendering pipeline failure")
        if (active) {
            var reasonChanged = simplifiedFallbackReason !== normalizedReason
            if (!simplifiedFallbackActive) {
                simplifiedFallbackActive = true
                simplifiedFallbackReason = normalizedReason
                console.warn("⚠️ PostEffects: requesting simplified rendering fallback ->", normalizedReason)
                simplifiedRenderingRequested(normalizedReason)
            } else if (reasonChanged) {
                simplifiedFallbackReason = normalizedReason
                console.warn("⚠️ PostEffects: simplified rendering reason updated ->", normalizedReason)
                simplifiedRenderingRequested(normalizedReason)
            }
        } else {
            if (simplifiedFallbackActive) {
                simplifiedFallbackActive = false
                simplifiedFallbackReason = ""
                console.log("✅ PostEffects: simplified rendering fallback cleared")
                simplifiedRenderingRecovered()
            } else if (simplifiedFallbackReason.length) {
                simplifiedFallbackReason = ""
            }
        }
    }

    function setEffectPersistentFailure(effectId, active, reason) {
        var normalizedId = effectId !== undefined && effectId !== null
                ? String(effectId)
                : "unknown"
        var state = persistentEffectFailures || ({})
        var nextState = ({})
        for (var key in state) {
            if (objectHasOwn.call(state, key))
                nextState[key] = state[key]
        }
        if (active) {
            var normalizedReason = ""
            if (reason !== undefined && reason !== null)
                normalizedReason = String(reason).trim()
            if (!normalizedReason.length)
                normalizedReason = qsTr("%1: persistent shader failure").arg(normalizedId)
            else if (normalizedReason.indexOf(normalizedId) !== 0)
                normalizedReason = normalizedId + ": " + normalizedReason
            nextState[normalizedId] = normalizedReason
        } else if (objectHasOwn.call(nextState, normalizedId)) {
            delete nextState[normalizedId]
        }
        updateEffectsBypassState(nextState)
    }

    function trySetEffectProperty(effectItem, propertyName, value) {
        if (!effectItem || !propertyName)
            return false
        try {
            if (propertyName in effectItem) {
                effectItem[propertyName] = value
                return true
            }
        } catch (error) {
            console.debug("⚠️", effectItem, "property lookup failed for", propertyName, error)
        }
        try {
            if (typeof effectItem.setProperty === "function")
                return effectItem.setProperty(propertyName, value)
        } catch (error) {
            console.debug("⚠️", effectItem, "does not support", propertyName, error)
        }
        return false
    }

    // Стратегия выбора профиля шейдеров:
    // 1. Не задаём language: Shader.GLSL, позволяя Qt Quick 3D автоматически
    //    подобрать профиль GLSL в зависимости от используемого графического API.
    // 2. Предпочтение GLES-профиля определяется логикой ниже и может быть
    //    переопределено свойством forceDesktopShaderProfile.
    // Shader profile selection strategy:
    // 1. Omit language: Shader.GLSL so Qt Quick 3D can automatically choose the
    //    correct GLSL profile for the active graphics backend.
    // 2. The GLES preference is decided by the detection logic below and can be
    //    overridden with forceDesktopShaderProfile.
    // qmllint disable unqualified
    property bool forceDesktopShaderProfile: false
    onForceDesktopShaderProfileChanged: {
        if (forceDesktopShaderProfile)
            console.warn("⚠️ PostEffects: desktop shader profile override enabled (preferring GLSL 450 resources)")
        else
            console.log("ℹ️ PostEffects: desktop shader profile override cleared; reverting to auto detection")
        shaderVariantSelectionCache = ({})
        resetShaderCaches()
    }

    readonly property bool preferDesktopShaderProfile: {
        if (forceDesktopShaderProfile)
            return true
        var normalized = normalizedRendererGraphicsApi
        if (normalized.length) {
            var normalizedCondensed = normalized.replace(/[\s_-]+/g, "")
            var normalizedWithSpaces = normalized.replace(/[_-]+/g, " ")
            if (normalized.indexOf("angle") !== -1)
                return false
            if (normalizedWithSpaces.indexOf("opengl es") !== -1
                    || normalizedCondensed.indexOf("opengles") !== -1
                    || normalizedCondensed.indexOf("gles") !== -1)
                return false
        }
        try {
            if (typeof qtGraphicsApiRequiresDesktopShaders === "boolean")
                return qtGraphicsApiRequiresDesktopShaders
        } catch (error) {
        }
        if (GraphicsInfo.api === GraphicsInfo.Direct3D11 && reportedGlesContext)
            return false
        if (!reportedGlesContext && GraphicsInfo.api === GraphicsInfo.OpenGL)
            return true
        return GraphicsInfo.api === GraphicsInfo.Direct3D11
                || GraphicsInfo.api === GraphicsInfo.Vulkan
                || GraphicsInfo.api === GraphicsInfo.Metal
                || GraphicsInfo.api === GraphicsInfo.Null
    }
    readonly property string rendererGraphicsApi: {
        try {
            if (typeof qtGraphicsApiName === "string")
                return qtGraphicsApiName
        } catch (error) {
        }
        switch (GraphicsInfo.api) {
        case GraphicsInfo.OpenGL:
            return "opengl"
        case GraphicsInfo.Direct3D11:
            return "direct3d11"
        case GraphicsInfo.Vulkan:
            return "vulkan"
        case GraphicsInfo.Metal:
            return "metal"
        case GraphicsInfo.Software:
            return "software"
        default:
            return "unknown"
        }
    }
    readonly property string normalizedRendererGraphicsApi: {
        var apiName = rendererGraphicsApi
        if (!apiName || typeof apiName !== "string")
            return ""
        return apiName.trim().toLowerCase()
    }
    readonly property string openGlVersionLabel: {
        if (GraphicsInfo.api !== GraphicsInfo.OpenGL)
            return ""
        var major = Number(GraphicsInfo.majorVersion)
        if (!isFinite(major) || major <= 0)
            return ""
        var minorValue = Number(GraphicsInfo.minorVersion)
        var minor = isFinite(minorValue) && minorValue >= 0 ? minorValue : 0
        return major + "." + minor
    }
    readonly property bool enforceLegacyFallbackShaders: {
        if (GraphicsInfo.api !== GraphicsInfo.OpenGL)
            return false
        var major = Number(GraphicsInfo.majorVersion)
        if (!isFinite(major) || major <= 0)
            return false
        if (major < 3)
            return true
        if (major === 3) {
            var minorValue = Number(GraphicsInfo.minorVersion)
            if (!isFinite(minorValue))
                return false
            return minorValue <= 3
        }
        return false
    }
    readonly property string legacyFallbackReason: enforceLegacyFallbackShaders
            ? qsTr("Legacy OpenGL profile detected (OpenGL %1); forcing GLSL 330 fallback shaders.")
                .arg(openGlVersionLabel.length ? openGlVersionLabel : "3.3")
            : ""
    readonly property bool reportedGlesContext: {
        if (forceDesktopShaderProfile)
            return false
// qmllint disable property
        try {
            if (GraphicsInfo.renderableType === GraphicsInfo.SurfaceFormatOpenGLES)
                return true
        } catch (error) {
        }
// qmllint enable property
        try {
            var normalized = normalizedRendererGraphicsApi
            if (!normalized.length)
                return false
            var normalizedCondensed = normalized.replace(/[\s_-]+/g, "")
            var normalizedWithSpaces = normalized.replace(/[_-]+/g, " ")
            if (normalized.indexOf("rhi") !== -1
                    && normalized.indexOf("opengl") !== -1
                    && normalizedCondensed.indexOf("gles") === -1)
                return false
            if (normalizedWithSpaces.indexOf("opengl es") !== -1)
                return true
            if (normalizedCondensed.indexOf("opengles") !== -1)
                return true
            if (normalizedCondensed.indexOf("gles") !== -1)
                return true
            if (GraphicsInfo.api === GraphicsInfo.Direct3D11
                    && normalized.indexOf("angle") !== -1)
                return true
        } catch (error) {
        }
        return false
    }
    // qmllint enable unqualified
    readonly property bool useGlesShaders: reportedGlesContext && !preferDesktopShaderProfile

    readonly property url shaderResourceDirectory: Qt.resolvedUrl("../../shaders/effects/")
    readonly property url legacyShaderResourceDirectory: Qt.resolvedUrl("../../shaders/effects/")
    readonly property url glesShaderResourceDirectory: Qt.resolvedUrl("../../shaders/effects/")
    readonly property url shaderRootUrl: Qt.resolvedUrl("../../shaders/")
    readonly property var shaderResourceDirectories: {
        var directories = []
        function appendDirectory(path) {
            if (!path || !path.length)
                return
            if (directories.indexOf(path) !== -1)
                return
            directories.push(path)
        }
        if (useGlesShaders) {
            appendDirectory(glesShaderResourceDirectory)
            appendDirectory(shaderResourceDirectory)
        } else {
            appendDirectory(shaderResourceDirectory)
            appendDirectory(glesShaderResourceDirectory)
        }
        appendDirectory(legacyShaderResourceDirectory)
        return directories
    }
    readonly property var desktopShaderSuffixes: ["_glsl450", "_desktop", "_core"]
    readonly property var glesShaderSuffixes: ["_es", "_gles", "_300es"]
    // qmllint disable unqualified
    readonly property var shaderResourceManifest: typeof effectShaderManifest !== "undefined"
            ? effectShaderManifest
            : ({})
    // qmllint enable unqualified
    property var shaderResourceAvailabilityCache: ({})
    property var shaderSanitizationCache: ({})
    property var shaderSanitizationWarnings: ({})
    property var shaderVariantSelectionCache: ({})
    property var shaderProfileMismatchWarnings: ({})
    property var shaderCompatibilityOverrides: ({})
    property var shaderVariantMissingWarnings: ({})

    onUseGlesShadersChanged: {
        console.log("🎚️ PostEffects: shader profile toggled ->", useGlesShaders
                ? "OpenGL ES (GLSL 300 es)"
                : "Desktop (GLSL 450 core)")
        shaderVariantSelectionCache = ({})
        resetShaderCaches()
    }

    function shaderCompilationMessage(shaderItem) {
        if (!shaderItem)
            return ""
        try {
            if ("log" in shaderItem && shaderItem.log)
                return shaderItem.log
        } catch (error) {
        }
        try {
            if ("compilationLog" in shaderItem && shaderItem.compilationLog)
                return shaderItem.compilationLog
        } catch (error) {
        }
        return ""
    }

    function attachShaderLogHandler(shaderItem, shaderId) {
        if (!shaderItem)
            return false
        function emitLog() {
            root.handleShaderCompilationLog(shaderId, shaderCompilationMessage(shaderItem))
        }
        try {
            if (typeof shaderItem.logChanged === "function") {
                shaderItem.logChanged.connect(emitLog)
                emitLog()
                return true
            }
        } catch (error) {
        }
        try {
            if (typeof shaderItem.compilationLogChanged === "function") {
                shaderItem.compilationLogChanged.connect(emitLog)
                emitLog()
                return true
            }
        } catch (error) {
        }
        return false
    }

    function resolvedShaderUrl(resourceName, resourceDirectory) {
        var baseDirectory = resourceDirectory && resourceDirectory.length
                ? resourceDirectory
                : (useGlesShaders ? glesShaderResourceDirectory : shaderResourceDirectory)
        return Qt.resolvedUrl(baseDirectory + resourceName)
    }

    function shaderResourceExists(url, resourceName, suppressErrors) {
        if (!url)
            return false

        var normalizedUrl = url
        if (typeof normalizedUrl === "object" && normalizedUrl !== null) {
            try {
                if (typeof normalizedUrl.toString === "function")
                    normalizedUrl = normalizedUrl.toString()
            } catch (error) {
            }
        }

        if (!normalizedUrl || !normalizedUrl.length)
            return false

        if (objectHasOwn.call(shaderResourceAvailabilityCache, normalizedUrl))
            return shaderResourceAvailabilityCache[normalizedUrl]

        var available = false

        var manifestEntry
        var manifestHasEntry = false
        var manifestEnabled = true
        var manifestPaths = []
        var normalizedUrlPath = ""
        var matchesManifestPath = false
        if (resourceName && objectHasOwn.call(shaderResourceManifest, resourceName)) {
            manifestEntry = shaderResourceManifest[resourceName]
            manifestHasEntry = true
            if (typeof manifestEntry === "boolean") {
                manifestEnabled = manifestEntry
            } else if (manifestEntry === null || manifestEntry === undefined) {
                manifestEnabled = false
            } else if (typeof manifestEntry === "string") {
                manifestPaths.push(manifestEntry)
            } else if (typeof manifestEntry === "object") {
                if (objectHasOwn.call(manifestEntry, "enabled"))
                    manifestEnabled = manifestEntry.enabled !== false
                if (objectHasOwn.call(manifestEntry, "path")) {
                    var manifestPath = manifestEntry.path
                    if (manifestPath && typeof manifestPath === "string")
                        manifestPaths.push(manifestPath)
                }
                if (objectHasOwn.call(manifestEntry, "paths") && manifestEntry.paths) {
                    var manifestPathList = manifestEntry.paths
                    for (var mpIdx = 0; mpIdx < manifestPathList.length; ++mpIdx) {
                        var manifestPathCandidate = manifestPathList[mpIdx]
                        if (!manifestPathCandidate || typeof manifestPathCandidate !== "string")
                            continue
                        if (manifestPaths.indexOf(manifestPathCandidate) === -1)
                            manifestPaths.push(manifestPathCandidate)
                    }
                }
            }
            if (!manifestEnabled) {
                shaderResourceAvailabilityCache[normalizedUrl] = false
                if (!suppressErrors)
                    console.error("❌ PostEffects: shader resource disabled by manifest", resourceName, normalizedUrl)
                return false
            }
            normalizedUrlPath = String(normalizedUrl).replace(/\\/g, "/")
        }

        if (manifestHasEntry && manifestEnabled) {
            var shaderRootHint = shaderRootUrl

            function manifestPathMatches(manifestPathEntry) {
                if (!manifestPathEntry)
                    return false

                var normalizedEntry = String(manifestPathEntry).replace(/\\/g, "/")
                if (!normalizedEntry.length)
                    return false

                if (normalizedUrlPath.endsWith(normalizedEntry))
                    return true

                var trimmedEntry = normalizedEntry.replace(/^\/+/, "")
                if (!trimmedEntry.length)
                    return false

                if (normalizedUrlPath.endsWith("/" + trimmedEntry))
                    return true

                var shaderRootIndex = normalizedUrlPath.indexOf(shaderRootHint)
                if (shaderRootIndex !== -1) {
                    var relativeUrlPath = normalizedUrlPath.slice(shaderRootIndex + shaderRootHint.length)
                    if (relativeUrlPath === trimmedEntry)
                        return true
                }

                return false
            }

            matchesManifestPath = manifestPaths.length === 0
            if (!matchesManifestPath) {
                for (var pathIdx = 0; pathIdx < manifestPaths.length; ++pathIdx) {
                    if (manifestPathMatches(manifestPaths[pathIdx])) {
                        matchesManifestPath = true
                        break
                    }
                }
            }

            if (matchesManifestPath && manifestPaths.length > 0) {
                shaderResourceAvailabilityCache[normalizedUrl] = true
                return true
            }
        }

        function checkAvailability(method) {
            try {
                var xhr = new XMLHttpRequest()
                xhr.open(method, normalizedUrl, false)
                xhr.send()
                if (xhr.status === 200 || xhr.status === 0) {
                    available = true
                    return true
                }
                if (xhr.status === 405 || xhr.status === 501)
                    return false
            } catch (error) {
                console.debug("PostEffects: shader availability check failed", resourceName, method, error)
            }
            return false
        }

        if (!checkAvailability("HEAD"))
            checkAvailability("GET")

        if (available) {
            shaderResourceAvailabilityCache[normalizedUrl] = true
            return true
        }

        if (manifestHasEntry && manifestEnabled) {
            if (matchesManifestPath) {
                shaderResourceAvailabilityCache[normalizedUrl] = false
                if (!suppressErrors)
                    console.error("❌ PostEffects: shader manifest mismatch", resourceName, normalizedUrl)
                return false
            }
            shaderResourceAvailabilityCache[normalizedUrl] = false
            if (!suppressErrors)
                console.error("❌ PostEffects: shader resource missing", resourceName, normalizedUrl)
            return false
        }

        shaderResourceAvailabilityCache[normalizedUrl] = false
        if (!suppressErrors)
            console.error("❌ PostEffects: shader resource missing", resourceName, normalizedUrl)

        return false
    }

    function shaderVariantCandidateNames(baseName, extension, suffixes, normalizedName) {
        var candidates = []
        var effectiveSuffixes = suffixes || []
        for (var sIdx = 0; sIdx < effectiveSuffixes.length; ++sIdx) {
            var suffix = effectiveSuffixes[sIdx]
            if (!suffix || !suffix.length)
                continue
            var candidateName = baseName + suffix + extension
            if (candidates.indexOf(candidateName) === -1)
                candidates.push(candidateName)
        }
        var normalizedCandidate = normalizedName && normalizedName.length
                ? normalizedName
                : baseName + extension
        if (candidates.indexOf(normalizedCandidate) === -1)
            candidates.push(normalizedCandidate)
        return candidates
    }

    function shaderPath(fileName) {
        if (!fileName || typeof fileName !== "string")
            return ""

        var normalized = String(fileName)
        var dotIndex = normalized.lastIndexOf(".")
        var baseName = dotIndex >= 0 ? normalized.slice(0, dotIndex) : normalized
        var extension = dotIndex >= 0 ? normalized.slice(dotIndex) : ""
        var suffixes = useGlesShaders ? glesShaderSuffixes : desktopShaderSuffixes

        var candidateNames = shaderVariantCandidateNames(baseName, extension, suffixes, normalized)

        var directories = shaderResourceDirectories
        if (!directories || !directories.length)
            directories = [useGlesShaders ? glesShaderResourceDirectory : shaderResourceDirectory]

        var selectedName = normalized
        var selectedUrl = resolvedShaderUrl(normalized, directories[0])
        var found = false
        for (var idx = 0; idx < candidateNames.length; ++idx) {
            var candidateName = candidateNames[idx]
            var suppressErrors = candidateName === normalized ? false : true
            var candidateFound = false
            for (var dirIdx = 0; dirIdx < directories.length; ++dirIdx) {
                var directory = directories[dirIdx]
                var candidateUrl = resolvedShaderUrl(candidateName, directory)
                if (shaderResourceExists(candidateUrl, candidateName, suppressErrors)) {
                    selectedName = candidateName
                    selectedUrl = candidateUrl
                    found = true
                    candidateFound = true
                    break
                }
            }
            if (candidateFound) {
                break
            }
            if (useGlesShaders && candidateName !== normalized) {
                if (!objectHasOwn.call(shaderVariantMissingWarnings, candidateName)) {
                    shaderVariantMissingWarnings[candidateName] = true
                    console.warn(`⚠️ PostEffects: GLES shader variant '${candidateName}' not found; using compatibility fallback`)
                }
            }
        }

        var glesVariantList = []
        if (useGlesShaders)
            glesVariantList = candidateNames.slice(0, Math.max(candidateNames.length - 1, 0))
        var requireCompatibilityFallback = false
        var fallbackCandidateNames = []
        var fallbackSelectedName = ""
        if (useGlesShaders && glesVariantList.length > 0) {
            var baseRequiresFallback = selectedName === normalized || !found
            if (baseRequiresFallback) {
                var fallbackBaseName = baseName.endsWith("_fallback") ? baseName : baseName + "_fallback"
                fallbackCandidateNames = shaderVariantCandidateNames(
                            fallbackBaseName,
                            extension,
                            glesShaderSuffixes,
                            fallbackBaseName + extension)
            }

            if (!found || selectedName === normalized) {
                if (!found)
                    console.warn("⚠️ PostEffects: GLES shader variants missing; trying fallback", glesVariantList)
                else
                    console.warn("⚠️ PostEffects: GLES shader variant not resolved; falling back", glesVariantList)

                var fallbackResolved = false
                for (var fbIdx = 0; fbIdx < fallbackCandidateNames.length && !fallbackResolved; ++fbIdx) {
                    var fallbackName = fallbackCandidateNames[fbIdx]
                    for (var fbDirIdx = 0; fbDirIdx < directories.length && !fallbackResolved; ++fbDirIdx) {
                        var fallbackUrl = resolvedShaderUrl(fallbackName, directories[fbDirIdx])
                        if (shaderResourceExists(fallbackUrl, fallbackName, false)) {
                            selectedName = fallbackName
                            selectedUrl = fallbackUrl
                            fallbackSelectedName = fallbackName
                            fallbackResolved = true
                        }
                    }
                }

                if (fallbackResolved && fallbackSelectedName.length > 0) {
                    requireCompatibilityFallback = true
                    found = true
                    console.warn("⚠️ PostEffects: GLES fallback shader selected", fallbackSelectedName)
                } else if (!found) {
                    requestDesktopShaderProfile(`Shader ${normalized} lacks GLES variants (${glesVariantList.join(", ")}); enforcing desktop profile`)
                }
            }
        }

        if (requireCompatibilityFallback) {
            if (!objectHasOwn.call(shaderCompatibilityOverrides, normalized))
                console.warn("⚠️ PostEffects: forcing fallback shaders for", normalized, "due to missing GLES profile")
            shaderCompatibilityOverrides[normalized] = true
        } else if (objectHasOwn.call(shaderCompatibilityOverrides, normalized)) {
            delete shaderCompatibilityOverrides[normalized]
        }

        var previousSelection = shaderVariantSelectionCache[normalized]
        if (previousSelection !== selectedName) {
            shaderVariantSelectionCache[normalized] = selectedName
            var profileLabel = useGlesShaders ? "OpenGL ES" : "Desktop"
            console.log(`🌐 PostEffects: resolved ${profileLabel} shader '${normalized}' -> '${selectedName}'`)
        }

        return sanitizedShaderUrl(selectedUrl, selectedName)
    }

    function resetShaderCaches() {
        shaderResourceAvailabilityCache = ({})
        shaderSanitizationCache = ({})
        shaderVariantSelectionCache = ({})
        shaderProfileMismatchWarnings = ({})
        shaderCompatibilityOverrides = ({})
        shaderVariantMissingWarnings = ({})
    }

    function requestDesktopShaderProfile(reason) {
        if (forceDesktopShaderProfile)
            return
        if (reportedGlesContext) {
            if (!objectHasOwn.call(shaderProfileMismatchWarnings, reason)) {
                shaderProfileMismatchWarnings[reason] = true
                console.warn(
                            "⚠️ PostEffects:", reason,
                            "– keeping OpenGL ES profile because desktop shaders are incompatible")
            }
            return
        }
        console.warn("⚠️ PostEffects:", reason, "– forcing desktop shader profile")
        forceDesktopShaderProfile = true
        resetShaderCaches()
    }

    function handleShaderCompilationLog(shaderId, message) {
        if (!useGlesShaders)
            return
        if (!message || !message.length)
            return
        var normalized = String(message).toLowerCase()
        if (normalized.indexOf("#version") === -1)
            return
        if (normalized.indexOf("profile") === -1 && normalized.indexOf("expected newline") === -1)
            return

        var reason = `Shader ${shaderId} reported #version incompatibility`
        if (!objectHasOwn.call(shaderProfileMismatchWarnings, reason)) {
            shaderProfileMismatchWarnings[reason] = true
            console.warn(
                        "⚠️ PostEffects:", reason,
                        "– activating fallback shaders without switching to desktop profile")
        }
        requestDesktopShaderProfile(reason)
    }

    function handleEffectShaderStatusChange(effectId, effectItem, shaderItem, shaderId, isFallback) {
        if (!shaderItem || !effectItem)
            return
        var status
        try {
            status = shaderItem.status
        } catch (error) {
            console.debug("PostEffects: unable to read shader status", effectId, shaderId, error)
            return
        }
        var cacheKey = effectId + "::" + shaderId
        var cachedStatuses = shaderStatusCache
        if (cachedStatuses && cachedStatuses[cacheKey] === status)
            return
        if (!cachedStatuses || typeof cachedStatuses !== "object")
            cachedStatuses = ({})
        cachedStatuses[cacheKey] = status
        shaderStatusCache = cachedStatuses
        // qmllint disable property
        if (status === Shader.Error) {
            var message = shaderCompilationMessage(shaderItem)
            if (!message.length) {
                message = isFallback
                        ? qsTr("%1 fallback shader %2 compilation failed").arg(effectId).arg(shaderId)
                        : qsTr("%1 shader %2 compilation failed").arg(effectId).arg(shaderId)
            }
            console.error(`❌ PostEffects (${effectId}):`, message)
            if (isFallback) {
                try {
                    effectItem.lastErrorLog = message
                } catch (error) {
                }
                try {
                    effectItem.persistentFailure = true
                } catch (error) {
                }
                root.setEffectPersistentFailure(effectId, true, message)
                root.notifyEffectCompilation(effectId, true, message)
                return
            }
            try {
                effectItem.compilationErrorLog = message
            } catch (error) {
            }
            try {
                if ("fallbackDueToCompilation" in effectItem)
                    effectItem.fallbackDueToCompilation = true
            } catch (error) {
            }
            if (!effectItem.fallbackActive)
                effectItem.fallbackActive = true
            if (effectItem.lastErrorLog !== message)
                effectItem.lastErrorLog = message
            root.notifyEffectCompilation(effectId, effectItem.fallbackActive, effectItem.lastErrorLog)
            return
        }
        if (status === Shader.Ready && isFallback) {
            var hadPersistentFailure = false
            try {
                hadPersistentFailure = !!effectItem.persistentFailure
            } catch (error) {
            }
            if (hadPersistentFailure) {
                try {
                    effectItem.persistentFailure = false
                } catch (error) {
                }
                root.setEffectPersistentFailure(effectId, false, "")
            }
        }
        if (status === Shader.Ready && !isFallback) {
            var dueToCompilation = false
            try {
                dueToCompilation = !!effectItem.fallbackDueToCompilation
            } catch (error) {
            }
            if (!dueToCompilation)
                return
            try {
                effectItem.fallbackDueToCompilation = false
            } catch (error) {
            }
            try {
                effectItem.compilationErrorLog = ""
            } catch (error) {
            }
            var requirementActive = false
            try {
                requirementActive = !!effectItem.fallbackDueToRequirements
            } catch (error) {
            }
            if (!requirementActive) {
                if (effectItem.fallbackActive)
                    effectItem.fallbackActive = false
                if (effectItem.lastErrorLog.length)
                    effectItem.lastErrorLog = ""
            } else {
                var requirementLog = ""
                try {
                    if (effectItem.requirementFallbackLog && effectItem.requirementFallbackLog.length)
                        requirementLog = effectItem.requirementFallbackLog
                } catch (error) {
                }
                if (!requirementLog.length) {
                    try {
                        if (effectItem.fallbackMessage)
                            requirementLog = effectItem.fallbackMessage
                    } catch (error) {
                    }
                }
                if (requirementLog.length && effectItem.lastErrorLog !== requirementLog)
                    effectItem.lastErrorLog = requirementLog
            }
            root.notifyEffectCompilation(effectId, effectItem.fallbackActive, effectItem.lastErrorLog)
        }
        // qmllint enable property
    }

    // qmllint disable unqualified
    function sanitizedShaderUrl(url, resourceName) {
        if (!url)
            return url

        var normalizedUrl = url
        if (typeof normalizedUrl === "object" && normalizedUrl !== null) {
            try {
                if (typeof normalizedUrl.toString === "function")
                    normalizedUrl = normalizedUrl.toString()
            } catch (error) {
            }
        }

        if (!normalizedUrl || !normalizedUrl.length)
            return normalizedUrl

        if (objectHasOwn.call(shaderSanitizationCache, normalizedUrl))
            return shaderSanitizationCache[normalizedUrl]

        var sanitizedUrl = normalizedUrl
        var sanitizationApplied = false

        try {
            var xhr = new XMLHttpRequest()
            xhr.open("GET", normalizedUrl, false)
            xhr.responseType = "text"
            xhr.send()
            if (xhr.status === 200 || xhr.status === 0) {
                var shaderSource = xhr.responseText
                if (shaderSource) {
                    var normalized = shaderSource
                    var mutated = false

                    if (normalized.indexOf("\r") !== -1) {
                        normalized = normalized.replace(/\r\n/g, "\n").replace(/\r/g, "\n")
                        mutated = true
                    }

                    if (normalized.length && normalized.charCodeAt(0) === 0xFEFF) {
                        normalized = normalized.slice(1)
                        mutated = true
                    }

                    var leadingWhitespaceMatch = normalized.match(/^[\s]+/)
                    if (leadingWhitespaceMatch && leadingWhitespaceMatch[0].length) {
                        normalized = normalized.slice(leadingWhitespaceMatch[0].length)
                        mutated = true
                    }

                    if (mutated && normalized !== shaderSource) {
                        var cacheKey = resourceName || normalizedUrl
                        if (!objectHasOwn.call(shaderSanitizationWarnings, cacheKey)) {
                            console.warn(
                                        "⚠️ PostEffects: shader", resourceName,
                                        "contains leading BOM/whitespace incompatible with Qt RHI; please clean the source file")
                            shaderSanitizationWarnings[cacheKey] = true
                        }
                        sanitizationApplied = true
                    }
                }
            }
        } catch (error) {
            console.debug("PostEffects: shader normalization skipped", resourceName, error)
        }

        shaderSanitizationCache[normalizedUrl] = sanitizedUrl
        if (sanitizationApplied)
            shaderSanitizationCache[normalizedUrl] = normalizedUrl
        return sanitizedUrl
    }
    // qmllint enable unqualified

    // Примечание по совместимости: для профиля OpenGL ES теперь поставляются
    // отдельные GLSL-файлы с суффиксом _es и корректной директивой #version 300 es.
    // При отсутствии GLES-варианта компонент автоматически переключается на
    // десктопный профиль, чтобы не оставлять эффект без шейдера.

    // Свойства управления эффектами
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
    property alias dofFocusDistance: dofEffect.focusDistance
    property alias dofFocusRange: dofEffect.focusRange
    property alias dofBlurAmount: dofEffect.blurAmount
    property alias depthOfFieldFallbackActive: dofEffect.fallbackActive
    property alias depthOfFieldFallbackDueToRequirements: dofEffect.fallbackDueToRequirements
    property alias depthOfFieldDepthTextureAvailable: dofEffect.depthTextureAvailable

    // Параметры камеры View3D, необходимые для корректного расчёта глубины
    property real cameraClipNear: 0.1
    property real cameraClipFar: 10000.0

    property bool motionBlurEnabled: false
    property alias motionBlurStrength: motionBlurEffect.strength
    property alias motionBlurSamples: motionBlurEffect.samples

    /**
     * Выбирает шейдерные программы для эффекта с учётом состояния фоллбэка.
     *
     * @param {bool} isEnabled     Флаг включения эффекта на уровне UI.
     * @param {Effect} effectItem   QML-объект Effect, для которого выполняется выбор.
     * @param {Shader} activeShader Основной шейдер, используемый при успешной компиляции.
     * @param {Shader} [fallbackShader] Необязательный альтернативный шейдер на случай ошибки компиляции.
     * @param {string} [shaderBaseName] Имя исходного файла шейдера для отслеживания совместимости профилей.
     * @returns {Shader[]} Список шейдеров, который необходимо передать в Pass.shaders.
     */
    function resolveShaders(isEnabled, effectItem, activeShader, fallbackShader, shaderBaseName) {
        const hasFallback = fallbackShader !== undefined && fallbackShader !== null
        if (root.effectsBypass)
            return []
        var persistentFailureActive = false
        try {
            persistentFailureActive = !!effectItem.persistentFailure
        } catch (error) {
        }
        if (persistentFailureActive)
            return []
        // Если эффект выключен, исключаем его из графа пост-обработки.
        if (!isEnabled) {
            trySetEffectProperty(effectItem, "fallbackActive", false)
            trySetEffectProperty(effectItem, "fallbackForcedByCompatibility", false)
            return []
        }
        // Включаем эффект и выбираем нужный шейдер. Если не хватает данных и активируется
        // фоллбэк, всегда возвращаем валидный шейдер.
        var compatibilityOverrideActive = false
        if (useGlesShaders && shaderBaseName && objectHasOwn.call(shaderCompatibilityOverrides, shaderBaseName))
            compatibilityOverrideActive = !!shaderCompatibilityOverrides[shaderBaseName]

        if (!compatibilityOverrideActive) {
            trySetEffectProperty(effectItem, "fallbackForcedByCompatibility", false)
            var fallbackLocked = false
            try {
                if (effectItem.fallbackDueToCompilation)
                    fallbackLocked = true
            } catch (error) {
            }
            if (!fallbackLocked) {
                try {
                    if (effectItem.fallbackDueToRequirements)
                        fallbackLocked = true
                } catch (error) {
                }
            }
            if (!fallbackLocked && effectItem.fallbackActive)
                trySetEffectProperty(effectItem, "fallbackActive", false)
        }

        if (compatibilityOverrideActive) {
            trySetEffectProperty(effectItem, "fallbackForcedByCompatibility", true)
            trySetEffectProperty(effectItem, "fallbackActive", true)
            if (hasFallback)
                return [fallbackShader]
            console.warn("⚠️", effectItem, "missing fallback shader for", shaderBaseName, "– disabling effect")
            return []
        }
        if (effectItem.fallbackActive)
            return hasFallback ? [fallbackShader] : []
        return [activeShader]
    }

    function ensureEffectRequirement(effectItem, propertyName, value, successLog, failureLog) {
        if (trySetEffectProperty(effectItem, propertyName, value)) {
            if (successLog && successLog.length > 0)
                console.log("✅", successLog)
            return true
        }
        const message = failureLog && failureLog.length > 0
                ? failureLog
                : `Effect requirement '${propertyName}' is not supported`
        console.warn("⚠️", message)
        return false
    }

    Component.onCompleted: {
        console.log("🎨 Post Effects Collection loaded")
        console.log("   Graphics API:", rendererGraphicsApi)
        if (normalizedRendererGraphicsApi.length)
            console.log("   Normalized API:", normalizedRendererGraphicsApi)
        console.log(
                    "   Shader profile:",
                    useGlesShaders
                    ? "OpenGL ES (GLSL 300 es)"
                    : "Desktop (GLSL 450 core)"
                    )
        console.log("   Profile decision flags ->",
                    "preferDesktop:", preferDesktopShaderProfile,
                    "reportedGles:", reportedGlesContext,
                    "forceDesktopOverride:", forceDesktopShaderProfile)
        if (legacyFallbackReason.length)
            console.warn("⚠️ PostEffects:", legacyFallbackReason)
        console.log("   Available effects: Bloom, SSAO, DOF, Motion Blur")
    }

    function valueFromKeys(container, keys) {
        if (!container || typeof container !== "object")
            return undefined
        var list = Array.isArray(keys) ? keys : [keys]
        for (var i = 0; i < list.length; ++i) {
            var key = list[i]
            if (objectHasOwn.call(container, key))
                return container[key]
        }
        return undefined
    }

    function valueFromPayload(params, keys, nestedKey) {
        var direct = valueFromKeys(params, keys)
        if (direct !== undefined)
            return direct
        if (nestedKey && params && typeof params[nestedKey] === "object")
            return valueFromKeys(params[nestedKey], keys)
        return undefined
    }

    function boolFromPayload(params, keys, nestedKey) {
        var raw = valueFromPayload(params, keys, nestedKey)
        if (raw === undefined)
            return undefined
        if (typeof raw === "boolean")
            return raw
        if (typeof raw === "number")
            return raw !== 0
        if (typeof raw === "string") {
            var lowered = raw.trim().toLowerCase()
            if (["true", "1", "yes", "on"].indexOf(lowered) !== -1)
                return true
            if (["false", "0", "no", "off"].indexOf(lowered) !== -1)
                return false
        }
        return !!raw
    }

    function numberFromPayload(params, keys, nestedKey) {
        var raw = valueFromPayload(params, keys, nestedKey)
        if (raw === undefined)
            return undefined
        var numeric = Number(raw)
        return isFinite(numeric) ? numeric : undefined
    }

    // Эффекты для добавления в View3D
    property list<Effect> effectList: [
        bloomEffect,
        ssaoEffect,
        dofEffect,
        motionBlurEffect
    ]

    // Bloom Effect (эффект свечения)
    Effect {
        id: bloomEffect

        Binding {
            target: bloomEffect
            property: "enabled"
            value: root.bloomEnabled
        }

        property bool fallbackActive: false
        property string lastErrorLog: ""
        property bool componentCompleted: false
        property bool fallbackDueToCompilation: false
        property string compilationErrorLog: ""
        property bool fallbackForcedByCompatibility: false
        property bool persistentFailure: false
        readonly property string fallbackMessage: qsTr("Bloom: fallback shader active")
        readonly property string compatibilityFallbackMessage: {
            var versionLabel = root.openGlVersionLabel.length
                    ? root.openGlVersionLabel
                    : "3.3"
            return qsTr("Bloom: forcing GLSL 330 fallback shader for OpenGL %1")
                    .arg(versionLabel)
        }

        Component.onCompleted: {
            if (root.enforceLegacyFallbackShaders && !fallbackForcedByCompatibility) {
                fallbackForcedByCompatibility = true
                var compatibilityLog = compatibilityFallbackMessage.length
                        ? compatibilityFallbackMessage
                        : root.legacyFallbackReason
                if ((!lastErrorLog || !lastErrorLog.length) && compatibilityLog.length)
                    lastErrorLog = compatibilityLog
                fallbackActive = true
                if (compatibilityLog.length)
                    console.warn("⚠️", compatibilityLog)
            }
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = fallbackMessage
            else if (!fallbackActive && lastErrorLog)
                lastErrorLog = ""
            root.notifyEffectCompilation("bloom", fallbackActive, lastErrorLog)
            componentCompleted = true
        }

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = fallbackMessage
            else if (!fallbackActive && lastErrorLog)
                lastErrorLog = ""
            root.notifyEffectCompilation("bloom", fallbackActive, lastErrorLog)
        }

        property real intensity: 0.3      // Интенсивность свечения
        property real threshold: 0.7      // Порог яркости для свечения
        property real blurAmount: 1.0     // Размытие свечения

        onBlurAmountChanged: {
            if (blurAmount < 0.0)
                blurAmount = 0.0
        }

        Shader {
            id: bloomFragmentShader
            stage: Shader.Fragment
            property real uIntensity: bloomEffect.intensity
            property real uThreshold: bloomEffect.threshold
            property real uBlurAmount: bloomEffect.blurAmount
            shader: root.shaderPath("bloom.frag")
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(bloomFragmentShader, "bloom.frag"))
                    console.debug("PostEffects: shader log handler unavailable for bloom.frag")
            }
        }

        Connections {
            target: bloomFragmentShader
            ignoreUnknownSignals: true
            function onStatusChanged(status) {
                root.handleEffectShaderStatusChange("bloom", bloomEffect, bloomFragmentShader, "bloom.frag", false)
            }
        }

        Shader {
            id: bloomFallbackShader
            stage: Shader.Fragment
            shader: root.shaderPath("bloom_fallback.frag")
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(bloomFallbackShader, "bloom_fallback.frag"))
                    console.debug("PostEffects: shader log handler unavailable for bloom_fallback.frag")
            }
        }

        Connections {
            target: bloomFallbackShader
            ignoreUnknownSignals: true
            function onStatusChanged() {
                root.handleEffectShaderStatusChange("bloom", bloomEffect, bloomFallbackShader, "bloom_fallback.frag", true)
            }
        }


        passes: [
            Pass {
                shaders: root.resolveShaders(root.bloomEnabled, bloomEffect, bloomFragmentShader, bloomFallbackShader, "bloom.frag")
            }
        ]
    }

    // SSAO Effect (Screen Space Ambient Occlusion)
    Effect {
        id: ssaoEffect

        Binding {
            target: ssaoEffect
            property: "enabled"
            value: root.ssaoEnabled
        }

        property bool fallbackActive: false
        property string lastErrorLog: ""
        property bool depthTextureAvailable: false
        property bool normalTextureAvailable: false
        property bool componentCompleted: false
        property bool fallbackDueToCompilation: false
        property bool fallbackDueToRequirements: false
        property string compilationErrorLog: ""
        property string requirementFallbackLog: ""
        property bool fallbackForcedByCompatibility: false
        property bool persistentFailure: false
        readonly property string fallbackMessage: qsTr("SSAO: fallback shader active")
        readonly property string compatibilityFallbackMessage: {
            var versionLabel = root.openGlVersionLabel.length
                    ? root.openGlVersionLabel
                    : "3.3"
            return qsTr("SSAO: forcing GLSL 330 fallback shader for OpenGL %1")
                    .arg(versionLabel)
        }

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
                    requirementFallbackLog = qsTr("SSAO: normal texture unavailable in this runtime; enabling compatibility SSAO")
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

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = fallbackMessage
            else if (!fallbackActive && lastErrorLog)
                lastErrorLog = ""
            root.notifyEffectCompilation("ssao", fallbackActive, lastErrorLog)
        }

        property real intensity: 0.5      // Интенсивность затенения
        property real radius: 2.0         // Радиус сэмплинга
        property real bias: 0.025         // Смещение для избежания самозатенения
        property bool dither: true        // Включение рандомизации сэмплов
        property int samples: 16          // Количество сэмплов

        onSamplesChanged: {
            if (samples < 1)
                samples = 1
        }

        Shader {
            id: ssaoFragmentShader
            stage: Shader.Fragment
            property real uIntensity: ssaoEffect.intensity
            property real uRadius: ssaoEffect.radius
            property real uBias: ssaoEffect.bias
            property int uSamples: ssaoEffect.samples
            property real uDitherToggle: ssaoEffect.dither ? 1.0 : 0.0
            shader: root.shaderPath("ssao.frag")
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(ssaoFragmentShader, "ssao.frag"))
                    console.debug("PostEffects: shader log handler unavailable for ssao.frag")
            }
        }

        Connections {
            target: ssaoFragmentShader
            ignoreUnknownSignals: true
            function onStatusChanged(status) {
                root.handleEffectShaderStatusChange("ssao", ssaoEffect, ssaoFragmentShader, "ssao.frag", false)
            }
        }

        Shader {
            id: ssaoFallbackShader
            stage: Shader.Fragment
            shader: root.shaderPath("ssao_fallback.frag")
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(ssaoFallbackShader, "ssao_fallback.frag"))
                    console.debug("PostEffects: shader log handler unavailable for ssao_fallback.frag")
            }
        }

        Connections {
            target: ssaoFallbackShader
            ignoreUnknownSignals: true
            function onStatusChanged(status) {
                root.handleEffectShaderStatusChange("ssao", ssaoEffect, ssaoFallbackShader, "ssao_fallback.frag", true)
            }
        }


        passes: [
            Pass {
                shaders: root.resolveShaders(root.ssaoEnabled, ssaoEffect, ssaoFragmentShader, ssaoFallbackShader, "ssao.frag")
            }
        ]

        // Effect.enabled is controlled externally via root.ssaoEnabled
    }

    // Depth of Field Effect
    Effect {
        id: dofEffect

        Binding {
            target: dofEffect
            property: "enabled"
            value: root.depthOfFieldEnabled
        }

        // Эффект глубины резкости использует буфер глубины сцены
        property bool fallbackActive: false
        property string lastErrorLog: ""
        property bool depthTextureAvailable: false
        property bool componentCompleted: false
        property bool fallbackDueToCompilation: false
        property bool fallbackDueToRequirements: false
        property string compilationErrorLog: ""
        property string requirementFallbackLog: ""
        property bool fallbackForcedByCompatibility: false
        property bool persistentFailure: false
        readonly property string fallbackMessage: qsTr("Depth of Field: fallback shader active")
        readonly property string compatibilityFallbackMessage: {
            var versionLabel = root.openGlVersionLabel.length
                    ? root.openGlVersionLabel
                    : "3.3"
            return qsTr("Depth of Field: forcing GLSL 330 fallback shader for OpenGL %1")
                    .arg(versionLabel)
        }

        property real focusDistance: 2000.0  // Расстояние фокуса (мм)
        property real focusRange: 1000.0     // Диапазон фокуса (мм)
        property real blurAmount: 1.0        // Сила размытия

        property real cameraNear: root.cameraClipNear
        property real cameraFar: root.cameraClipFar


        onBlurAmountChanged: {
            if (blurAmount < 0.0)
                blurAmount = 0.0
        }

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

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = fallbackMessage
            else if (!fallbackActive && lastErrorLog)
                lastErrorLog = ""
            root.notifyEffectCompilation("depthOfField", fallbackActive, lastErrorLog)
        }

        Shader {
            id: dofFragmentShader
            stage: Shader.Fragment
            property real uFocusDistance: dofEffect.focusDistance
            property real uFocusRange: dofEffect.focusRange
            property real uBlurAmount: dofEffect.blurAmount
            property real uCameraNear: dofEffect.cameraNear
            property real uCameraFar: dofEffect.cameraFar
            shader: root.shaderPath("dof.frag")
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(dofFragmentShader, "dof.frag"))
                    console.debug("PostEffects: shader log handler unavailable for dof.frag")
            }
        }

        Connections {
            target: dofFragmentShader
            ignoreUnknownSignals: true
            function onStatusChanged(status) {
                root.handleEffectShaderStatusChange("depthOfField", dofEffect, dofFragmentShader, "dof.frag", false)
            }
        }

        Shader {
            id: dofFallbackShader
            stage: Shader.Fragment
            shader: root.shaderPath("dof_fallback.frag")
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(dofFallbackShader, "dof_fallback.frag"))
                    console.debug("PostEffects: shader log handler unavailable for dof_fallback.frag")
            }
        }

        Connections {
            target: dofFallbackShader
            ignoreUnknownSignals: true
            function onStatusChanged() {
                root.handleEffectShaderStatusChange("depthOfField", dofEffect, dofFallbackShader, "dof_fallback.frag", true)
            }
        }


        passes: [
            Pass {
                shaders: root.resolveShaders(root.depthOfFieldEnabled, dofEffect, dofFragmentShader, dofFallbackShader, "dof.frag")
            }
        ]

        // Effect.enabled is controlled externally via root.depthOfFieldEnabled
    }

    // Motion Blur Effect
    Effect {
        id: motionBlurEffect

        Binding {
            target: motionBlurEffect
            property: "enabled"
            value: root.motionBlurEnabled
        }

        // Эффект размытия движения читает текстуру скоростей
        property bool fallbackActive: false
        property string lastErrorLog: ""
        property bool velocityTextureAvailable: false
        property bool componentCompleted: false
        property bool fallbackDueToCompilation: false
        property bool fallbackDueToRequirements: false
        property string compilationErrorLog: ""
        property string requirementFallbackLog: ""
        property bool fallbackForcedByCompatibility: false
        property bool persistentFailure: false
        readonly property string fallbackMessage: qsTr("Motion Blur: fallback shader active")
        readonly property string compatibilityFallbackMessage: {
            var versionLabel = root.openGlVersionLabel.length
                    ? root.openGlVersionLabel
                    : "3.3"
            return qsTr("Motion Blur: forcing GLSL 330 fallback shader for OpenGL %1")
                    .arg(versionLabel)
        }

        property real strength: 0.5          // Сила размытия движения
        property int samples: 8              // Количество сэмплов
        onSamplesChanged: {
            if (samples < 1)
                samples = 1
        }

        Component.onCompleted: {
            velocityTextureAvailable = root.ensureEffectRequirement(
                        motionBlurEffect,
                        "requiresVelocityTexture",
                        true,
                        "Motion Blur: velocity texture support enabled",
                        "Motion Blur: velocity texture unavailable; using fallback shader")

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

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = fallbackMessage
            else if (!fallbackActive && lastErrorLog)
                lastErrorLog = ""
            root.notifyEffectCompilation("motionBlur", fallbackActive, lastErrorLog)
        }

        Shader {
            id: motionBlurFragmentShader
            stage: Shader.Fragment
            property real uStrength: motionBlurEffect.strength
            property int uSamples: motionBlurEffect.samples
            shader: root.shaderPath("motion_blur.frag")
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(motionBlurFragmentShader, "motion_blur.frag"))
                    console.debug("PostEffects: shader log handler unavailable for motion_blur.frag")
            }
        }

        Connections {
            target: motionBlurFragmentShader
            ignoreUnknownSignals: true
            function onStatusChanged(status) {
                root.handleEffectShaderStatusChange("motionBlur", motionBlurEffect, motionBlurFragmentShader, "motion_blur.frag", false)
            }
        }

        Shader {
            id: motionBlurFallbackShader
            stage: Shader.Fragment
            shader: root.shaderPath("motion_blur_fallback.frag")
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(motionBlurFallbackShader, "motion_blur_fallback.frag"))
                    console.debug("PostEffects: shader log handler unavailable for motion_blur_fallback.frag")
            }
        }

        Connections {
            target: motionBlurFallbackShader
            ignoreUnknownSignals: true
            function onStatusChanged() {
                root.handleEffectShaderStatusChange("motionBlur", motionBlurEffect, motionBlurFallbackShader, "motion_blur_fallback.frag", true)
            }
        }


        passes: [
            Pass {
                shaders: root.resolveShaders(root.motionBlurEnabled, motionBlurEffect, motionBlurFragmentShader, motionBlurFallbackShader, "motion_blur.frag")
            }
        ]

        // Effect.enabled is controlled externally via root.motionBlurEnabled
    }

    function applyPayload(params, environment) {
        logDiagnostics("PostEffects.applyPayload", params, environment)
        var env = environment || null
        var toSceneLength = env && typeof env.toSceneLength === "function"
            ? env.toSceneLength
            : null

        function coerceNumber(value) {
            var numeric = Number(value)
            return isFinite(numeric) ? numeric : undefined
        }

        function coerceInt(value) {
            var numeric = coerceNumber(value)
            if (numeric === undefined)
                return undefined
            return Math.round(numeric)
        }

        function convertLength(value) {
            var numeric = coerceNumber(value)
            if (numeric === undefined)
                return undefined
            return toSceneLength ? toSceneLength(numeric) : numeric
        }

        function assignEffectProperty(effectItem, propertyName, value) {
            if (value === undefined || value === null)
                return
            if (!trySetEffectProperty(effectItem, propertyName, value)) {
                console.debug("PostEffects.applyPayload", "property assignment skipped", propertyName)
            }
        }

        function envHasProperty(propertyName) {
            if (!env)
                return false
            try {
                return objectHasOwn.call(env, propertyName)
            } catch (error) {
                return false
            }
        }

        function payloadHas(source, key) {
            if (!source || typeof source !== "object")
                return false
            return objectHasOwn.call(source, key)
        }

        function assignRootBool(propertyName, value) {
            if (value === undefined)
                return
            var normalized = !!value
            try {
                if (root[propertyName] !== normalized)
                    root[propertyName] = normalized
            } catch (error) {
                console.warn("⚠️ PostEffects:", propertyName, "bool assignment failed", error)
            }
        }

        function assignRootNumber(propertyName, value, options) {
            if (value === undefined)
                return
            var numeric = coerceNumber(value)
            if (numeric === undefined)
                return
            var opts = options || {}
            var finalValue = numeric
            if (opts.min !== undefined && finalValue < opts.min)
                finalValue = opts.min
            if (opts.max !== undefined && finalValue > opts.max)
                finalValue = opts.max
            try {
                root[propertyName] = finalValue
            } catch (error) {
                console.warn("⚠️ PostEffects:", propertyName, "numeric assignment failed", error)
            }
        }

        if (env) {
            if (envHasProperty("bloomEnabled"))
                assignRootBool("bloomEnabled", env.bloomEnabled)

            if (envHasProperty("bloomIntensity")) {
                var envBloomIntensity = coerceNumber(env.bloomIntensity)
                if (envBloomIntensity !== undefined)
                    assignEffectProperty(bloomEffect, "intensity", envBloomIntensity)
            }

            if (envHasProperty("bloomThreshold")) {
                var envBloomThreshold = coerceNumber(env.bloomThreshold)
                if (envBloomThreshold !== undefined)
                    assignEffectProperty(bloomEffect, "threshold", envBloomThreshold)
            }

            if (envHasProperty("bloomSpread")) {
                var envBloomSpread = coerceNumber(env.bloomSpread)
                if (envBloomSpread !== undefined)
                    assignEffectProperty(bloomEffect, "blurAmount", Math.max(0.0, envBloomSpread))
            }

            if (envHasProperty("ssaoEnabled"))
                assignRootBool("ssaoEnabled", env.ssaoEnabled)

            if (envHasProperty("ssaoIntensity")) {
                var envSsaoIntensity = coerceNumber(env.ssaoIntensity)
                if (envSsaoIntensity !== undefined)
                    assignEffectProperty(ssaoEffect, "intensity", envSsaoIntensity)
            }

            if (envHasProperty("ssaoRadius")) {
                var envSsaoRadius = coerceNumber(env.ssaoRadius)
                if (envSsaoRadius !== undefined) {
                    if (envSsaoRadius < 0.1)
                        envSsaoRadius *= 1000.0
                    assignEffectProperty(ssaoEffect, "radius", Math.max(0.01, envSsaoRadius))
                }
            }

            if (envHasProperty("ssaoBias")) {
                var envSsaoBias = coerceNumber(env.ssaoBias)
                if (envSsaoBias !== undefined)
                    assignEffectProperty(ssaoEffect, "bias", Math.max(0.0, envSsaoBias))
            }

            if (envHasProperty("ssaoSampleRate")) {
                var envSsaoSamples = coerceInt(env.ssaoSampleRate)
                if (envSsaoSamples !== undefined)
                    assignEffectProperty(ssaoEffect, "samples", Math.max(1, envSsaoSamples))
            }

            if (envHasProperty("ssaoSamples")) {
                var envSsaoSamplesAlias = coerceInt(env.ssaoSamples)
                if (envSsaoSamplesAlias !== undefined)
                    assignEffectProperty(ssaoEffect, "samples", Math.max(1, envSsaoSamplesAlias))
            }

            if (envHasProperty("ssaoDither")) {
                var envSsaoDither = env.ssaoDither
                if (envSsaoDither !== undefined)
                    assignEffectProperty(ssaoEffect, "dither", !!envSsaoDither)
            }

            if (envHasProperty("internalDepthOfFieldEnabled"))
                assignRootBool("depthOfFieldEnabled", env.internalDepthOfFieldEnabled)
            else if (envHasProperty("depthOfFieldEnabled"))
                assignRootBool("depthOfFieldEnabled", env.depthOfFieldEnabled)

            if (envHasProperty("dofFocusDistance")) {
                var envDofFocus = coerceNumber(env.dofFocusDistance)
                if (envDofFocus !== undefined)
                    assignEffectProperty(dofEffect, "focusDistance", Math.max(0.0, envDofFocus))
            }

            if (envHasProperty("dofFocusRange")) {
                var envDofRange = coerceNumber(env.dofFocusRange)
                if (envDofRange !== undefined)
                    assignEffectProperty(dofEffect, "focusRange", Math.max(0.0, envDofRange))
            }

            if (envHasProperty("dofBlurAmount")) {
                var envDofBlur = coerceNumber(env.dofBlurAmount)
                if (envDofBlur !== undefined)
                    assignEffectProperty(dofEffect, "blurAmount", Math.max(0.0, envDofBlur))
            }

            if (envHasProperty("motionBlurEnabled"))
                assignRootBool("motionBlurEnabled", env.motionBlurEnabled)

            if (envHasProperty("motionBlurStrength")) {
                var envMotionStrength = coerceNumber(env.motionBlurStrength)
                if (envMotionStrength !== undefined)
                    assignEffectProperty(motionBlurEffect, "strength", Math.max(0.0, envMotionStrength))
            }

            if (envHasProperty("motionBlurSamples")) {
                var envMotionSamples = coerceInt(env.motionBlurSamples)
                if (envMotionSamples !== undefined)
                    assignEffectProperty(motionBlurEffect, "samples", Math.max(1, envMotionSamples))
            }
        }

        if (params && typeof params === "object") {
            var bloomEnabledValue = boolFromPayload(params, ["bloomEnabled", "bloom_enabled"], "bloom")
            if (bloomEnabledValue !== undefined)
                assignRootBool("bloomEnabled", bloomEnabledValue)

            var bloomIntensityValue = numberFromPayload(params, ["bloomIntensity", "bloom_intensity"], "bloom")
            if (bloomIntensityValue !== undefined)
                assignEffectProperty(bloomEffect, "intensity", bloomIntensityValue)

            var bloomThresholdValue = numberFromPayload(params, ["bloomThreshold", "bloom_threshold"], "bloom")
            if (bloomThresholdValue !== undefined)
                assignEffectProperty(bloomEffect, "threshold", bloomThresholdValue)

            var bloomBlurValue = numberFromPayload(params, ["bloomBlurAmount", "bloom_spread"], "bloom")
            if (bloomBlurValue !== undefined)
                assignEffectProperty(bloomEffect, "blurAmount", Math.max(0.0, bloomBlurValue))

            var ssaoEnabledValue = boolFromPayload(params, ["ssaoEnabled", "ao_enabled"], "ssao")
            if (ssaoEnabledValue !== undefined)
                assignRootBool("ssaoEnabled", ssaoEnabledValue)

            var ssaoIntensityValue = numberFromPayload(params, ["ssaoIntensity", "ao_strength"], "ssao")
            if (ssaoIntensityValue !== undefined)
                assignEffectProperty(ssaoEffect, "intensity", ssaoIntensityValue)

            var ssaoRadiusValue = numberFromPayload(params, ["ssaoRadius", "ao_radius"], "ssao")
            if (ssaoRadiusValue !== undefined) {
                var radius = ssaoRadiusValue
                if (radius < 0.1)
                    radius *= 1000.0
                assignEffectProperty(ssaoEffect, "radius", Math.max(0.01, radius))
            }

            var ssaoBiasValue = numberFromPayload(params, ["ssaoBias", "ao_bias"], "ssao")
            if (ssaoBiasValue !== undefined)
                assignEffectProperty(ssaoEffect, "bias", Math.max(0.0, ssaoBiasValue))

            var ssaoDitherValue = boolFromPayload(params, ["ssaoDither", "ao_dither"], "ssao")
            if (ssaoDitherValue !== undefined)
                assignEffectProperty(ssaoEffect, "dither", !!ssaoDitherValue)

            var ssaoSamplesValue = numberFromPayload(params, ["ssaoSamples", "ao_sample_rate"], "ssao")
            if (ssaoSamplesValue !== undefined)
                assignEffectProperty(ssaoEffect, "samples", Math.max(1, Math.round(ssaoSamplesValue)))

            var dofEnabledValue = boolFromPayload(params, ["depthOfFieldEnabled", "depth_of_field"], "depthOfField")
            if (dofEnabledValue !== undefined)
                assignRootBool("depthOfFieldEnabled", dofEnabledValue)

            var dofFocusValue = numberFromPayload(params, ["dofFocusDistance", "dof_focus_distance"], "depthOfField")
            if (dofFocusValue !== undefined) {
                var convertedFocus = convertLength(dofFocusValue)
                if (convertedFocus !== undefined)
                    assignEffectProperty(dofEffect, "focusDistance", Math.max(0.0, convertedFocus))
            }

            var dofRangeValue = numberFromPayload(params, ["dofFocusRange", "dof_focus_range"], "depthOfField")
            if (dofRangeValue !== undefined) {
                var convertedRange = convertLength(dofRangeValue)
                if (convertedRange !== undefined)
                    assignEffectProperty(dofEffect, "focusRange", Math.max(0.0, convertedRange))
            }

            var dofBlurValue = numberFromPayload(params, ["dofBlurAmount", "dof_blur"], "depthOfField")
            if (dofBlurValue !== undefined)
                assignEffectProperty(dofEffect, "blurAmount", Math.max(0.0, dofBlurValue))

            var motionEnabledValue = boolFromPayload(params, ["motionBlurEnabled", "motion_blur"], "motion")
            if (motionEnabledValue !== undefined)
                assignRootBool("motionBlurEnabled", motionEnabledValue)

            var motionStrengthValue = numberFromPayload(params, ["motionBlurStrength", "motion_blur_amount"], "motion")
            if (motionStrengthValue !== undefined)
                assignEffectProperty(motionBlurEffect, "strength", Math.max(0.0, motionStrengthValue))

            var motionSamplesValue = numberFromPayload(params, ["motionBlurSamples", "motion_blur_samples"], "motion")
            if (motionSamplesValue !== undefined)
                assignEffectProperty(motionBlurEffect, "samples", Math.max(1, Math.round(motionSamplesValue)))
        }
    }

    // Функции управления эффектами
    function enableBloom(intensity, threshold) {
        bloomEffect.intensity = intensity;
        bloomEffect.threshold = threshold;
        root.bloomEnabled = true;
        console.log("✨ Bloom enabled:", intensity, threshold);
    }

    function enableSSAO(intensity, radius) {
        ssaoEffect.intensity = intensity;
        ssaoEffect.radius = radius;
        root.ssaoEnabled = true;
        console.log("🌑 SSAO enabled:", intensity, radius);
    }

    function enableDepthOfField(focusDistance, focusRange) {
        dofEffect.focusDistance = focusDistance;
        dofEffect.focusRange = focusRange;
        root.depthOfFieldEnabled = true;
        console.log("📷 DOF enabled:", focusDistance, focusRange);
    }

    function enableMotionBlur(strength) {
        motionBlurEffect.strength = strength;
        root.motionBlurEnabled = true;
        console.log("💨 Motion Blur enabled:", strength);
    }

    function disableAllEffects() {
        root.bloomEnabled = false;
        root.ssaoEnabled = false;
        root.depthOfFieldEnabled = false;
        root.motionBlurEnabled = false;
        console.log("🚫 All post-effects disabled");
    }

}
// qmllint enable property
