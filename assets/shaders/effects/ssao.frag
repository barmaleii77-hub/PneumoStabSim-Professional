#version 450 core
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

#ifndef MAIN
#define MAIN main
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

void MAIN()
{
    vec4 original = INPUT;
    vec3 normal = normalize(texture(qt_NormalTexture, INPUT_UV).xyz * 2.0 - 1.0);
    float depth = texture(qt_DepthTexture, INPUT_UV).r;

    if (depth >= 1.0) {
        FRAGCOLOR = original;
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

    FRAGCOLOR = vec4(original.rgb * occlusion, original.a);
}
