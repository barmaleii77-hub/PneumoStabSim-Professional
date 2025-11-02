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

layout(binding = 0) uniform sampler2D qt_Texture0;
layout(binding = 1) uniform sampler2D qt_DepthTexture;

#ifndef INPUT
#define INPUT texture(qt_Texture0, INPUT_UV)
#endif

uniform float uFocusDistance;
uniform float uFocusRange;
uniform float uBlurAmount;
uniform float uCameraNear;
uniform float uCameraFar;

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

void MAIN()
{
    vec4 original = INPUT;
    float depth = texture(qt_DepthTexture, INPUT_UV).r;
    float linearDepth = linearizeDepth(depth);

    float focusFactor = abs(linearDepth - uFocusDistance) / max(0.0001, uFocusRange);
    float blurRadius = clamp(focusFactor, 0.0, 1.0) * uBlurAmount * 0.01;

    vec3 blurred = circularBlur(INPUT_UV, blurRadius);
    vec3 result = mix(original.rgb, blurred, clamp(focusFactor, 0.0, 1.0));

    FRAGCOLOR = vec4(result, original.a);
}
