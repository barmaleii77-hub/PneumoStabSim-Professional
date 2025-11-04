import QtQuick
import QtQuick.Window
import QtQuick3D 6.10
// qmllint disable unused-imports
import QtQuick3D.Effects
import QtQuick3D.Helpers
// qmllint enable unused-imports

/*
 * Улучшенный эффект тумана с расширенными настройками
 * Enhanced fog effect with advanced settings
 */
Effect {
    id: fogEffect

    // Управляемые свойства тумана
    property real fogDensity: 0.1          // Плотность тумана (0.0 - 1.0)
    property color fogColor: "#808080"      // Цвет тумана
    property real fogStartDistance: 1000.0  // Расстояние начала тумана
    property real fogEndDistance: 5000.0    // Расстояние конца тумана
    property real fogHeight: 2000.0         // Высота слоя тумана
    property bool heightBasedFog: false     // Туман на основе высоты
    property real fogLeastIntenseY: 0.0     // Нижняя граница высоты
    property real fogMostIntenseY: 3.0      // Верхняя граница высоты
    property real fogHeightCurve: 1.0       // Кривая распределения по высоте
    property bool fogTransmitEnabled: false // Включить просвечивание
    property real fogTransmitCurve: 1.0     // Кривая просвечивания
    property real fogScattering: 0.5        // Рассеивание света в тумане

    // Анимация тумана
    property bool animatedFog: false        // Анимированный туман
    property real animationSpeed: 0.1       // Скорость анимации
    property real time: 0.0                 // Время для анимации

    // Параметры камеры для реконструкции глубины
    property real cameraClipNear: 0.1
    property real cameraClipFar: 10000.0
    property real cameraFieldOfView: 60.0
    property real cameraAspectRatio: 1.0

    // qmllint disable missing-property import
    parameters: [
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
        }
    ]
    // qmllint enable missing-property import

    // Доступность depth-текстуры
    property bool depthTextureAvailable: false
    property bool forceDepthTextureUnavailable: false
    property bool _depthInitializationStarted: false
    readonly property bool _depthInitializationComplete: initializeDepthTextureSupport()

    property bool fallbackActive: false
    property string fallbackReason: ""
    property bool fallbackDueToDepth: false
    property bool fallbackDueToCompilation: false
    property string compilationErrorLog: ""
    readonly property bool compilationFallbackActive: fallbackDueToCompilation
    property var activePassShaders: {
        var _ = _depthInitializationComplete
        return []
    }
    property bool _usingFallbackPassConfiguration: false

    onDepthTextureAvailableChanged: {
        fallbackDueToDepth = !depthTextureAvailable
        updateFallbackActivation()
    }

    onForceDepthTextureUnavailableChanged: {
        if (_depthInitializationStarted)
            initializeDepthTextureSupport()
    }

    onFallbackActiveChanged: {
        if (fallbackActive) {
            var message = fallbackReason.length
                    ? fallbackReason
                    : qsTr("Fallback shader active")
            console.warn("⚠️ FogEffect:", message)
        } else {
            console.log("✅ FogEffect: primary shader path restored")
        }
        refreshPassConfiguration()
    }

    onFallbackReasonChanged: {
        if (fallbackActive && fallbackReason.length)
            console.warn("⚠️ FogEffect: fallback reason updated ->", fallbackReason)
    }

    function enableDepthTextureSupport() {
        const propertyName = "requiresDepthTexture"
        var depthReady = true
        var previousDepthState = depthTextureAvailable

        if (forceDepthTextureUnavailable) {
            depthReady = false
        } else if (propertyName in fogEffect) {
            try {
                fogEffect[propertyName] = true
            } catch (error) {
                depthReady = false
                console.debug("FogEffect requiresDepthTexture assignment failed", error)
            }
        } else {
            depthReady = false
        }

        if (depthReady) {
            depthTextureAvailable = true
            fallbackDueToDepth = false
            if (!previousDepthState)
                console.log("🌫️ FogEffect: depth texture support enabled")
        } else {
            depthTextureAvailable = false
            fallbackDueToDepth = true
            var warningMessage = forceDepthTextureUnavailable
                    ? qsTr("Depth texture support forced unavailable; using fallback shader")
                    : qsTr("Depth texture not supported; using fallback shader")
            console.warn("⚠️ FogEffect:", warningMessage)
        }

        if (previousDepthState === depthTextureAvailable)
            updateFallbackActivation()

        return depthTextureAvailable
    }

    function initializeDepthTextureSupport() {
        if (!_depthInitializationStarted)
            _depthInitializationStarted = true
        return enableDepthTextureSupport()
    }

    // Стратегия выбора профиля шейдеров:
    // 1. Не задаём language: Shader.GLSL, чтобы Qt Quick 3D самостоятельно
    //    выбрал корректный профиль GLSL для активного графического API.
    // 2. Приоритет GLES-профиля задаётся детектором платформы ниже и может
    //    быть переопределён свойством forceDesktopShaderProfile.
    // Shader profile selection strategy:
    // 1. Omit language: Shader.GLSL so Qt Quick 3D can choose the best GLSL
    //    profile automatically for the current graphics backend.
    // 2. The GLES preference is driven by the platform detection logic below
    //    and can be overridden via forceDesktopShaderProfile.
    // qmllint disable unqualified
    property bool forceDesktopShaderProfile: false
    property bool forceGlesShaderProfile: false
    property var shaderProfileFailoverAttempts: ({})
    onForceDesktopShaderProfileChanged: {
        if (forceDesktopShaderProfile && forceGlesShaderProfile) {
            console.assert(false,
                "FogEffect: forceDesktopShaderProfile and forceGlesShaderProfile cannot both be true")
            console.warn("⚠️ FogEffect: disabling forceGlesShaderProfile to honour desktop override")
            forceGlesShaderProfile = false
        }
        if (forceDesktopShaderProfile)
            console.warn("⚠️ FogEffect: desktop shader profile override enabled (preferring GLSL 450 resources)")
        else
            console.log("ℹ️ FogEffect: desktop shader profile override cleared; reverting to auto detection")
        shaderVariantSelectionCache = ({})
        scheduleShaderCacheReset()
    }
    onForceGlesShaderProfileChanged: {
        if (forceDesktopShaderProfile && forceGlesShaderProfile) {
            console.assert(false,
                "FogEffect: forceDesktopShaderProfile and forceGlesShaderProfile cannot both be true")
            console.warn("⚠️ FogEffect: disabling forceDesktopShaderProfile to honour GLES override")
            forceDesktopShaderProfile = false
        }
        if (forceGlesShaderProfile)
            console.warn("⚠️ FogEffect: GLES shader profile override enabled (preferring GLSL 300 es resources)")
        else
            console.log("ℹ️ FogEffect: GLES shader profile override cleared; reverting to auto detection")
        shaderVariantSelectionCache = ({})
        scheduleShaderCacheReset()
    }
    property bool preferUnifiedShaderSources: false

    readonly property bool preferDesktopShaderProfile: {
        if (forceGlesShaderProfile)
            return false
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
    property bool compatibilityFallbackLogged: false
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
    readonly property string compatibilityFallbackMessage: enforceLegacyFallbackShaders
            ? qsTr("FogEffect: forcing GLSL 330 fallback shader for OpenGL %1")
                .arg(openGlVersionLabel.length ? openGlVersionLabel : "3.3")
            : ""
    readonly property bool reportedGlesContext: {
        if (forceDesktopShaderProfile)
            return false
        // qmllint disable missing-property
        try {
            if (GraphicsInfo.renderableType === GraphicsInfo.OpenGLES)
                return true
        } catch (error) {
        }
        // qmllint enable missing-property
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
    readonly property bool useGlesShaders: {
        if (forceDesktopShaderProfile)
            return false
        if (forceGlesShaderProfile)
            return true
        return !preferDesktopShaderProfile
    }

    readonly property string shaderResourceDirectory: "../../shaders/effects/"
    readonly property string legacyShaderResourceDirectory: "../../shaders/effects/"
    readonly property string glesShaderResourceDirectory: "../../shaders/effects/"
    // qmllint disable unqualified
    readonly property var shaderResourceManifest: typeof effectShaderManifest !== "undefined"
            ? effectShaderManifest
            : ({})
    // qmllint enable unqualified
    readonly property var desktopShaderSuffixes: ["_glsl450", "_desktop", "_core"]
    readonly property var glesShaderSuffixes: ["_es", "_gles", "_300es"]
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
    property var shaderResourceAvailabilityCache: ({})
    property var shaderSanitizationCache: ({})
    property var shaderSanitizationWarnings: ({})
    property var shaderVariantSelectionCache: ({})
    property var shaderVariantMissingWarnings: ({})

    onUseGlesShadersChanged: {
        console.log("🎚️ FogEffect: shader profile toggled ->", useGlesShaders
                ? "OpenGL ES (GLSL 300 es)"
                : "Desktop (GLSL 450 core)")
        shaderVariantSelectionCache = ({})
        scheduleShaderCacheReset()
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

        if (Object.prototype.hasOwnProperty.call(shaderResourceAvailabilityCache, normalizedUrl))
            return shaderResourceAvailabilityCache[normalizedUrl]

        var available = false

        var manifestEntry
        var manifestHasEntry = false
        var manifestEnabled = true
        var manifestPaths = []
        var normalizedUrlPath = ""
        var matchesManifestPath = false
        if (resourceName && Object.prototype.hasOwnProperty.call(shaderResourceManifest, resourceName)) {
            manifestEntry = shaderResourceManifest[resourceName]
            manifestHasEntry = true
            if (typeof manifestEntry === "boolean") {
                manifestEnabled = manifestEntry
            } else if (manifestEntry === null || manifestEntry === undefined) {
                manifestEnabled = false
            } else if (typeof manifestEntry === "string") {
                manifestPaths.push(manifestEntry)
            } else if (typeof manifestEntry === "object") {
                if (Object.prototype.hasOwnProperty.call(manifestEntry, "enabled"))
                    manifestEnabled = manifestEntry.enabled !== false
                if (Object.prototype.hasOwnProperty.call(manifestEntry, "path")) {
                    var manifestPath = manifestEntry.path
                    if (manifestPath && typeof manifestPath === "string")
                        manifestPaths.push(manifestPath)
                }
                if (Object.prototype.hasOwnProperty.call(manifestEntry, "paths") && manifestEntry.paths) {
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
                    console.error("❌ FogEffect: shader resource disabled by manifest", resourceName, normalizedUrl)
                return false
            }
            normalizedUrlPath = String(normalizedUrl).replace(/\\/g, "/")
        }

        if (manifestHasEntry && manifestEnabled) {
            var shaderRootHint = "/assets/shaders/"

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
                console.debug("FogEffect: shader availability check failed", resourceName, method, error)
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
                    console.error("❌ FogEffect: shader manifest mismatch", resourceName, normalizedUrl)
                return false
            }
            shaderResourceAvailabilityCache[normalizedUrl] = false
            if (!suppressErrors)
                console.error("❌ FogEffect: shader resource missing", resourceName, normalizedUrl)
            return false
        }

        shaderResourceAvailabilityCache[normalizedUrl] = false
        if (!suppressErrors)
            console.error("❌ FogEffect: shader resource missing", resourceName, normalizedUrl)

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
        var candidateSuffixes = []
        if (!preferUnifiedShaderSources)
            candidateSuffixes = useGlesShaders ? glesShaderSuffixes : desktopShaderSuffixes

        var candidateNames = shaderVariantCandidateNames(baseName, extension, candidateSuffixes, normalized)

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
            if (candidateFound)
                break
            if (useGlesShaders && candidateName !== normalized) {
                if (!Object.prototype.hasOwnProperty.call(shaderVariantMissingWarnings, candidateName)) {
                    shaderVariantMissingWarnings[candidateName] = true
                    console.warn(`⚠️ FogEffect: GLES shader variant '${candidateName}' not found; using compatibility fallback`)
                }
            }
        }

        var glesVariantList = []
        if (useGlesShaders)
            glesVariantList = candidateNames.slice(0, Math.max(candidateNames.length - 1, 0))
        var fallbackCandidateNames = []
        if (useGlesShaders && !preferUnifiedShaderSources && glesVariantList.length > 0) {
            var needsFallback = !found || selectedName === normalized
            if (needsFallback) {
                var fallbackBaseName = baseName.endsWith("_fallback") ? baseName : baseName + "_fallback"
                fallbackCandidateNames = shaderVariantCandidateNames(
                            fallbackBaseName,
                            extension,
                            glesShaderSuffixes,
                            fallbackBaseName + extension)

                if (!found)
                    console.warn("⚠️ FogEffect: GLES shader variants missing; trying fallback", glesVariantList)
                else
                    console.warn("⚠️ FogEffect: GLES shader variant not resolved; falling back", glesVariantList)

                var fallbackResolved = false
                for (var candidateIndex = 0; candidateIndex < fallbackCandidateNames.length && !fallbackResolved; ++candidateIndex) {
                    var fallbackName = fallbackCandidateNames[candidateIndex]
                    for (var fbDirIdx = 0; fbDirIdx < directories.length && !fallbackResolved; ++fbDirIdx) {
                        var fallbackUrl = resolvedShaderUrl(fallbackName, directories[fbDirIdx])
                        if (shaderResourceExists(fallbackUrl, fallbackName, false)) {
                            selectedName = fallbackName
                            selectedUrl = fallbackUrl
                            fallbackResolved = true
                            console.warn("⚠️ FogEffect: GLES fallback shader selected", fallbackName)
                        }
                    }
                }

                if (fallbackResolved) {
                    found = true
                } else if (!found) {
                    requestDesktopShaderProfile(`Shader ${normalized} lacks GLES variants (${glesVariantList.join(", ")}); enforcing desktop profile`)
                }
            }
        }

        var previousSelection = shaderVariantSelectionCache[normalized]
        if (previousSelection !== selectedName) {
            shaderVariantSelectionCache[normalized] = selectedName
            var profileLabel = useGlesShaders ? "OpenGL ES" : "Desktop"
            console.log(`🌐 FogEffect: resolved ${profileLabel} shader '${normalized}' -> '${selectedName}'`)
        }

        return sanitizedShaderUrl(selectedUrl, selectedName)
    }

    // Для профиля OpenGL ES поставляются отдельные GLSL-файлы с суффиксом _es,
    // содержащие корректную директиву #version 300 es. Свойство
    // preferUnifiedShaderSources можно использовать для диагностики, чтобы
    // принудительно задействовать единый файл, но по умолчанию мы выбираем
    // специализированные GLES-варианты и избегаем ошибок компиляции из-за
    // неподдерживаемого профиля #version.

    function scheduleShaderCacheReset() {
        Qt.callLater(function() {
            shaderResourceAvailabilityCache = ({})
            shaderSanitizationCache = ({})
            shaderSanitizationWarnings = ({})
            shaderVariantSelectionCache = ({})
            shaderVariantMissingWarnings = ({})
        })
    }

    function requestDesktopShaderProfile(reason) {
        if (forceDesktopShaderProfile)
            return
        console.warn("⚠️ FogEffect:", reason, "– forcing desktop shader profile")
        if (forceGlesShaderProfile)
            forceGlesShaderProfile = false
        forceDesktopShaderProfile = true
        scheduleShaderCacheReset()
    }

    function requestGlesShaderProfile(reason) {
        if (forceGlesShaderProfile)
            return
        console.warn("⚠️ FogEffect:", reason, "– forcing GLES shader profile")
        if (forceDesktopShaderProfile)
            forceDesktopShaderProfile = false
        forceGlesShaderProfile = true
        scheduleShaderCacheReset()
    }

    /**
     * Проверяет содержимое шейдера на предмет несовместимых префиксов (CRLF,
     * BOM, лидирующие пробелы) и логирует предупреждение при обнаружении.
     * В отличие от предыдущей реализации больше не создаёт Blob/data URL,
     * поскольку Qt RHI не принимает такие схемы. Шейдер по-прежнему
     * загружается по исходному URL.
     * @param url {string} - исходный URL
     * @param resourceName {string} - имя ресурса (для логирования)
     * @returns {string} исходный URL (для совместимости биндингов)
     */
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

        if (Object.prototype.hasOwnProperty.call(shaderSanitizationCache, normalizedUrl))
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
                        if (!Object.prototype.hasOwnProperty.call(shaderSanitizationWarnings, cacheKey)) {
                            console.warn(
                                        "⚠️ FogEffect: shader", resourceName,
                                        "contains leading BOM/whitespace incompatible with Qt RHI; please clean the source file")
                            shaderSanitizationWarnings[cacheKey] = true
                        }
                        sanitizationApplied = true
                    }
                }
            }
        } catch (error) {
            console.debug("FogEffect: shader normalization skipped", resourceName, error)
        }

        shaderSanitizationCache[normalizedUrl] = sanitizedUrl
        if (sanitizationApplied)
            shaderSanitizationCache[normalizedUrl] = normalizedUrl
        return sanitizedUrl

    }
    // qmllint enable unqualified

    function handleShaderCompilationLog(shaderId, message) {
        if (!message || !message.length)
            return
        var normalized = String(message).toLowerCase()
        if (normalized.indexOf("#version") === -1)
            return
        if (normalized.indexOf("profile") === -1 && normalized.indexOf("expected newline") === -1)
            return
        var history = shaderProfileFailoverAttempts[shaderId]
        if (!history) {
            history = ({ requestedDesktop: false, requestedGles: false, exhausted: false })
            shaderProfileFailoverAttempts[shaderId] = history
        }

        if (history.exhausted)
            return

        if (useGlesShaders) {
            if (history.requestedDesktop) {
                history.exhausted = true
                shaderProfileFailoverAttempts[shaderId] = history
                console.error(`FogEffect: shader ${shaderId} failed under both profiles; leaving GLES active`)
                return
            }
            history.requestedDesktop = true
            shaderProfileFailoverAttempts[shaderId] = history
            requestDesktopShaderProfile(
                        `Shader ${shaderId} reported #version incompatibility while using GLES profile`)
        } else {
            if (history.requestedGles) {
                history.exhausted = true
                shaderProfileFailoverAttempts[shaderId] = history
                console.error(`FogEffect: shader ${shaderId} failed under both profiles; leaving desktop active`)
                return
            }
            history.requestedGles = true
            shaderProfileFailoverAttempts[shaderId] = history
            requestGlesShaderProfile(
                        `Shader ${shaderId} reported #version incompatibility while using desktop profile`)
        }
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
            fogEffect.handleShaderCompilationLog(shaderId, shaderCompilationMessage(shaderItem))
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

    function updateFallbackActivation() {
        var compatibilityFallback = enforceLegacyFallbackShaders
        var shouldFallback = fallbackDueToDepth || fallbackDueToCompilation || compatibilityFallback
        var reason = ""
        if (fallbackDueToDepth) {
            reason = forceDepthTextureUnavailable
                    ? qsTr("Depth texture support forcibly disabled; using fallback shader")
                    : qsTr("Depth texture unavailable; using fallback shader")
        } else if (fallbackDueToCompilation) {
            reason = compilationErrorLog && compilationErrorLog.length
                    ? compilationErrorLog
                    : qsTr("Fog shader compilation failed; fallback shader active")
        }
        if (compatibilityFallback) {
            var compatibilityMessage = compatibilityFallbackMessage.length
                    ? compatibilityFallbackMessage
                    : qsTr("FogEffect: forcing GLSL 330 fallback shader for legacy OpenGL profile")
            if (reason.length && compatibilityMessage.length)
                reason = reason + " | " + compatibilityMessage
            else if (compatibilityMessage.length)
                reason = compatibilityMessage
            if (!compatibilityFallbackLogged && compatibilityMessage.length) {
                console.warn("⚠️ FogEffect:", compatibilityMessage)
                compatibilityFallbackLogged = true
            }
        }
        if (fallbackReason !== reason)
            fallbackReason = reason
        if (fallbackActive !== shouldFallback)
            fallbackActive = shouldFallback
        else
            refreshPassConfiguration()
    }

    function setCompilationFallbackState(active, message) {
        var normalizedMessage = active && message ? String(message) : ""
        var previouslyActive = fallbackDueToCompilation
        fallbackDueToCompilation = !!active
        compilationErrorLog = fallbackDueToCompilation ? normalizedMessage : ""
        updateFallbackActivation()
        if (fallbackDueToCompilation && !previouslyActive) {
            var logMessage = normalizedMessage.length
                    ? normalizedMessage
                    : qsTr("Fog shader compilation failed; fallback shader active")
            console.warn("⚠️ FogEffect: shader compilation error detected ->", logMessage)
        } else if (!fallbackDueToCompilation && previouslyActive) {
            console.log("✅ FogEffect: shader compilation recovered; attempting primary shader rebuild")
        }
    }

    function refreshPassConfiguration() {
        var useFallback = fallbackActive || !depthTextureAvailable
        var newShaders = useFallback
                ? [fogVertexShader, fogFallbackShader]
                : [fogVertexShader, fogFragmentShader]
        if (_usingFallbackPassConfiguration !== useFallback) {
            var transitionMessage = fallbackReason && fallbackReason.length
                    ? fallbackReason
                    : (useFallback
                        ? (fallbackDueToCompilation
                            ? qsTr("Fog shader compilation failed; fallback pass engaged")
                            : qsTr("Depth texture unavailable; using fallback shader pass"))
                        : qsTr("Primary fog shader path restored"))
            if (useFallback)
                console.warn("⚠️ FogEffect: switching passes to fallback shader ->", transitionMessage)
            else
                console.log("✅ FogEffect: fallback shader pass released; primary pipeline active")
            _usingFallbackPassConfiguration = useFallback
        }
        activePassShaders = newShaders
    }

    function handleShaderStatusChange(shaderItem, shaderId) {
        if (!shaderItem)
            return
        var status
        try {
            status = shaderItem.status
        } catch (error) {
            console.debug("FogEffect: unable to read shader status", shaderId, error)
            return
        }
        // qmllint disable missing-property
        if (shaderItem === fogFragmentShader) {
            if (status === Shader.Error) {
                var message = shaderCompilationMessage(shaderItem)
                if (!message.length)
                    message = qsTr("FogEffect shader %1 compilation failed").arg(shaderId)
                console.error("❌ FogEffect:", message)
                setCompilationFallbackState(true, message)
            } else if (status === Shader.Ready) {
                setCompilationFallbackState(false, "")
            }
        } else if (shaderItem === fogFallbackShader) {
            if (status === Shader.Error) {
                var fallbackMessage = shaderCompilationMessage(shaderItem)
                if (!fallbackMessage.length)
                    fallbackMessage = qsTr("FogEffect fallback shader %1 compilation failed").arg(shaderId)
                console.error("❌ FogEffect:", fallbackMessage)
            }
        } else if (shaderItem === fogVertexShader && status === Shader.Error) {
            var vertexMessage = shaderCompilationMessage(shaderItem)
            if (!vertexMessage.length)
                vertexMessage = qsTr("FogEffect shader %1 compilation failed").arg(shaderId)
            console.error("❌ FogEffect:", vertexMessage)
        }
        // qmllint enable missing-property
    }

    Shader {
        id: fogVertexShader
        stage: Shader.Vertex
        shader: fogEffect.shaderPath("fog.vert")
        Component.onCompleted: {
            if (!fogEffect.attachShaderLogHandler(fogVertexShader, "fog.vert"))
                console.debug("FogEffect: shader log handler unavailable for fog.vert")
        }
    }

    Connections {
        target: fogVertexShader

        function onStatusChanged() {
            fogEffect.handleShaderStatusChange(fogVertexShader, "fog.vert")
        }
    }

    Shader {
        id: fogFragmentShader
        stage: Shader.Fragment
        property real userFogDensity: fogEffect.fogDensity
        property real userFogStart: fogEffect.fogStartDistance
        property real userFogEnd: fogEffect.fogEndDistance
        property real userFogLeast: fogEffect.fogLeastIntenseY
        property real userFogMost: fogEffect.fogMostIntenseY
        property real userFogHeightCurve: fogEffect.fogHeightCurve
        property real userFogHeightEnabled: fogEffect.heightBasedFog ? 1.0 : 0.0
        property real userFogScattering: fogEffect.fogScattering
        property real userFogTransmitEnabled: fogEffect.fogTransmitEnabled ? 1.0 : 0.0
        property real userFogTransmitCurve: fogEffect.fogTransmitCurve
        property real userFogAnimated: fogEffect.animatedFog ? 1.0 : 0.0
        property real userFogAnimationSpeed: fogEffect.animationSpeed
        property real userFogTime: fogEffect.time
        property color userFogColor: fogEffect.fogColor
        property real userCameraNear: fogEffect.cameraClipNear
        property real userCameraFar: fogEffect.cameraClipFar
        property real userCameraFov: fogEffect.cameraFieldOfView
        property real userCameraAspect: fogEffect.cameraAspectRatio
        shader: fogEffect.shaderPath("fog.frag")
        Component.onCompleted: {
            if (!fogEffect.attachShaderLogHandler(fogFragmentShader, "fog.frag"))
                console.debug("FogEffect: shader log handler unavailable for fog.frag")
        }
    }

    Connections {
        target: fogFragmentShader

        function onStatusChanged() {
            fogEffect.handleShaderStatusChange(fogFragmentShader, "fog.frag")
        }
    }

    Shader {
        id: fogFallbackShader
        stage: Shader.Fragment
        shader: fogEffect.shaderPath("fog_fallback.frag")
        property real userFogDensity: fogEffect.fogDensity
        property color userFogColor: fogEffect.fogColor
        Component.onCompleted: {
            if (!fogEffect.attachShaderLogHandler(fogFallbackShader, "fog_fallback.frag"))
                console.debug("FogEffect: shader log handler unavailable for fog_fallback.frag")
        }
    }

    Connections {
        target: fogFallbackShader

        function onStatusChanged() {
            fogEffect.handleShaderStatusChange(fogFallbackShader, "fog_fallback.frag")
        }
    }

    passes: [
        Pass {
            shaders: fogEffect.activePassShaders
        }
    ]

    Timer {
        id: animationTimer
        running: fogEffect.animatedFog
                && fogEffect.depthTextureAvailable
                && !fogEffect.fallbackActive
        interval: 16  // 60 FPS
        repeat: true
        onTriggered: fogEffect.time += 0.016
    }

    Component.onCompleted: {
        var depthReady = _depthInitializationComplete
        updateFallbackActivation()
        if (enforceLegacyFallbackShaders && compatibilityFallbackMessage.length && !compatibilityFallbackLogged) {
            console.warn("⚠️ FogEffect:", compatibilityFallbackMessage)
            compatibilityFallbackLogged = true
        }
        refreshPassConfiguration()
        console.log("🌫️ FogEffect graphics API:", rendererGraphicsApi)
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
        console.log("🌫️ Enhanced Fog Effect loaded")
        console.log("   Density:", fogDensity)
        console.log("   Color:", fogColor)
        console.log("   Distance range:", fogStartDistance, "-", fogEndDistance)
        console.log("   Height-based:", heightBasedFog)
        console.log("   Animated:", animatedFog)
        if (!depthReady)
            console.warn("⚠️ FogEffect: depth texture unavailable, fallback shader active")
    }

}
