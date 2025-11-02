import QtQuick
import QtQuick.Window
import QtQuick3D

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
    // qmllint disable unqualified
    readonly property bool preferDesktopShaderProfile: {
        try {
            if (typeof qtGraphicsApiRequiresDesktopShaders === "boolean")
                return qtGraphicsApiRequiresDesktopShaders
        } catch (error) {
        }
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
    readonly property bool reportedGlesContext: {
        try {
            return typeof qtGraphicsApiName === "string"
                    && qtGraphicsApiName.toLowerCase().indexOf("es") !== -1
        } catch (error) {
        }
        return false
    }
    // qmllint enable unqualified
    readonly property bool useGlesShaders: reportedGlesContext && !preferDesktopShaderProfile

    function shaderPath(fileName) {
        if (!fileName || typeof fileName !== "string")
            return ""

        var normalized = String(fileName)
        if (useGlesShaders) {
            var dotIndex = normalized.lastIndexOf(".")
            if (dotIndex > 0) {
                normalized = normalized.slice(0, dotIndex) + "_es" + normalized.slice(dotIndex)
            } else {
                normalized = normalized + "_es"
            }
        }

        return Qt.resolvedUrl("../../shaders/effects/" + normalized)
    }

    // Примечание по совместимости: в средах OpenGL используем GLSL 330 core,
    // а для OpenGL ES автоматически подключаем GLSL 300 es версии шейдеров.
    // Текстурные юниты задаются через layout(binding=...), чтобы Qt не вставлял
    // дополнительные объявления перед директивой #version.

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

    Component.onCompleted: {
        console.log("🎨 Post Effects Collection loaded")
        console.log("   Graphics API:", rendererGraphicsApi)
        console.log(
                    "   Shader profile:",
                    useGlesShaders
                    ? "OpenGL ES (GLSL 300 es)"
                    : "Desktop (GLSL 330 core)"
                    )
        console.log("   Available effects: Bloom, SSAO, DOF, Motion Blur")
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

        Component.onCompleted: {
            root.notifyEffectCompilation("bloom", fallbackActive, lastErrorLog)
            componentCompleted = true
        }

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = qsTr("Bloom: fallback shader active")
            root.notifyEffectCompilation("bloom", fallbackActive, lastErrorLog)
            if (!fallbackActive)
                lastErrorLog = ""
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
            autoInsertHeader: false
            property real uIntensity: bloomEffect.intensity
            property real uThreshold: bloomEffect.threshold
            property real uBlurAmount: bloomEffect.blurAmount
            shader: root.shaderPath("bloom.frag")
        }

        Shader {
            id: bloomFallbackShader
            stage: Shader.Fragment
            autoInsertHeader: false
            shader: root.shaderPath("bloom_fallback.frag")
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
                root.notifyEffectCompilation("ssao", true, lastErrorLog)
            } else {
                lastErrorLog = ""
                fallbackActive = false
                root.notifyEffectCompilation("ssao", false, lastErrorLog)
            }
            componentCompleted = true
        }

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = qsTr("SSAO: fallback shader active")
            root.notifyEffectCompilation("ssao", fallbackActive, lastErrorLog)
            if (!fallbackActive)
                lastErrorLog = ""
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
            autoInsertHeader: false
            property real uIntensity: ssaoEffect.intensity
            property real uRadius: ssaoEffect.radius
            property real uBias: ssaoEffect.bias
            property int uSamples: ssaoEffect.samples
            shader: root.shaderPath("ssao.frag")
        }

        Shader {
            id: ssaoFallbackShader
            stage: Shader.Fragment
            autoInsertHeader: false
            shader: root.shaderPath("ssao_fallback.frag")
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
                root.notifyEffectCompilation("depthOfField", true, lastErrorLog)
            } else {
                lastErrorLog = ""
                fallbackActive = false
                root.notifyEffectCompilation("depthOfField", false, lastErrorLog)
            }
            componentCompleted = true
        }

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = qsTr("Depth of Field: fallback shader active")
            root.notifyEffectCompilation("depthOfField", fallbackActive, lastErrorLog)
            if (!fallbackActive)
                lastErrorLog = ""
        }

        Shader {
            id: dofFragmentShader
            stage: Shader.Fragment
            autoInsertHeader: false
            property real uFocusDistance: dofEffect.focusDistance
            property real uFocusRange: dofEffect.focusRange
            property real uBlurAmount: dofEffect.blurAmount
            property real uCameraNear: dofEffect.cameraNear
            property real uCameraFar: dofEffect.cameraFar
            shader: root.shaderPath("dof.frag")
        }

        Shader {
            id: dofFallbackShader
            stage: Shader.Fragment
            autoInsertHeader: false
            shader: root.shaderPath("dof_fallback.frag")
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
                root.notifyEffectCompilation("motionBlur", true, lastErrorLog)
            } else {
                lastErrorLog = ""
                fallbackActive = false
                root.notifyEffectCompilation("motionBlur", false, lastErrorLog)
            }
            componentCompleted = true
        }

        onFallbackActiveChanged: {
            if (!componentCompleted)
                return
            if (fallbackActive && !lastErrorLog)
                lastErrorLog = qsTr("Motion Blur: fallback shader active")
            root.notifyEffectCompilation("motionBlur", fallbackActive, lastErrorLog)
            if (!fallbackActive)
                lastErrorLog = ""
        }

        Shader {
            id: motionBlurFragmentShader
            stage: Shader.Fragment
            autoInsertHeader: false
            property real uStrength: motionBlurEffect.strength
            property int uSamples: motionBlurEffect.samples
            shader: root.shaderPath("motion_blur.frag")
        }

        Shader {
            id: motionBlurFallbackShader
            stage: Shader.Fragment
            autoInsertHeader: false
            shader: root.shaderPath("motion_blur_fallback.frag")
        }


        passes: [
            Pass {
                shaders: root.resolveShaders(root.motionBlurEnabled, motionBlurEffect, motionBlurFragmentShader, motionBlurFallbackShader)
            }
        ]

        // Effect.enabled is controlled externally via root.motionBlurEnabled
    }

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
