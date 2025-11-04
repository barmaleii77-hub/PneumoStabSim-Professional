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

void bloomMain(inout vec4 fragColor)
{
    vec4 original = INPUT;

    float lum = luminance(original.rgb);
    vec2 texelSize = 1.0 / vec2(textureSize(qt_Texture0, 0));
    vec3 blurredBright = gaussianBlur(INPUT_UV, texelSize, uBlurAmount);

    vec3 bloom = blurredBright * uIntensity;
    vec3 result = original.rgb + bloom;

    fragColor = vec4(result, original.a);
}

#if QSB_USES_QT_CUSTOM_MAIN
void MAIN(inout vec4 fragColor)
{
    bloomMain(fragColor);
}
#else
void MAIN()
{
    vec4 fragColor = vec4(0.0);
    bloomMain(fragColor);
    FRAGCOLOR = fragColor;
}
#endif
