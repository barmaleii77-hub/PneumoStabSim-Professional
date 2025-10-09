import QtQuick
import QtQuick3D
import QtQuick3D.Effects

/*
 * Коллекция пост-эффектов для улучшенной визуализации
 * Collection of post-effects for enhanced visualization
 */
Item {
    id: root
    
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
        
        property real intensity: 0.3      // Интенсивность свечения
        property real threshold: 0.7      // Порог яркости для свечения
        property real blurAmount: 1.0     // Размытие свечения
        
        passes: [
            Pass {
                shaders: [
                    Shader {
                        stage: Shader.Fragment
                        shader: "
                            #version 440
                            
                            layout(location = 0) in vec2 coord;
                            layout(location = 0) out vec4 fragColor;
                            
                            layout(std140, binding = 0) uniform buf {
                                float intensity;
                                float threshold;
                                float blurAmount;
                            } ubuf;
                            
                            layout(binding = 1) uniform sampler2D qt_Texture0;
                            
                            // Функция luminance
                            float luminance(vec3 color) {
                                return dot(color, vec3(0.299, 0.587, 0.114));
                            }
                            
                            // Gaussian blur
                            vec3 gaussianBlur(sampler2D tex, vec2 uv, vec2 direction, float blurSize) {
                                vec3 color = vec3(0.0);
                                
                                // 9-точечный Gaussian kernel
                                float weights[9] = float[](
                                    0.05, 0.09, 0.12, 0.15, 0.18, 0.15, 0.12, 0.09, 0.05
                                );
                                
                                for (int i = -4; i <= 4; i++) {
                                    vec2 offset = direction * float(i) * blurSize * 0.01;
                                    color += texture(tex, uv + offset).rgb * weights[i + 4];
                                }
                                
                                return color;
                            }
                            
                            void main() {
                                vec4 original = texture(qt_Texture0, coord);
                                
                                // Извлечение ярких областей
                                float lum = luminance(original.rgb);
                                vec3 bright = original.rgb * max(0.0, lum - ubuf.threshold);
                                
                                // Размытие ярких областей
                                vec2 texelSize = 1.0 / textureSize(qt_Texture0, 0);
                                vec3 blurredBright = gaussianBlur(qt_Texture0, coord, texelSize, ubuf.blurAmount);
                                
                                // Комбинирование
                                vec3 bloom = blurredBright * ubuf.intensity;
                                vec3 result = original.rgb + bloom;
                                
                                fragColor = vec4(result, original.a);
                            }
                        "
                    }
                ]
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
        
        property real intensity: 0.5      // Интенсивность затенения
        property real radius: 2.0         // Радиус сэмплинга
        property real bias: 0.025         // Смещение для избежания самозатенения
        property int samples: 16          // Количество сэмплов
        
        passes: [
            Pass {
                shaders: [
                    Shader {
                        stage: Shader.Fragment
                        shader: "
                            #version 440
                            
                            layout(location = 0) in vec2 coord;
                            layout(location = 0) out vec4 fragColor;
                            
                            layout(std140, binding = 0) uniform buf {
                                float intensity;
                                float radius;
                                float bias;
                                int samples;
                                mat4 projectionMatrix;
                                mat4 viewMatrix;
                            } ubuf;
                            
                            layout(binding = 1) uniform sampler2D qt_Texture0;
                            layout(binding = 2) uniform sampler2D depthTexture;
                            layout(binding = 3) uniform sampler2D normalTexture;
                            
                            // Генерация случайных векторов для сэмплинга
                            vec3 generateSampleVector(int index, vec2 screenCoord) {
                                float angle = float(index) * 0.39269908; // 2π/16
                                float radius = float(index + 1) / float(ubuf.samples);
                                
                                return vec3(
                                    cos(angle) * radius,
                                    sin(angle) * radius,
                                    radius * 0.5 + 0.5
                                );
                            }
                            
                            void main() {
                                vec4 original = texture(qt_Texture0, coord);
                                vec3 normal = normalize(texture(normalTexture, coord).xyz * 2.0 - 1.0);
                                float depth = texture(depthTexture, coord).r;
                                
                                if (depth >= 1.0) {
                                    fragColor = original;
                                    return;
                                }
                                
                                float occlusion = 0.0;
                                vec2 texelSize = 1.0 / textureSize(qt_Texture0, 0);
                                
                                // SSAO сэмплинг
                                for (int i = 0; i < ubuf.samples; i++) {
                                    vec3 sampleVec = generateSampleVector(i, coord);
                                    
                                    // Ориентация сэмплов по нормали
                                    sampleVec = normalize(sampleVec);
                                    if (dot(sampleVec, normal) < 0.0) {
                                        sampleVec = -sampleVec;
                                    }
                                    
                                    vec2 sampleCoord = coord + sampleVec.xy * ubuf.radius * texelSize;
                                    float sampleDepth = texture(depthTexture, sampleCoord).r;
                                    
                                    // Проверка окклюзии
                                    float depthDiff = depth - sampleDepth;
                                    if (depthDiff > ubuf.bias) {
                                        occlusion += 1.0;
                                    }
                                }
                                
                                occlusion /= float(ubuf.samples);
                                occlusion = 1.0 - (occlusion * ubuf.intensity);
                                
                                fragColor = vec4(original.rgb * occlusion, original.a);
                            }
                        "
                    }
                ]
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
        
        property real focusDistance: 2000.0  // Расстояние фокуса (мм)
        property real focusRange: 1000.0     // Диапазон фокуса (мм)
        property real blurAmount: 1.0        // Сила размытия
        
        passes: [
            Pass {
                shaders: [
                    Shader {
                        stage: Shader.Fragment
                        shader: "
                            #version 440
                            
                            layout(location = 0) in vec2 coord;
                            layout(location = 0) out vec4 fragColor;
                            
                            layout(std140, binding = 0) uniform buf {
                                float focusDistance;
                                float focusRange;
                                float blurAmount;
                                float cameraNear;
                                float cameraFar;
                            } ubuf;
                            
                            layout(binding = 1) uniform sampler2D qt_Texture0;
                            layout(binding = 2) uniform sampler2D depthTexture;
                            
                            // Преобразование depth buffer в линейную глубину
                            float linearizeDepth(float depth) {
                                float z = depth * 2.0 - 1.0;
                                return (2.0 * ubuf.cameraNear * ubuf.cameraFar) / 
                                       (ubuf.cameraFar + ubuf.cameraNear - z * (ubuf.cameraFar - ubuf.cameraNear));
                            }
                            
                            // Размытие по кругу (bokeh)
                            vec3 circularBlur(sampler2D tex, vec2 uv, float radius) {
                                vec3 color = vec3(0.0);
                                int samples = 16;
                                
                                for (int i = 0; i < samples; i++) {
                                    float angle = float(i) * 6.28318 / float(samples);
                                    vec2 offset = vec2(cos(angle), sin(angle)) * radius;
                                    color += texture(tex, uv + offset).rgb;
                                }
                                
                                return color / float(samples);
                            }
                            
                            void main() {
                                vec4 original = texture(qt_Texture0, coord);
                                float depth = texture(depthTexture, coord).r;
                                float linearDepth = linearizeDepth(depth);
                                
                                // Расчет blur радиуса на основе расстояния от фокуса
                                float focusFactor = abs(linearDepth - ubuf.focusDistance) / ubuf.focusRange;
                                float blurRadius = clamp(focusFactor, 0.0, 1.0) * ubuf.blurAmount * 0.01;
                                
                                vec3 blurred = circularBlur(qt_Texture0, coord, blurRadius);
                                vec3 result = mix(original.rgb, blurred, clamp(focusFactor, 0.0, 1.0));
                                
                                fragColor = vec4(result, original.a);
                            }
                        "
                    }
                ]
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
        
        property real strength: 0.5          // Сила размытия движения
        property int samples: 8              // Количество сэмплов
        
        passes: [
            Pass {
                shaders: [
                    Shader {
                        stage: Shader.Fragment
                        shader: "
                            #version 440
                            
                            layout(location = 0) in vec2 coord;
                            layout(location = 0) out vec4 fragColor;
                            
                            layout(std140, binding = 0) uniform buf {
                                float strength;
                                int samples;
                                mat4 previousViewProjection;
                                mat4 currentViewProjection;
                            } ubuf;
                            
                            layout(binding = 1) uniform sampler2D qt_Texture0;
                            layout(binding = 2) uniform sampler2D velocityTexture;
                            
                            void main() {
                                vec4 original = texture(qt_Texture0, coord);
                                vec2 velocity = texture(velocityTexture, coord).xy;
                                
                                vec3 color = original.rgb;
                                vec2 step = velocity * ubuf.strength / float(ubuf.samples);
                                
                                // Сэмплирование вдоль вектора движения
                                for (int i = 1; i < ubuf.samples; i++) {
                                    vec2 sampleCoord = coord + step * float(i);
                                    color += texture(qt_Texture0, sampleCoord).rgb;
                                }
                                
                                color /= float(ubuf.samples);
                                fragColor = vec4(color, original.a);
                            }
                        "
                    }
                ]
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
