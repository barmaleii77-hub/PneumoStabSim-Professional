#version 300 es
// Qt Quick 3D post-processing shader.
// Shader logic must live in qt_customMain; a thin main() wrapper is appended for shader tooling compatibility.
// Requires an OpenGL ES 3.0 context for Qt Quick 3D runtime compatibility.

#ifdef GL_ES
precision highp float;
precision highp int;
precision highp sampler2D;
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
    float uDitherToggle;
    int uSamples;
};
#else
uniform float uIntensity;
uniform float uRadius;
uniform float uBias;
uniform float uDitherToggle;
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

float randomValue(vec2 co)
{
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
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

        vec2 offset = sampleVec.xy * uRadius;
        if (uDitherToggle > 0.5) {
            vec2 noiseSeed = INPUT_UV * 2048.0 + vec2(float(i), float(sampleCount));
            vec2 jitter = vec2(
                randomValue(noiseSeed + 0.12345),
                randomValue(noiseSeed.yx + 0.98765)
            ) - 0.5;
            offset += jitter * uRadius * 0.35;
        }

        vec2 sampleCoord = INPUT_UV + offset * texelSize;
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

void qt_customMain()
{
    vec4 fragColor = vec4(0.0);
    ssaoESMain(fragColor);
    FRAGCOLOR = fragColor;
}

void main()
{
    qt_customMain();
}
