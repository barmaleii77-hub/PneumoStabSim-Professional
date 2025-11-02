#version 330 core

layout(location = 0) in vec2 v_uv;

#ifndef INPUT_UV
#define INPUT_UV v_uv
#endif

#ifndef FRAGCOLOR
layout(location = 0) out vec4 qt_FragColor;
#define FRAGCOLOR qt_FragColor
#endif

layout(binding = 0) uniform sampler2D qt_Texture0;
layout(binding = 1) uniform sampler2D qt_DepthTexture;

#ifndef INPUT
#define INPUT texture(qt_Texture0, INPUT_UV)
#endif

layout(std140) uniform qt_effectUniforms {
    mat4 qt_ModelMatrix;
    mat4 qt_ModelViewProjectionMatrix;
    mat4 qt_ViewMatrix;
    vec3 qt_CameraPosition;
    float qt_Opacity;
} ubuf;

#ifndef CAMERA_POSITION
#define CAMERA_POSITION ubuf.qt_CameraPosition
#endif

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

    mat4 invView = inverse(ubuf.qt_ViewMatrix);
    vec4 worldPos = invView * vec4(viewPos, 1.0);
    return worldPos.xyz / worldPos.w;
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

void MAIN()
{
    vec4 original = INPUT;
    float depth = texture(qt_DepthTexture, INPUT_UV).r;

    if (depth >= 1.0) {
        FRAGCOLOR = original;
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

    FRAGCOLOR = vec4(result, original.a);
}
