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

#ifndef VARYING_UV
#define VARYING_UV v_uv
#endif

#ifndef SAMPLER_BINDING
#if defined(GL_ES)
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define SAMPLER_BINDING(index)
#else
#define SAMPLER_BINDING(index) layout(binding = index)
#endif
#endif

#ifndef DECLARE_INPUT_UV
#if defined(GL_ES)
#define DECLARE_INPUT_UV in vec2 VARYING_UV;
#else
#define DECLARE_INPUT_UV layout(location = 0) in vec2 VARYING_UV;
#endif
#endif
DECLARE_INPUT_UV

#ifndef UBO_BINDING
#if defined(GL_ES)
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#else
#define UBO_BINDING(index) layout(binding = index)
#endif
#endif

#ifndef INPUT_UV
#define INPUT_UV VARYING_UV
#endif

#ifndef FRAGCOLOR
layout(location = 0) out vec4 qt_FragColor;
#define FRAGCOLOR qt_FragColor
#endif

SAMPLER_BINDING(0) uniform sampler2D qt_Texture0;

#ifndef INPUT
#define INPUT texture(qt_Texture0, INPUT_UV)
#endif

#ifdef QSB_USE_UNIFORM_BLOCK
layout(std140) UBO_BINDING(10) uniform QsbBloomParams {
    float uIntensity;
    float uThreshold;
    float uBlurAmount;
};
#else
uniform float uIntensity;
uniform float uThreshold;
uniform float uBlurAmount;
#endif

float luminance(vec3 color)
{
    return dot(color, vec3(0.299, 0.587, 0.114));
}

vec3 gaussianBlur(vec2 uv, vec2 texelStep, float blurSize)
{
    vec3 color = vec3(0.0);

    float weights[9] = float[](
        0.05, 0.09, 0.12,
        0.15, 0.18, 0.15,
        0.12, 0.09, 0.05
    );

    for (int i = -4; i <= 4; i++) {
        vec2 offset = texelStep * float(i) * blurSize * 0.01;
        color += texture(qt_Texture0, uv + offset).rgb * weights[i + 4];
    }

    return color;
}

void bloomESMain(inout vec4 fragColor)
{
    vec4 original = INPUT;

    float lum = luminance(original.rgb);
    vec2 texelSize = 1.0 / vec2(textureSize(qt_Texture0, 0));
    vec3 blurredBright = gaussianBlur(INPUT_UV, texelSize, uBlurAmount);

    vec3 bloom = blurredBright * uIntensity;
    vec3 result = original.rgb + bloom;

    fragColor = vec4(result, original.a);
}

void qt_customMain()
{
    vec4 fragColor = vec4(0.0);
    bloomESMain(fragColor);
    FRAGCOLOR = fragColor;
}
