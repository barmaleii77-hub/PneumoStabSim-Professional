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
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define SAMPLER_BINDING(index)
#else
#define SAMPLER_BINDING(index) layout(binding = index)
#endif
#else
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define SAMPLER_BINDING(index)
#endif
#endif

#ifdef QSB_ADD_BINDINGS
#ifdef GL_ES
in vec2 v_uv;
#else
layout(location = 0) in vec2 v_uv;
#endif
#else
in vec2 v_uv;
#endif

#ifndef UBO_BINDING
#ifdef QSB_ADD_BINDINGS
#ifdef GL_ES
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#else
#define UBO_BINDING(index) layout(binding = index)
#endif
#else
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#endif
#endif

#ifndef INPUT_UV
#define INPUT_UV v_uv
#endif

#ifndef MAIN
#define MAIN qt_customMain
#endif

#ifndef FRAGCOLOR
layout(location = 0) out vec4 qt_FragColor;
#define FRAGCOLOR qt_FragColor
#endif

SAMPLER_BINDING(0) uniform sampler2D qt_Texture0;
SAMPLER_BINDING(1) uniform sampler2D qt_DepthTexture;
SAMPLER_BINDING(2) uniform sampler2D qt_NormalTexture;

#ifndef INPUT
#define INPUT texture(qt_Texture0, INPUT_UV)
#endif

#ifdef QSB_USE_UNIFORM_BLOCK
layout(std140) UBO_BINDING(10) uniform QsbSsaoParams {
    float uIntensity;
    float uRadius;
    float uBias;
    int uSamples;
};
#else
uniform float uIntensity;
uniform float uRadius;
uniform float uBias;
uniform int uSamples;
#endif

vec3 generateSampleVector(int index)
{
    float angle = float(index) * 0.39269908;
    float radius = float(index + 1) / max(1.0, float(uSamples));

    return vec3(
        cos(angle) * radius,
        sin(angle) * radius,
        radius * 0.5 + 0.5
    );
}

void ssaoESMain(inout vec4 fragColor)
{
    vec4 original = INPUT;
    vec3 normal = normalize(texture(qt_NormalTexture, INPUT_UV).xyz * 2.0 - 1.0);
    float depth = texture(qt_DepthTexture, INPUT_UV).r;

    if (depth >= 1.0) {
        fragColor = original;
        return;
    }

    float occlusion = 0.0;
    vec2 texelSize = 1.0 / vec2(textureSize(qt_Texture0, 0));
    int sampleCount = max(uSamples, 1);

    for (int i = 0; i < sampleCount; i++) {
        vec3 sampleVec = normalize(generateSampleVector(i));
        if (dot(sampleVec, normal) < 0.0) {
            sampleVec = -sampleVec;
        }

        vec2 sampleCoord = INPUT_UV + sampleVec.xy * uRadius * texelSize;
        float sampleDepth = texture(qt_DepthTexture, sampleCoord).r;

        float depthDiff = depth - sampleDepth;
        if (depthDiff > uBias) {
            occlusion += 1.0;
        }
    }

    occlusion /= max(1.0, float(sampleCount));
    occlusion = 1.0 - (occlusion * uIntensity);

    fragColor = vec4(original.rgb * occlusion, original.a);
}

void MAIN()
{
    vec4 fragColor = vec4(0.0);
    ssaoESMain(fragColor);
    FRAGCOLOR = fragColor;
}

void MAIN(inout vec4 fragColor)
{
    ssaoESMain(fragColor);
}
