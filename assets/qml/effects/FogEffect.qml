import QtQuick
import QtQuick.Window
import QtQuick3D 6.10
// qmllint disable unused-imports
import QtQuick3D.Effects 6.10
import QtQuick3D.Helpers
// qmllint enable unused-imports
import "../components/ShaderProfileHelper.js" as SPH

/*
 * Улучшенный эффект тумана с расширенными настройками
 * Enhanced fog effect with advanced settings
 */
Effect {
    id: fogEffect

    property bool verboseLogging: false
    readonly property var shaderMetrics: SPH.ShaderProfileHelper.metricsSnapshot()

    Component.onCompleted: {
        // Fallback helper shims (если отсутствуют внешние функции)
        if (typeof resolvedShaderUrl !== 'function') {
            resolvedShaderUrl = function(name, directory) {
                var dirStr = String(directory || fogEffect.shaderResourceDirectory)
                if (dirStr.length && dirStr.charAt(dirStr.length - 1) !== '/' && dirStr.charAt(dirStr.length - 1) !== '\\')
                    dirStr += '/'
                return dirStr + name
            }
        }
        if (typeof shaderResourceExists !== 'function') {
            shaderResourceExists = function(url, resourceName, suppressErrors, manifest) {
                try {
                    if (manifest && Object.prototype.hasOwnProperty.call(manifest, resourceName)) {
                        var entry = manifest[resourceName]
                        if (entry === false) {
                            if (!suppressErrors && fogEffect.verboseLogging)
                                console.warn('⚠️ FogEffect: shader disabled by manifest', resourceName)
                            return false
                        }
                    }
                } catch (e) {}
                return true
            }
        }
    }

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
    // qmllint enable missing-property import

    // Доступность depth-текстуры
    property bool depthTextureAvailable: false
    property bool forceDepthTextureUnavailable: false
    property bool _depthInitializationStarted: false
    property bool _depthInitializationComplete: false

    property bool fallbackActive: false
    property string fallbackReason: ""
    property bool fallbackDueToDepth: false
    property bool fallbackDueToCompilation: false
    property string compilationErrorLog: ""
    readonly property bool compilationFallbackActive: fallbackDueToCompilation
    property bool _usingFallbackPassConfiguration: false
    property bool _cacheResetScheduled: false // Флаг для предотвращения многократного планирования сброса кэша

    onDepthTextureAvailableChanged: {
        fallbackDueToDepth = !depthTextureAvailable
        updateFallbackActivation()
    }

    onForceDepthTextureUnavailableChanged: {
        if (!_depthInitializationStarted) return
        if (!forceDepthTextureUnavailable) {
            depthTextureAvailable = (GraphicsInfo.api === GraphicsInfo.OpenGL) || preferDesktopShaderProfile
            fallbackDueToDepth = !depthTextureAvailable
        } else {
            depthTextureAvailable = false
            fallbackDueToDepth = true
        }
        updateFallbackActivation()
        refreshPassConfiguration()
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
    property bool preferUnifiedShaderSources: false

    readonly property string normalizedRendererGraphicsApi: {
        var apiName = rendererGraphicsApi
        if (!apiName || typeof apiName !== 'string') return ''
        return apiName.trim().toLowerCase()
    }

    readonly property bool preferDesktopShaderProfile: SPH.ShaderProfileHelper.preferDesktopProfile(forceDesktopShaderProfile, forceGlesShaderProfile, normalizedRendererGraphicsApi, reportedGlesContext, (function(){ try { return qtGraphicsApiRequiresDesktopShaders } catch(e){ return undefined } })(), GraphicsInfo)
    readonly property bool useGlesShaders: !preferDesktopShaderProfile

    onForceDesktopShaderProfileChanged: {
        SPH.ShaderProfileHelper.markProfileSwitch()
        shaderVariantSelectionCache = ({})
        scheduleShaderCacheReset()
        if (verboseLogging) console.log('[FogEffect] profile override desktop=', forceDesktopShaderProfile)
    }
    onForceGlesShaderProfileChanged: {
        SPH.ShaderProfileHelper.markProfileSwitch()
        shaderVariantSelectionCache = ({})
        scheduleShaderCacheReset()
        if (verboseLogging) console.log('[FogEffect] profile override gles=', forceGlesShaderProfile)
    }
    onUseGlesShadersChanged: {
        SPH.ShaderProfileHelper.markProfileSwitch()
        shaderVariantSelectionCache = ({})
        scheduleShaderCacheReset()
        if (verboseLogging) console.log('[FogEffect] useGlesShaders ->', useGlesShaders)
    }

    function shaderPath(fileName) {
        return SPH.ShaderProfileHelper.resolveVariant(
                    fileName,
                    useGlesShaders,
                    preferUnifiedShaderSources,
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
        shaderVariantMissingWarnings = ({})
        _shaderVariantCache = ({})
        _shaderVariantCacheKeys = []
        _cacheResetScheduled = false
        SPH.ShaderProfileHelper.resetCaches()
        rebindShaders()
        if (verboseLogging) console.log('[FogEffect] caches reset; metrics=', JSON.stringify(shaderMetrics))
    }
    // Canonical shader path map (migration finalized: only effects/)
    readonly property var _shaderCanonicalMap: ({
        fogVert: "effects/fog.vert",
        fogFrag: "effects/fog.frag",
        fogFragFallback: "effects/fog_fallback.frag"
    })
    readonly property bool _legacyPathsEnabled: {
        try { return String(Qt.binding(function(){ return typeof pssEnableLegacyPaths !== 'undefined' && pssEnableLegacyPaths })).toLowerCase() in ['1','true','yes','on'] } catch(e) { }
        try { return String((typeof globalThis !== 'undefined' && globalThis.PSS_ENABLE_LEGACY_POST_EFFECTS_PATHS) || "").toLowerCase() in ['1','true','yes','on'] } catch(e) { }
        return false
    }

    function _logManifestMismatchIfNeeded(actual) {
        if (_legacyPathsEnabled) {
            var expected = String(actual).replace('effects/', 'post_effects/')
            if (expected !== actual) {
                console.warn('ℹ️ FogEffect: legacy path accepted', expected, '→', actual)
            }
            return
        }
        // Legacy disabled: no mismatch warnings
    }

    // Rename simple canonical resolver to avoid shadowing advanced variant resolver
    function _canonicalShaderPath(key) {
        var map = _shaderCanonicalMap
        var resolved = map[key] || key
        _logManifestMismatchIfNeeded(resolved)
        return Qt.resolvedUrl('../../shaders/' + resolved)
    }
    // Remove legacy simple sanitizedShaderUrl with XHR (single non-blocking version retained above)
    // LRU cache for variant resolution
    property var _shaderVariantCache: ({})
    property var _shaderVariantCacheKeys: []
    readonly property int _shaderVariantCacheLimit: 32
    function _cacheShaderVariant(name, url) {
        if (!name || !url) return
        if (!_shaderVariantCache[name]) {
            _shaderVariantCache[name] = url
            _shaderVariantCacheKeys.push(name)
            if (_shaderVariantCacheKeys.length > _shaderVariantCacheLimit) {
                var evicted = _shaderVariantCacheKeys.shift()
                delete _shaderVariantCache[evicted]
            }
        }
    }
    // Advanced variant selector (kept, but now uses cache and canonical path function for base)
    function shaderPath(fileName) {
        if (!fileName || typeof fileName !== "string")
            return ""
        if (_shaderVariantCache[fileName])
            return _shaderVariantCache[fileName]
        var normalized = String(fileName)
        var dotIndex = normalized.lastIndexOf('.')
        var baseName = dotIndex >= 0 ? normalized.slice(0, dotIndex) : normalized
        var extension = dotIndex >= 0 ? normalized.slice(dotIndex) : ''
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
            if (candidateFound) break
            if (useGlesShaders && candidateName !== normalized) {
                if (!Object.prototype.hasOwnProperty.call(shaderVariantMissingWarnings, candidateName)) {
                    shaderVariantMissingWarnings[candidateName] = true
                    console.warn("⚠️ FogEffect: GLES shader variant missing; using fallback", candidateName)
                }
            }
        }
        _cacheShaderVariant(fileName, sanitizedShaderUrl(selectedUrl, selectedName))
        if (!found) {
            // Attempt fallback variants only once
            if (useGlesShaders) {
                requestDesktopShaderProfile("Variants not found for " + normalized)
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
    // Unified sanitizedShaderUrl (non-blocking, no XHR)
    function sanitizedShaderUrl(url, resourceName) {
        if (!url) return url
        var normalizedUrl = String(url)
        if (Object.prototype.hasOwnProperty.call(shaderSanitizationCache, normalizedUrl))
            return shaderSanitizationCache[normalizedUrl]
        shaderSanitizationCache[normalizedUrl] = normalizedUrl
        return normalizedUrl
    }
    // Rebind shaders explicitly after profile failover
    function rebindShaders() {
        if (!fogVertexShader || !fogFragmentShader || !fogFallbackShader) return
        fogVertexShader.shader = shaderPath('fog.vert')
        fogFragmentShader.shader = shaderPath('fog.frag')
        fogFallbackShader.shader = shaderPath('fog_fallback.frag')
    }
    function resetPasses() {
        rebindShaders()
        refreshPassConfiguration()
    }

    // Централизованный сброс кэшей
    function resetShaderCaches() {
        shaderResourceAvailabilityCache = ({})
        shaderSanitizationCache = ({})
        shaderSanitizationWarnings = ({})
        shaderVariantSelectionCache = ({})
        shaderVariantMissingWarnings = ({})
        _shaderVariantCache = ({})
        _shaderVariantCacheKeys = []
        _cacheResetScheduled = false
        SPH.ShaderProfileHelper.resetCaches()
        rebindShaders()
        if (verboseLogging) console.log('[FogEffect] caches reset; metrics=', JSON.stringify(shaderMetrics))
    }
    function scheduleShaderCacheReset() {
        if (_cacheResetScheduled) return
        _cacheResetScheduled = true
        Qt.callLater(function() { resetShaderCaches() })
    }
    function requestDesktopShaderProfile(reason) {
        if (forceDesktopShaderProfile) return
        console.warn('⚠️ FogEffect:', reason, '– desktop profile forced')
        if (forceGlesShaderProfile) forceGlesShaderProfile = false
        forceDesktopShaderProfile = true
        scheduleShaderCacheReset()
    }
    function requestGlesShaderProfile(reason) {
        if (forceGlesShaderProfile) return
        console.warn('⚠️ FogEffect:', reason, '– GLES profile forced')
        if (forceDesktopShaderProfile) forceDesktopShaderProfile = false
        forceGlesShaderProfile = true
        scheduleShaderCacheReset()
    }

    // Активные шейдеры прохода (единственное объявление)
    property var activePassShaders: []

    function refreshPassConfiguration() {
        var useFallback = fallbackActive || !depthTextureAvailable
        var newShaders = useFallback ? [fogVertexShader, fogFallbackShader] : [fogVertexShader, fogFragmentShader]
        if (_usingFallbackPassConfiguration !== useFallback) {
            var msg = useFallback ? (fallbackReason || 'Fallback engaged') : 'Primary pipeline active'
            if (useFallback) console.warn('⚠️ FogEffect: switching passes ->', msg)
            else console.log('✅ FogEffect:', msg)
            _usingFallbackPassConfiguration = useFallback
        }
        // Избегаем лишних присваиваний
        if (activePassShaders !== newShaders)
            activePassShaders = newShaders
    }

    // Актуализация fallbackActive по агрегированным причинам
    function updateFallbackActivation() {
        var shouldBeActive = fallbackDueToDepth || fallbackDueToCompilation
        if (fallbackActive === shouldBeActive)
            return
        if (shouldBeActive && !fallbackReason.length) {
            if (fallbackDueToCompilation)
                fallbackReason = qsTr('Shader compilation failed')
            else if (fallbackDueToDepth)
                fallbackReason = qsTr('Depth texture unavailable')
        }
        fallbackActive = shouldBeActive
    }

    // Обработчики статуса и логов шейдеров (устойчивость при отсутствии внешнего API)
    function attachShaderLogHandler(shader, name) {
        try {
            if (!shader || !shader.logChanged) return false
            shader.logChanged.connect(function() {
                if (shader.status === Shader.Error) {
                    compilationErrorLog = shader.log || ''
                }
            })
            return true
        } catch(e) { return false }
    }
    function handleShaderStatusChange(shader, name) {
        try {
            if (!shader) return
            shaderStatusCache[name] = shader.status
            if (shader.status === Shader.Error) {
                fallbackDueToCompilation = true
                compilationErrorLog = shader.log || ''
                fallbackReason = qsTr('Compilation failed for %1').arg(name)
                updateFallbackActivation()
            }
        } catch(e) {}
    }

    Shader {
        id: fogVertexShader
        stage: Shader.Vertex
        shader: fogEffect.shaderPath('fog.vert')
        Component.onCompleted: {
            if (!fogEffect.attachShaderLogHandler(fogVertexShader, 'fog.vert'))
                console.debug('FogEffect: log handler unavailable for fog.vert')
            fogEffect.handleShaderStatusChange(fogVertexShader, 'fog.vert')
        }
        onStatusChanged: fogEffect.handleShaderStatusChange(fogVertexShader, 'fog.vert')
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
        shader: fogEffect.shaderPath('fog.frag')
        Component.onCompleted: {
            if (!fogEffect.attachShaderLogHandler(fogFragmentShader, 'fog.frag'))
                console.debug('FogEffect: log handler unavailable for fog.frag')
            fogEffect.handleShaderStatusChange(fogFragmentShader, 'fog.frag')
        }
        onStatusChanged: fogEffect.handleShaderStatusChange(fogFragmentShader, 'fog.frag')
    }
    Shader {
        id: fogFallbackShader
        stage: Shader.Fragment
        shader: fogEffect.shaderPath('fog_fallback.frag')
        Component.onCompleted: {
            if (!fogEffect.attachShaderLogHandler(fogFallbackShader, 'fog_fallback.frag'))
                console.debug('FogEffect: log handler unavailable for fog_fallback.frag')
            fogEffect.handleShaderStatusChange(fogFallbackShader, 'fog_fallback.frag')
        }
        onStatusChanged: fogEffect.handleShaderStatusChange(fogFallbackShader, 'fog_fallback.frag')
    }
    Component.onDestruction: {
        shaderResourceAvailabilityCache = ({})
        shaderSanitizationCache = ({})
        shaderSanitizationWarnings = ({})
        shaderVariantSelectionCache = ({})
        shaderVariantMissingWarnings = ({})
        _shaderVariantCache = ({})
        _shaderVariantCacheKeys = []
    }
    Timer {
        id: animationTimer
        running: fogEffect.animatedFog && fogEffect.depthTextureAvailable && !fogEffect.fallbackActive
        interval: 16
        repeat: true
        onTriggered: fogEffect.time += (interval / 1000.0) * fogEffect.animationSpeed // скорость теперь влияет на анимацию
    }

}
