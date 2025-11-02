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
            if (dotIndex > 0)
                normalized = normalized.slice(0, dotIndex) + "_es" + normalized.slice(dotIndex)
            else
                normalized = normalized + "_es"
        }

        return Qt.resolvedUrl("../../shaders/effects/" + normalized)
    }

    // Используем GLSL 330 core на OpenGL и GLSL 300 es в контекстах OpenGL ES.
    // Текстурные юниты привязываются явно через layout(binding=...), чтобы
    // избежать автоматических префиксов Qt перед директивой #version.

    Shader {
        id: fogVertexShader
        stage: Shader.Vertex
        autoInsertHeader: false
        shader: fogEffect.shaderPath("fog.vert")
    }

    Shader {
        id: fogFragmentShader
        stage: Shader.Fragment
        autoInsertHeader: false
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
        shader: fogEffect.shaderPath("fog.frag")
    }

    Shader {
        id: fogFallbackShader
        stage: Shader.Fragment
        autoInsertHeader: false
        property real userFogDensity: fogEffect.fogDensity
        property color userFogColor: fogEffect.fogColor
        shader: fogEffect.shaderPath("fog_fallback.frag")
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
        console.log("🌫️ FogEffect graphics API:", rendererGraphicsApi)
        console.log(
                    "   Shader profile:",
                    useGlesShaders
                    ? "OpenGL ES (GLSL 300 es)"
                    : "Desktop (GLSL 330 core)"
                    )
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
