import QtQuick
import QtQuick3D
import QtQuick3D.Effects

/*
 * Коллекция пост-эффектов для улучшенной визуализации
 * Collection of post-effects for enhanced visualization
 */
Item {
    id: root

    signal effectCompilationError(string effectId, string errorLog)
    signal effectCompilationRecovered(string effectId)

    function handleShaderStatus(effectId, shaderItem, effectItem) {
        if (!shaderItem)
            return

        switch (shaderItem.status) {
        case Shader.Error:
            if (!effectItem.fallbackActive) {
                effectItem.fallbackActive = true
                effectItem.lastErrorLog = shaderItem.log || ""
                console.error("⚠️", effectId, "shader compilation failed:", effectItem.lastErrorLog)
                root.effectCompilationError(effectId, effectItem.lastErrorLog)
            }
            break
        case Shader.Ready:
            if (effectItem.fallbackActive) {
                effectItem.fallbackActive = false
                effectItem.lastErrorLog = ""
                console.log("✅", effectId, "shader compiled successfully, restoring effect")
                root.effectCompilationRecovered(effectId)
            }
            break
        default:
            break
        }
    }

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

    function resolveShaders(isEnabled, effectItem, activeShader, fallbackShader) {
        // Если эффект выключен, отключаем его полностью
        if (!isEnabled) {
            effectItem.enabled = false
            return []
        }
        // Включаем эффект и выбираем нужный шейдер
        effectItem.enabled = true
        return effectItem.fallbackActive ? [fallbackShader] : [activeShader]
    }

    Component.onCompleted: {
        console.log("🎨 Post Effects Collection loaded")
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
        property bool requiresDepthTexture: true
        property bool requiresNormalTexture: true

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
            shader: "
                            #version 440
                            
                            #ifndef INPUT_UV
                            #define INPUT_UV v_uv
                            #endif

                            #ifndef FRAGCOLOR
                            layout(location = 0) out vec4 qt_FragColor;
                            #define FRAGCOLOR qt_FragColor
                            #endif

                            layout(binding = 1) uniform sampler2D qt_Texture0;

                            #ifndef INPUT
                            #define INPUT texture(qt_Texture0, INPUT_UV)
                            #endif

                            uniform float uIntensity;
                            uniform float uThreshold;
                            uniform float uBlurAmount;

                            // Функция luminance
                            float luminance(vec3 color) {
                                return dot(color, vec3(0.299, 0.587, 0.114));
                            }

                            // Gaussian blur
                            vec3 gaussianBlur(vec2 uv, vec2 texelStep, float blurSize) {
                                vec3 color = vec3(0.0);

                                // 9-точечный Gaussian kernel
                                float weights[9] = float[](
                                    0.05, 0.09, 0.12, 0.15, 0.18, 0.15, 0.12, 0.09, 0.05
                                );

                                for (int i = -4; i <= 4; i++) {
                                    vec2 offset = texelStep * float(i) * blurSize * 0.01;
                                    color += texture(qt_Texture0, uv + offset).rgb * weights[i + 4];
                                }

                                return color;
                            }

                            void qt_customMain() {
                                vec4 original = INPUT;

                                // Извлечение ярких областей
                                float lum = luminance(original.rgb);

                                // Размытие ярких областей
                                vec2 texelSize = 1.0 / vec2(textureSize(qt_Texture0, 0));
                                vec3 blurredBright = gaussianBlur(INPUT_UV, texelSize, uBlurAmount);

                                // Комбинирование
                                vec3 bloom = blurredBright * uIntensity;
                                vec3 result = original.rgb + bloom;

                                FRAGCOLOR = vec4(result, original.a);
                            }
                        "
        }

        Shader {
            id: bloomFallbackShader
            stage: Shader.Fragment
            shader: "
                            #version 440

                            
                            #ifndef INPUT_UV
                            #define INPUT_UV v_uv
                            #endif

                            #ifndef FRAGCOLOR
                            layout(location = 0) out vec4 qt_FragColor;
                            #define FRAGCOLOR qt_FragColor
                            #endif

                            layout(binding = 1) uniform sampler2D qt_Texture0;

                            void qt_customMain() {
                                FRAGCOLOR = texture(qt_Texture0, INPUT_UV);
                            }
                        "
        }

        passes: [
            Pass {
                shaders: resolveShaders(root.bloomEnabled, bloomEffect, bloomFragmentShader, bloomFallbackShader)
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

        Component.onCompleted: {
            depthTextureAvailable = true
            normalTextureAvailable = true
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
            property real uCameraNear: root.cameraClipNear
            property real uCameraFar: root.cameraClipFar
            shader: "
                            #version 440

                            layout(location = 0) out vec4 fragColor;
                            #define FRAGCOLOR fragColor

                            uniform sampler2D INPUT;
                            uniform sampler2D DEPTH_TEXTURE;

                            uniform float uIntensity;
                            uniform float uRadius;
                            uniform float uBias;
                            uniform int uSamples;
                            uniform float uCameraNear;
                            uniform float uCameraFar;

                            float random(vec2 co) {
                                return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
                            }

                            float linearizeDepth(float depth) {
                                float z = depth * 2.0 - 1.0;
                                return (2.0 * uCameraNear * uCameraFar)
                                       / (uCameraFar + uCameraNear - z * (uCameraFar - uCameraNear));
                            }

                            void MAIN() {
                                vec4 original = texture(INPUT, INPUT_UV);
                                float depthSample = texture(DEPTH_TEXTURE, INPUT_UV).r;

                                if (depthSample >= 1.0) {
                                    FRAGCOLOR = original;
                                    return;
                                }

                                float centerDepth = linearizeDepth(depthSample);
                                vec2 texelSize = 1.0 / vec2(textureSize(INPUT, 0));
                                float occlusion = 0.0;
                                int sampleCount = max(uSamples, 1);

                                for (int i = 0; i < sampleCount; ++i) {
                                    float progress = (float(i) + random(INPUT_UV + float(i))) / float(sampleCount);
                                    float angle = progress * 6.2831853;
                                    vec2 direction = vec2(cos(angle), sin(angle));
                                    vec2 sampleUV = clamp(INPUT_UV + direction * texelSize * uRadius, 0.0, 1.0);

                                    float sampleDepthRaw = texture(DEPTH_TEXTURE, sampleUV).r;
                                    float sampleDepth = linearizeDepth(sampleDepthRaw);
                                    float depthDiff = sampleDepth - centerDepth;
                                    float rangeCheck = smoothstep(0.0, 1.0, uRadius - abs(depthDiff));
                                    occlusion += depthDiff > uBias ? rangeCheck : 0.0;
                                }

                                float aoFactor = 1.0 - clamp(occlusion / float(sampleCount), 0.0, 1.0) * uIntensity;
                                FRAGCOLOR = vec4(original.rgb * aoFactor, original.a);
                            }
                        "
        }

        Shader {
            id: ssaoFallbackShader
            stage: Shader.Fragment
            shader: "
                            #version 440

                            layout(location = 0) out vec4 fragColor;
                            #define FRAGCOLOR fragColor

                            uniform sampler2D INPUT;

                            void MAIN() {
                                FRAGCOLOR = texture(INPUT, INPUT_UV);
                            }
                        "
        }

        passes: [
            Pass {
                shaders: resolveShaders(root.ssaoEnabled, ssaoEffect, ssaoFragmentShader, ssaoFallbackShader)
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
        property bool requiresDepthTexture: true

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
            depthTextureAvailable = true
        }

        Shader {
            id: dofFragmentShader
            stage: Shader.Fragment
            property real uFocusDistance: dofEffect.focusDistance
            property real uFocusRange: dofEffect.focusRange
            property real uBlurAmount: dofEffect.blurAmount
            property real uCameraNear: dofEffect.cameraNear
            property real uCameraFar: dofEffect.cameraFar
            shader: "
                            #version 440

                            layout(location = 0) out vec4 fragColor;
                            #define FRAGCOLOR fragColor

                            uniform sampler2D INPUT;
                            uniform sampler2D DEPTH_TEXTURE;

                            uniform float uFocusDistance;
                            uniform float uFocusRange;
                            uniform float uBlurAmount;
                            uniform float uCameraNear;
                            uniform float uCameraFar;

                            float linearizeDepth(float depth) {
                                float z = depth * 2.0 - 1.0;
                                return (2.0 * uCameraNear * uCameraFar)
                                       / (uCameraFar + uCameraNear - z * (uCameraFar - uCameraNear));
                            }

                            vec3 circularBlur(vec2 uv, float radius) {
                                vec3 color = vec3(0.0);
                                int samples = 16;

                                for (int i = 0; i < samples; ++i) {
                                    float angle = float(i) * 6.2831853 / float(samples);
                                    vec2 offset = vec2(cos(angle), sin(angle)) * radius;
                                    color += texture(INPUT, uv + offset).rgb;
                                }

                                return color / float(samples);
                            }

                            void MAIN() {
                                vec4 original = texture(INPUT, INPUT_UV);
                                float depth = texture(DEPTH_TEXTURE, INPUT_UV).r;

                                if (depth >= 1.0) {
                                    FRAGCOLOR = original;
                                    return;
                                }

                                float linearDepth = linearizeDepth(depth);
                                float focusFactor = abs(linearDepth - uFocusDistance) / max(0.0001, uFocusRange);
                                float blurRadius = clamp(focusFactor, 0.0, 1.0) * uBlurAmount * 0.01;

                                vec3 blurred = circularBlur(INPUT_UV, blurRadius);
                                vec3 result = mix(original.rgb, blurred, clamp(focusFactor, 0.0, 1.0));

                                FRAGCOLOR = vec4(result, original.a);
                            }
                        "
        }

        Shader {
            id: dofFallbackShader
            stage: Shader.Fragment
            shader: "
                            #version 440

                            layout(location = 0) out vec4 fragColor;
                            #define FRAGCOLOR fragColor

                            uniform sampler2D INPUT;

                            void MAIN() {
                                FRAGCOLOR = texture(INPUT, INPUT_UV);
                            }
                        "
        }

        passes: [
            Pass {
                shaders: resolveShaders(root.depthOfFieldEnabled, dofEffect, dofFragmentShader, dofFallbackShader)
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
        property bool requiresVelocityTexture: false

        property real strength: 0.5          // Сила размытия движения
        property int samples: 8              // Количество сэмплов
        onSamplesChanged: {
            if (samples < 1)
                samples = 1
        }

         Component.onCompleted: {
            velocityTextureAvailable = true
        }

        readonly property real feedbackAmount: Math.min(0.95, Math.max(0.0, 1.0 - 1.0 / Math.max(1, samples)))
        readonly property real enabledFactor: (root.motionBlurEnabled && strength > 0.0 ? 1.0 : 0.0)

        Buffer {
            id: motionBlurHistory
            name: "motionBlurHistory"
            bufferFlags: Buffer.SceneLifetime
        }

        Shader {
            id: motionBlurHistoryShader
            stage: Shader.Fragment
            property real uFeedback: motionBlurEffect.feedbackAmount
            property real uEnabled: motionBlurEffect.enabledFactor
            shader: "
                            #version 440

                            layout(location = 0) out vec4 fragColor;
                            #define FRAGCOLOR fragColor

                            uniform sampler2D INPUT;
                            uniform sampler2D uPrevious;
                            uniform float uFeedback;
                            uniform float uEnabled;

                            void MAIN() {
                                vec4 current = texture(INPUT, INPUT_UV);
                                vec4 previous = texture(uPrevious, INPUT_UV);
                                float active = clamp(uEnabled, 0.0, 1.0);
                                float feedback = clamp(uFeedback, 0.0, 0.95) * active;
                                FRAGCOLOR = mix(current, previous, feedback);
                            }
                        "
        }

        Shader {
            id: motionBlurCompositeShader
            stage: Shader.Fragment
            property real uStrength: motionBlurEffect.strength
            property real uEnabled: motionBlurEffect.enabledFactor
            shader: "
                            #version 440

                            layout(location = 0) out vec4 fragColor;
                            #define FRAGCOLOR fragColor

                            uniform sampler2D INPUT;
                            uniform sampler2D uHistory;
                            uniform float uStrength;
                            uniform float uEnabled;

                            void MAIN() {
                                vec4 current = texture(INPUT, INPUT_UV);
                                vec4 history = texture(uHistory, INPUT_UV);
                                float active = clamp(uEnabled, 0.0, 1.0);
                                float blend = clamp(uStrength, 0.0, 1.0) * active;
                                FRAGCOLOR = mix(current, history, blend);
                            }
                        "
        }

        passes: [
            Pass {
                output: motionBlurHistory
                shaders: [motionBlurHistoryShader]
                commands: [
                    BufferInput {
                        buffer: motionBlurHistory
                        sampler: "uPrevious"
                    }
                ]
            },
            Pass {
                shaders: [motionBlurCompositeShader]
                commands: [
                    BufferInput {
                        buffer: motionBlurHistory
                        sampler: "uHistory"
                    }
                ]
            }
        ]
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
