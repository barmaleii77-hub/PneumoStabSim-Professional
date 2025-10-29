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

                        layout(location = 0) in vec3 qt_Vertex;
                        layout(location = 1) in vec2 qt_MultiTexCoord0;

                        layout(location = 0) out vec2 coord;
                        layout(location = 1) out vec3 worldPos;
                        layout(location = 2) out vec3 viewPos;

                        layout(std140, binding = 0) uniform buf {
                            mat4 qt_Matrix;
                            mat4 qt_ModelViewProjectionMatrix;
                            mat4 qt_ViewMatrix;
                            vec3 qt_CameraPosition;
                            float qt_Opacity;
                        } ubuf;

                        void MAIN() {
                            coord = qt_MultiTexCoord0;
                            worldPos = qt_Vertex;
                            viewPos = (ubuf.qt_ViewMatrix * vec4(qt_Vertex, 1.0)).xyz;
                            gl_Position = ubuf.qt_ModelViewProjectionMatrix * vec4(qt_Vertex, 1.0);
                        }
                    "
                },
                Shader {
                    id: fogFragmentShader
                    stage: Shader.Fragment
                    shader: "
                        #version 440

                        layout(location = 0) in vec2 coord;
                        layout(location = 1) in vec3 worldPos;
                        layout(location = 2) in vec3 viewPos;
                        layout(location = 0) out vec4 fragColor;

                        layout(std140, binding = 0) uniform buf {
                            mat4 qt_Matrix;
                            mat4 qt_ModelViewProjectionMatrix;
                            mat4 qt_ViewMatrix;
                            vec3 qt_CameraPosition;
                            float qt_Opacity;
                        } ubuf;

                        layout(binding = 2) uniform sampler2D qt_Texture0;

                        layout(std140, binding = 1) uniform FogParams {
                            float userFogDensity;
                            float userFogStart;
                            float userFogEnd;
                            float userFogLeast;
                            float userFogMost;
                            float userFogHeightCurve;
                            float userFogHeightEnabled;
                            float userFogScattering;
                            float userFogTransmitEnabled;
                            float userFogTransmitCurve;
                            float userFogAnimated;
                            float userFogAnimationSpeed;
                            float userFogTime;
                            vec4 userFogColor;
                        } fogParams;

                        float calculateFogFactor(vec3 worldPosition, vec3 cameraPosition) {
                            float distance = length(worldPosition - cameraPosition);

                            float span = max(0.001, fogParams.userFogEnd - fogParams.userFogStart);
                            float linearFog = clamp((distance - fogParams.userFogStart) / span, 0.0, 1.0);

                            float expFog = 1.0 - exp(-fogParams.userFogDensity * distance * 0.0001);

                            float heightFog = 1.0;
                            if (fogParams.userFogHeightEnabled > 0.5) {
                                float bottom = min(fogParams.userFogLeast, fogParams.userFogMost);
                                float top = max(fogParams.userFogLeast, fogParams.userFogMost);
                                float heightSpan = max(0.001, top - bottom);
                                float relative = clamp((top - worldPosition.y) / heightSpan, 0.0, 1.0);
                                float curve = max(0.0001, fogParams.userFogHeightCurve);
                                heightFog = pow(relative, curve);
                            }

                            float animationFactor = 1.0;
                            if (fogParams.userFogAnimated > 0.5) {
                                vec3 noisePos = worldPosition * 0.001 + vec3(fogParams.userFogTime * fogParams.userFogAnimationSpeed);
                                float noise = sin(noisePos.x * 12.9898 + noisePos.y * 78.233 + noisePos.z * 37.719) * 43758.5453;
                                noise = (sin(noise) + 1.0) * 0.5;
                                animationFactor = 0.8 + 0.4 * noise;
                            }

                            return clamp(linearFog * expFog * heightFog * animationFactor, 0.0, 1.0);
                        }

                        void qt_customMain(inout vec4 color) {
                            vec4 originalColor = color;

                            float fogFactor = calculateFogFactor(worldPos, ubuf.qt_CameraPosition);

                            vec3 scatteredColor = fogParams.userFogColor.rgb * fogParams.userFogScattering;
                            vec3 foggedColor = mix(
                                originalColor.rgb,
                                fogParams.userFogColor.rgb + scatteredColor,
                                fogFactor
                            );

                            if (fogParams.userFogTransmitEnabled > 0.5) {
                                float transmitCurve = max(0.0001, fogParams.userFogTransmitCurve);
                                float transmission = pow(1.0 - fogFactor, transmitCurve);
                                foggedColor = mix(foggedColor, originalColor.rgb, transmission);
                            }

                            color = vec4(foggedColor, originalColor.a) * ubuf.qt_Opacity;
                        }

                        void MAIN() {
                            vec4 color = texture(qt_Texture0, coord);
                            qt_customMain(color);
                            fragColor = color;
                        }
                    "
                }
            ]
        }
    ]

    parameters: [
        Parameter {
            name: "userFogDensity"
            value: fogEffect.fogDensity
        },
        Parameter {
            name: "userFogColor"
            value: fogEffect.fogColor
        },
        Parameter {
            name: "userFogStart"
            value: fogEffect.fogStartDistance
        },
        Parameter {
            name: "userFogEnd"
            value: fogEffect.fogEndDistance
        },
        Parameter {
            name: "userFogLeast"
            value: fogEffect.fogLeastIntenseY
        },
        Parameter {
            name: "userFogMost"
            value: fogEffect.fogMostIntenseY
        },
        Parameter {
            name: "userFogHeightCurve"
            value: fogEffect.fogHeightCurve
        },
        Parameter {
            name: "userFogHeightEnabled"
            value: fogEffect.heightBasedFog ? 1.0 : 0.0
        },
        Parameter {
            name: "userFogScattering"
            value: fogEffect.fogScattering
        },
        Parameter {
            name: "userFogTransmitEnabled"
            value: fogEffect.fogTransmitEnabled ? 1.0 : 0.0
        },
        Parameter {
            name: "userFogTransmitCurve"
            value: fogEffect.fogTransmitCurve
        },
        Parameter {
            name: "userFogAnimated"
            value: fogEffect.animatedFog ? 1.0 : 0.0
        },
        Parameter {
            name: "userFogAnimationSpeed"
            value: fogEffect.animationSpeed
        },
        Parameter {
            name: "userFogTime"
            value: fogEffect.time
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
