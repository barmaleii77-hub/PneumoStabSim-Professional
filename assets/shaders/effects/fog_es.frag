#version 300 es
// Requires an OpenGL ES 3.0 context for Qt Quick 3D runtime compatibility.

#ifdef GL_ES
precision highp float;
precision highp int;
precision mediump sampler2D;
#endif

#ifdef QSB_ADD_BINDINGS
#ifndef GL_ES
#extension GL_ARB_shading_language_420pack : enable
#extension GL_ARB_separate_shader_objects : enable
#endif
#endif



#ifndef SAMPLER_BINDING
#ifdef QSB_ADD_BINDINGS
#ifdef GL_ES
// GLSL 330 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define SAMPLER_BINDING(index)
#else
#define SAMPLER_BINDING(index) layout(binding = index)
#endif
#else
// GLSL 330 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define SAMPLER_BINDING(index)
#endif
#endif

#ifndef UBO_BINDING
#ifdef QSB_ADD_BINDINGS
#ifdef GL_ES
// GLSL 330 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#else
#define UBO_BINDING(index) layout(binding = index)
#endif
#else
// GLSL 330 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#endif
#endif

layout(location = 0) in vec2 v_uv;

#ifndef INPUT_UV
#define INPUT_UV v_uv
#endif

#ifndef MAIN
#define MAIN qt_customMain
#define QSB_USES_QT_CUSTOM_MAIN 1
#endif

#ifndef QSB_USES_QT_CUSTOM_MAIN
#define QSB_USES_QT_CUSTOM_MAIN 0
#endif

#ifndef FRAGCOLOR
layout(location = 0) out vec4 qt_FragColor;
#define FRAGCOLOR qt_FragColor
#endif

SAMPLER_BINDING(0) uniform sampler2D qt_Texture0;
SAMPLER_BINDING(1) uniform sampler2D qt_DepthTexture;

#ifndef INPUT
#define INPUT texture(qt_Texture0, INPUT_UV)
#endif

layout(std140) UBO_BINDING(0) uniform qt_effectUniforms {
    mat4 qt_ModelMatrix;
    mat4 qt_ModelViewProjectionMatrix;
    mat4 qt_ViewMatrix;
    vec3 qt_CameraPosition;
    float qt_Opacity;
} ubuf;

#ifndef CAMERA_POSITION
#define CAMERA_POSITION ubuf.qt_CameraPosition
#endif

#ifdef QSB_USE_UNIFORM_BLOCK
layout(std140) UBO_BINDING(10) uniform QsbFogParams {
    float userFogDensity;
    vec3 userFogColor;
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
    float userCameraNear;
    float userCameraFar;
    float userCameraFov;
    float userCameraAspect;
};
#else
uniform float userFogDensity;
uniform vec3 userFogColor;
uniform float userFogStart;
uniform float userFogEnd;
uniform float userFogLeast;
uniform float userFogMost;
uniform float userFogHeightCurve;
uniform float userFogHeightEnabled;
uniform float userFogScattering;
uniform float userFogTransmitEnabled;
uniform float userFogTransmitCurve;
uniform float userFogAnimated;
uniform float userFogAnimationSpeed;
uniform float userFogTime;
uniform float userCameraNear;
uniform float userCameraFar;
uniform float userCameraFov;
uniform float userCameraAspect;
#endif

float computeHeightFactor(float worldY)
{
    if (userFogHeightEnabled < 0.5)
        return 1.0;

    float heightRange = userFogMost - userFogLeast;
    if (abs(heightRange) < 0.0001)
        return 1.0;

    float normalized = clamp((worldY - userFogLeast) / heightRange, 0.0, 1.0);
    return pow(normalized, max(0.1, userFogHeightCurve));
}

float computeTransmit(float fogFactor)
{
    if (userFogTransmitEnabled < 0.5)
        return 1.0;

    float transmit = pow(1.0 - fogFactor, max(0.1, userFogTransmitCurve));
    return mix(1.0, transmit, userFogTransmitEnabled);
}

float linearizeDepth(float depth)
{
    float z = depth * 2.0 - 1.0;
    return (2.0 * userCameraNear * userCameraFar)
           / (userCameraFar + userCameraNear - z * (userCameraFar - userCameraNear));
}

vec3 reconstructWorldPosition(vec2 uv, float depth)
{
    float fov = radians(userCameraFov);
    float tanHalfFov = tan(fov / 2.0);
    vec2 ndc = uv * 2.0 - 1.0;
    vec3 ray = vec3(ndc.x * tanHalfFov * userCameraAspect,
                    ndc.y * tanHalfFov,
                    -1.0);
    ray = normalize(ray);
    float linearDepth = linearizeDepth(depth);
    vec3 viewPos = ray * linearDepth;

    mat3 viewRotation = mat3(ubuf.qt_ViewMatrix);
    vec3 worldOffset = transpose(viewRotation) * viewPos;
    return CAMERA_POSITION + worldOffset;
}

float computeFogFactor(float distance)
{
    float fogRange = max(0.001, userFogEnd - userFogStart);
    float factor = clamp((distance - userFogStart) / fogRange, 0.0, 1.0);
    return 1.0 - exp(-pow(factor, 1.5) * userFogDensity * 4.0);
}

vec3 animateFog(vec3 color, vec3 worldPos)
{
    if (userFogAnimated < 0.5)
        return color;

    float wave = sin(worldPos.x * 0.1 + userFogTime * userFogAnimationSpeed)
                 * cos(worldPos.z * 0.1 + userFogTime * userFogAnimationSpeed);
    float modulation = 0.5 + 0.5 * wave;
    return mix(color, color * (0.7 + 0.3 * modulation), 0.5);
}

vec3 applyScattering(vec3 fogColor, vec3 sceneColor, float fogFactor, vec3 normal)
{
    vec3 lightDir = normalize(vec3(0.2, 0.7, 0.3));
    float phase = max(dot(normal, lightDir), 0.0);
    float scattering = mix(0.2, 1.0, phase) * userFogScattering;
    return mix(sceneColor, fogColor * scattering, fogFactor);
}

void fogESMain(inout vec4 fragColor)
{
    vec4 original = INPUT;
    float depth = texture(qt_DepthTexture, INPUT_UV).r;

    if (depth >= 1.0) {
        fragColor = original;
        return;
    }

    vec3 worldPos = reconstructWorldPosition(INPUT_UV, depth);
    float distance = length(worldPos - CAMERA_POSITION);
    float fogFactor = computeFogFactor(distance);

    float heightFactor = computeHeightFactor(worldPos.y);
    fogFactor *= heightFactor;

    vec3 fogColor = userFogColor.rgb;
    fogColor = animateFog(fogColor, worldPos);

    vec3 normal = vec3(0.0, 1.0, 0.0);
    vec3 result = applyScattering(fogColor, original.rgb, fogFactor, normal);

    float transmit = computeTransmit(fogFactor);
    result = mix(result, original.rgb, transmit * (1.0 - fogFactor));

    fragColor = vec4(result, original.a);
}

#if QSB_USES_QT_CUSTOM_MAIN
void MAIN(inout vec4 fragColor)
{
    fogESMain(fragColor);
}
#else
void MAIN()
{
    vec4 fragColor = vec4(0.0);
    fogESMain(fragColor);
    FRAGCOLOR = fragColor;
}
#endif
