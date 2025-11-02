import QtQuick
import QtQuick.Window
import QtQuick3D
// qmllint disable unused-imports
import QtQuick3D.Effects
import QtQuick3D.Helpers
// qmllint enable unused-imports

/*
 * Коллекция пост-эффектов для улучшенной визуализации
 * Collection of post-effects for enhanced visualization
 */
Item {
    id: root

    signal effectCompilationError(var effectId, string errorLog)
    signal effectCompilationRecovered(var effectId)

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

    function trySetEffectProperty(effectItem, propertyName, value) {
        if (!effectItem || typeof effectItem.setProperty !== "function")
            return false
        try {
            return effectItem.setProperty(propertyName, value)
        } catch (error) {
            console.debug("⚠️", effectItem, "does not support", propertyName, error)
            return false
        }
    }

    // Используем версию шейдеров OpenGL ES только при реальном контексте OpenGL ES.
    // Программный или RHI-рендерер Qt требует десктопный профиль GLSL.
    // Свойство language: Shader.GLSL намеренно не задаём — Qt Quick 3D
    // самостоятельно подбирает подходящий профиль GLSL под активный API.
    // We intentionally omit language: Shader.GLSL so Qt Quick 3D selects
    // the correct GLSL profile for the active graphics backend.
    // qmllint disable unqualified
    property bool forceDesktopShaderProfile: false

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

    property bool shaderAutoHeaderToggleSupported: false
    property bool useManualShaderHeaders: false
    property bool inlineShaderCodeSupported: false
    property int shaderReloadToken: 0
    property var shaderCache: ({})

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

    function shaderPath(fileName) {
        if (!fileName || typeof fileName !== "string")
            return ""

        return Qt.resolvedUrl("../../shaders/effects/" + String(fileName))
    }

    function loadShaderSource(fileName) {
        var url = shaderPath(fileName)
        if (!url)
            return ""
        try {
            var xhr = new XMLHttpRequest()
            xhr.open("GET", url, false)
            xhr.send()
            if (xhr.status !== 200 && xhr.status !== 0) {
                console.warn("⚠️ PostEffects: failed to load shader", url, xhr.status)
                return ""
            }
            var source = xhr.responseText || ""
            if (useManualShaderHeaders)
                return source

            var lines = source.split(/\r?\n/)
            while (lines.length && lines[0].trim().startsWith("#version"))
                lines.shift()
            return lines.join("\n")
        } catch (error) {
            console.warn("⚠️ PostEffects: shader load error", url, error)
        }
        return ""
    }

    function shaderSource(fileName) {
        var cacheKey = (useManualShaderHeaders ? "manual:" : "auto:")
                + (useGlesShaders ? "es:" : "desktop:") + fileName
        if (shaderCache.hasOwnProperty(cacheKey))
            return shaderCache[cacheKey]

        var source = loadShaderSource(fileName)
        shaderCache[cacheKey] = source
        return source
    }

    function shaderSourceWithToken(fileName, reloadToken) {
        reloadToken
        return shaderSource(fileName)
    }

    function reloadShaderSources() {
        shaderCache = ({})
        shaderReloadToken += 1
    }

    function requestDesktopShaderProfile(reason) {
        if (forceDesktopShaderProfile)
            return
        console.warn("⚠️ PostEffects:", reason, "– forcing desktop shader profile")
        forceDesktopShaderProfile = true
        Qt.callLater(function() {
            reloadShaderSources()
            refreshAllShaderAssignments()
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
            console.warn("⚠️ PostEffects: failed to encode shader source", error)
        }
        return ""
    }

    function refreshAllShaderAssignments() {
        // Bindings keep shader URLs synchronized automatically.
    }

    // Примечание по совместимости: единый GLSL-файл обслуживает OpenGL и GLES.
    // Внутри шейдера блок #ifdef GL_ES добавляет precision-объявления,
    // поэтому раздельные файлы с суффиксом _es больше не требуются.

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

    property bool depthOfFieldEnabled: false
    property alias dofFocusDistance: dofEffect.focusDistance
    property alias dofFocusRange: dofEffect.focusRange
    property alias dofBlurAmount: dofEffect.blurAmount

    // Параметры камеры View3D, необходимые для корректного расчёта глубины
    property real cameraClipNear: 0.1
    property real cameraClipFar: 10000.0

    property bool motionBlurEnabled: false
    property alias motionBlurStrength: motionBlurEffect.strength
    property alias motionBlurSamples: motionBlurEffect.samples

    /**
     * Выбирает шейдерные программы для эффекта с учётом состояния фоллбэка.
     *
     * @param {bool} isEnabled            Флаг включения эффекта на уровне UI.
     * @param {Effect} effectItem          QML-объект Effect, для которого выполняется выбор.
     * @param {Shader} activeShader        Основной шейдер, используемый при успешной компиляции.
     * @param {Shader|undefined} fallbackShader  Альтернативный шейдер, применяемый при ошибке компиляции.
     * @returns {list<Shader>} Список шейдеров, который необходимо передать в Pass.shaders.
     */
    function resolveShaders(isEnabled, effectItem, activeShader, fallbackShader) {
        const hasFallback = fallbackShader !== undefined && fallbackShader !== null
        // Если эффект выключен, отключаем его полностью, но оставляем безопасный шейдер,
        // чтобы движок QtQuick3D не создавал пустой шейдер и не завершал компиляцию.
        if (!isEnabled) {
            trySetEffectProperty(effectItem, "enabled", false)
            return hasFallback ? [fallbackShader] : []
        }
        // Включаем эффект и выбираем нужный шейдер. Если не хватает данных и активируется
        // фоллбэк, всегда возвращаем валидный шейдер.
        trySetEffectProperty(effectItem, "enabled", true)
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

    function emitEffectCompilationStatus(effectId, effectItem, fallbackMessage) {
        if (!effectItem)
            return
        var hasLog = typeof effectItem.lastErrorLog !== "undefined"
        var logValue = hasLog ? effectItem.lastErrorLog : ""
        if (effectItem.fallbackActive) {
            if (!logValue && fallbackMessage && hasLog) {
                effectItem.lastErrorLog = fallbackMessage
                logValue = effectItem.lastErrorLog
            }
            root.notifyEffectCompilation(effectId, true, logValue)
        } else {
            root.notifyEffectCompilation(effectId, false, logValue)
            if (hasLog && logValue)
                effectItem.lastErrorLog = ""
        }
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
                    : "Desktop (GLSL 330 core)"
                    )
        console.log("   Profile decision flags ->",
                    "preferDesktop:", preferDesktopShaderProfile,
                    "reportedGles:", reportedGlesContext,
                    "forceDesktopOverride:", forceDesktopShaderProfile)
        console.log("   Available effects: Bloom, SSAO, DOF, Motion Blur")

        inlineShaderCodeSupported = shaderSupportsInlineCode(bloomFragmentShader)
                && shaderSupportsInlineCode(bloomFallbackShader)
                && shaderSupportsInlineCode(ssaoFragmentShader)
                && shaderSupportsInlineCode(ssaoFallbackShader)
                && shaderSupportsInlineCode(dofFragmentShader)
                && shaderSupportsInlineCode(dofFallbackShader)
                && shaderSupportsInlineCode(motionBlurFragmentShader)
                && shaderSupportsInlineCode(motionBlurFallbackShader)
        if (!inlineShaderCodeSupported)
            console.warn("⚠️ PostEffects: inline shader code not supported; using shader URL fallback")

        // qmllint disable missing-property
        shaderAutoHeaderToggleSupported = typeof bloomFragmentShader.autoInsertHeader === "boolean"
                && typeof bloomFallbackShader.autoInsertHeader === "boolean"
                && typeof ssaoFragmentShader.autoInsertHeader === "boolean"
                && typeof ssaoFallbackShader.autoInsertHeader === "boolean"
                && typeof dofFragmentShader.autoInsertHeader === "boolean"
                && typeof dofFallbackShader.autoInsertHeader === "boolean"
                && typeof motionBlurFragmentShader.autoInsertHeader === "boolean"
                && typeof motionBlurFallbackShader.autoInsertHeader === "boolean"
        // qmllint enable missing-property
        useManualShaderHeaders = shaderAutoHeaderToggleSupported
        if (shaderAutoHeaderToggleSupported) {
            var shaders = [
                        bloomFragmentShader,
                        bloomFallbackShader,
                        ssaoFragmentShader,
                        ssaoFallbackShader,
                        dofFragmentShader,
                        dofFallbackShader,
                        motionBlurFragmentShader,
                        motionBlurFallbackShader
                    ]
            // qmllint disable missing-property
            for (var i = 0; i < shaders.length; ++i) {
                try {
                    shaders[i].autoInsertHeader = false
                } catch (error) {
                    console.debug("⚠️ PostEffects: unable to disable auto header", shaders[i], error)
                }
            }
            // qmllint enable missing-property
        } else {
            console.warn("⚠️ PostEffects: Shader.autoInsertHeader unavailable; stripping #version from custom shader sources")
        }
        reloadShaderSources()
        refreshAllShaderAssignments()
    }

    function valueFromKeys(container, keys) {
        if (!container || typeof container !== "object")
            return undefined
        var list = Array.isArray(keys) ? keys : [keys]
        for (var i = 0; i < list.length; ++i) {
            var key = list[i]
            if (container.hasOwnProperty(key))
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

        property bool fallbackActive: false
        property string lastErrorLog: ""
        property bool componentCompleted: false
        readonly property string fallbackMessage: qsTr("Bloom: fallback shader active")

        Component.onCompleted: {
            root.emitEffectCompilationStatus("bloom", bloomEffect, fallbackMessage)
            componentCompleted = true
        }

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = fallbackMessage
            root.emitEffectCompilationStatus("bloom", bloomEffect, fallbackMessage)
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
            property string shaderSource: root.shaderSourceWithToken("bloom.frag", root.shaderReloadToken)
            // qmllint disable import missing-property
            shader: ShaderData {
                source: root.shaderDataUrl(bloomFragmentShader.shaderSource)
            }
            // qmllint enable import missing-property
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(bloomFragmentShader, "bloom.frag"))
                    console.debug("PostEffects: shader log handler unavailable for bloom.frag")
            }
        }

        Shader {
            id: bloomFallbackShader
            stage: Shader.Fragment
            property string shaderSource: root.shaderSourceWithToken("bloom_fallback.frag", root.shaderReloadToken)
            // qmllint disable import missing-property
            shader: ShaderData {
                source: root.shaderDataUrl(bloomFallbackShader.shaderSource)
            }
            // qmllint enable import missing-property
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(bloomFallbackShader, "bloom_fallback.frag"))
                    console.debug("PostEffects: shader log handler unavailable for bloom_fallback.frag")
            }
        }


        passes: [
            Pass {
                shaders: root.resolveShaders(root.bloomEnabled, bloomEffect, bloomFragmentShader, bloomFallbackShader)
            }
        ]

        // Включение свечения контролируется через выбор шейдера (resolveShaders) по root.bloomEnabled,
        // а не через свойство Effect.enabled — эффект всегда активен, но визуализация зависит от выбранного шейдера.
    }

    // SSAO Effect (Screen Space Ambient Occlusion)
    Effect {
        id: ssaoEffect

        property bool fallbackActive: false
        property string lastErrorLog: ""
        property bool depthTextureAvailable: false
        property bool normalTextureAvailable: false
        property bool componentCompleted: false
        readonly property string fallbackMessage: qsTr("SSAO: fallback shader active")

        Component.onCompleted: {
            depthTextureAvailable = root.ensureEffectRequirement(
                        ssaoEffect,
                        "requiresDepthTexture",
                        true,
                        "SSAO: depth texture support enabled",
                        "SSAO: depth texture buffer is not supported; disabling advanced SSAO")
            // fixed: removed deprecated 'requiresNormalTexture' requirement (Qt 6)
            normalTextureAvailable = false

            var requiresFallback = !depthTextureAvailable || !normalTextureAvailable
            if (requiresFallback) {
                lastErrorLog = qsTr("SSAO: depth texture buffer is not supported; disabling advanced SSAO")
                console.warn("⚠️ SSAO: switching to passthrough fallback due to missing textures")
                fallbackActive = true
                root.emitEffectCompilationStatus("ssao", ssaoEffect, fallbackMessage)
            } else {
                lastErrorLog = ""
                fallbackActive = false
                root.emitEffectCompilationStatus("ssao", ssaoEffect, fallbackMessage)
            }
            componentCompleted = true
        }

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = fallbackMessage
            root.emitEffectCompilationStatus("ssao", ssaoEffect, fallbackMessage)
        }

        property real intensity: 0.5      // Интенсивность затенения
        property real radius: 2.0         // Радиус сэмплинга
        property real bias: 0.025         // Смещение для избежания самозатенения
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
            property string shaderSource: root.shaderSourceWithToken("ssao.frag", root.shaderReloadToken)
            // qmllint disable import missing-property
            shader: ShaderData {
                source: root.shaderDataUrl(ssaoFragmentShader.shaderSource)
            }
            // qmllint enable import missing-property
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(ssaoFragmentShader, "ssao.frag"))
                    console.debug("PostEffects: shader log handler unavailable for ssao.frag")
            }
        }

        Shader {
            id: ssaoFallbackShader
            stage: Shader.Fragment
            property string shaderSource: root.shaderSourceWithToken("ssao_fallback.frag", root.shaderReloadToken)
            // qmllint disable import missing-property
            shader: ShaderData {
                source: root.shaderDataUrl(ssaoFallbackShader.shaderSource)
            }
            // qmllint enable import missing-property
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(ssaoFallbackShader, "ssao_fallback.frag"))
                    console.debug("PostEffects: shader log handler unavailable for ssao_fallback.frag")
            }
        }


        passes: [
            Pass {
                shaders: root.resolveShaders(root.ssaoEnabled, ssaoEffect, ssaoFragmentShader, ssaoFallbackShader)
            }
        ]

        // Effect.enabled is controlled externally via root.ssaoEnabled
    }

    // Depth of Field Effect
    Effect {
        id: dofEffect

        // Эффект глубины резкости использует буфер глубины сцены
        property bool fallbackActive: false
        property string lastErrorLog: ""
        property bool depthTextureAvailable: false
        property bool componentCompleted: false
        readonly property string fallbackMessage: qsTr("Depth of Field: fallback shader active")

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

            var requiresFallback = !depthTextureAvailable
            if (requiresFallback) {
                lastErrorLog = qsTr("Depth of Field: depth texture unavailable; using fallback shader")
                console.warn("⚠️ Depth of Field: switching to passthrough fallback due to missing depth texture")
                fallbackActive = true
                root.emitEffectCompilationStatus("depthOfField", dofEffect, fallbackMessage)
            } else {
                lastErrorLog = ""
                fallbackActive = false
                root.emitEffectCompilationStatus("depthOfField", dofEffect, fallbackMessage)
            }
            componentCompleted = true
        }

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = fallbackMessage
            root.emitEffectCompilationStatus("depthOfField", dofEffect, fallbackMessage)
        }

        Shader {
            id: dofFragmentShader
            stage: Shader.Fragment
            property real uFocusDistance: dofEffect.focusDistance
            property real uFocusRange: dofEffect.focusRange
            property real uBlurAmount: dofEffect.blurAmount
            property real uCameraNear: dofEffect.cameraNear
            property real uCameraFar: dofEffect.cameraFar
            property string shaderSource: root.shaderSourceWithToken("dof.frag", root.shaderReloadToken)
            // qmllint disable import missing-property
            shader: ShaderData {
                source: root.shaderDataUrl(dofFragmentShader.shaderSource)
            }
            // qmllint enable import missing-property
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(dofFragmentShader, "dof.frag"))
                    console.debug("PostEffects: shader log handler unavailable for dof.frag")
            }
        }

        Shader {
            id: dofFallbackShader
            stage: Shader.Fragment
            property string shaderSource: root.shaderSourceWithToken("dof_fallback.frag", root.shaderReloadToken)
            // qmllint disable import missing-property
            shader: ShaderData {
                source: root.shaderDataUrl(dofFallbackShader.shaderSource)
            }
            // qmllint enable import missing-property
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(dofFallbackShader, "dof_fallback.frag"))
                    console.debug("PostEffects: shader log handler unavailable for dof_fallback.frag")
            }
        }


        passes: [
            Pass {
                shaders: root.resolveShaders(root.depthOfFieldEnabled, dofEffect, dofFragmentShader, dofFallbackShader)
            }
        ]

        // Effect.enabled is controlled externally via root.depthOfFieldEnabled
    }

    // Motion Blur Effect
    Effect {
        id: motionBlurEffect

        // Эффект размытия движения читает текстуру скоростей
        property bool fallbackActive: false
        property string lastErrorLog: ""
        property bool velocityTextureAvailable: false
        property bool componentCompleted: false
        readonly property string fallbackMessage: qsTr("Motion Blur: fallback shader active")

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

            var requiresFallback = !velocityTextureAvailable
            if (requiresFallback) {
                lastErrorLog = qsTr("Motion Blur: velocity texture unavailable; using fallback shader")
                console.warn("⚠️ Motion Blur: switching to passthrough fallback due to missing velocity texture")
                fallbackActive = true
                root.emitEffectCompilationStatus("motionBlur", motionBlurEffect, fallbackMessage)
            } else {
                lastErrorLog = ""
                fallbackActive = false
                root.emitEffectCompilationStatus("motionBlur", motionBlurEffect, fallbackMessage)
            }
            componentCompleted = true
        }

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = fallbackMessage
            root.emitEffectCompilationStatus("motionBlur", motionBlurEffect, fallbackMessage)
        }

        Shader {
            id: motionBlurFragmentShader
            stage: Shader.Fragment
            property real uStrength: motionBlurEffect.strength
            property int uSamples: motionBlurEffect.samples
            property string shaderSource: root.shaderSourceWithToken("motion_blur.frag", root.shaderReloadToken)
            // qmllint disable import missing-property
            shader: ShaderData {
                source: root.shaderDataUrl(motionBlurFragmentShader.shaderSource)
            }
            // qmllint enable import missing-property
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(motionBlurFragmentShader, "motion_blur.frag"))
                    console.debug("PostEffects: shader log handler unavailable for motion_blur.frag")
            }
        }

        Shader {
            id: motionBlurFallbackShader
            stage: Shader.Fragment
            property string shaderSource: root.shaderSourceWithToken("motion_blur_fallback.frag", root.shaderReloadToken)
            // qmllint disable import missing-property
            shader: ShaderData {
                source: root.shaderDataUrl(motionBlurFallbackShader.shaderSource)
            }
            // qmllint enable import missing-property
            Component.onCompleted: {
                if (!root.attachShaderLogHandler(motionBlurFallbackShader, "motion_blur_fallback.frag"))
                    console.debug("PostEffects: shader log handler unavailable for motion_blur_fallback.frag")
            }
        }


        passes: [
            Pass {
                shaders: root.resolveShaders(root.motionBlurEnabled, motionBlurEffect, motionBlurFragmentShader, motionBlurFallbackShader)
            }
        ]

        // Effect.enabled is controlled externally via root.motionBlurEnabled
    }

    onUseGlesShadersChanged: reloadShaderSources()

    function applyPayload(params, environment) {
        var env = environment || null
        var toSceneLength = env && typeof env.toSceneLength === "function"
            ? env.toSceneLength
            : null

        // Хелпер для безопасного преобразования числовых значений из payload
        function numberFromPayload(value) {
            var num = Number(value)
            return isFinite(num) ? num : undefined
        }

        function convertLength(value) {
            var num = numberFromPayload(value)
            if (num === undefined)
                return undefined
            return toSceneLength ? toSceneLength(num) : num
        }

        if (env) {
            if (env.bloomEnabled !== undefined)
                root.bloomEnabled = !!env.bloomEnabled
            var bloomIntensity = numberFromPayload(env.bloomIntensity)
            if (bloomIntensity !== undefined)
                bloomEffect.intensity = bloomIntensity
            var bloomThreshold = numberFromPayload(env.bloomThreshold)
            if (bloomThreshold !== undefined)
                bloomEffect.threshold = bloomThreshold
            var bloomSpread = numberFromPayload(env.bloomSpread)
            if (bloomSpread !== undefined)
                bloomEffect.blurAmount = Math.max(0.0, bloomSpread)

            if (env.ssaoEnabled !== undefined)
                root.ssaoEnabled = !!env.ssaoEnabled
            var ssaoIntensity = numberFromPayload(env.ssaoIntensity)
            if (ssaoIntensity !== undefined)
                ssaoEffect.intensity = ssaoIntensity
            var ssaoRadius = numberFromPayload(env.ssaoRadius)
            if (ssaoRadius !== undefined) {
                var envRadius = ssaoRadius
                if (envRadius < 0.1)
                    envRadius *= 1000.0
                ssaoEffect.radius = Math.max(0.01, envRadius)
            }
            var ssaoSampleRate = numberFromPayload(env.ssaoSampleRate)
            if (ssaoSampleRate !== undefined)
                ssaoEffect.samples = Math.max(1, Math.round(ssaoSampleRate))

            if (env.internalDepthOfFieldEnabled !== undefined)
                root.depthOfFieldEnabled = !!env.internalDepthOfFieldEnabled
            else if (env.depthOfFieldEnabled !== undefined)
                root.depthOfFieldEnabled = !!env.depthOfFieldEnabled
            var dofFocusDistance = numberFromPayload(env.dofFocusDistance)
            if (dofFocusDistance !== undefined)
                dofEffect.focusDistance = Math.max(0.0, dofFocusDistance)
            var dofFocusRange = numberFromPayload(env.dofFocusRange)
            if (dofFocusRange !== undefined)
                dofEffect.focusRange = Math.max(0.0, dofFocusRange)
            var dofBlurAmount = numberFromPayload(env.dofBlurAmount)
            if (dofBlurAmount !== undefined)
                dofEffect.blurAmount = Math.max(0.0, dofBlurAmount)
        }

        if (params) {
            var bloomEnabledValue = boolFromPayload(params, ["bloomEnabled", "bloom_enabled"], "bloom")
            if (bloomEnabledValue !== undefined)
                root.bloomEnabled = bloomEnabledValue
            var bloomIntensityValue = numberFromPayload(params, ["bloomIntensity", "bloom_intensity"], "bloom")
            if (bloomIntensityValue !== undefined)
                bloomEffect.intensity = bloomIntensityValue
            var bloomThresholdValue = numberFromPayload(params, ["bloomThreshold", "bloom_threshold"], "bloom")
            if (bloomThresholdValue !== undefined)
                bloomEffect.threshold = bloomThresholdValue
            var bloomBlurValue = numberFromPayload(params, ["bloomBlurAmount", "bloom_spread"], "bloom")
            if (bloomBlurValue !== undefined)
                bloomEffect.blurAmount = Math.max(0.0, bloomBlurValue)

            var ssaoEnabledValue = boolFromPayload(params, ["ssaoEnabled", "ao_enabled"], "ssao")
            if (ssaoEnabledValue !== undefined)
                root.ssaoEnabled = ssaoEnabledValue
            var ssaoIntensityValue = numberFromPayload(params, ["ssaoIntensity", "ao_strength"], "ssao")
            if (ssaoIntensityValue !== undefined)
                ssaoEffect.intensity = ssaoIntensityValue
            var ssaoRadiusValue = numberFromPayload(params, ["ssaoRadius", "ao_radius"], "ssao")
            if (ssaoRadiusValue !== undefined) {
                var radius = ssaoRadiusValue
                if (radius < 0.1)
                    radius *= 1000.0
                ssaoEffect.radius = Math.max(0.01, radius)
            }
            var ssaoBiasValue = numberFromPayload(params, ["ssaoBias", "ao_bias"], "ssao")
            if (ssaoBiasValue !== undefined)
                ssaoEffect.bias = Math.max(0.0, ssaoBiasValue)
            var ssaoSamplesValue = numberFromPayload(params, ["ssaoSamples", "ao_sample_rate"], "ssao")
            if (ssaoSamplesValue !== undefined)
                ssaoEffect.samples = Math.max(1, Math.round(ssaoSamplesValue))

            var dofEnabledValue = boolFromPayload(params, ["depthOfFieldEnabled", "depth_of_field"], "depthOfField")
            if (dofEnabledValue !== undefined)
                root.depthOfFieldEnabled = dofEnabledValue
            var dofFocusValue = numberFromPayload(params, ["dofFocusDistance", "dof_focus_distance"], "depthOfField")
            if (dofFocusValue !== undefined) {
                var convertedFocus = convertLength(dofFocusValue)
                if (convertedFocus !== undefined)
                    dofEffect.focusDistance = Math.max(0.0, convertedFocus)
            }
            var dofRangeValue = numberFromPayload(params, ["dofFocusRange", "dof_focus_range"], "depthOfField")
            if (dofRangeValue !== undefined) {
                var convertedRange = convertLength(dofRangeValue)
                if (convertedRange !== undefined)
                    dofEffect.focusRange = Math.max(0.0, convertedRange)
            }
            var dofBlurValue = numberFromPayload(params, ["dofBlurAmount", "dof_blur"], "depthOfField")
            if (dofBlurValue !== undefined)
                dofEffect.blurAmount = Math.max(0.0, dofBlurValue)

            var motionEnabledValue = boolFromPayload(params, ["motionBlurEnabled", "motion_blur"], "motion")
            if (motionEnabledValue !== undefined)
                root.motionBlurEnabled = motionEnabledValue
            var motionStrengthValue = numberFromPayload(params, ["motionBlurStrength", "motion_blur_amount"], "motion")
            if (motionStrengthValue !== undefined)
                motionBlurEffect.strength = Math.max(0.0, motionStrengthValue)
            var motionSamplesValue = numberFromPayload(params, ["motionBlurSamples", "motion_blur_samples"], "motion")
            if (motionSamplesValue !== undefined)
                motionBlurEffect.samples = Math.max(1, Math.round(motionSamplesValue))
        }
    }

    // Функции управления эффектами
    function enableBloom(intensity: real, threshold: real) {
        bloomEffect.intensity = intensity;
        bloomEffect.threshold = threshold;
        root.bloomEnabled = true;
        console.log("✨ Bloom enabled:", intensity, threshold);
    }

    function enableSSAO(intensity: real, radius: real) {
        ssaoEffect.intensity = intensity;
        ssaoEffect.radius = radius;
        root.ssaoEnabled = true;
        console.log("🌑 SSAO enabled:", intensity, radius);
    }

    function enableDepthOfField(focusDistance: real, focusRange: real) {
        dofEffect.focusDistance = focusDistance;
        dofEffect.focusRange = focusRange;
        root.depthOfFieldEnabled = true;
        console.log("📷 DOF enabled:", focusDistance, focusRange);
    }

    function enableMotionBlur(strength: real) {
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
