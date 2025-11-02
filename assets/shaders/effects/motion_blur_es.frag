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
layout(binding = 1) uniform sampler2D qt_VelocityTexture;

#ifndef INPUT
#define INPUT texture(qt_Texture0, INPUT_UV)
#endif

uniform float uStrength;
uniform int uSamples;

void MAIN()
{
    vec4 original = INPUT;
    vec2 velocity = texture(qt_VelocityTexture, INPUT_UV).xy;

    vec3 color = original.rgb;
    int sampleCount = max(uSamples, 1);
    vec2 step = velocity * uStrength / max(1.0, float(sampleCount));

    for (int i = 1; i < sampleCount; i++) {
        vec2 sampleCoord = INPUT_UV + step * float(i);
        color += texture(qt_Texture0, sampleCoord).rgb;
    }

    color /= max(1.0, float(sampleCount));
    FRAGCOLOR = vec4(color, original.a);
}
