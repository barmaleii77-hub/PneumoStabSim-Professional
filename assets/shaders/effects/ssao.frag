#version 330 core

#ifndef INPUT_UV
#define INPUT_UV v_uv
#endif

#ifndef FRAGCOLOR
layout(location = 0) out vec4 qt_FragColor;
#define FRAGCOLOR qt_FragColor
#endif

layout(binding = 0) uniform sampler2D qt_Texture0;
layout(binding = 1) uniform sampler2D qt_DepthTexture;
layout(binding = 2) uniform sampler2D qt_NormalTexture;

#ifndef INPUT
#define INPUT texture(qt_Texture0, INPUT_UV)
#endif

uniform float uIntensity;
uniform float uRadius;
uniform float uBias;
uniform int uSamples;

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
        if (dot(sampleVec, normal) < 0.0)
            sampleVec = -sampleVec;

        vec2 sampleCoord = INPUT_UV + sampleVec.xy * uRadius * texelSize;
        float sampleDepth = texture(qt_DepthTexture, sampleCoord).r;

        float depthDiff = depth - sampleDepth;
        if (depthDiff > uBias)
            occlusion += 1.0;
    }

    occlusion /= max(1.0, float(sampleCount));
    occlusion = 1.0 - (occlusion * uIntensity);

    FRAGCOLOR = vec4(original.rgb * occlusion, original.a);
}
