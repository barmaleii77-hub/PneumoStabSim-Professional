#version 300 es
precision highp float;
precision highp int;
precision mediump sampler2D;

#ifndef INPUT_UV
#define INPUT_UV v_uv
#endif

#ifndef FRAGCOLOR
layout(location = 0) out vec4 qt_FragColor;
#define FRAGCOLOR qt_FragColor
#endif

uniform sampler2D qt_Texture0;

#ifndef INPUT
#define INPUT texture(qt_Texture0, INPUT_UV)
#endif

uniform float uIntensity;
uniform float uThreshold;
uniform float uBlurAmount;

float luminance(vec3 color)
{
    return dot(color, vec3(0.299, 0.587, 0.114));
}

vec3 gaussianBlur(vec2 uv, vec2 texelStep, float blurSize)
{
    vec3 color = vec3(0.0);

    float weights[9] = float[](0.05, 0.09, 0.12, 0.15, 0.18, 0.15, 0.12, 0.09, 0.05);

    for (int i = -4; i <= 4; i++) {
        vec2 offset = texelStep * float(i) * blurSize * 0.01;
        color += texture(qt_Texture0, uv + offset).rgb * weights[i + 4];
    }

    return color;
}

void MAIN()
{
    vec4 original = INPUT;

    float lum = luminance(original.rgb);
    vec2 texelSize = 1.0 / vec2(textureSize(qt_Texture0, 0));
    vec3 blurredBright = gaussianBlur(INPUT_UV, texelSize, uBlurAmount);

    vec3 bloom = blurredBright * uIntensity;
    vec3 result = original.rgb + bloom;

    FRAGCOLOR = vec4(result, original.a);
}
