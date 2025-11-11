#version 450 core
// Qt Quick 3D post-processing shader.
// Shader logic executes in main() with helper functions for readability.
// Requires GLSL 4.50 core for Qt Quick 3D SPIR-V runtime compatibility.

#ifdef GL_ES
precision highp float;
precision highp int;
precision mediump sampler2D;
#endif

#ifndef SAMPLER_BINDING
#define SAMPLER_BINDING(index) layout(binding = index)
#endif

#ifndef VARYING_UV
#define VARYING_UV v_uv
#endif

#ifndef DECLARE_INPUT_UV
#define DECLARE_INPUT_UV layout(location = 0) in vec2 VARYING_UV;
#endif
DECLARE_INPUT_UV

#ifndef UBO_BINDING
#define UBO_BINDING(index) layout(binding = index)
#endif

#ifndef INPUT_UV
#define INPUT_UV VARYING_UV
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

#ifdef QSB_USE_UNIFORM_BLOCK
layout(std140) UBO_BINDING(10) uniform QsbDofParams {
    float uFocusDistance;
    float uFocusRange;
    float uBlurAmount;
    float uCameraNear;
    float uCameraFar;
};
#else
uniform float uFocusDistance;
uniform float uFocusRange;
uniform float uBlurAmount;
uniform float uCameraNear;
uniform float uCameraFar;
#endif

float linearizeDepth(float depth)
{
    float z = depth * 2.0 - 1.0;
    return (2.0 * uCameraNear * uCameraFar)
        / (uCameraFar + uCameraNear - z * (uCameraFar - uCameraNear));
}

vec3 circularBlur(vec2 uv, float radius)
{
    vec3 color = vec3(0.0);
    int samples = 16;

    for (int i = 0; i < samples; i++) {
        float angle = float(i) * 6.28318 / float(samples);
        vec2 offset = vec2(cos(angle), sin(angle)) * radius;
        color += texture(qt_Texture0, uv + offset).rgb;
    }

    return color / float(samples);
}

void dofMain(inout vec4 fragColor)
{
    vec4 original = INPUT;
    float depth = texture(qt_DepthTexture, INPUT_UV).r;
    float linearDepth = linearizeDepth(depth);

    float focusFactor = abs(linearDepth - uFocusDistance) / max(0.0001, uFocusRange);
    float blurRadius = clamp(focusFactor, 0.0, 1.0) * uBlurAmount * 0.01;

    vec3 blurred = circularBlur(INPUT_UV, blurRadius);
    vec3 result = mix(original.rgb, blurred, clamp(focusFactor, 0.0, 1.0));

    fragColor = vec4(result, original.a);
}

void main()
{
    vec4 fragColor = vec4(0.0);
    dofMain(fragColor);
    FRAGCOLOR = fragColor;
}
