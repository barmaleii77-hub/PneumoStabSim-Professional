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
    property alias bloomEnabled: bloomEffect.enabled
    property alias bloomIntensity: bloomEffect.intensity
    property alias bloomThreshold: bloomEffect.threshold
    property alias bloomBlurAmount: bloomEffect.blurAmount

    property alias ssaoEnabled: ssaoEffect.enabled
    property alias ssaoIntensity: ssaoEffect.intensity
    property alias ssaoRadius: ssaoEffect.radius
    property alias ssaoBias: ssaoEffect.bias
    property alias ssaoSamples: ssaoEffect.samples

    property alias depthOfFieldEnabled: dofEffect.enabled
    property alias dofFocusDistance: dofEffect.focusDistance
    property alias dofFocusRange: dofEffect.focusRange
    property alias dofBlurAmount: dofEffect.blurAmount

    property alias motionBlurEnabled: motionBlurEffect.enabled
    property alias motionBlurStrength: motionBlurEffect.strength
    property alias motionBlurSamples: motionBlurEffect.samples

    // Эффекты для добавления в View3D
    property list<Effect> effects: [
        bloomEffect,
        ssaoEffect,
        dofEffect,
        motionBlurEffect
    ]

    // Bloom Effect (эффект свечения)
    Effect {
        id: bloomEffect
        enabled: false

        property bool fallbackActive: false
        property string lastErrorLog: ""

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

                            layout(location = 0) in vec2 coord;
                            
                            #ifndef INPUT_UV
                            #define INPUT_UV coord
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
            onStatusChanged: root.handleShaderStatus("Bloom", bloomFragmentShader, bloomEffect)
        }

        Shader {
            id: bloomFallbackShader
            stage: Shader.Fragment
            shader: "
                            #version 440

                            layout(location = 0) in vec2 coord;
                            
                            #ifndef INPUT_UV
                            #define INPUT_UV coord
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
                shaders: bloomEffect.fallbackActive ? [bloomFallbackShader] : [bloomFragmentShader]
            }
        ]

        onEnabledChanged: {
            if (enabled) {
                console.log("✨ Bloom effect enabled - intensity:", intensity);
            }
        }
    }

    // SSAO Effect (Screen Space Ambient Occlusion)
    Effect {
        id: ssaoEffect
        enabled: false

        requiresDepthTexture: true
        requiresNormalTexture: true

        // Явное связывание текстур глубины и нормалей для SSAO
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
        }
        Parameter {
            name: "normalTexture"
            value: Effect.NormalTexture
        }
        // Явное связывание текстур глубины и нормалей для SSAO
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
        }
        Parameter {
            name: "normalTexture"
            value: Effect.NormalTexture
        }
        // Явное связывание текстур глубины и нормалей для SSAO
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
        }
        Parameter {
            name: "normalTexture"
            value: Effect.NormalTexture
        }
        // Явное связывание текстур глубины и нормалей для SSAO
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
        }
        Parameter {
            name: "normalTexture"
            value: Effect.NormalTexture
        }
        // Явное связывание текстур глубины и нормалей для SSAO
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
        }
        Parameter {
            name: "normalTexture"
            value: Effect.NormalTexture
        }
        // Явное связывание текстур глубины и нормалей для SSAO
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
        }
        Parameter {
            name: "normalTexture"
            value: Effect.NormalTexture
        }
        // Явное связывание текстур глубины и нормалей для SSAO
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
        }
        Parameter {
            name: "normalTexture"
            value: Effect.NormalTexture
        }
        property bool fallbackActive: false
        property string lastErrorLog: ""

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
            shader: "
                            #version 440

                            layout(location = 0) in vec2 coord;
                            
                            #ifndef INPUT_UV
                            #define INPUT_UV coord
                            #endif

                            #ifndef FRAGCOLOR
                            layout(location = 0) out vec4 qt_FragColor;
                            #define FRAGCOLOR qt_FragColor
                            #endif

                            layout(binding = 1) uniform sampler2D qt_Texture0;
                            layout(binding = 2) uniform sampler2D depthTexture;
                            layout(binding = 3) uniform sampler2D normalTexture;

                            #ifndef INPUT
                            #define INPUT texture(qt_Texture0, INPUT_UV)
                            #endif

                            uniform float uIntensity;
                            uniform float uRadius;
                            uniform float uBias;
                            uniform int uSamples;

                            // Генерация случайных векторов для сэмплинга
                            vec3 generateSampleVector(int index) {
                                float angle = float(index) * 0.39269908; // 2π/16
                                float radius = float(index + 1) / max(1.0, float(uSamples));

                                return vec3(
                                    cos(angle) * radius,
                                    sin(angle) * radius,
                                    radius * 0.5 + 0.5
                                );
                            }

                            void qt_customMain() {
                                vec4 original = INPUT;
                                vec3 normal = normalize(texture(normalTexture, INPUT_UV).xyz * 2.0 - 1.0);
                                float depth = texture(depthTexture, INPUT_UV).r;

                                if (depth >= 1.0) {
                                    FRAGCOLOR = original;
                                    return;
                                }

                                float occlusion = 0.0;
                                vec2 texelSize = 1.0 / vec2(textureSize(qt_Texture0, 0));
                                int sampleCount = max(uSamples, 1);

                                // SSAO сэмплинг
                                for (int i = 0; i < sampleCount; i++) {
                                    vec3 sampleVec = generateSampleVector(i);

                                    // Ориентация сэмплов по нормали
                                    sampleVec = normalize(sampleVec);
                                    if (dot(sampleVec, normal) < 0.0) {
                                        sampleVec = -sampleVec;
                                    }

                                    vec2 sampleCoord = INPUT_UV + sampleVec.xy * uRadius * texelSize;
                                    float sampleDepth = texture(depthTexture, sampleCoord).r;

                                    // Проверка окклюзии
                                    float depthDiff = depth - sampleDepth;
                                    if (depthDiff > uBias) {
                                        occlusion += 1.0;
                                    }
                                }

                                occlusion /= max(1.0, float(sampleCount));
                                occlusion = 1.0 - (occlusion * uIntensity);

                                FRAGCOLOR = vec4(original.rgb * occlusion, original.a);
                            }
                        "
            onStatusChanged: root.handleShaderStatus("SSAO", ssaoFragmentShader, ssaoEffect)
        }

        Shader {
            id: ssaoFallbackShader
            stage: Shader.Fragment
            shader: "
                            #version 440

                            layout(location = 0) in vec2 coord;

                            #ifndef INPUT_UV
                            #define INPUT_UV coord
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
                shaders: ssaoEffect.fallbackActive ? [ssaoFallbackShader] : [ssaoFragmentShader]
            }
        ]

        onEnabledChanged: {
            if (enabled) {
                console.log("🌑 SSAO effect enabled - intensity:", intensity);
            }
        }
    }

    // Depth of Field Effect
    Effect {
        id: dofEffect
        enabled: false

        property bool fallbackActive: false
        property string lastErrorLog: ""

        property real focusDistance: 2000.0  // Расстояние фокуса (мм)
        property real focusRange: 1000.0     // Диапазон фокуса (мм)
        property real blurAmount: 1.0        // Сила размытия

        property real cameraNear: 0.1
        property real cameraFar: 10000.0

        requiresDepthTexture: true

        // Явное связывание depthTexture для шейдера (binding=2)
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        // Явное связывание depthTexture для шейдера (binding=2)
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        // Явное связывание depthTexture для шейдера (binding=2)
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        // Явное связывание depthTexture для шейдера (binding=2)
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        // Явное связывание depthTexture для шейдера (binding=2)
        Parameter {
            name: "depthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        onBlurAmountChanged: {
            if (blurAmount < 0.0)
                blurAmount = 0.0
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

                            layout(location = 0) in vec2 coord;
                            
                            #ifndef INPUT_UV
                            #define INPUT_UV coord
                            #endif

                            #ifndef FRAGCOLOR
                            layout(location = 0) out vec4 qt_FragColor;
                            #define FRAGCOLOR qt_FragColor
                            #endif

                            layout(binding = 1) uniform sampler2D qt_Texture0;
                            layout(binding = 2) uniform sampler2D depthTexture;

                            #ifndef INPUT
                            #define INPUT texture(qt_Texture0, INPUT_UV)
                            #endif

                            uniform float uFocusDistance;
                            uniform float uFocusRange;
                            uniform float uBlurAmount;
                            uniform float uCameraNear;
                            uniform float uCameraFar;

                            // Преобразование depth buffer в линейную глубину
                            float linearizeDepth(float depth) {
                                float z = depth * 2.0 - 1.0;
                                return (2.0 * uCameraNear * uCameraFar) /
                                       (uCameraFar + uCameraNear - z * (uCameraFar - uCameraNear));
                            }

                            // Размытие по кругу (bokeh)
                            vec3 circularBlur(vec2 uv, float radius) {
                                vec3 color = vec3(0.0);
                                int samples = 16;

                                for (int i = 0; i < samples; i++) {
                                    float angle = float(i) * 6.28318 / float(samples);
                                    vec2 offset = vec2(cos(angle), sin(angle)) * radius;
                                    color += texture(qt_Texture0, uv + offset).rgb;
                                }

                                return color / float(samples);
                            }

                            void qt_customMain() {
                                vec4 original = INPUT;
                                float depth = texture(depthTexture, INPUT_UV).r;
                                float linearDepth = linearizeDepth(depth);

                                // Расчет blur радиуса на основе расстояния от фокуса
                                float focusFactor = abs(linearDepth - uFocusDistance) / max(0.0001, uFocusRange);
                                float blurRadius = clamp(focusFactor, 0.0, 1.0) * uBlurAmount * 0.01;

                                vec3 blurred = circularBlur(INPUT_UV, blurRadius);
                                vec3 result = mix(original.rgb, blurred, clamp(focusFactor, 0.0, 1.0));

                                FRAGCOLOR = vec4(result, original.a);
                            }
                        "
            onStatusChanged: root.handleShaderStatus("DepthOfField", dofFragmentShader, dofEffect)
        }

        Shader {
            id: dofFallbackShader
            stage: Shader.Fragment
            shader: "
                            #version 440

                            layout(location = 0) in vec2 coord;

                            #ifndef INPUT_UV
                            #define INPUT_UV coord
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
                shaders: dofEffect.fallbackActive ? [dofFallbackShader] : [dofFragmentShader]
            }
        ]

        onEnabledChanged: {
            if (enabled) {
                console.log("📷 Depth of Field enabled - focus:", focusDistance);
            }
        }
    }

    // Motion Blur Effect
    Effect {
        id: motionBlurEffect
        enabled: false

        property bool fallbackActive: false
        property string lastErrorLog: ""

        property real strength: 0.5          // Сила размытия движения
        property int samples: 8              // Количество сэмплов
        requiresDepthTexture: true
        requiresVelocityTexture: true

        // Явное связывание depth и velocity текстур через Parameter
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        Parameter {
            name: "qt_VelocityTexture"
            value: Effect.VelocityTexture
            binding: 3
        }
        // Явное связывание depth и velocity текстур через Parameter
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        Parameter {
            name: "qt_VelocityTexture"
            value: Effect.VelocityTexture
            binding: 3
        }
        // Явное связывание depth и velocity текстур через Parameter
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        Parameter {
            name: "qt_VelocityTexture"
            value: Effect.VelocityTexture
            binding: 3
        }
        // Явное связывание depth и velocity текстур через Parameter
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        Parameter {
            name: "qt_VelocityTexture"
            value: Effect.VelocityTexture
            binding: 3
        }
        // Явное связывание depth и velocity текстур через Parameter
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        Parameter {
            name: "qt_VelocityTexture"
            value: Effect.VelocityTexture
            binding: 3
        }
        // Явное связывание depth и velocity текстур через Parameter
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        Parameter {
            name: "qt_VelocityTexture"
            value: Effect.VelocityTexture
            binding: 3
        }
        // Явное связывание depth и velocity текстур через Parameter
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        Parameter {
            name: "qt_VelocityTexture"
            value: Effect.VelocityTexture
            binding: 3
        }
        // Явное связывание depth и velocity текстур через Parameter
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        Parameter {
            name: "qt_VelocityTexture"
            value: Effect.VelocityTexture
            binding: 3
        }
        // Явное связывание depth и velocity текстур через Parameter
        Parameter {
            name: "qt_DepthTexture"
            value: Effect.DepthTexture
            binding: 2
        }
        Parameter {
            name: "qt_VelocityTexture"
            value: Effect.VelocityTexture
            binding: 3
        }
        onSamplesChanged: {
            if (samples < 1)
                samples = 1
        }

        Shader {
            id: motionBlurFragmentShader
            stage: Shader.Fragment
            property real uStrength: motionBlurEffect.strength
            property int uSamples: motionBlurEffect.samples
            shader: "
                            #version 440

                            layout(location = 0) in vec2 coord;
                            
                            #ifndef INPUT_UV
                            #define INPUT_UV coord
                            #endif

                            #ifndef FRAGCOLOR
                            layout(location = 0) out vec4 qt_FragColor;
                            #define FRAGCOLOR qt_FragColor
                            #endif

                            layout(binding = 1) uniform sampler2D qt_Texture0;
                            layout(binding = 2) uniform sampler2D velocityTexture;

                            #ifndef INPUT
                            #define INPUT texture(qt_Texture0, INPUT_UV)
                            #endif

                            uniform float uStrength;
                            uniform int uSamples;

                            void qt_customMain() {
                                vec4 original = INPUT;
                                vec2 velocity = texture(velocityTexture, INPUT_UV).xy;

                                vec3 color = original.rgb;
                                int sampleCount = max(uSamples, 1);
                                vec2 step = velocity * uStrength / max(1.0, float(sampleCount));

                                // Сэмплирование вдоль вектора движения
                                for (int i = 1; i < sampleCount; i++) {
                                    vec2 sampleCoord = INPUT_UV + step * float(i);
                                    color += texture(qt_Texture0, sampleCoord).rgb;
                                }

                                color /= max(1.0, float(sampleCount));
                                FRAGCOLOR = vec4(color, original.a);
                            }
                        "
            onStatusChanged: root.handleShaderStatus("MotionBlur", motionBlurFragmentShader, motionBlurEffect)
        }

        Shader {
            id: motionBlurFallbackShader
            stage: Shader.Fragment
            shader: "
                            #version 440

                            layout(location = 0) in vec2 coord;

                            #ifndef INPUT_UV
                            #define INPUT_UV coord
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
                shaders: motionBlurEffect.fallbackActive ? [motionBlurFallbackShader] : [motionBlurFragmentShader]
            }
        ]

        onEnabledChanged: {
            if (enabled) {
                console.log("💨 Motion Blur enabled - strength:", strength);
            }
        }
    }

    // Функции управления эффектами
    function enableBloom(intensity: real, threshold: real) {
        bloomEffect.intensity = intensity;
        bloomEffect.threshold = threshold;
        bloomEffect.enabled = true;
        console.log("✨ Bloom enabled:", intensity, threshold);
    }

    function enableSSAO(intensity: real, radius: real) {
        ssaoEffect.intensity = intensity;
        ssaoEffect.radius = radius;
        ssaoEffect.enabled = true;
        console.log("🌑 SSAO enabled:", intensity, radius);
    }

    function enableDepthOfField(focusDistance: real, focusRange: real) {
        dofEffect.focusDistance = focusDistance;
        dofEffect.focusRange = focusRange;
        dofEffect.enabled = true;
        console.log("📷 DOF enabled:", focusDistance, focusRange);
    }

    function enableMotionBlur(strength: real) {
        motionBlurEffect.strength = strength;
        motionBlurEffect.enabled = true;
        console.log("💨 Motion Blur enabled:", strength);
    }

    function disableAllEffects() {
        bloomEffect.enabled = false;
        ssaoEffect.enabled = false;
        dofEffect.enabled = false;
        motionBlurEffect.enabled = false;
        console.log("🚫 All post-effects disabled");
    }

    Component.onCompleted: {
        console.log("🎨 Post Effects Collection loaded");
        console.log("   Available effects: Bloom, SSAO, DOF, Motion Blur");
    }
}
