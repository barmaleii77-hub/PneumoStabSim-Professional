import QtQuick
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

    // Шейдер тумана (uniform parameters configured directly inside shader for Qt 6.10 runtime)
    passes: [
        Pass {
            shaders: [
                Shader {
                    id: fogVertexShader
                    stage: Shader.Vertex
                    shader: "
                        #version 440

                        #ifndef INPUT_POSITION
                        #define INPUT_POSITION qt_Vertex
                        #endif

                        #ifndef INPUT_UV
                        #define INPUT_UV qt_MultiTexCoord0
                        #endif

                        // fixed: rely on QtQuick3D-provided POSITION instead of defining gl_Position
                        layout(location = 0) out vec2 v_uv;
                        layout(location = 1) out vec3 v_worldPos;

                        layout(std140, binding = 0) uniform qt_effectUniforms {
                            mat4 qt_ModelMatrix;
                            mat4 qt_ModelViewProjectionMatrix;
                            mat4 qt_ViewMatrix;
                            vec3 qt_CameraPosition;
                            float qt_Opacity;
                        } ubuf;
                        #ifndef CAMERA_POSITION
                        #define CAMERA_POSITION ubuf.qt_CameraPosition
                        #endif
                        #ifndef EFFECT_OPACITY
                        #define EFFECT_OPACITY ubuf.qt_Opacity
                        #endif

                        void qt_customMain() {
                            vec4 localPosition = vec4(INPUT_POSITION, 1.0);
                            v_uv = INPUT_UV;
                            v_worldPos = (ubuf.qt_ModelMatrix * localPosition).xyz;
                            POSITION = ubuf.qt_ModelViewProjectionMatrix * localPosition;
                        }
                    "
                },
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
                    shader: "
                        #version 440

                        layout(location = 0) in vec2 v_uv;
                        layout(location = 1) in vec3 v_worldPos;

                        #ifndef INPUT_UV
                        #define INPUT_UV v_uv
                        #endif

                        #ifndef FRAGCOLOR
                        layout(location = 0) out vec4 qt_FragColor;
                        #define FRAGCOLOR qt_FragColor
                        #endif

                        #ifndef INPUT
                        layout(binding = 1) uniform sampler2D qt_Texture0;
                        #define INPUT texture(qt_Texture0, INPUT_UV)
                        #endif

                        layout(std140, binding = 0) uniform qt_effectUniforms {
                            mat4 qt_ModelMatrix;
                            mat4 qt_ModelViewProjectionMatrix;
                            mat4 qt_ViewMatrix;
                            vec3 qt_CameraPosition;
                            float qt_Opacity;
                        } ubuf;
                        #ifndef CAMERA_POSITION
                        #define CAMERA_POSITION ubuf.qt_CameraPosition
                        #endif
                        #ifndef EFFECT_OPACITY
                        #define EFFECT_OPACITY ubuf.qt_Opacity
                        #endif

                        float calculateFogFactor(vec3 worldPosition, vec3 cameraPosition) {
                            float distance = length(worldPosition - cameraPosition);

                            float span = max(0.001, userFogEnd - userFogStart);
                            float linearFog = clamp((distance - userFogStart) / span, 0.0, 1.0);

                            float expFog = 1.0 - exp(-userFogDensity * distance * 0.0001);

                            float heightFog = 1.0;
                            if (userFogHeightEnabled > 0.5) {
                                float bottom = min(userFogLeast, userFogMost);
                                float top = max(userFogLeast, userFogMost);
                                float heightSpan = max(0.001, top - bottom);
                                float relative = clamp((top - worldPosition.y) / heightSpan, 0.0, 1.0);
                                float curve = max(0.0001, userFogHeightCurve);
                                heightFog = pow(relative, curve);
                            }

                            float animationFactor = 1.0;
                            if (userFogAnimated > 0.5) {
                                vec3 noisePos = worldPosition * 0.001 + vec3(userFogTime * userFogAnimationSpeed);
                                float noise = sin(noisePos.x * 12.9898 + noisePos.y * 78.233 + noisePos.z * 37.719) * 43758.5453;
                                noise = (sin(noise) + 1.0) * 0.5;
                                animationFactor = 0.8 + 0.4 * noise;
                            }

                            return clamp(linearFog * expFog * heightFog * animationFactor, 0.0, 1.0);
                        }

                        void qt_customMain() {
                            vec4 originalColor = INPUT;

                            float fogFactor = calculateFogFactor(v_worldPos, CAMERA_POSITION);

                            vec3 scatteredColor = userFogColor.rgb * userFogScattering;
                            vec3 foggedColor = mix(
                                originalColor.rgb,
                                userFogColor.rgb + scatteredColor,
                                fogFactor
                            );

                            if (userFogTransmitEnabled > 0.5) {
                                float transmitCurve = max(0.0001, userFogTransmitCurve);
                                float transmission = pow(1.0 - fogFactor, transmitCurve);
                                foggedColor = mix(foggedColor, originalColor.rgb, transmission);
                            }

                            FRAGCOLOR = vec4(foggedColor, originalColor.a) * EFFECT_OPACITY;
                        }
                    "
                }
            ]
        }
    ]
    // Таймер для анимации тумана
    Timer {
        id: animationTimer
        running: fogEffect.animatedFog
        interval: 16  // 60 FPS
        repeat: true
        onTriggered: {
            fogEffect.time += 0.016;
        }
    }

    // Отладочная информация
    Component.onCompleted: {
        console.log("🌫️ Enhanced Fog Effect loaded");
        console.log("   Density:", fogDensity);
        console.log("   Color:", fogColor);
        console.log("   Distance range:", fogStartDistance, "-", fogEndDistance);
        console.log("   Height-based:", heightBasedFog);
        console.log("   Animated:", animatedFog);
    }
}
