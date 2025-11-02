import QtQuick
import QtQuick.Window
import QtQuick3D 6.10
import QtQuick3D.Effects 6.10

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

    // Доступность depth-текстуры
    property bool depthTextureAvailable: false

    function enableDepthTextureSupport() {
        const propertyName = "requiresDepthTexture"
        if (propertyName in fogEffect) {
            try {
                fogEffect[propertyName] = true
                depthTextureAvailable = true
                console.log("🌫️ FogEffect: depth texture support enabled")
                return
            } catch (error) {
                console.debug("FogEffect requiresDepthTexture assignment failed", error)
            }
        }
        depthTextureAvailable = false
        console.warn("⚠️ FogEffect: depth texture not supported; using fallback shader")
    }

    // Используем GLSL ES только при наличии реального контекста OpenGL ES.
    // Для программного или RHI-рендерера требуются варианты core.
    // qmllint disable unqualified
    property bool forceDesktopShaderProfile: false
    property bool preferUnifiedShaderSources: true

    readonly property bool preferDesktopShaderProfile: {
        if (forceDesktopShaderProfile)
            return true
        var normalized = normalizedRendererGraphicsApi
        if (normalized.length) {
            if (normalized.indexOf("angle") !== -1)
                return false
            if (normalized.indexOf("opengl es") !== -1
                    || normalized.indexOf("opengles") !== -1
                    || normalized.indexOf("gles") !== -1)
                return false
        }
        try {
            if (typeof qtGraphicsApiRequiresDesktopShaders === "boolean")
                return qtGraphicsApiRequiresDesktopShaders
        } catch (error) {
        }
        if (GraphicsInfo.api === GraphicsInfo.Direct3D11 && reportedGlesContext)
            return false
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
    readonly property bool reportedGlesContext: {
        if (forceDesktopShaderProfile)
            return false
        try {
            if (GraphicsInfo.renderableType === GraphicsInfo.OpenGLES)
                return true
        } catch (error) {
        }
        try {
            var normalized = normalizedRendererGraphicsApi
            if (!normalized.length)
                return false
            if (normalized.indexOf("rhi") !== -1
                    && normalized.indexOf("opengl") !== -1
                    && normalized.indexOf("gles") === -1)
                return false
            if (normalized.indexOf("opengl es") !== -1)
                return true
            if (normalized.indexOf("opengles") !== -1)
                return true
            if (normalized.indexOf("gles") !== -1)
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

    readonly property string shaderResourceDirectory: "../../shaders/effects/"
    property var shaderResourceAvailabilityCache: ({})

    function resolvedShaderUrl(resourceName) {
        return Qt.resolvedUrl(shaderResourceDirectory + resourceName)
    }

    function shaderResourceExists(url, resourceName, suppressErrors) {
        if (!url || !url.length)
            return false

        if (Object.prototype.hasOwnProperty.call(shaderResourceAvailabilityCache, url))
            return shaderResourceAvailabilityCache[url]

        var available = false

        function checkAvailability(method) {
            try {
                var xhr = new XMLHttpRequest()
                xhr.open(method, url, false)
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

        shaderResourceAvailabilityCache[url] = available
        if (!available && !suppressErrors)
            console.error("❌ FogEffect: shader resource missing", resourceName, url)

        return available
    }

    function shaderPath(fileName) {
        if (!fileName || typeof fileName !== "string")
            return ""

        var normalized = String(fileName)
        if (!preferUnifiedShaderSources && useGlesShaders) {
            var dotIndex = normalized.lastIndexOf(".")
            var glesName
            if (dotIndex > 0)
                glesName = normalized.slice(0, dotIndex) + "_es" + normalized.slice(dotIndex)
            else
                glesName = normalized + "_es"

            var glesUrl = resolvedShaderUrl(glesName)
            if (shaderResourceExists(glesUrl, glesName, false))
                return glesUrl
        }

        var resolvedUrl = resolvedShaderUrl(normalized)
        shaderResourceExists(resolvedUrl, normalized, false)
        return resolvedUrl
    }

    // Шейдеры поставляются в единственном варианте; внутри GLSL-файлов
    // присутствует блок #ifdef GL_ES, добавляющий precision для GLES.
    // Это устраняет необходимость в отдельных файлах с суффиксом _es.

    property bool supportsAutoInsertHeader: false
    property bool useManualShaderHeaders: false
    property bool inlineShaderCodeSupported: false

    property string vertexShaderCode: ""
    property string fragmentShaderCode: ""
    property string fallbackShaderCode: ""

    function requestDesktopShaderProfile(reason) {
        if (forceDesktopShaderProfile)
            return
        console.warn("⚠️ FogEffect:", reason, "– forcing desktop shader profile")
        forceDesktopShaderProfile = true
        Qt.callLater(function() {
            refreshShaderSources()
            refreshShaderAssignments()
        })
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
        requestDesktopShaderProfile(
                    `Shader ${shaderId} reported #version incompatibility`)
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

    function loadShaderSource(fileName, stripVersionDirective) {
        var url = shaderPath(fileName)
        if (!url)
            return ""

        try {
            var xhr = new XMLHttpRequest()
            xhr.open("GET", url, false)
            xhr.send()
            if (xhr.status !== 200 && xhr.status !== 0) {
                console.warn("⚠️ FogEffect: failed to load shader", url, xhr.status)
                return ""
            }

            var source = xhr.responseText || ""
            if (!stripVersionDirective)
                return source

            var lines = source.split(/\r?\n/)
            while (lines.length && lines[0].trim().startsWith("#version"))
                lines.shift()
            return lines.join("\n")
        } catch (error) {
            console.warn("⚠️ FogEffect: shader load error", url, error)
        }
        return ""
    }

    function refreshShaderSources() {
        var stripVersion = !useManualShaderHeaders
        vertexShaderCode = loadShaderSource("fog.vert", stripVersion)
        fragmentShaderCode = loadShaderSource("fog.frag", stripVersion)
        fallbackShaderCode = loadShaderSource("fog_fallback.frag", stripVersion)
    }

    function shaderSupportsInlineCode(shaderItem) {
        if (!shaderItem)
            return false
        try {
            return "code" in shaderItem
        } catch (error) {
        }
        return false
    }

    function shaderDataUrl(source) {
        if (!source || !source.length)
            return ""
        try {
            return "data:text/plain;base64," + Qt.btoa(source)
        } catch (error) {
            console.warn("⚠️ FogEffect: failed to encode shader source", error)
        }
        return ""
    }

    function assignShaderSource(shaderItem, source, fileName) {
        if (!shaderItem)
            return
        if (inlineShaderCodeSupported && shaderSupportsInlineCode(shaderItem)) {
            try {
                shaderItem.code = source
                return
            } catch (error) {
                console.warn("⚠️ FogEffect: unable to assign inline shader code", error)
            }
        }

        if ("shader" in shaderItem) {
            var fallbackUrl = shaderPath(fileName)
            var encoded = shaderDataUrl(source)
            if (encoded && encoded.length) {
                shaderItem.shader = encoded
            } else {
                shaderItem.shader = fallbackUrl
            }
        } else {
            console.warn("⚠️ FogEffect: shader item lacks compatible properties", shaderItem)
        }
    }

    function refreshShaderAssignments() {
        assignShaderSource(fogVertexShader, vertexShaderCode, "fog.vert")
        assignShaderSource(fogFragmentShader, fragmentShaderCode, "fog.frag")
        assignShaderSource(fogFallbackShader, fallbackShaderCode, "fog_fallback.frag")
    }

    Shader {
        id: fogVertexShader
        stage: Shader.Vertex
        Component.onCompleted: {
            fogEffect.assignShaderSource(
                        fogVertexShader,
                        fogEffect.vertexShaderCode,
                        "fog.vert")
            if (!fogEffect.attachShaderLogHandler(fogVertexShader, "fog.vert"))
                console.debug("FogEffect: shader log handler unavailable for fog.vert")
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
        Component.onCompleted: {
            fogEffect.assignShaderSource(
                        fogFragmentShader,
                        fogEffect.fragmentShaderCode,
                        "fog.frag")
            if (!fogEffect.attachShaderLogHandler(fogFragmentShader, "fog.frag"))
                console.debug("FogEffect: shader log handler unavailable for fog.frag")
        }
    }

    Shader {
        id: fogFallbackShader
        stage: Shader.Fragment
        property real userFogDensity: fogEffect.fogDensity
        property color userFogColor: fogEffect.fogColor
        Component.onCompleted: {
            fogEffect.assignShaderSource(
                        fogFallbackShader,
                        fogEffect.fallbackShaderCode,
                        "fog_fallback.frag")
            if (!fogEffect.attachShaderLogHandler(fogFallbackShader, "fog_fallback.frag"))
                console.debug("FogEffect: shader log handler unavailable for fog_fallback.frag")
        }
    }

    passes: [
        Pass {
            shaders: fogEffect.depthTextureAvailable
                    ? [fogVertexShader, fogFragmentShader]
                    : [fogVertexShader, fogFallbackShader]
        }
    ]

    Timer {
        id: animationTimer
        running: fogEffect.animatedFog && fogEffect.depthTextureAvailable
        interval: 16  // 60 FPS
        repeat: true
        onTriggered: fogEffect.time += 0.016
    }

    onVertexShaderCodeChanged: refreshShaderAssignments()
    onFragmentShaderCodeChanged: refreshShaderAssignments()
    onFallbackShaderCodeChanged: refreshShaderAssignments()

    Component.onCompleted: {
        inlineShaderCodeSupported = shaderSupportsInlineCode(fogVertexShader)
                && shaderSupportsInlineCode(fogFragmentShader)
                && shaderSupportsInlineCode(fogFallbackShader)
        if (!inlineShaderCodeSupported)
            console.warn("⚠️ FogEffect: inline shader code not supported; using shader URL fallback")
        supportsAutoInsertHeader = typeof fogVertexShader.autoInsertHeader === "boolean"
                && typeof fogFragmentShader.autoInsertHeader === "boolean"
                && typeof fogFallbackShader.autoInsertHeader === "boolean"
        useManualShaderHeaders = supportsAutoInsertHeader
        if (supportsAutoInsertHeader) {
            fogVertexShader.autoInsertHeader = false
            fogFragmentShader.autoInsertHeader = false
            fogFallbackShader.autoInsertHeader = false
        } else {
            console.warn("⚠️ FogEffect: Shader.autoInsertHeader unavailable; stripping #version from shader sources")
        }
        refreshShaderSources()
        refreshShaderAssignments()
        console.log("🌫️ FogEffect graphics API:", rendererGraphicsApi)
        if (normalizedRendererGraphicsApi.length)
            console.log("   Normalized API:", normalizedRendererGraphicsApi)
        console.log(
                    "   Shader profile:",
                    useGlesShaders
                    ? "OpenGL ES (GLSL 300 es)"
                    : "Desktop (GLSL 330 core)"
                    )
        console.log("   Profile decision flags ->",
                    "preferDesktop:", preferDesktopShaderProfile,
                    "reportedGles:", reportedGlesContext,
                    "forceDesktopOverride:", forceDesktopShaderProfile)
        enableDepthTextureSupport()
        console.log("🌫️ Enhanced Fog Effect loaded")
        console.log("   Density:", fogDensity)
        console.log("   Color:", fogColor)
        console.log("   Distance range:", fogStartDistance, "-", fogEndDistance)
        console.log("   Height-based:", heightBasedFog)
        console.log("   Animated:", animatedFog)
        if (!depthTextureAvailable)
            console.warn("⚠️ FogEffect: depth texture unavailable, fallback shader active")
    }

    onUseGlesShadersChanged: refreshShaderSources()
}
