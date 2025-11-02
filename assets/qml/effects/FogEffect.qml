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

    function glsl(lines) {
        return lines.join("\n")
    }

    // Используем GLSL 330 core для совместимости с OpenGL 3.3.
    // Qt Quick 3D сам привязывает текстурные юниты, поэтому layout(binding=...)
    // намеренно не применяются.

    Shader {
        id: fogVertexShader
        stage: Shader.Vertex
        readonly property string shaderSource: fogEffect.glsl([
            "#version 330 core",
            "",
            "#ifndef INPUT_POSITION",
            "#define INPUT_POSITION qt_Vertex",
            "#endif",
            "",
            "#ifndef INPUT_UV",
            "#define INPUT_UV qt_MultiTexCoord0",
            "#endif",
            "",
            "layout(location = 0) out vec2 v_uv;",
            "",
            "// layout(binding = 0) опущен: GLSL 330 не поддерживает явные binding для блоков,",
            "// Qt Quick 3D автоматически назначает точки привязки uniform-блоков.",
            "layout(std140) uniform qt_effectUniforms {",
            "    mat4 qt_ModelMatrix;",
            "    mat4 qt_ModelViewProjectionMatrix;",
            "    mat4 qt_ViewMatrix;",
            "    vec3 qt_CameraPosition;",
            "    float qt_Opacity;",
            "} ubuf;",
            "",
            "void MAIN() {",
            "    vec4 localPosition = vec4(INPUT_POSITION, 1.0);",
            "    v_uv = INPUT_UV;",
            "    POSITION = ubuf.qt_ModelViewProjectionMatrix * localPosition;",
            "}"
        ])
        shader: ShaderCode {
            source: fogVertexShader.shaderSource
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
        readonly property string shaderSource: fogEffect.glsl([
            "#version 330 core",
            "",
            "layout(location = 0) in vec2 v_uv;",
            "",
            "#ifndef INPUT_UV",
            "#define INPUT_UV v_uv",
            "#endif",
            "",
            "#ifndef FRAGCOLOR",
            "layout(location = 0) out vec4 qt_FragColor;",
            "#define FRAGCOLOR qt_FragColor",
            "#endif",
            "",
            "uniform sampler2D qt_Texture0;",
            "uniform sampler2D qt_DepthTexture;",
            "// layout(binding = 0) опущен: GLSL 330 не поддерживает явные binding для блоков,",
            "// Qt Quick 3D автоматически назначает точки привязки uniform-блоков.",
            "",
            "#ifndef INPUT",
            "#define INPUT texture(qt_Texture0, INPUT_UV)",
            "#endif",
            "",
            "layout(std140) uniform qt_effectUniforms {",
            "    mat4 qt_ModelMatrix;",
            "    mat4 qt_ModelViewProjectionMatrix;",
            "    mat4 qt_ViewMatrix;",
            "    vec3 qt_CameraPosition;",
            "    float qt_Opacity;",
            "} ubuf;",
            "",
            "#ifndef CAMERA_POSITION",
            "#define CAMERA_POSITION ubuf.qt_CameraPosition",
            "#endif",
            "",
            "#ifndef EFFECT_OPACITY",
            "#define EFFECT_OPACITY ubuf.qt_Opacity",
            "#endif",
            "",
            "uniform float userFogDensity;",
            "uniform float userFogStart;",
            "uniform float userFogEnd;",
            "uniform float userFogLeast;",
            "uniform float userFogMost;",
            "uniform float userFogHeightCurve;",
            "uniform float userFogHeightEnabled;",
            "uniform float userFogScattering;",
            "uniform float userFogTransmitEnabled;",
            "uniform float userFogTransmitCurve;",
            "uniform float userFogAnimated;",
            "uniform float userFogAnimationSpeed;",
            "uniform float userFogTime;",
            "uniform vec4 userFogColor;",
            "uniform float userCameraNear;",
            "uniform float userCameraFar;",
            "uniform float userCameraFov;",
            "uniform float userCameraAspect;",
            "",
            "float linearizeDepth(float depth) {",
            "    float z = depth * 2.0 - 1.0;",
            "    return (2.0 * userCameraNear * userCameraFar) /",
            "           (userCameraFar + userCameraNear - z * (userCameraFar - userCameraNear));",
            "}",
            "",
            "vec3 reconstructWorldPosition(vec2 uv, float linearDepth) {",
            "    float clampedFov = clamp(userCameraFov, 1.0, 179.0);",
            "    float tanHalfFov = tan(radians(clampedFov) * 0.5);",
            "    float aspect = max(userCameraAspect, 0.0001);",
            "    vec2 clip = vec2(uv.x * 2.0 - 1.0, (1.0 - uv.y) * 2.0 - 1.0);",
            "    vec3 viewDir = normalize(vec3(clip.x * tanHalfFov * aspect,",
            "                                  clip.y * tanHalfFov,",
            "                                  -1.0));",
            "    mat3 viewRotation = mat3(ubuf.qt_ViewMatrix);",
            "    mat3 inverseRotation = transpose(viewRotation);",
            "    vec3 worldDir = normalize(inverseRotation * viewDir);",
            "    return CAMERA_POSITION + worldDir * linearDepth;",
            "}",
            "",
            "float computeHeightFactor(vec3 worldPosition) {",
            "    if (userFogHeightEnabled <= 0.5)",
            "        return 1.0;",
            "    float bottom = min(userFogLeast, userFogMost);",
            "    float top = max(userFogLeast, userFogMost);",
            "    float span = max(0.001, top - bottom);",
            "    float relative = clamp((top - worldPosition.y) / span, 0.0, 1.0);",
            "    float curve = max(0.0001, userFogHeightCurve);",
            "    return pow(relative, curve);",
            "}",
            "",
            "float computeAnimatedFactor(vec3 worldPosition) {",
            "    if (userFogAnimated <= 0.5)",
            "        return 1.0;",
            "    vec3 noisePos = worldPosition * 0.001 + vec3(userFogTime * userFogAnimationSpeed);",
            "    float noise = sin(dot(noisePos, vec3(12.9898, 78.233, 37.719)));",
            "    noise = (sin(noise) + 1.0) * 0.5;",
            "    return 0.8 + 0.4 * noise;",
            "}",
            "",
            "void MAIN() {",
            "    vec4 originalColor = INPUT;",
            "    float depth = texture(qt_DepthTexture, INPUT_UV).r;",
            "",
            "    if (depth >= 1.0) {",
            "        FRAGCOLOR = originalColor;",
            "        return;",
            "    }",
            "",
            "    float linearDepth = linearizeDepth(depth);",
            "    vec3 worldPosition = reconstructWorldPosition(INPUT_UV, linearDepth);",
            "",
            "    float span = max(0.001, userFogEnd - userFogStart);",
            "    float distanceFactor = clamp((linearDepth - userFogStart) / span, 0.0, 1.0);",
            "    float densityFactor = 1.0 - exp(-userFogDensity * linearDepth * 0.001);",
            "    float heightFactor = computeHeightFactor(worldPosition);",
            "    float animationFactor = computeAnimatedFactor(worldPosition);",
            "",
            "    float fogFactor = clamp(distanceFactor * densityFactor * heightFactor * animationFactor, 0.0, 1.0);",
            "",
            "    vec3 scatteredColor = userFogColor.rgb * userFogScattering;",
            "    vec3 foggedColor = mix(",
            "        originalColor.rgb,",
            "        userFogColor.rgb + scatteredColor,",
            "        fogFactor",
            "    );",
            "",
            "    if (userFogTransmitEnabled > 0.5) {",
            "        float transmitCurve = max(0.0001, userFogTransmitCurve);",
            "        float transmission = pow(1.0 - fogFactor, transmitCurve);",
            "        foggedColor = mix(foggedColor, originalColor.rgb, transmission);",
            "    }",
            "",
            "    FRAGCOLOR = vec4(foggedColor, originalColor.a) * EFFECT_OPACITY;",
            "}"
        ])
        shader: ShaderCode {
            source: fogFragmentShader.shaderSource
        }
    }

    Shader {
        id: fogFallbackShader
        stage: Shader.Fragment
        property real userFogDensity: fogEffect.fogDensity
        property color userFogColor: fogEffect.fogColor
        readonly property string shaderSource: fogEffect.glsl([
            "#version 330 core",
            "",
            "#ifndef INPUT_UV",
            "#define INPUT_UV v_uv",
            "#endif",
            "",
            "layout(location = 0) in vec2 v_uv;",
            "",
            "#ifndef FRAGCOLOR",
            "layout(location = 0) out vec4 qt_FragColor;",
            "#define FRAGCOLOR qt_FragColor",
            "#endif",
            "",
            "uniform sampler2D qt_Texture0;",
            "",
            "#ifndef INPUT",
            "#define INPUT texture(qt_Texture0, INPUT_UV)",
            "#endif",
            "",
            "uniform float userFogDensity;",
            "uniform vec4 userFogColor;",
            "",
            "void MAIN() {",
            "    vec4 originalColor = INPUT;",
            "    float fogFactor = clamp(userFogDensity, 0.0, 1.0);",
            "    vec3 foggedColor = mix(originalColor.rgb, userFogColor.rgb, fogFactor);",
            "    FRAGCOLOR = vec4(foggedColor, originalColor.a);",
            "}"
        ])
        shader: ShaderCode {
            source: fogFallbackShader.shaderSource
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

    Component.onCompleted: {
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
}
