import QtQuick
import QtQuick3D
import QtQuick3D.Effects

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
    property real fogScattering: 0.5        // Рассеивание света в тумане
    
    // Анимация тумана
    property bool animatedFog: false        // Анимированный туман
    property real animationSpeed: 0.1       // Скорость анимации
    property real time: 0.0                 // Время для анимации
    
    // Шейдер тумана
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
                        
                        void main() {
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
                            
                            // Fog parameters
                            float fogDensity;
                            vec3 fogColor;
                            float fogStartDistance;
                            float fogEndDistance;
                            float fogHeight;
                            bool heightBasedFog;
                            float fogScattering;
                            bool animatedFog;
                            float animationSpeed;
                            float time;
                        } ubuf;
                        
                        layout(binding = 1) uniform sampler2D qt_Texture0;
                        
                        // Функция расчета тумана
                        float calculateFogFactor(vec3 worldPos, vec3 cameraPos) {
                            float distance = length(worldPos - cameraPos);
                            
                            // Линейный туман по расстоянию
                            float linearFog = clamp(
                                (distance - ubuf.fogStartDistance) / 
                                (ubuf.fogEndDistance - ubuf.fogStartDistance), 
                                0.0, 1.0
                            );
                            
                            // Экспоненциальный туман по плотности
                            float expFog = 1.0 - exp(-ubuf.fogDensity * distance * 0.0001);
                            
                            // Туман на основе высоты
                            float heightFog = 1.0;
                            if (ubuf.heightBasedFog) {
                                float heightFactor = clamp(
                                    (ubuf.fogHeight - worldPos.y) / ubuf.fogHeight, 
                                    0.0, 1.0
                                );
                                heightFog = heightFactor;
                            }
                            
                            // Анимированное возмущение
                            float animationFactor = 1.0;
                            if (ubuf.animatedFog) {
                                vec3 noisePos = worldPos * 0.001 + vec3(ubuf.time * ubuf.animationSpeed);
                                
                                // Простой 3D шум (псевдослучайная функция)
                                float noise = sin(noisePos.x * 12.9898 + noisePos.y * 78.233 + noisePos.z * 37.719) * 43758.5453;
                                noise = (sin(noise) + 1.0) * 0.5;
                                
                                animationFactor = 0.8 + 0.4 * noise;
                            }
                            
                            // Комбинация эффектов
                            return clamp(linearFog * expFog * heightFog * animationFactor, 0.0, 1.0);
                        }
                        
                        void main() {
                            // Исходный цвет из текстуры
                            vec4 originalColor = texture(qt_Texture0, coord);
                            
                            // Расчет фактора тумана
                            float fogFactor = calculateFogFactor(worldPos, ubuf.qt_CameraPosition);
                            
                            // Рассеивание света в тумане
                            vec3 scatteredColor = ubuf.fogColor.rgb * ubuf.fogScattering;
                            
                            // Смешивание с туманом
                            vec3 finalColor = mix(
                                originalColor.rgb, 
                                ubuf.fogColor.rgb + scatteredColor, 
                                fogFactor
                            );
                            
                            fragColor = vec4(finalColor, originalColor.a) * ubuf.qt_Opacity;
                        }
                    "
                }
            ]
            
            // Передача параметров в шейдер
            Buffer {
                id: fogUniformBuffer
                type: Buffer.UniformBuffer
                data: {
                    var buf = new ArrayBuffer(128);
                    var view = new Float32Array(buf);
                    var offset = 0;
                    
                    // Матрицы (уже в базовом буфере)
                    offset += 16 * 4; // 4 матрицы по 16 float
                    
                    // Fog parameters
                    view[offset++] = fogEffect.fogDensity;
                    view[offset++] = fogEffect.fogColor.r;
                    view[offset++] = fogEffect.fogColor.g;
                    view[offset++] = fogEffect.fogColor.b;
                    view[offset++] = fogEffect.fogStartDistance;
                    view[offset++] = fogEffect.fogEndDistance;
                    view[offset++] = fogEffect.fogHeight;
                    view[offset++] = fogEffect.heightBasedFog ? 1.0 : 0.0;
                    view[offset++] = fogEffect.fogScattering;
                    view[offset++] = fogEffect.animatedFog ? 1.0 : 0.0;
                    view[offset++] = fogEffect.animationSpeed;
                    view[offset++] = fogEffect.time;
                    
                    return buf;
                }
            }
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
